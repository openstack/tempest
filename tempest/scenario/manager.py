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
from oslo_utils import netutils

from tempest.common import compute
from tempest.common import image as common_image
from tempest.common.utils.linux import remote_client
from tempest.common.utils import net_utils
from tempest.common import waiters
from tempest import config
from tempest import exceptions
from tempest.lib.common import api_microversion_fixture
from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions as lib_exc
import tempest.test

CONF = config.CONF

LOG = log.getLogger(__name__)

LATEST_MICROVERSION = 'latest'


class ScenarioTest(tempest.test.BaseTestCase):
    """Base class for scenario tests. Uses tempest own clients. """

    credentials = ['primary']

    compute_min_microversion = None
    compute_max_microversion = LATEST_MICROVERSION
    volume_min_microversion = None
    volume_max_microversion = LATEST_MICROVERSION
    placement_min_microversion = None
    placement_max_microversion = LATEST_MICROVERSION

    @classmethod
    def skip_checks(cls):
        super(ScenarioTest, cls).skip_checks()
        api_version_utils.check_skip_with_microversion(
            cls.compute_min_microversion, cls.compute_max_microversion,
            CONF.compute.min_microversion, CONF.compute.max_microversion)
        api_version_utils.check_skip_with_microversion(
            cls.volume_min_microversion, cls.volume_max_microversion,
            CONF.volume.min_microversion, CONF.volume.max_microversion)
        api_version_utils.check_skip_with_microversion(
            cls.placement_min_microversion, cls.placement_max_microversion,
            CONF.placement.min_microversion, CONF.placement.max_microversion)

    @classmethod
    def resource_setup(cls):
        super(ScenarioTest, cls).resource_setup()
        cls.compute_request_microversion = (
            api_version_utils.select_request_microversion(
                cls.compute_min_microversion,
                CONF.compute.min_microversion))
        cls.volume_request_microversion = (
            api_version_utils.select_request_microversion(
                cls.volume_min_microversion,
                CONF.volume.min_microversion))
        cls.placement_request_microversion = (
            api_version_utils.select_request_microversion(
                cls.placement_min_microversion,
                CONF.placement.min_microversion))

    def setUp(self):
        super(ScenarioTest, self).setUp()
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            compute_microversion=self.compute_request_microversion,
            volume_microversion=self.volume_request_microversion,
            placement_microversion=self.placement_request_microversion))

    @classmethod
    def setup_clients(cls):
        super(ScenarioTest, cls).setup_clients()
        # Clients (in alphabetical order)
        cls.flavors_client = cls.os_primary.flavors_client
        cls.compute_floating_ips_client = (
            cls.os_primary.compute_floating_ips_client)
        if CONF.service_available.glance:
            # Check if glance v1 is available to determine which client to use.
            if CONF.image_feature_enabled.api_v1:
                cls.image_client = cls.os_primary.image_client
            elif CONF.image_feature_enabled.api_v2:
                cls.image_client = cls.os_primary.image_client_v2
            else:
                raise lib_exc.InvalidConfiguration(
                    'Either api_v1 or api_v2 must be True in '
                    '[image-feature-enabled].')
        # Compute image client
        cls.compute_images_client = cls.os_primary.compute_images_client
        cls.keypairs_client = cls.os_primary.keypairs_client
        # Nova security groups client
        cls.compute_security_groups_client = (
            cls.os_primary.compute_security_groups_client)
        cls.compute_security_group_rules_client = (
            cls.os_primary.compute_security_group_rules_client)
        cls.servers_client = cls.os_primary.servers_client
        cls.interface_client = cls.os_primary.interfaces_client
        # Neutron network client
        cls.networks_client = cls.os_primary.networks_client
        cls.ports_client = cls.os_primary.ports_client
        cls.routers_client = cls.os_primary.routers_client
        cls.subnets_client = cls.os_primary.subnets_client
        cls.floating_ips_client = cls.os_primary.floating_ips_client
        cls.security_groups_client = cls.os_primary.security_groups_client
        cls.security_group_rules_client = (
            cls.os_primary.security_group_rules_client)
        # Use the latest available volume clients
        if CONF.service_available.cinder:
            cls.volumes_client = cls.os_primary.volumes_client_latest
            cls.snapshots_client = cls.os_primary.snapshots_client_latest
            cls.backups_client = cls.os_primary.backups_client_latest

    # ## Test functions library
    #
    # The create_[resource] functions only return body and discard the
    # resp part which is not used in scenario tests

    def create_port(self, network_id, client=None, **kwargs):
        if not client:
            client = self.ports_client
        name = data_utils.rand_name(self.__class__.__name__)
        if CONF.network.port_vnic_type and 'binding:vnic_type' not in kwargs:
            kwargs['binding:vnic_type'] = CONF.network.port_vnic_type
        if CONF.network.port_profile and 'binding:profile' not in kwargs:
            kwargs['binding:profile'] = CONF.network.port_profile
        result = client.create_port(
            name=name,
            network_id=network_id,
            **kwargs)
        port = result['port']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        client.delete_port, port['id'])
        return port

    def create_keypair(self, client=None):
        if not client:
            client = self.keypairs_client
        name = data_utils.rand_name(self.__class__.__name__)
        # We don't need to create a keypair by pubkey in scenario
        body = client.create_keypair(name=name)
        self.addCleanup(client.delete_keypair, name)
        return body['keypair']

    def create_server(self, name=None, image_id=None, flavor=None,
                      validatable=False, wait_until='ACTIVE',
                      clients=None, **kwargs):
        """Wrapper utility that returns a test server.

        This wrapper utility calls the common create test server and
        returns a test server. The purpose of this wrapper is to minimize
        the impact on the code of the tests already using this
        function.

        :param **kwargs:
            See extra parameters below

        :Keyword Arguments:
            * *vnic_type* (``string``) --
              used when launching instances with pre-configured ports.
              Examples:
                normal: a traditional virtual port that is either attached
                        to a linux bridge or an openvswitch bridge on a
                        compute node.
                direct: an SR-IOV port that is directly attached to a VM
                macvtap: an SR-IOV port that is attached to a VM via a macvtap
                         device.
              Defaults to ``CONF.network.port_vnic_type``.
            * *port_profile* (``dict``) --
              This attribute is a dictionary that can be used (with admin
              credentials) to supply information influencing the binding of
              the port.
              example: port_profile = "capabilities:[switchdev]"
              Defaults to ``CONF.network.port_profile``.
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
            clients = self.os_primary

        if name is None:
            name = data_utils.rand_name(self.__class__.__name__ + "-server")

        vnic_type = kwargs.pop('vnic_type', CONF.network.port_vnic_type)
        profile = kwargs.pop('port_profile', CONF.network.port_profile)

        # If vnic_type or profile are configured create port for
        # every network
        if vnic_type or profile:
            ports = []
            create_port_body = {}

            if vnic_type:
                create_port_body['binding:vnic_type'] = vnic_type

            if profile:
                create_port_body['binding:profile'] = profile

            if kwargs:
                # Convert security group names to security group ids
                # to pass to create_port
                if 'security_groups' in kwargs:
                    security_groups = \
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
                networks = kwargs.pop('networks', [])
            else:
                networks = []

            # If there are no networks passed to us we look up
            # for the project's private networks and create a port.
            # The same behaviour as we would expect when passing
            # the call to the clients with no networks
            if not networks:
                networks = clients.networks_client.list_networks(
                    **{'router:external': False, 'fields': 'id'})['networks']

            # It's net['uuid'] if networks come from kwargs
            # and net['id'] if they come from
            # clients.networks_client.list_networks
            for net in networks:
                net_id = net.get('uuid', net.get('id'))
                if 'port' not in net:
                    port = self.create_port(network_id=net_id,
                                            client=clients.ports_client,
                                            **create_port_body)
                    ports.append({'port': port['id']})
                else:
                    ports.append({'port': net['port']})
            if ports:
                kwargs['networks'] = ports
            self.ports = ports

        tenant_network = self.get_tenant_network()

        if CONF.compute.compute_volume_common_az:
            kwargs.setdefault('availability_zone',
                              CONF.compute.compute_volume_common_az)

        body, _ = compute.create_test_server(
            clients,
            tenant_network=tenant_network,
            wait_until=wait_until,
            name=name, flavor=flavor,
            image_id=image_id, **kwargs)

        self.addCleanup(waiters.wait_for_server_termination,
                        clients.servers_client, body['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        clients.servers_client.delete_server, body['id'])
        server = clients.servers_client.show_server(body['id'])['server']
        return server

    def create_volume(self, size=None, name=None, snapshot_id=None,
                      imageRef=None, volume_type=None):
        if size is None:
            size = CONF.volume.volume_size
        if imageRef:
            if CONF.image_feature_enabled.api_v1:
                resp = self.image_client.check_image(imageRef)
                image = common_image.get_image_meta_from_headers(resp)
            else:
                image = self.image_client.show_image(imageRef)
            min_disk = image.get('min_disk')
            size = max(size, min_disk)
        if name is None:
            name = data_utils.rand_name(self.__class__.__name__ + "-volume")
        kwargs = {'display_name': name,
                  'snapshot_id': snapshot_id,
                  'imageRef': imageRef,
                  'volume_type': volume_type,
                  'size': size}

        if CONF.compute.compute_volume_common_az:
            kwargs.setdefault('availability_zone',
                              CONF.compute.compute_volume_common_az)

        volume = self.volumes_client.create_volume(**kwargs)['volume']

        self.addCleanup(self.volumes_client.wait_for_resource_deletion,
                        volume['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.volumes_client.delete_volume, volume['id'])
        self.assertEqual(name, volume['name'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        # The volume retrieved on creation has a non-up-to-date status.
        # Retrieval after it becomes active ensures correct details.
        volume = self.volumes_client.show_volume(volume['id'])['volume']
        return volume

    def create_backup(self, volume_id, name=None, description=None,
                      force=False, snapshot_id=None, incremental=False,
                      container=None):

        name = name or data_utils.rand_name(
            self.__class__.__name__ + "-backup")
        kwargs = {'name': name,
                  'description': description,
                  'force': force,
                  'snapshot_id': snapshot_id,
                  'incremental': incremental,
                  'container': container}
        backup = self.backups_client.create_backup(volume_id=volume_id,
                                                   **kwargs)['backup']
        self.addCleanup(self.backups_client.delete_backup, backup['id'])
        waiters.wait_for_volume_resource_status(self.backups_client,
                                                backup['id'], 'available')
        return backup

    def restore_backup(self, backup_id):
        restore = self.backups_client.restore_backup(backup_id)['restore']
        self.addCleanup(self.volumes_client.delete_volume,
                        restore['volume_id'])
        waiters.wait_for_volume_resource_status(self.backups_client,
                                                backup_id, 'available')
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                restore['volume_id'],
                                                'available')
        self.assertEqual(backup_id, restore['backup_id'])
        return restore

    def create_volume_snapshot(self, volume_id, name=None, description=None,
                               metadata=None, force=False):
        name = name or data_utils.rand_name(
            self.__class__.__name__ + '-snapshot')
        snapshot = self.snapshots_client.create_snapshot(
            volume_id=volume_id,
            force=force,
            display_name=name,
            description=description,
            metadata=metadata)['snapshot']
        self.addCleanup(self.snapshots_client.wait_for_resource_deletion,
                        snapshot['id'])
        self.addCleanup(self.snapshots_client.delete_snapshot, snapshot['id'])
        waiters.wait_for_volume_resource_status(self.snapshots_client,
                                                snapshot['id'], 'available')
        snapshot = self.snapshots_client.show_snapshot(
            snapshot['id'])['snapshot']
        return snapshot

    def _cleanup_volume_type(self, volume_type):
        """Clean up a given volume type.

        Ensuring all volumes associated to a type are first removed before
        attempting to remove the type itself. This includes any image volume
        cache volumes stored in a separate tenant to the original volumes
        created from the type.
        """
        admin_volume_type_client = self.os_admin.volume_types_client_latest
        admin_volumes_client = self.os_admin.volumes_client_latest
        volumes = admin_volumes_client.list_volumes(
            detail=True, params={'all_tenants': 1})['volumes']
        type_name = volume_type['name']
        for volume in [v for v in volumes if v['volume_type'] == type_name]:
            test_utils.call_and_ignore_notfound_exc(
                admin_volumes_client.delete_volume, volume['id'])
            admin_volumes_client.wait_for_resource_deletion(volume['id'])
        admin_volume_type_client.delete_volume_type(volume_type['id'])

    def create_volume_type(self, client=None, name=None, backend_name=None):
        if not client:
            client = self.os_admin.volume_types_client_latest
        if not name:
            class_name = self.__class__.__name__
            name = data_utils.rand_name(class_name + '-volume-type')
        randomized_name = data_utils.rand_name('scenario-type-' + name)

        LOG.debug("Creating a volume type: %s on backend %s",
                  randomized_name, backend_name)
        extra_specs = {}
        if backend_name:
            extra_specs = {"volume_backend_name": backend_name}

        volume_type = client.create_volume_type(
            name=randomized_name, extra_specs=extra_specs)['volume_type']
        self.addCleanup(self._cleanup_volume_type, volume_type)
        return volume_type

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
            test_utils.call_and_ignore_notfound_exc,
            self.compute_security_groups_client.delete_security_group,
            secgroup['id'])

        # Add rules to the security group
        self._create_loginable_secgroup_rule(secgroup['id'])

        return secgroup

    def get_remote_client(self, ip_address, username=None, private_key=None,
                          server=None):
        """Get a SSH client to a remote server

        :param ip_address: the server floating or fixed IP address to use
                           for ssh validation
        :param username: name of the Linux account on the remote server
        :param private_key: the SSH private key to use
        :param server: server dict, used for debugging purposes
        :return: a RemoteClient object
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
        linux_client = remote_client.RemoteClient(
            ip_address, username, pkey=private_key, password=password,
            server=server, servers_client=self.servers_client)
        linux_client.validate_authentication()
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
        }
        if CONF.image_feature_enabled.api_v1:
            params['is_public'] = 'False'
            params['properties'] = properties
            params = {'headers': common_image.image_meta_to_headers(**params)}
        else:
            params['visibility'] = 'private'
            # Additional properties are flattened out in the v2 API.
            params.update(properties)
        body = self.image_client.create_image(**params)
        image = body['image'] if 'image' in body else body
        self.addCleanup(self.image_client.delete_image, image['id'])
        self.assertEqual("queued", image['status'])
        with open(path, 'rb') as image_file:
            if CONF.image_feature_enabled.api_v1:
                self.image_client.update_image(image['id'], data=image_file)
            else:
                self.image_client.store_image_file(image['id'], image_file)
        return image['id']

    def glance_image_create(self):
        img_path = CONF.scenario.img_dir + "/" + CONF.scenario.img_file
        aki_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.aki_img_file
        ari_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.ari_img_file
        ami_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.ami_img_file
        img_container_format = CONF.scenario.img_container_format
        img_disk_format = CONF.scenario.img_disk_format
        img_properties = CONF.scenario.img_properties
        LOG.debug("paths: img: %s, container_format: %s, disk_format: %s, "
                  "properties: %s, ami: %s, ari: %s, aki: %s",
                  img_path, img_container_format, img_disk_format,
                  img_properties, ami_img_path, ari_img_path, aki_img_path)
        try:
            image = self._image_create('scenario-img',
                                       img_container_format,
                                       img_path,
                                       disk_format=img_disk_format,
                                       properties=img_properties)
        except IOError:
            LOG.warning(
                "A(n) %s image was not found. Retrying with uec image.",
                img_disk_format)
            kernel = self._image_create('scenario-aki', 'aki', aki_img_path)
            ramdisk = self._image_create('scenario-ari', 'ari', ari_img_path)
            properties = {'kernel_id': kernel, 'ramdisk_id': ramdisk}
            image = self._image_create('scenario-ami', 'ami',
                                       path=ami_img_path,
                                       properties=properties)
        LOG.debug("image:%s", image)

        return image

    def _log_console_output(self, servers=None, client=None):
        if not CONF.compute_feature_enabled.console_output:
            LOG.debug('Console output not supported, cannot log')
            return
        client = client or self.servers_client
        if not servers:
            servers = client.list_servers()
            servers = servers['servers']
        for server in servers:
            try:
                console_output = client.get_console_output(
                    server['id'])['output']
                LOG.debug('Console output for %s\nbody=\n%s',
                          server['id'], console_output)
            except lib_exc.NotFound:
                LOG.debug("Server %s disappeared(deleted) while looking "
                          "for the console log", server['id'])

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
            name = data_utils.rand_name(self.__class__.__name__ + 'snapshot')
        LOG.debug("Creating a snapshot image for server: %s", server['name'])
        image = _images_client.create_image(server['id'], name=name)
        image_id = image.response['location'].split('images/')[1]
        waiters.wait_for_image_status(_image_client, image_id, 'active')

        self.addCleanup(_image_client.wait_for_resource_deletion,
                        image_id)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        _image_client.delete_image, image_id)

        if CONF.image_feature_enabled.api_v1:
            # In glance v1 the additional properties are stored in the headers.
            resp = _image_client.check_image(image_id)
            snapshot_image = common_image.get_image_meta_from_headers(resp)
            image_props = snapshot_image.get('properties', {})
        else:
            # In glance v2 the additional properties are flattened.
            snapshot_image = _image_client.show_image(image_id)
            image_props = snapshot_image

        bdm = image_props.get('block_device_mapping')
        if bdm:
            bdm = json.loads(bdm)
            if bdm and 'snapshot_id' in bdm[0]:
                snapshot_id = bdm[0]['snapshot_id']
                self.addCleanup(
                    self.snapshots_client.wait_for_resource_deletion,
                    snapshot_id)
                self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                                self.snapshots_client.delete_snapshot,
                                snapshot_id)
                waiters.wait_for_volume_resource_status(self.snapshots_client,
                                                        snapshot_id,
                                                        'available')
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
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'in-use')

        # Return the updated volume after the attachment
        return self.volumes_client.show_volume(volume['id'])['volume']

    def nova_volume_detach(self, server, volume):
        self.servers_client.detach_volume(server['id'], volume['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')

    def ping_ip_address(self, ip_address, should_succeed=True,
                        ping_timeout=None, mtu=None, server=None):
        timeout = ping_timeout or CONF.validation.ping_timeout
        cmd = ['ping', '-c1', '-w1']

        if mtu:
            cmd += [
                # don't fragment
                '-M', 'do',
                # ping receives just the size of ICMP payload
                '-s', str(net_utils.get_ping_payload_size(mtu, 4))
            ]
        cmd.append(ip_address)

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.communicate()

            return (proc.returncode == 0) == should_succeed

        caller = test_utils.find_test_caller()
        LOG.debug('%(caller)s begins to ping %(ip)s in %(timeout)s sec and the'
                  ' expected result is %(should_succeed)s', {
                      'caller': caller, 'ip': ip_address, 'timeout': timeout,
                      'should_succeed':
                      'reachable' if should_succeed else 'unreachable'
                  })
        result = test_utils.call_until_true(ping, timeout, 1)
        LOG.debug('%(caller)s finishes ping %(ip)s in %(timeout)s sec and the '
                  'ping result is %(result)s', {
                      'caller': caller, 'ip': ip_address, 'timeout': timeout,
                      'result': 'expected' if result else 'unexpected'
                  })
        if server:
            self._log_console_output([server])
        return result

    def check_vm_connectivity(self, ip_address,
                              username=None,
                              private_key=None,
                              should_connect=True,
                              extra_msg="",
                              server=None,
                              mtu=None):
        """Check server connectivity

        :param ip_address: server to test against
        :param username: server's ssh username
        :param private_key: server's ssh private key to be used
        :param should_connect: True/False indicates positive/negative test
            positive - attempt ping and ssh
            negative - attempt ping and fail if succeed
        :param extra_msg: Message to help with debugging if ``ping_ip_address``
            fails
        :param server: The server whose console to log for debugging
        :param mtu: network MTU to use for connectivity validation

        :raises: AssertError if the result of the connectivity check does
            not match the value of the should_connect param
        """
        LOG.debug('checking network connections to IP %s with user: %s',
                  ip_address, username)
        if should_connect:
            msg = "Timed out waiting for %s to become reachable" % ip_address
        else:
            msg = "ip address %s is reachable" % ip_address
        if extra_msg:
            msg = "%s\n%s" % (extra_msg, msg)
        self.assertTrue(self.ping_ip_address(ip_address,
                                             should_succeed=should_connect,
                                             mtu=mtu, server=server),
                        msg=msg)
        if should_connect:
            # no need to check ssh for negative connectivity
            try:
                self.get_remote_client(ip_address, username, private_key,
                                       server=server)
            except Exception:
                if not extra_msg:
                    extra_msg = 'Failed to ssh to %s' % ip_address
                LOG.exception(extra_msg)
                raise

    def create_floating_ip(self, thing, pool_name=None):
        """Create a floating IP and associates to a server on Nova"""

        if not pool_name:
            pool_name = CONF.network.floating_network_name
        floating_ip = (self.compute_floating_ips_client.
                       create_floating_ip(pool=pool_name)['floating_ip'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.compute_floating_ips_client.delete_floating_ip,
                        floating_ip['id'])
        self.compute_floating_ips_client.associate_floating_ip_to_server(
            floating_ip['ip'], thing['id'])
        return floating_ip

    def create_timestamp(self, ip_address, dev_name=None, mount_path='/mnt',
                         private_key=None, server=None):
        ssh_client = self.get_remote_client(ip_address,
                                            private_key=private_key,
                                            server=server)
        if dev_name is not None:
            ssh_client.make_fs(dev_name)
            ssh_client.exec_command('sudo mount /dev/%s %s' % (dev_name,
                                                               mount_path))
        cmd_timestamp = 'sudo sh -c "date > %s/timestamp; sync"' % mount_path
        ssh_client.exec_command(cmd_timestamp)
        timestamp = ssh_client.exec_command('sudo cat %s/timestamp'
                                            % mount_path)
        if dev_name is not None:
            ssh_client.exec_command('sudo umount %s' % mount_path)
        return timestamp

    def get_timestamp(self, ip_address, dev_name=None, mount_path='/mnt',
                      private_key=None, server=None):
        ssh_client = self.get_remote_client(ip_address,
                                            private_key=private_key,
                                            server=server)
        if dev_name is not None:
            ssh_client.mount(dev_name, mount_path)
        timestamp = ssh_client.exec_command('sudo cat %s/timestamp'
                                            % mount_path)
        if dev_name is not None:
            ssh_client.exec_command('sudo umount %s' % mount_path)
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
            # Determine the network name to look for based on config or creds
            # provider network resources.
            if CONF.validation.network_for_ssh:
                addresses = server['addresses'][
                    CONF.validation.network_for_ssh]
            else:
                network = self.get_tenant_network()
                addresses = (server['addresses'][network['name']]
                             if network else [])
            for address in addresses:
                if (address['version'] == CONF.validation.ip_version_for_ssh and  # noqa
                        address['OS-EXT-IPS:type'] == 'fixed'):
                    return address['addr']
            raise exceptions.ServerUnreachable(server_id=server['id'])
        else:
            raise lib_exc.InvalidConfiguration()

    @classmethod
    def get_host_for_server(cls, server_id):
        server_details = cls.os_admin.servers_client.show_server(server_id)
        return server_details['server']['OS-EXT-SRV-ATTR:host']


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

    def _create_network(self, networks_client=None,
                        tenant_id=None,
                        namestart='network-smoke-',
                        port_security_enabled=True, **net_dict):
        if not networks_client:
            networks_client = self.networks_client
        if not tenant_id:
            tenant_id = networks_client.tenant_id
        name = data_utils.rand_name(namestart)
        network_kwargs = dict(name=name, tenant_id=tenant_id)
        if net_dict:
            network_kwargs.update(net_dict)
        # Neutron disables port security by default so we have to check the
        # config before trying to create the network with port_security_enabled
        if CONF.network_feature_enabled.port_security:
            network_kwargs['port_security_enabled'] = port_security_enabled
        result = networks_client.create_network(**network_kwargs)
        network = result['network']

        self.assertEqual(network['name'], name)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        networks_client.delete_network,
                        network['id'])
        return network

    def create_subnet(self, network, subnets_client=None,
                      namestart='subnet-smoke', **kwargs):
        """Create a subnet for the given network

        within the cidr block configured for tenant networks.
        """
        if not subnets_client:
            subnets_client = self.subnets_client

        def cidr_in_use(cidr, tenant_id):
            """Check cidr existence

            :returns: True if subnet with cidr already exist in tenant
                  False else
            """
            cidr_in_use = self.os_admin.subnets_client.list_subnets(
                tenant_id=tenant_id, cidr=cidr)['subnets']
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
            if cidr_in_use(str_cidr, tenant_id=network['tenant_id']):
                continue

            subnet = dict(
                name=data_utils.rand_name(namestart),
                network_id=network['id'],
                tenant_id=network['tenant_id'],
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

        subnet = result['subnet']
        self.assertEqual(subnet['cidr'], str_cidr)

        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        subnets_client.delete_subnet, subnet['id'])

        return subnet

    def _get_server_port_id_and_ip4(self, server, ip_addr=None):
        if ip_addr:
            ports = self.os_admin.ports_client.list_ports(
                device_id=server['id'],
                fixed_ips='ip_address=%s' % ip_addr)['ports']
        else:
            ports = self.os_admin.ports_client.list_ports(
                device_id=server['id'])['ports']
        # A port can have more than one IP address in some cases.
        # If the network is dual-stack (IPv4 + IPv6), this port is associated
        # with 2 subnets
        p_status = ['ACTIVE']
        # NOTE(vsaienko) With Ironic, instances live on separate hardware
        # servers. Neutron does not bind ports for Ironic instances, as a
        # result the port remains in the DOWN state.
        # TODO(vsaienko) remove once bug: #1599836 is resolved.
        if getattr(CONF.service_available, 'ironic', False):
            p_status.append('DOWN')
        port_map = [(p["id"], fxip["ip_address"])
                    for p in ports
                    for fxip in p["fixed_ips"]
                    if (netutils.is_valid_ipv4(fxip["ip_address"]) and
                        p['status'] in p_status)]
        inactive = [p for p in ports if p['status'] != 'ACTIVE']
        if inactive:
            LOG.warning("Instance has ports that are not ACTIVE: %s", inactive)

        self.assertNotEmpty(port_map,
                            "No IPv4 addresses found in: %s" % ports)
        self.assertEqual(len(port_map), 1,
                         "Found multiple IPv4 addresses: %s. "
                         "Unable to determine which port to target."
                         % port_map)
        return port_map[0]

    def _get_network_by_name(self, network_name):
        net = self.os_admin.networks_client.list_networks(
            name=network_name)['networks']
        self.assertNotEmpty(net,
                            "Unable to get network by name: %s" % network_name)
        return net[0]

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
        floating_ip = result['floatingip']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        client.delete_floatingip,
                        floating_ip['id'])
        return floating_ip

    def check_floating_ip_status(self, floating_ip, status):
        """Verifies floatingip reaches the given status

        :param dict floating_ip: floating IP dict to check status
        :param status: target status
        :raises: AssertionError if status doesn't match
        """
        floatingip_id = floating_ip['id']

        def refresh():
            result = (self.floating_ips_client.
                      show_floatingip(floatingip_id)['floatingip'])
            return status == result['status']

        if not test_utils.call_until_true(refresh,
                                          CONF.network.build_timeout,
                                          CONF.network.build_interval):
            floating_ip = self.floating_ips_client.show_floatingip(
                floatingip_id)['floatingip']
            self.assertEqual(status, floating_ip['status'],
                             message="FloatingIP: {fp} is at status: {cst}. "
                                     "failed  to reach status: {st}"
                             .format(fp=floating_ip, cst=floating_ip['status'],
                                     st=status))
        LOG.info("FloatingIP: {fp} is at status: {st}"
                 .format(fp=floating_ip, st=status))

    def check_tenant_network_connectivity(self, server,
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
            for ip_addresses in server['addresses'].values():
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

    def check_remote_connectivity(self, source, dest, should_succeed=True,
                                  nic=None, protocol='icmp'):
        """check server connectivity via source ssh connection

        :param source: RemoteClient: an ssh connection from which to execute
            the check
        :param dest: an IP to check connectivity against
        :param should_succeed: boolean should connection succeed or not
        :param nic: specific network interface to test connectivity from
        :param protocol: the protocol used to test connectivity with.
        :returns: True, if the connection succeeded and it was expected to
            succeed. False otherwise.
        """
        method_name = '%s_check' % protocol
        connectivity_checker = getattr(source, method_name)

        def connect_remote():
            try:
                connectivity_checker(dest, nic=nic)
            except lib_exc.SSHExecCommandFailed:
                LOG.warning('Failed to check %(protocol)s connectivity for '
                            'IP %(dest)s via a ssh connection from: %(src)s.',
                            dict(protocol=protocol, dest=dest,
                                 src=source.ssh_client.host))
                return not should_succeed
            return should_succeed

        result = test_utils.call_until_true(connect_remote,
                                            CONF.validation.ping_timeout, 1)
        if result:
            return

        source_host = source.ssh_client.host
        if should_succeed:
            msg = "Timed out waiting for %s to become reachable from %s" \
                % (dest, source_host)
        else:
            msg = "%s is reachable from %s" % (dest, source_host)
        self._log_console_output()
        self.fail(msg)

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
            self.assertEqual(tenant_id, rule['tenant_id'])
            self.assertEqual(secgroup['id'], rule['security_group_id'])
        return secgroup

    def _create_empty_security_group(self, client=None, tenant_id=None,
                                     namestart='secgroup-smoke'):
        """Create a security group without rules.

        Default rules will be created:
         - IPv4 egress to any
         - IPv6 egress to any

        :param tenant_id: secgroup will be created in this tenant
        :returns: the created security group
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

        secgroup = result['security_group']
        self.assertEqual(secgroup['name'], sg_name)
        self.assertEqual(tenant_id, secgroup['tenant_id'])
        self.assertEqual(secgroup['description'], sg_desc)

        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        client.delete_security_group, secgroup['id'])
        return secgroup

    def _create_security_group_rule(self, secgroup=None,
                                    sec_group_rules_client=None,
                                    tenant_id=None,
                                    security_groups_client=None, **kwargs):
        """Create a rule from a dictionary of rule parameters.

        Create a rule in a secgroup. if secgroup not defined will search for
        default secgroup in tenant_id.

        :param secgroup: the security group.
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
            # Get default secgroup for tenant_id
            default_secgroups = security_groups_client.list_security_groups(
                name='default', tenant_id=tenant_id)['security_groups']
            msg = "No default security group for tenant %s." % (tenant_id)
            self.assertNotEmpty(default_secgroups, msg)
            secgroup = default_secgroups[0]

        ruleset = dict(security_group_id=secgroup['id'],
                       tenant_id=secgroup['tenant_id'])
        ruleset.update(kwargs)

        sg_rule = sec_group_rules_client.create_security_group_rule(**ruleset)
        sg_rule = sg_rule['security_group_rule']

        self.assertEqual(secgroup['tenant_id'], sg_rule['tenant_id'])
        self.assertEqual(secgroup['id'], sg_rule['security_group_id'])

        return sg_rule

    def _create_loginable_secgroup_rule(self, security_group_rules_client=None,
                                        secgroup=None,
                                        security_groups_client=None):
        """Create loginable security group rule

        This function will create:
        1. egress and ingress tcp port 22 allow rule in order to allow ssh
        access for ipv4.
        2. egress and ingress ipv6 icmp allow rule, in order to allow icmpv6.
        3. egress and ingress ipv4 icmp allow rule, in order to allow icmpv4.
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
                    self.assertEqual(r_direction, sg_rule['direction'])
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
            return body['router']
        elif network_id:
            router = client.create_router(
                name=data_utils.rand_name(self.__class__.__name__ + '-router'),
                admin_state_up=True,
                tenant_id=tenant_id,
                external_gateway_info=dict(network_id=network_id))['router']
            self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                            client.delete_router, router['id'])
            return router
        else:
            raise Exception("Neither of 'public_router_id' or "
                            "'public_network_id' has been defined.")

    def create_networks(self, networks_client=None,
                        routers_client=None, subnets_client=None,
                        tenant_id=None, dns_nameservers=None,
                        port_security_enabled=True, **net_dict):
        """Create a network with a subnet connected to a router.

        The baremetal driver is a special case since all nodes are
        on the same shared network.

        :param tenant_id: id of tenant to create resources in.
        :param dns_nameservers: list of dns servers to send to subnet.
        :param port_security_enabled: whether or not port_security is enabled
        :param net_dict: a dict containing experimental network information in
                a form like this: {'provider:network_type': 'vlan',
                                   'provider:physical_network': 'foo',
                                   'provider:segmentation_id': '42'}
        :returns: network, subnet, router
        """
        if CONF.network.shared_physical_network:
            # NOTE(Shrews): This exception is for environments where tenant
            # credential isolation is available, but network separation is
            # not (the current baremetal case). Likely can be removed when
            # test account mgmt is reworked:
            # https://blueprints.launchpad.net/tempest/+spec/test-accounts
            if not CONF.compute.fixed_network_name:
                m = 'fixed_network_name must be specified in config'
                raise lib_exc.InvalidConfiguration(m)
            network = self._get_network_by_name(
                CONF.compute.fixed_network_name)
            router = None
            subnet = None
        else:
            network = self._create_network(
                networks_client=networks_client,
                tenant_id=tenant_id,
                port_security_enabled=port_security_enabled,
                **net_dict)
            router = self._get_router(client=routers_client,
                                      tenant_id=tenant_id)
            subnet_kwargs = dict(network=network,
                                 subnets_client=subnets_client)
            # use explicit check because empty list is a valid option
            if dns_nameservers is not None:
                subnet_kwargs['dns_nameservers'] = dns_nameservers
            subnet = self.create_subnet(**subnet_kwargs)
            if not routers_client:
                routers_client = self.routers_client
            router_id = router['id']
            routers_client.add_router_interface(router_id,
                                                subnet_id=subnet['id'])

            # save a cleanup job to remove this association between
            # router and subnet
            self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                            routers_client.remove_router_interface, router_id,
                            subnet_id=subnet['id'])
        return network, subnet, router


class EncryptionScenarioTest(ScenarioTest):
    """Base class for encryption scenario tests"""

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(EncryptionScenarioTest, cls).setup_clients()
        cls.admin_volume_types_client = cls.os_admin.volume_types_client_latest
        cls.admin_encryption_types_client =\
            cls.os_admin.encryption_types_client_latest

    def create_encryption_type(self, client=None, type_id=None, provider=None,
                               key_size=None, cipher=None,
                               control_location=None):
        if not client:
            client = self.admin_encryption_types_client
        if not type_id:
            volume_type = self.create_volume_type()
            type_id = volume_type['id']
        LOG.debug("Creating an encryption type for volume type: %s", type_id)
        client.create_encryption_type(
            type_id, provider=provider, key_size=key_size, cipher=cipher,
            control_location=control_location)

    def create_encrypted_volume(self, encryption_provider, volume_type,
                                key_size=256, cipher='aes-xts-plain64',
                                control_location='front-end'):
        volume_type = self.create_volume_type(name=volume_type)
        self.create_encryption_type(type_id=volume_type['id'],
                                    provider=encryption_provider,
                                    key_size=key_size,
                                    cipher=cipher,
                                    control_location=control_location)
        return self.create_volume(volume_type=volume_type['name'])


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
        self.container_client.update_container(name)
        # look for the container to assure it is created
        self.list_and_check_container_objects(name)
        LOG.debug('Container %s created', name)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.container_client.delete_container,
                        name)
        return name

    def delete_container(self, container_name):
        self.container_client.delete_container(container_name)
        LOG.debug('Container %s deleted', container_name)

    def upload_object_to_container(self, container_name, obj_name=None):
        obj_name = obj_name or data_utils.rand_name('swift-scenario-object')
        obj_data = data_utils.random_bytes()
        self.object_client.create_object(container_name, obj_name, obj_data)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
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
        _, object_list = self.container_client.list_container_objects(
            container_name)
        if present_obj:
            for obj in present_obj:
                self.assertIn(obj, object_list)
        if not_present_obj:
            for obj in not_present_obj:
                self.assertNotIn(obj, object_list)

    def download_and_verify(self, container_name, obj_name, expected_data):
        _, obj = self.object_client.get_object(container_name, obj_name)
        self.assertEqual(obj, expected_data)
