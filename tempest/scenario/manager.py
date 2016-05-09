# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import subprocess

import netaddr
from oslo_log import log
from oslo_serialization import jsonutils as json
import six

from tempest.common import compute
from tempest.common.utils import data_utils
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest import exceptions
from tempest.lib.common.utils import misc as misc_utils
from tempest.lib import exceptions as lib_exc
from tempest.scenario import network_resources
import tempest.test

CONF = config.CONF

LOG = log.getLogger(__name__)


class ScenarioTest(tempest.test.BaseTestCase):
    """Base class for scenario tests. Uses tempest own clients. """

    credentials = ['primary']

    @classmethod
    def setup_clients(cls):
        super(ScenarioTest, cls).setup_clients()
        # Clients (in alphabetical order)
        cls.flavors_client = cls.manager.flavors_client
        cls.compute_floating_ips_client = (
            cls.manager.compute_floating_ips_client)
        if CONF.service_available.glance:
            # Glance image client v1
            cls.image_client = cls.manager.image_client
        # Compute image client
        cls.compute_images_client = cls.manager.compute_images_client
        cls.keypairs_client = cls.manager.keypairs_client
        # Nova security groups client
        cls.compute_security_groups_client = (
            cls.manager.compute_security_groups_client)
        cls.compute_security_group_rules_client = (
            cls.manager.compute_security_group_rules_client)
        cls.servers_client = cls.manager.servers_client
        cls.interface_client = cls.manager.interfaces_client
        # Neutron network client
        cls.networks_client = cls.manager.networks_client
        cls.ports_client = cls.manager.ports_client
        cls.routers_client = cls.manager.routers_client
        cls.subnets_client = cls.manager.subnets_client
        cls.floating_ips_client = cls.manager.floating_ips_client
        cls.security_groups_client = cls.manager.security_groups_client
        cls.security_group_rules_client = (
            cls.manager.security_group_rules_client)
        # Heat client
        cls.orchestration_client = cls.manager.orchestration_client

        if CONF.volume_feature_enabled.api_v1:
            cls.volumes_client = cls.manager.volumes_client
            cls.snapshots_client = cls.manager.snapshots_client
        else:
            cls.volumes_client = cls.manager.volumes_v2_client
            cls.snapshots_client = cls.manager.snapshots_v2_client

    # ## Methods to handle sync and async deletes

    def setUp(self):
        super(ScenarioTest, self).setUp()
        self.cleanup_waits = []
        # NOTE(mtreinish) This is safe to do in setUp instead of setUp class
        # because scenario tests in the same test class should not share
        # resources. If resources were shared between test cases then it
        # should be a single scenario test instead of multiples.

        # NOTE(yfried): this list is cleaned at the end of test_methods and
        # not at the end of the class
        self.addCleanup(self._wait_for_cleanups)

    def delete_wrapper(self, delete_thing, *args, **kwargs):
        """Ignores NotFound exceptions for delete operations.

        @param delete_thing: delete method of a resource. method will be
            executed as delete_thing(*args, **kwargs)

        """
        try:
            # Tempest clients return dicts, so there is no common delete
            # method available. Using a callable instead
            delete_thing(*args, **kwargs)
        except lib_exc.NotFound:
            # If the resource is already missing, mission accomplished.
            pass

    def addCleanup_with_wait(self, waiter_callable, thing_id, thing_id_param,
                             cleanup_callable, cleanup_args=None,
                             cleanup_kwargs=None, waiter_client=None):
        """Adds wait for async resource deletion at the end of cleanups

        @param waiter_callable: callable to wait for the resource to delete
            with the following waiter_client if specified.
        @param thing_id: the id of the resource to be cleaned-up
        @param thing_id_param: the name of the id param in the waiter
        @param cleanup_callable: method to load pass to self.addCleanup with
            the following *cleanup_args, **cleanup_kwargs.
            usually a delete method.
        """
        if cleanup_args is None:
            cleanup_args = []
        if cleanup_kwargs is None:
            cleanup_kwargs = {}
        self.addCleanup(cleanup_callable, *cleanup_args, **cleanup_kwargs)
        wait_dict = {
            'waiter_callable': waiter_callable,
            thing_id_param: thing_id
        }
        if waiter_client:
            wait_dict['client'] = waiter_client
        self.cleanup_waits.append(wait_dict)

    def _wait_for_cleanups(self):
        # To handle async delete actions, a list of waits is added
        # which will be iterated over as the last step of clearing the
        # cleanup queue. That way all the delete calls are made up front
        # and the tests won't succeed unless the deletes are eventually
        # successful. This is the same basic approach used in the api tests to
        # limit cleanup execution time except here it is multi-resource,
        # because of the nature of the scenario tests.
        for wait in self.cleanup_waits:
            waiter_callable = wait.pop('waiter_callable')
            waiter_callable(**wait)

    # ## Test functions library
    #
    # The create_[resource] functions only return body and discard the
    # resp part which is not used in scenario tests

    def create_keypair(self, client=None):
        if not client:
            client = self.keypairs_client
        name = data_utils.rand_name(self.__class__.__name__)
        # We don't need to create a keypair by pubkey in scenario
        body = client.create_keypair(name=name)
        self.addCleanup(client.delete_keypair, name)
        return body['keypair']

    def create_server(self, name=None, image_id=None, flavor=None,
                      validatable=False, wait_until=None,
                      wait_on_delete=True, clients=None, **kwargs):
        """Wrapper utility that returns a test server.

        This wrapper utility calls the common create test server and
        returns a test server. The purpose of this wrapper is to minimize
        the impact on the code of the tests already using this
        function.
        """

        # NOTE(jlanoux): As a first step, ssh checks in the scenario
        # tests need to be run regardless of the run_validation and
        # validatable parameters and thus until the ssh validation job
        # becomes voting in CI. The test resources management and IP
        # association are taken care of in the scenario tests.
        # Therefore, the validatable parameter is set to false in all
        # those tests. In this way create_server just return a standard
        # server and the scenario tests always perform ssh checks.

        # Needed for the cross_tenant_traffic test:
        if clients is None:
            clients = self.manager

        vnic_type = CONF.network.port_vnic_type

        # If vnic_type is configured create port for
        # every network
        if vnic_type:
            ports = []
            networks = []
            create_port_body = {'binding:vnic_type': vnic_type,
                                'namestart': 'port-smoke'}
            if kwargs:
                # Convert security group names to security group ids
                # to pass to create_port
                if 'security_groups' in kwargs:
                    security_groups =\
                        clients.security_groups_client.list_security_groups(
                        ).get('security_groups')
                    sec_dict = dict([(s['name'], s['id'])
                                    for s in security_groups])

                    sec_groups_names = [s['name'] for s in kwargs.pop(
                        'security_groups')]
                    security_groups_ids = [sec_dict[s]
                                           for s in sec_groups_names]

                    if security_groups_ids:
                        create_port_body[
                            'security_groups'] = security_groups_ids
                networks = kwargs.pop('networks')

            # If there are no networks passed to us we look up
            # for the project's private networks and create a port
            # if there is only one private network. The same behaviour
            # as we would expect when passing the call to the clients
            # with no networks
            if not networks:
                networks = clients.networks_client.list_networks(
                    filters={'router:external': False})
                self.assertEqual(1, len(networks),
                                 "There is more than one"
                                 " network for the tenant")
            for net in networks:
                net_id = net['uuid']
                port = self._create_port(network_id=net_id,
                                         client=clients.ports_client,
                                         **create_port_body)
                ports.append({'port': port.id})
            if ports:
                kwargs['networks'] = ports
            self.ports = ports

        tenant_network = self.get_tenant_network()

        body, servers = compute.create_test_server(
            clients,
            tenant_network=tenant_network,
            wait_until=wait_until,
            name=name, flavor=flavor,
            image_id=image_id, **kwargs)

        # TODO(jlanoux) Move wait_on_delete in compute.py
        if wait_on_delete:
            self.addCleanup(waiters.wait_for_server_termination,
                            clients.servers_client,
                            body['id'])

        self.addCleanup_with_wait(
            waiter_callable=waiters.wait_for_server_termination,
            thing_id=body['id'], thing_id_param='server_id',
            cleanup_callable=self.delete_wrapper,
            cleanup_args=[clients.servers_client.delete_server, body['id']],
            waiter_client=clients.servers_client)
        server = clients.servers_client.show_server(body['id'])['server']
        return server

    def create_volume(self, size=None, name=None, snapshot_id=None,
                      imageRef=None, volume_type=None):
        if name is None:
            name = data_utils.rand_name(self.__class__.__name__)
        kwargs = {'display_name': name,
                  'snapshot_id': snapshot_id,
                  'imageRef': imageRef,
                  'volume_type': volume_type}
        if size is not None:
            kwargs.update({'size': size})
        volume = self.volumes_client.create_volume(**kwargs)['volume']

        self.addCleanup(self.volumes_client.wait_for_resource_deletion,
                        volume['id'])
        self.addCleanup(self.delete_wrapper,
                        self.volumes_client.delete_volume, volume['id'])

        # NOTE(e0ne): Cinder API v2 uses name instead of display_name
        if 'display_name' in volume:
            self.assertEqual(name, volume['display_name'])
        else:
            self.assertEqual(name, volume['name'])
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume['id'], 'available')
        # The volume retrieved on creation has a non-up-to-date status.
        # Retrieval after it becomes active ensures correct details.
        volume = self.volumes_client.show_volume(volume['id'])['volume']
        return volume

    def _create_loginable_secgroup_rule(self, secgroup_id=None):
        _client = self.compute_security_groups_client
        _client_rules = self.compute_security_group_rules_client
        if secgroup_id is None:
            sgs = _client.list_security_groups()['security_groups']
            for sg in sgs:
                if sg['name'] == 'default':
                    secgroup_id = sg['id']

        # These rules are intended to permit inbound ssh and icmp
        # traffic from all sources, so no group_id is provided.
        # Setting a group_id would only permit traffic from ports
        # belonging to the same security group.
        rulesets = [
            {
                # ssh
                'ip_protocol': 'tcp',
                'from_port': 22,
                'to_port': 22,
                'cidr': '0.0.0.0/0',
            },
            {
                # ping
                'ip_protocol': 'icmp',
                'from_port': -1,
                'to_port': -1,
                'cidr': '0.0.0.0/0',
            }
        ]
        rules = list()
        for ruleset in rulesets:
            sg_rule = _client_rules.create_security_group_rule(
                parent_group_id=secgroup_id, **ruleset)['security_group_rule']
            rules.append(sg_rule)
        return rules

    def _create_security_group(self):
        # Create security group
        sg_name = data_utils.rand_name(self.__class__.__name__)
        sg_desc = sg_name + " description"
        secgroup = self.compute_security_groups_client.create_security_group(
            name=sg_name, description=sg_desc)['security_group']
        self.assertEqual(secgroup['name'], sg_name)
        self.assertEqual(secgroup['description'], sg_desc)
        self.addCleanup(
            self.delete_wrapper,
            self.compute_security_groups_client.delete_security_group,
            secgroup['id'])

        # Add rules to the security group
        self._create_loginable_secgroup_rule(secgroup['id'])

        return secgroup

    def get_remote_client(self, ip_address, username=None, private_key=None):
        """Get a SSH client to a remote server

        @param ip_address the server floating or fixed IP address to use
                          for ssh validation
        @param username name of the Linux account on the remote server
        @param private_key the SSH private key to use
        @return a RemoteClient object
        """

        if username is None:
            username = CONF.validation.image_ssh_user
        # Set this with 'keypair' or others to log in with keypair or
        # username/password.
        if CONF.validation.auth_method == 'keypair':
            password = None
            if private_key is None:
                private_key = self.keypair['private_key']
        else:
            password = CONF.validation.image_ssh_password
            private_key = None
        linux_client = remote_client.RemoteClient(ip_address, username,
                                                  pkey=private_key,
                                                  password=password)
        try:
            linux_client.validate_authentication()
        except Exception as e:
            message = ('Initializing SSH connection to %(ip)s failed. '
                       'Error: %(error)s' % {'ip': ip_address,
                                             'error': e})
            caller = misc_utils.find_test_caller()
            if caller:
                message = '(%s) %s' % (caller, message)
            LOG.exception(message)
            self._log_console_output()
            raise

        return linux_client

    def _image_create(self, name, fmt, path,
                      disk_format=None, properties=None):
        if properties is None:
            properties = {}
        name = data_utils.rand_name('%s-' % name)
        params = {
            'name': name,
            'container_format': fmt,
            'disk_format': disk_format or fmt,
            'is_public': 'False',
        }
        params['properties'] = properties
        image = self.image_client.create_image(**params)['image']
        self.addCleanup(self.image_client.delete_image, image['id'])
        self.assertEqual("queued", image['status'])
        with open(path, 'rb') as image_file:
            self.image_client.update_image(image['id'], data=image_file)
        return image['id']

    def glance_image_create(self):
        img_path = CONF.scenario.img_dir + "/" + CONF.scenario.img_file
        aki_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.aki_img_file
        ari_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.ari_img_file
        ami_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.ami_img_file
        img_container_format = CONF.scenario.img_container_format
        img_disk_format = CONF.scenario.img_disk_format
        img_properties = CONF.scenario.img_properties
        LOG.debug("paths: img: %s, container_fomat: %s, disk_format: %s, "
                  "properties: %s, ami: %s, ari: %s, aki: %s" %
                  (img_path, img_container_format, img_disk_format,
                   img_properties, ami_img_path, ari_img_path, aki_img_path))
        try:
            image = self._image_create('scenario-img',
                                       img_container_format,
                                       img_path,
                                       disk_format=img_disk_format,
                                       properties=img_properties)
        except IOError:
            LOG.debug("A qcow2 image was not found. Try to get a uec image.")
            kernel = self._image_create('scenario-aki', 'aki', aki_img_path)
            ramdisk = self._image_create('scenario-ari', 'ari', ari_img_path)
            properties = {'kernel_id': kernel, 'ramdisk_id': ramdisk}
            image = self._image_create('scenario-ami', 'ami',
                                       path=ami_img_path,
                                       properties=properties)
        LOG.debug("image:%s" % image)

        return image

    def _log_console_output(self, servers=None):
        if not CONF.compute_feature_enabled.console_output:
            LOG.debug('Console output not supported, cannot log')
            return
        if not servers:
            servers = self.servers_client.list_servers()
            servers = servers['servers']
        for server in servers:
            console_output = self.servers_client.get_console_output(
                server['id'])['output']
            LOG.debug('Console output for %s\nbody=\n%s',
                      server['id'], console_output)

    def _log_net_info(self, exc):
        # network debug is called as part of ssh init
        if not isinstance(exc, lib_exc.SSHTimeout):
            LOG.debug('Network information on a devstack host')

    def create_server_snapshot(self, server, name=None):
        # Glance client
        _image_client = self.image_client
        # Compute client
        _images_client = self.compute_images_client
        if name is None:
            name = data_utils.rand_name('scenario-snapshot')
        LOG.debug("Creating a snapshot image for server: %s", server['name'])
        image = _images_client.create_image(server['id'], name=name)
        image_id = image.response['location'].split('images/')[1]
        _image_client.wait_for_image_status(image_id, 'active')
        self.addCleanup_with_wait(
            waiter_callable=_image_client.wait_for_resource_deletion,
            thing_id=image_id, thing_id_param='id',
            cleanup_callable=self.delete_wrapper,
            cleanup_args=[_image_client.delete_image, image_id])
        snapshot_image = _image_client.get_image_meta(image_id)

        bdm = snapshot_image.get('properties', {}).get('block_device_mapping')
        if bdm:
            bdm = json.loads(bdm)
            if bdm and 'snapshot_id' in bdm[0]:
                snapshot_id = bdm[0]['snapshot_id']
                self.addCleanup(
                    self.snapshots_client.wait_for_resource_deletion,
                    snapshot_id)
                self.addCleanup(
                    self.delete_wrapper, self.snapshots_client.delete_snapshot,
                    snapshot_id)
                waiters.wait_for_snapshot_status(self.snapshots_client,
                                                 snapshot_id, 'available')

        image_name = snapshot_image['name']
        self.assertEqual(name, image_name)
        LOG.debug("Created snapshot image %s for server %s",
                  image_name, server['name'])
        return snapshot_image

    def nova_volume_attach(self, server, volume_to_attach):
        volume = self.servers_client.attach_volume(
            server['id'], volumeId=volume_to_attach['id'], device='/dev/%s'
            % CONF.compute.volume_device_name)['volumeAttachment']
        self.assertEqual(volume_to_attach['id'], volume['id'])
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume['id'], 'in-use')

        # Return the updated volume after the attachment
        return self.volumes_client.show_volume(volume['id'])['volume']

    def nova_volume_detach(self, server, volume):
        self.servers_client.detach_volume(server['id'], volume['id'])
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume['id'], 'available')

        volume = self.volumes_client.show_volume(volume['id'])['volume']
        self.assertEqual('available', volume['status'])

    def rebuild_server(self, server_id, image=None,
                       preserve_ephemeral=False, wait=True,
                       rebuild_kwargs=None):
        if image is None:
            image = CONF.compute.image_ref

        rebuild_kwargs = rebuild_kwargs or {}

        LOG.debug("Rebuilding server (id: %s, image: %s, preserve eph: %s)",
                  server_id, image, preserve_ephemeral)
        self.servers_client.rebuild_server(
            server_id=server_id, image_ref=image,
            preserve_ephemeral=preserve_ephemeral,
            **rebuild_kwargs)
        if wait:
            waiters.wait_for_server_status(self.servers_client,
                                           server_id, 'ACTIVE')

    def ping_ip_address(self, ip_address, should_succeed=True,
                        ping_timeout=None):
        timeout = ping_timeout or CONF.validation.ping_timeout
        cmd = ['ping', '-c1', '-w1', ip_address]

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.communicate()

            return (proc.returncode == 0) == should_succeed

        caller = misc_utils.find_test_caller()
        LOG.debug('%(caller)s begins to ping %(ip)s in %(timeout)s sec and the'
                  ' expected result is %(should_succeed)s' % {
                      'caller': caller, 'ip': ip_address, 'timeout': timeout,
                      'should_succeed':
                      'reachable' if should_succeed else 'unreachable'
                  })
        result = tempest.test.call_until_true(ping, timeout, 1)
        LOG.debug('%(caller)s finishes ping %(ip)s in %(timeout)s sec and the '
                  'ping result is %(result)s' % {
                      'caller': caller, 'ip': ip_address, 'timeout': timeout,
                      'result': 'expected' if result else 'unexpected'
                  })
        return result

    def check_vm_connectivity(self, ip_address,
                              username=None,
                              private_key=None,
                              should_connect=True):
        """Check server connectivity

        :param ip_address: server to test against
        :param username: server's ssh username
        :param private_key: server's ssh private key to be used
        :param should_connect: True/False indicates positive/negative test
            positive - attempt ping and ssh
            negative - attempt ping and fail if succeed

        :raises: AssertError if the result of the connectivity check does
            not match the value of the should_connect param
        """
        if should_connect:
            msg = "Timed out waiting for %s to become reachable" % ip_address
        else:
            msg = "ip address %s is reachable" % ip_address
        self.assertTrue(self.ping_ip_address(ip_address,
                                             should_succeed=should_connect),
                        msg=msg)
        if should_connect:
            # no need to check ssh for negative connectivity
            self.get_remote_client(ip_address, username, private_key)

    def check_public_network_connectivity(self, ip_address, username,
                                          private_key, should_connect=True,
                                          msg=None, servers=None):
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        LOG.debug('checking network connections to IP %s with user: %s' %
                  (ip_address, username))
        try:
            self.check_vm_connectivity(ip_address,
                                       username,
                                       private_key,
                                       should_connect=should_connect)
        except Exception:
            ex_msg = 'Public network connectivity check failed'
            if msg:
                ex_msg += ": " + msg
            LOG.exception(ex_msg)
            self._log_console_output(servers)
            raise

    def create_floating_ip(self, thing, pool_name=None):
        """Create a floating IP and associates to a server on Nova"""

        if not pool_name:
            pool_name = CONF.network.floating_network_name
        floating_ip = (self.compute_floating_ips_client.
                       create_floating_ip(pool=pool_name)['floating_ip'])
        self.addCleanup(self.delete_wrapper,
                        self.compute_floating_ips_client.delete_floating_ip,
                        floating_ip['id'])
        self.compute_floating_ips_client.associate_floating_ip_to_server(
            floating_ip['ip'], thing['id'])
        return floating_ip

    def create_timestamp(self, ip_address, dev_name=None, mount_path='/mnt',
                         private_key=None):
        ssh_client = self.get_remote_client(ip_address,
                                            private_key=private_key)
        if dev_name is not None:
            ssh_client.make_fs(dev_name)
            ssh_client.mount(dev_name, mount_path)
        cmd_timestamp = 'sudo sh -c "date > %s/timestamp; sync"' % mount_path
        ssh_client.exec_command(cmd_timestamp)
        timestamp = ssh_client.exec_command('sudo cat %s/timestamp'
                                            % mount_path)
        if dev_name is not None:
            ssh_client.umount(mount_path)
        return timestamp

    def get_timestamp(self, ip_address, dev_name=None, mount_path='/mnt',
                      private_key=None):
        ssh_client = self.get_remote_client(ip_address,
                                            private_key=private_key)
        if dev_name is not None:
            ssh_client.mount(dev_name, mount_path)
        timestamp = ssh_client.exec_command('sudo cat %s/timestamp'
                                            % mount_path)
        if dev_name is not None:
            ssh_client.umount(mount_path)
        return timestamp

    def get_server_ip(self, server):
        """Get the server fixed or floating IP.

        Based on the configuration we're in, return a correct ip
        address for validating that a guest is up.
        """
        if CONF.validation.connect_method == 'floating':
            # The tests calling this method don't have a floating IP
            # and can't make use of the validation resources. So the
            # method is creating the floating IP there.
            return self.create_floating_ip(server)['ip']
        elif CONF.validation.connect_method == 'fixed':
            addresses = server['addresses'][CONF.validation.network_for_ssh]
            for address in addresses:
                if address['version'] == CONF.validation.ip_version_for_ssh:
                    return address['addr']
            raise exceptions.ServerUnreachable()
        else:
            raise exceptions.InvalidConfiguration()


class NetworkScenarioTest(ScenarioTest):
    """Base class for network scenario tests.

    This class provide helpers for network scenario tests, using the neutron
    API. Helpers from ancestor which use the nova network API are overridden
    with the neutron API.

    This Class also enforces using Neutron instead of novanetwork.
    Subclassed tests will be skipped if Neutron is not enabled

    """

    credentials = ['primary', 'admin']

    @classmethod
    def skip_checks(cls):
        super(NetworkScenarioTest, cls).skip_checks()
        if not CONF.service_available.neutron:
            raise cls.skipException('Neutron not available')

    @classmethod
    def resource_setup(cls):
        super(NetworkScenarioTest, cls).resource_setup()
        cls.tenant_id = cls.manager.identity_client.tenant_id

    def _create_network(self, networks_client=None,
                        routers_client=None, tenant_id=None,
                        namestart='network-smoke-'):
        if not networks_client:
            networks_client = self.networks_client
        if not routers_client:
            routers_client = self.routers_client
        if not tenant_id:
            tenant_id = networks_client.tenant_id
        name = data_utils.rand_name(namestart)
        result = networks_client.create_network(name=name, tenant_id=tenant_id)
        network = network_resources.DeletableNetwork(
            networks_client=networks_client, routers_client=routers_client,
            **result['network'])
        self.assertEqual(network.name, name)
        self.addCleanup(self.delete_wrapper, network.delete)
        return network

    def _list_networks(self, *args, **kwargs):
        """List networks using admin creds """
        networks_list = self.admin_manager.networks_client.list_networks(
            *args, **kwargs)
        return networks_list['networks']

    def _list_subnets(self, *args, **kwargs):
        """List subnets using admin creds """
        subnets_list = self.admin_manager.subnets_client.list_subnets(
            *args, **kwargs)
        return subnets_list['subnets']

    def _list_routers(self, *args, **kwargs):
        """List routers using admin creds """
        routers_list = self.admin_manager.routers_client.list_routers(
            *args, **kwargs)
        return routers_list['routers']

    def _list_ports(self, *args, **kwargs):
        """List ports using admin creds """
        ports_list = self.admin_manager.ports_client.list_ports(
            *args, **kwargs)
        return ports_list['ports']

    def _list_agents(self, *args, **kwargs):
        """List agents using admin creds """
        agents_list = self.admin_manager.network_agents_client.list_agents(
            *args, **kwargs)
        return agents_list['agents']

    def _create_subnet(self, network, subnets_client=None,
                       routers_client=None, namestart='subnet-smoke',
                       **kwargs):
        """Create a subnet for the given network

        within the cidr block configured for tenant networks.
        """
        if not subnets_client:
            subnets_client = self.subnets_client
        if not routers_client:
            routers_client = self.routers_client

        def cidr_in_use(cidr, tenant_id):
            """Check cidr existence

            :returns: True if subnet with cidr already exist in tenant
                  False else
            """
            cidr_in_use = self._list_subnets(tenant_id=tenant_id, cidr=cidr)
            return len(cidr_in_use) != 0

        ip_version = kwargs.pop('ip_version', 4)

        if ip_version == 6:
            tenant_cidr = netaddr.IPNetwork(
                CONF.network.project_network_v6_cidr)
            num_bits = CONF.network.project_network_v6_mask_bits
        else:
            tenant_cidr = netaddr.IPNetwork(CONF.network.project_network_cidr)
            num_bits = CONF.network.project_network_mask_bits

        result = None
        str_cidr = None
        # Repeatedly attempt subnet creation with sequential cidr
        # blocks until an unallocated block is found.
        for subnet_cidr in tenant_cidr.subnet(num_bits):
            str_cidr = str(subnet_cidr)
            if cidr_in_use(str_cidr, tenant_id=network.tenant_id):
                continue

            subnet = dict(
                name=data_utils.rand_name(namestart),
                network_id=network.id,
                tenant_id=network.tenant_id,
                cidr=str_cidr,
                ip_version=ip_version,
                **kwargs
            )
            try:
                result = subnets_client.create_subnet(**subnet)
                break
            except lib_exc.Conflict as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        self.assertIsNotNone(result, 'Unable to allocate tenant network')
        subnet = network_resources.DeletableSubnet(
            subnets_client=subnets_client,
            routers_client=routers_client, **result['subnet'])
        self.assertEqual(subnet.cidr, str_cidr)
        self.addCleanup(self.delete_wrapper, subnet.delete)
        return subnet

    def _create_port(self, network_id, client=None, namestart='port-quotatest',
                     **kwargs):
        if not client:
            client = self.ports_client
        name = data_utils.rand_name(namestart)
        result = client.create_port(
            name=name,
            network_id=network_id,
            **kwargs)
        self.assertIsNotNone(result, 'Unable to allocate port')
        port = network_resources.DeletablePort(ports_client=client,
                                               **result['port'])
        self.addCleanup(self.delete_wrapper, port.delete)
        return port

    def _get_server_port_id_and_ip4(self, server, ip_addr=None):
        ports = self._list_ports(device_id=server['id'], fixed_ip=ip_addr)
        # A port can have more then one IP address in some cases.
        # If the network is dual-stack (IPv4 + IPv6), this port is associated
        # with 2 subnets
        port_map = [(p["id"], fxip["ip_address"])
                    for p in ports
                    for fxip in p["fixed_ips"]
                    if netaddr.valid_ipv4(fxip["ip_address"])
                    and p['status'] == 'ACTIVE']
        inactive = [p for p in ports if p['status'] != 'ACTIVE']
        if inactive:
            LOG.warning("Instance has ports that are not ACTIVE: %s", inactive)

        self.assertNotEqual(0, len(port_map),
                            "No IPv4 addresses found in: %s" % ports)
        self.assertEqual(len(port_map), 1,
                         "Found multiple IPv4 addresses: %s. "
                         "Unable to determine which port to target."
                         % port_map)
        return port_map[0]

    def _get_network_by_name(self, network_name):
        net = self._list_networks(name=network_name)
        self.assertNotEqual(len(net), 0,
                            "Unable to get network by name: %s" % network_name)
        return network_resources.AttributeDict(net[0])

    def create_floating_ip(self, thing, external_network_id=None,
                           port_id=None, client=None):
        """Create a floating IP and associates to a resource/port on Neutron"""
        if not external_network_id:
            external_network_id = CONF.network.public_network_id
        if not client:
            client = self.floating_ips_client
        if not port_id:
            port_id, ip4 = self._get_server_port_id_and_ip4(thing)
        else:
            ip4 = None
        result = client.create_floatingip(
            floating_network_id=external_network_id,
            port_id=port_id,
            tenant_id=thing['tenant_id'],
            fixed_ip_address=ip4
        )
        floating_ip = network_resources.DeletableFloatingIp(
            client=client,
            **result['floatingip'])
        self.addCleanup(self.delete_wrapper, floating_ip.delete)
        return floating_ip

    def _associate_floating_ip(self, floating_ip, server):
        port_id, _ = self._get_server_port_id_and_ip4(server)
        floating_ip.update(port_id=port_id)
        self.assertEqual(port_id, floating_ip.port_id)
        return floating_ip

    def _disassociate_floating_ip(self, floating_ip):
        """:param floating_ip: type DeletableFloatingIp"""
        floating_ip.update(port_id=None)
        self.assertIsNone(floating_ip.port_id)
        return floating_ip

    def check_floating_ip_status(self, floating_ip, status):
        """Verifies floatingip reaches the given status

        :param floating_ip: network_resources.DeletableFloatingIp floating
        IP to check status
        :param status: target status
        :raises: AssertionError if status doesn't match
        """
        def refresh():
            floating_ip.refresh()
            return status == floating_ip.status

        tempest.test.call_until_true(refresh,
                                     CONF.network.build_timeout,
                                     CONF.network.build_interval)
        self.assertEqual(status, floating_ip.status,
                         message="FloatingIP: {fp} is at status: {cst}. "
                                 "failed  to reach status: {st}"
                         .format(fp=floating_ip, cst=floating_ip.status,
                                 st=status))
        LOG.info("FloatingIP: {fp} is at status: {st}"
                 .format(fp=floating_ip, st=status))

    def _check_tenant_network_connectivity(self, server,
                                           username,
                                           private_key,
                                           should_connect=True,
                                           servers_for_debug=None):
        if not CONF.network.project_networks_reachable:
            msg = 'Tenant networks not configured to be reachable.'
            LOG.info(msg)
            return
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        try:
            for net_name, ip_addresses in six.iteritems(server['addresses']):
                for ip_address in ip_addresses:
                    self.check_vm_connectivity(ip_address['addr'],
                                               username,
                                               private_key,
                                               should_connect=should_connect)
        except Exception as e:
            LOG.exception('Tenant network connectivity check failed')
            self._log_console_output(servers_for_debug)
            self._log_net_info(e)
            raise

    def _check_remote_connectivity(self, source, dest, should_succeed=True,
                                   nic=None):
        """check ping server via source ssh connection

        :param source: RemoteClient: an ssh connection from which to ping
        :param dest: and IP to ping against
        :param should_succeed: boolean should ping succeed or not
        :param nic: specific network interface to ping from
        :returns: boolean -- should_succeed == ping
        :returns: ping is false if ping failed
        """
        def ping_remote():
            try:
                source.ping_host(dest, nic=nic)
            except lib_exc.SSHExecCommandFailed:
                LOG.warning('Failed to ping IP: %s via a ssh connection '
                            'from: %s.' % (dest, source.ssh_client.host))
                return not should_succeed
            return should_succeed

        return tempest.test.call_until_true(ping_remote,
                                            CONF.validation.ping_timeout,
                                            1)

    def _create_security_group(self, security_group_rules_client=None,
                               tenant_id=None,
                               namestart='secgroup-smoke',
                               security_groups_client=None):
        if security_group_rules_client is None:
            security_group_rules_client = self.security_group_rules_client
        if security_groups_client is None:
            security_groups_client = self.security_groups_client
        if tenant_id is None:
            tenant_id = security_groups_client.tenant_id
        secgroup = self._create_empty_security_group(
            namestart=namestart, client=security_groups_client,
            tenant_id=tenant_id)

        # Add rules to the security group
        rules = self._create_loginable_secgroup_rule(
            security_group_rules_client=security_group_rules_client,
            secgroup=secgroup,
            security_groups_client=security_groups_client)
        for rule in rules:
            self.assertEqual(tenant_id, rule.tenant_id)
            self.assertEqual(secgroup.id, rule.security_group_id)
        return secgroup

    def _create_empty_security_group(self, client=None, tenant_id=None,
                                     namestart='secgroup-smoke'):
        """Create a security group without rules.

        Default rules will be created:
         - IPv4 egress to any
         - IPv6 egress to any

        :param tenant_id: secgroup will be created in this tenant
        :returns: DeletableSecurityGroup -- containing the secgroup created
        """
        if client is None:
            client = self.security_groups_client
        if not tenant_id:
            tenant_id = client.tenant_id
        sg_name = data_utils.rand_name(namestart)
        sg_desc = sg_name + " description"
        sg_dict = dict(name=sg_name,
                       description=sg_desc)
        sg_dict['tenant_id'] = tenant_id
        result = client.create_security_group(**sg_dict)
        secgroup = network_resources.DeletableSecurityGroup(
            client=client, routers_client=self.routers_client,
            **result['security_group']
        )
        self.assertEqual(secgroup.name, sg_name)
        self.assertEqual(tenant_id, secgroup.tenant_id)
        self.assertEqual(secgroup.description, sg_desc)
        self.addCleanup(self.delete_wrapper, secgroup.delete)
        return secgroup

    def _default_security_group(self, client=None, tenant_id=None):
        """Get default secgroup for given tenant_id.

        :returns: DeletableSecurityGroup -- default secgroup for given tenant
        """
        if client is None:
            client = self.security_groups_client
        if not tenant_id:
            tenant_id = client.tenant_id
        sgs = [
            sg for sg in client.list_security_groups().values()[0]
            if sg['tenant_id'] == tenant_id and sg['name'] == 'default'
        ]
        msg = "No default security group for tenant %s." % (tenant_id)
        self.assertTrue(len(sgs) > 0, msg)
        return network_resources.DeletableSecurityGroup(client=client,
                                                        **sgs[0])

    def _create_security_group_rule(self, secgroup=None,
                                    sec_group_rules_client=None,
                                    tenant_id=None,
                                    security_groups_client=None, **kwargs):
        """Create a rule from a dictionary of rule parameters.

        Create a rule in a secgroup. if secgroup not defined will search for
        default secgroup in tenant_id.

        :param secgroup: type DeletableSecurityGroup.
        :param tenant_id: if secgroup not passed -- the tenant in which to
            search for default secgroup
        :param kwargs: a dictionary containing rule parameters:
            for example, to allow incoming ssh:
            rule = {
                    direction: 'ingress'
                    protocol:'tcp',
                    port_range_min: 22,
                    port_range_max: 22
                    }
        """
        if sec_group_rules_client is None:
            sec_group_rules_client = self.security_group_rules_client
        if security_groups_client is None:
            security_groups_client = self.security_groups_client
        if not tenant_id:
            tenant_id = security_groups_client.tenant_id
        if secgroup is None:
            secgroup = self._default_security_group(
                client=security_groups_client, tenant_id=tenant_id)

        ruleset = dict(security_group_id=secgroup.id,
                       tenant_id=secgroup.tenant_id)
        ruleset.update(kwargs)

        sg_rule = sec_group_rules_client.create_security_group_rule(**ruleset)
        sg_rule = network_resources.DeletableSecurityGroupRule(
            client=sec_group_rules_client,
            **sg_rule['security_group_rule']
        )
        self.assertEqual(secgroup.tenant_id, sg_rule.tenant_id)
        self.assertEqual(secgroup.id, sg_rule.security_group_id)

        return sg_rule

    def _create_loginable_secgroup_rule(self, security_group_rules_client=None,
                                        secgroup=None,
                                        security_groups_client=None):
        """Create loginable security group rule

        These rules are intended to permit inbound ssh and icmp
        traffic from all sources, so no group_id is provided.
        Setting a group_id would only permit traffic from ports
        belonging to the same security group.
        """

        if security_group_rules_client is None:
            security_group_rules_client = self.security_group_rules_client
        if security_groups_client is None:
            security_groups_client = self.security_groups_client
        rules = []
        rulesets = [
            dict(
                # ssh
                protocol='tcp',
                port_range_min=22,
                port_range_max=22,
            ),
            dict(
                # ping
                protocol='icmp',
            ),
            dict(
                # ipv6-icmp for ping6
                protocol='icmp',
                ethertype='IPv6',
            )
        ]
        sec_group_rules_client = security_group_rules_client
        for ruleset in rulesets:
            for r_direction in ['ingress', 'egress']:
                ruleset['direction'] = r_direction
                try:
                    sg_rule = self._create_security_group_rule(
                        sec_group_rules_client=sec_group_rules_client,
                        secgroup=secgroup,
                        security_groups_client=security_groups_client,
                        **ruleset)
                except lib_exc.Conflict as ex:
                    # if rule already exist - skip rule and continue
                    msg = 'Security group rule already exists'
                    if msg not in ex._error_string:
                        raise ex
                else:
                    self.assertEqual(r_direction, sg_rule.direction)
                    rules.append(sg_rule)

        return rules

    def _get_router(self, client=None, tenant_id=None):
        """Retrieve a router for the given tenant id.

        If a public router has been configured, it will be returned.

        If a public router has not been configured, but a public
        network has, a tenant router will be created and returned that
        routes traffic to the public network.
        """
        if not client:
            client = self.routers_client
        if not tenant_id:
            tenant_id = client.tenant_id
        router_id = CONF.network.public_router_id
        network_id = CONF.network.public_network_id
        if router_id:
            body = client.show_router(router_id)
            return network_resources.AttributeDict(**body['router'])
        elif network_id:
            router = self._create_router(client, tenant_id)
            router.set_gateway(network_id)
            return router
        else:
            raise Exception("Neither of 'public_router_id' or "
                            "'public_network_id' has been defined.")

    def _create_router(self, client=None, tenant_id=None,
                       namestart='router-smoke'):
        if not client:
            client = self.routers_client
        if not tenant_id:
            tenant_id = client.tenant_id
        name = data_utils.rand_name(namestart)
        result = client.create_router(name=name,
                                      admin_state_up=True,
                                      tenant_id=tenant_id)
        router = network_resources.DeletableRouter(routers_client=client,
                                                   **result['router'])
        self.assertEqual(router.name, name)
        self.addCleanup(self.delete_wrapper, router.delete)
        return router

    def _update_router_admin_state(self, router, admin_state_up):
        router.update(admin_state_up=admin_state_up)
        self.assertEqual(admin_state_up, router.admin_state_up)

    def create_networks(self, networks_client=None,
                        routers_client=None, subnets_client=None,
                        tenant_id=None, dns_nameservers=None):
        """Create a network with a subnet connected to a router.

        The baremetal driver is a special case since all nodes are
        on the same shared network.

        :param tenant_id: id of tenant to create resources in.
        :param dns_nameservers: list of dns servers to send to subnet.
        :returns: network, subnet, router
        """
        if CONF.baremetal.driver_enabled:
            # NOTE(Shrews): This exception is for environments where tenant
            # credential isolation is available, but network separation is
            # not (the current baremetal case). Likely can be removed when
            # test account mgmt is reworked:
            # https://blueprints.launchpad.net/tempest/+spec/test-accounts
            if not CONF.compute.fixed_network_name:
                m = 'fixed_network_name must be specified in config'
                raise exceptions.InvalidConfiguration(m)
            network = self._get_network_by_name(
                CONF.compute.fixed_network_name)
            router = None
            subnet = None
        else:
            network = self._create_network(
                networks_client=networks_client,
                tenant_id=tenant_id)
            router = self._get_router(client=routers_client,
                                      tenant_id=tenant_id)

            subnet_kwargs = dict(network=network,
                                 subnets_client=subnets_client,
                                 routers_client=routers_client)
            # use explicit check because empty list is a valid option
            if dns_nameservers is not None:
                subnet_kwargs['dns_nameservers'] = dns_nameservers
            subnet = self._create_subnet(**subnet_kwargs)
            subnet.add_to_router(router.id)
        return network, subnet, router


# power/provision states as of icehouse
class BaremetalPowerStates(object):
    """Possible power states of an Ironic node."""
    POWER_ON = 'power on'
    POWER_OFF = 'power off'
    REBOOT = 'rebooting'
    SUSPEND = 'suspended'


class BaremetalProvisionStates(object):
    """Possible provision states of an Ironic node."""
    NOSTATE = None
    INIT = 'initializing'
    ACTIVE = 'active'
    BUILDING = 'building'
    DEPLOYWAIT = 'wait call-back'
    DEPLOYING = 'deploying'
    DEPLOYFAIL = 'deploy failed'
    DEPLOYDONE = 'deploy complete'
    DELETING = 'deleting'
    DELETED = 'deleted'
    ERROR = 'error'


class BaremetalScenarioTest(ScenarioTest):

    credentials = ['primary', 'admin']

    @classmethod
    def skip_checks(cls):
        super(BaremetalScenarioTest, cls).skip_checks()
        if (not CONF.service_available.ironic or
           not CONF.baremetal.driver_enabled):
            msg = 'Ironic not available or Ironic compute driver not enabled'
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(BaremetalScenarioTest, cls).setup_clients()

        cls.baremetal_client = cls.admin_manager.baremetal_client

    @classmethod
    def resource_setup(cls):
        super(BaremetalScenarioTest, cls).resource_setup()
        # allow any issues obtaining the node list to raise early
        cls.baremetal_client.list_nodes()

    def _node_state_timeout(self, node_id, state_attr,
                            target_states, timeout=10, interval=1):
        if not isinstance(target_states, list):
            target_states = [target_states]

        def check_state():
            node = self.get_node(node_id=node_id)
            if node.get(state_attr) in target_states:
                return True
            return False

        if not tempest.test.call_until_true(
            check_state, timeout, interval):
            msg = ("Timed out waiting for node %s to reach %s state(s) %s" %
                   (node_id, state_attr, target_states))
            raise exceptions.TimeoutException(msg)

    def wait_provisioning_state(self, node_id, state, timeout):
        self._node_state_timeout(
            node_id=node_id, state_attr='provision_state',
            target_states=state, timeout=timeout)

    def wait_power_state(self, node_id, state):
        self._node_state_timeout(
            node_id=node_id, state_attr='power_state',
            target_states=state, timeout=CONF.baremetal.power_timeout)

    def wait_node(self, instance_id):
        """Waits for a node to be associated with instance_id."""

        def _get_node():
            node = None
            try:
                node = self.get_node(instance_id=instance_id)
            except lib_exc.NotFound:
                pass
            return node is not None

        if not tempest.test.call_until_true(
            _get_node, CONF.baremetal.association_timeout, 1):
            msg = ('Timed out waiting to get Ironic node by instance id %s'
                   % instance_id)
            raise exceptions.TimeoutException(msg)

    def get_node(self, node_id=None, instance_id=None):
        if node_id:
            _, body = self.baremetal_client.show_node(node_id)
            return body
        elif instance_id:
            _, body = self.baremetal_client.show_node_by_instance_uuid(
                instance_id)
            if body['nodes']:
                return body['nodes'][0]

    def get_ports(self, node_uuid):
        ports = []
        _, body = self.baremetal_client.list_node_ports(node_uuid)
        for port in body['ports']:
            _, p = self.baremetal_client.show_port(port['uuid'])
            ports.append(p)
        return ports

    def add_keypair(self):
        self.keypair = self.create_keypair()

    def boot_instance(self):
        self.instance = self.create_server(
            key_name=self.keypair['name'])

        self.wait_node(self.instance['id'])
        self.node = self.get_node(instance_id=self.instance['id'])

        self.wait_power_state(self.node['uuid'], BaremetalPowerStates.POWER_ON)

        self.wait_provisioning_state(
            self.node['uuid'],
            [BaremetalProvisionStates.DEPLOYWAIT,
             BaremetalProvisionStates.ACTIVE],
            timeout=15)

        self.wait_provisioning_state(self.node['uuid'],
                                     BaremetalProvisionStates.ACTIVE,
                                     timeout=CONF.baremetal.active_timeout)

        waiters.wait_for_server_status(self.servers_client,
                                       self.instance['id'], 'ACTIVE')
        self.node = self.get_node(instance_id=self.instance['id'])
        self.instance = (self.servers_client.show_server(self.instance['id'])
                         ['server'])

    def terminate_instance(self):
        self.servers_client.delete_server(self.instance['id'])
        self.wait_power_state(self.node['uuid'],
                              BaremetalPowerStates.POWER_OFF)
        self.wait_provisioning_state(
            self.node['uuid'],
            BaremetalProvisionStates.NOSTATE,
            timeout=CONF.baremetal.unprovision_timeout)


class EncryptionScenarioTest(ScenarioTest):
    """Base class for encryption scenario tests"""

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(EncryptionScenarioTest, cls).setup_clients()
        if CONF.volume_feature_enabled.api_v1:
            cls.admin_volume_types_client = cls.os_adm.volume_types_client
        else:
            cls.admin_volume_types_client = cls.os_adm.volume_types_v2_client

    def create_volume_type(self, client=None, name=None):
        if not client:
            client = self.admin_volume_types_client
        if not name:
            name = 'generic'
        randomized_name = data_utils.rand_name('scenario-type-' + name)
        LOG.debug("Creating a volume type: %s", randomized_name)
        body = client.create_volume_type(
            name=randomized_name)['volume_type']
        self.assertIn('id', body)
        self.addCleanup(client.delete_volume_type, body['id'])
        return body

    def create_encryption_type(self, client=None, type_id=None, provider=None,
                               key_size=None, cipher=None,
                               control_location=None):
        if not client:
            client = self.admin_volume_types_client
        if not type_id:
            volume_type = self.create_volume_type()
            type_id = volume_type['id']
        LOG.debug("Creating an encryption type for volume type: %s", type_id)
        client.create_encryption_type(
            type_id, provider=provider, key_size=key_size, cipher=cipher,
            control_location=control_location)['encryption']


class ObjectStorageScenarioTest(ScenarioTest):
    """Provide harness to do Object Storage scenario tests.

    Subclasses implement the tests that use the methods provided by this
    class.
    """

    @classmethod
    def skip_checks(cls):
        super(ObjectStorageScenarioTest, cls).skip_checks()
        if not CONF.service_available.swift:
            skip_msg = ("%s skipped as swift is not available" %
                        cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(ObjectStorageScenarioTest, cls).setup_credentials()
        operator_role = CONF.object_storage.operator_role
        cls.os_operator = cls.get_client_manager(roles=[operator_role])

    @classmethod
    def setup_clients(cls):
        super(ObjectStorageScenarioTest, cls).setup_clients()
        # Clients for Swift
        cls.account_client = cls.os_operator.account_client
        cls.container_client = cls.os_operator.container_client
        cls.object_client = cls.os_operator.object_client

    def get_swift_stat(self):
        """get swift status for our user account."""
        self.account_client.list_account_containers()
        LOG.debug('Swift status information obtained successfully')

    def create_container(self, container_name=None):
        name = container_name or data_utils.rand_name(
            'swift-scenario-container')
        self.container_client.create_container(name)
        # look for the container to assure it is created
        self.list_and_check_container_objects(name)
        LOG.debug('Container %s created' % (name))
        self.addCleanup(self.delete_wrapper,
                        self.container_client.delete_container,
                        name)
        return name

    def delete_container(self, container_name):
        self.container_client.delete_container(container_name)
        LOG.debug('Container %s deleted' % (container_name))

    def upload_object_to_container(self, container_name, obj_name=None):
        obj_name = obj_name or data_utils.rand_name('swift-scenario-object')
        obj_data = data_utils.arbitrary_string()
        self.object_client.create_object(container_name, obj_name, obj_data)
        self.addCleanup(self.delete_wrapper,
                        self.object_client.delete_object,
                        container_name,
                        obj_name)
        return obj_name, obj_data

    def delete_object(self, container_name, filename):
        self.object_client.delete_object(container_name, filename)
        self.list_and_check_container_objects(container_name,
                                              not_present_obj=[filename])

    def list_and_check_container_objects(self, container_name,
                                         present_obj=None,
                                         not_present_obj=None):
        # List objects for a given container and assert which are present and
        # which are not.
        if present_obj is None:
            present_obj = []
        if not_present_obj is None:
            not_present_obj = []
        _, object_list = self.container_client.list_container_contents(
            container_name)
        if present_obj:
            for obj in present_obj:
                self.assertIn(obj, object_list)
        if not_present_obj:
            for obj in not_present_obj:
                self.assertNotIn(obj, object_list)

    def change_container_acl(self, container_name, acl):
        metadata_param = {'metadata_prefix': 'x-container-',
                          'metadata': {'read': acl}}
        self.container_client.update_container_metadata(container_name,
                                                        **metadata_param)
        resp, _ = self.container_client.list_container_metadata(container_name)
        self.assertEqual(resp['x-container-read'], acl)

    def download_and_verify(self, container_name, obj_name, expected_data):
        _, obj = self.object_client.get_object(container_name, obj_name)
        self.assertEqual(obj, expected_data)
