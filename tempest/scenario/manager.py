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

import logging
import os
import re
import six
import subprocess
import time

from cinderclient import exceptions as cinder_exceptions
import glanceclient
from heatclient import exc as heat_exceptions
import netaddr
from neutronclient.common import exceptions as exc
from novaclient import exceptions as nova_exceptions

from tempest.api.network import common as net_common
from tempest import auth
from tempest import clients
from tempest.common import debug
from tempest.common import isolated_creds
from tempest.common.utils import data_utils
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log
from tempest.openstack.common import timeutils
import tempest.test

CONF = config.CONF

LOG = log.getLogger(__name__)

# NOTE(afazekas): Workaround for the stdout logging
LOG_nova_client = logging.getLogger('novaclient.client')
LOG_nova_client.addHandler(log.NullHandler())

LOG_cinder_client = logging.getLogger('cinderclient.client')
LOG_cinder_client.addHandler(log.NullHandler())


class ScenarioTest(tempest.test.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(ScenarioTest, cls).setUpClass()
        cls.isolated_creds = isolated_creds.IsolatedCreds(
            cls.__name__, tempest_client=True,
            network_resources=cls.network_resources)
        cls.manager = clients.Manager(
            credentials=cls.credentials()
        )

    @classmethod
    def _get_credentials(cls, get_creds, ctype):
        if CONF.compute.allow_tenant_isolation:
            creds = get_creds()
        else:
            creds = auth.get_default_credentials(ctype)
        return creds

    @classmethod
    def credentials(cls):
        return cls._get_credentials(cls.isolated_creds.get_primary_creds,
                                    'user')


class OfficialClientTest(tempest.test.BaseTestCase):
    """
    Official Client test base class for scenario testing.

    Official Client tests are tests that have the following characteristics:

     * Test basic operations of an API, typically in an order that
       a regular user would perform those operations
     * Test only the correct inputs and action paths -- no fuzz or
       random input data is sent, only valid inputs.
     * Use only the default client tool for calling an API
    """

    @classmethod
    def setUpClass(cls):
        super(OfficialClientTest, cls).setUpClass()
        cls.isolated_creds = isolated_creds.IsolatedCreds(
            cls.__name__, tempest_client=False,
            network_resources=cls.network_resources)

        cls.manager = clients.OfficialClientManager(
            credentials=cls.credentials())
        cls.compute_client = cls.manager.compute_client
        cls.image_client = cls.manager.image_client
        cls.baremetal_client = cls.manager.baremetal_client
        cls.identity_client = cls.manager.identity_client
        cls.network_client = cls.manager.network_client
        cls.volume_client = cls.manager.volume_client
        cls.object_storage_client = cls.manager.object_storage_client
        cls.orchestration_client = cls.manager.orchestration_client
        cls.data_processing_client = cls.manager.data_processing_client
        cls.ceilometer_client = cls.manager.ceilometer_client

    @classmethod
    def tearDownClass(cls):
        cls.isolated_creds.clear_isolated_creds()
        super(OfficialClientTest, cls).tearDownClass()

    @classmethod
    def _get_credentials(cls, get_creds, ctype):
        if CONF.compute.allow_tenant_isolation:
            creds = get_creds()
        else:
            creds = auth.get_default_credentials(ctype)
        return creds

    @classmethod
    def credentials(cls):
        return cls._get_credentials(cls.isolated_creds.get_primary_creds,
                                    'user')

    @classmethod
    def alt_credentials(cls):
        return cls._get_credentials(cls.isolated_creds.get_alt_creds,
                                    'alt_user')

    @classmethod
    def admin_credentials(cls):
        return cls._get_credentials(cls.isolated_creds.get_admin_creds,
                                    'identity_admin')

    def setUp(self):
        super(OfficialClientTest, self).setUp()
        self.cleanup_waits = []
        # NOTE(mtreinish) This is safe to do in setUp instead of setUp class
        # because scenario tests in the same test class should not share
        # resources. If resources were shared between test cases then it
        # should be a single scenario test instead of multiples.

        # NOTE(yfried): this list is cleaned at the end of test_methods and
        # not at the end of the class
        self.addCleanup(self._wait_for_cleanups)

    @staticmethod
    def not_found_exception(exception):
        """
        @return: True if exception is of NotFound type
        """
        NOT_FOUND_LIST = ['NotFound', 'HTTPNotFound']
        return (exception.__class__.__name__ in NOT_FOUND_LIST
                or
                hasattr(exception, 'status_code') and
                exception.status_code == 404)

    def delete_wrapper(self, thing):
        """Ignores NotFound exceptions for delete operations.

        @param thing: object with delete() method.
            OpenStack resources are assumed to have a delete() method which
            destroys the resource
        """

        try:
            thing.delete()
        except Exception as e:
            # If the resource is already missing, mission accomplished.
            if not self.not_found_exception(e):
                raise

    def _wait_for_cleanups(self):
        """To handle async delete actions, a list of waits is added
        which will be iterated over as the last step of clearing the
        cleanup queue. That way all the delete calls are made up front
        and the tests won't succeed unless the deletes are eventually
        successful. This is the same basic approach used in the api tests to
        limit cleanup execution time except here it is multi-resource,
        because of the nature of the scenario tests.
        """
        for wait in self.cleanup_waits:
            self.delete_timeout(**wait)

    def addCleanup_with_wait(self, things, thing_id,
                             error_status='ERROR',
                             exc_type=nova_exceptions.NotFound,
                             cleanup_callable=None, cleanup_args=[],
                             cleanup_kwargs={}):
        """Adds wait for ansyc resource deletion at the end of cleanups

        @param things: type of the resource to delete
        @param thing_id:
        @param error_status: see manager.delete_timeout()
        @param exc_type: see manager.delete_timeout()
        @param cleanup_callable: method to load pass to self.addCleanup with
            the following *cleanup_args, **cleanup_kwargs.
            usually a delete method. if not used, will try to use:
            things.delete(thing_id)
        """
        if cleanup_callable is None:
            LOG.debug("no delete method passed. using {rclass}.delete({id}) as"
                      " default".format(rclass=things, id=thing_id))
            self.addCleanup(things.delete, thing_id)
        else:
            self.addCleanup(cleanup_callable, *cleanup_args, **cleanup_kwargs)
        wait_dict = {
            'things': things,
            'thing_id': thing_id,
            'error_status': error_status,
            'not_found_exception': exc_type,
        }
        self.cleanup_waits.append(wait_dict)

    def status_timeout(self, things, thing_id, expected_status,
                       error_status='ERROR',
                       not_found_exception=nova_exceptions.NotFound):
        """
        Given a thing and an expected status, do a loop, sleeping
        for a configurable amount of time, checking for the
        expected status to show. At any time, if the returned
        status of the thing is ERROR, fail out.
        """
        self._status_timeout(things, thing_id,
                             expected_status=expected_status,
                             error_status=error_status,
                             not_found_exception=not_found_exception)

    def delete_timeout(self, things, thing_id,
                       error_status='ERROR',
                       not_found_exception=nova_exceptions.NotFound):
        """
        Given a thing, do a loop, sleeping
        for a configurable amount of time, checking for the
        deleted status to show. At any time, if the returned
        status of the thing is ERROR, fail out.
        """
        self._status_timeout(things,
                             thing_id,
                             allow_notfound=True,
                             error_status=error_status,
                             not_found_exception=not_found_exception)

    def _status_timeout(self,
                        things,
                        thing_id,
                        expected_status=None,
                        allow_notfound=False,
                        error_status='ERROR',
                        not_found_exception=nova_exceptions.NotFound):

        log_status = expected_status if expected_status else ''
        if allow_notfound:
            log_status += ' or NotFound' if log_status != '' else 'NotFound'

        def check_status():
            # python-novaclient has resources available to its client
            # that all implement a get() method taking an identifier
            # for the singular resource to retrieve.
            try:
                thing = things.get(thing_id)
            except not_found_exception:
                if allow_notfound:
                    return True
                raise
            except Exception as e:
                if allow_notfound and self.not_found_exception(e):
                    return True
                raise

            new_status = thing.status

            # Some components are reporting error status in lower case
            # so case sensitive comparisons can really mess things
            # up.
            if new_status.lower() == error_status.lower():
                message = ("%s failed to get to expected status (%s). "
                           "In %s state.") % (thing, expected_status,
                                              new_status)
                raise exceptions.BuildErrorException(message,
                                                     server_id=thing_id)
            elif new_status == expected_status and expected_status is not None:
                return True  # All good.
            LOG.debug("Waiting for %s to get to %s status. "
                      "Currently in %s status",
                      thing, log_status, new_status)
        if not tempest.test.call_until_true(
            check_status,
            CONF.compute.build_timeout,
            CONF.compute.build_interval):
            message = ("Timed out waiting for thing %s "
                       "to become %s") % (thing_id, log_status)
            raise exceptions.TimeoutException(message)

    def _create_loginable_secgroup_rule_nova(self, client=None,
                                             secgroup_id=None):
        if client is None:
            client = self.compute_client
        if secgroup_id is None:
            sgs = client.security_groups.list()
            for sg in sgs:
                if sg.name == 'default':
                    secgroup_id = sg.id

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
            sg_rule = client.security_group_rules.create(secgroup_id,
                                                         **ruleset)
            self.addCleanup(self.delete_wrapper, sg_rule)
            rules.append(sg_rule)
        return rules

    def _create_security_group_nova(self, client=None,
                                    namestart='secgroup-smoke-'):
        if client is None:
            client = self.compute_client
        # Create security group
        sg_name = data_utils.rand_name(namestart)
        sg_desc = sg_name + " description"
        secgroup = client.security_groups.create(sg_name, sg_desc)
        self.assertEqual(secgroup.name, sg_name)
        self.assertEqual(secgroup.description, sg_desc)
        self.addCleanup(self.delete_wrapper, secgroup)

        # Add rules to the security group
        self._create_loginable_secgroup_rule_nova(client, secgroup.id)

        return secgroup

    def create_server(self, client=None, name=None, image=None, flavor=None,
                      wait_on_boot=True, wait_on_delete=True,
                      create_kwargs={}):
        """Creates VM instance.

        @param client: compute client to create the instance
        @param image: image from which to create the instance
        @param wait_on_boot: wait for status ACTIVE before continue
        @param wait_on_delete: force synchronous delete on cleanup
        @param create_kwargs: additional details for instance creation
        @return: client.server object
        """
        if client is None:
            client = self.compute_client
        if name is None:
            name = data_utils.rand_name('scenario-server-')
        if image is None:
            image = CONF.compute.image_ref
        if flavor is None:
            flavor = CONF.compute.flavor_ref

        fixed_network_name = CONF.compute.fixed_network_name
        if 'nics' not in create_kwargs and fixed_network_name:
            networks = client.networks.list()
            # If several networks found, set the NetID on which to connect the
            # server to avoid the following error "Multiple possible networks
            # found, use a Network ID to be more specific."
            # See Tempest #1250866
            if len(networks) > 1:
                for network in networks:
                    if network.label == fixed_network_name:
                        create_kwargs['nics'] = [{'net-id': network.id}]
                        break
                # If we didn't find the network we were looking for :
                else:
                    msg = ("The network on which the NIC of the server must "
                           "be connected can not be found : "
                           "fixed_network_name=%s. Starting instance without "
                           "specifying a network.") % fixed_network_name
                    LOG.info(msg)

        LOG.debug("Creating a server (name: %s, image: %s, flavor: %s)",
                  name, image, flavor)
        server = client.servers.create(name, image, flavor, **create_kwargs)
        self.assertEqual(server.name, name)
        if wait_on_delete:
            self.addCleanup(self.delete_timeout,
                            self.compute_client.servers,
                            server.id)
        self.addCleanup_with_wait(self.compute_client.servers, server.id,
                                  cleanup_callable=self.delete_wrapper,
                                  cleanup_args=[server])
        if wait_on_boot:
            self.status_timeout(client.servers, server.id, 'ACTIVE')
        # The instance retrieved on creation is missing network
        # details, necessitating retrieval after it becomes active to
        # ensure correct details.
        server = client.servers.get(server.id)
        LOG.debug("Created server: %s", server)
        return server

    def create_volume(self, client=None, size=1, name=None,
                      snapshot_id=None, imageRef=None, volume_type=None,
                      wait_on_delete=True):
        if client is None:
            client = self.volume_client
        if name is None:
            name = data_utils.rand_name('scenario-volume-')
        LOG.debug("Creating a volume (size: %s, name: %s)", size, name)
        volume = client.volumes.create(size=size, display_name=name,
                                       snapshot_id=snapshot_id,
                                       imageRef=imageRef,
                                       volume_type=volume_type)
        if wait_on_delete:
            self.addCleanup(self.delete_timeout,
                            self.volume_client.volumes,
                            volume.id)
        self.addCleanup_with_wait(self.volume_client.volumes, volume.id,
                                  exc_type=cinder_exceptions.NotFound)
        self.assertEqual(name, volume.display_name)
        self.status_timeout(client.volumes, volume.id, 'available')
        LOG.debug("Created volume: %s", volume)
        return volume

    def create_server_snapshot(self, server, compute_client=None,
                               image_client=None, name=None):
        if compute_client is None:
            compute_client = self.compute_client
        if image_client is None:
            image_client = self.image_client
        if name is None:
            name = data_utils.rand_name('scenario-snapshot-')
        LOG.debug("Creating a snapshot image for server: %s", server.name)
        image_id = compute_client.servers.create_image(server, name)
        self.addCleanup_with_wait(self.image_client.images, image_id,
                                  exc_type=glanceclient.exc.HTTPNotFound)
        self.status_timeout(image_client.images, image_id, 'active')
        snapshot_image = image_client.images.get(image_id)
        self.assertEqual(name, snapshot_image.name)
        LOG.debug("Created snapshot image %s for server %s",
                  snapshot_image.name, server.name)
        return snapshot_image

    def create_keypair(self, client=None, name=None):
        if client is None:
            client = self.compute_client
        if name is None:
            name = data_utils.rand_name('scenario-keypair-')
        keypair = client.keypairs.create(name)
        self.assertEqual(keypair.name, name)
        self.addCleanup(self.delete_wrapper, keypair)
        return keypair

    def get_remote_client(self, server_or_ip, username=None, private_key=None):
        if isinstance(server_or_ip, six.string_types):
            ip = server_or_ip
        else:
            network_name_for_ssh = CONF.compute.network_for_ssh
            ip = server_or_ip.networks[network_name_for_ssh][0]
        if username is None:
            username = CONF.scenario.ssh_user
        if private_key is None:
            private_key = self.keypair.private_key
        linux_client = remote_client.RemoteClient(ip, username,
                                                  pkey=private_key)
        try:
            linux_client.validate_authentication()
        except exceptions.SSHTimeout:
            LOG.exception('ssh connection to %s failed' % ip)
            debug.log_net_debug()
            raise

        return linux_client

    def _log_console_output(self, servers=None):
        if not servers:
            servers = self.compute_client.servers.list()
        for server in servers:
            LOG.debug('Console output for %s', server.id)
            LOG.debug(server.get_console_output())

    def wait_for_volume_status(self, status):
        volume_id = self.volume.id
        self.status_timeout(
            self.volume_client.volumes, volume_id, status)

    def _image_create(self, name, fmt, path, properties={}):
        name = data_utils.rand_name('%s-' % name)
        image_file = open(path, 'rb')
        self.addCleanup(image_file.close)
        params = {
            'name': name,
            'container_format': fmt,
            'disk_format': fmt,
            'is_public': 'False',
        }
        params.update(properties)
        image = self.image_client.images.create(**params)
        self.addCleanup(self.image_client.images.delete, image)
        self.assertEqual("queued", image.status)
        image.update(data=image_file)
        return image.id

    def glance_image_create(self):
        qcow2_img_path = (CONF.scenario.img_dir + "/" +
                          CONF.scenario.qcow2_img_file)
        aki_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.aki_img_file
        ari_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.ari_img_file
        ami_img_path = CONF.scenario.img_dir + "/" + CONF.scenario.ami_img_file
        LOG.debug("paths: img: %s, ami: %s, ari: %s, aki: %s"
                  % (qcow2_img_path, ami_img_path, ari_img_path, aki_img_path))
        try:
            self.image = self._image_create('scenario-img',
                                            'bare',
                                            qcow2_img_path,
                                            properties={'disk_format':
                                                        'qcow2'})
        except IOError:
            LOG.debug("A qcow2 image was not found. Try to get a uec image.")
            kernel = self._image_create('scenario-aki', 'aki', aki_img_path)
            ramdisk = self._image_create('scenario-ari', 'ari', ari_img_path)
            properties = {
                'properties': {'kernel_id': kernel, 'ramdisk_id': ramdisk}
            }
            self.image = self._image_create('scenario-ami', 'ami',
                                            path=ami_img_path,
                                            properties=properties)
        LOG.debug("image:%s" % self.image)


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


class BaremetalScenarioTest(OfficialClientTest):
    @classmethod
    def setUpClass(cls):
        super(BaremetalScenarioTest, cls).setUpClass()

        if (not CONF.service_available.ironic or
           not CONF.baremetal.driver_enabled):
            msg = 'Ironic not available or Ironic compute driver not enabled'
            raise cls.skipException(msg)

        # use an admin client manager for baremetal client
        admin_creds = cls.admin_credentials()
        manager = clients.OfficialClientManager(credentials=admin_creds)
        cls.baremetal_client = manager.baremetal_client

        # allow any issues obtaining the node list to raise early
        cls.baremetal_client.node.list()

    def _node_state_timeout(self, node_id, state_attr,
                            target_states, timeout=10, interval=1):
        if not isinstance(target_states, list):
            target_states = [target_states]

        def check_state():
            node = self.get_node(node_id=node_id)
            if getattr(node, state_attr) in target_states:
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
        from ironicclient import exc as ironic_exceptions

        def _get_node():
            node = None
            try:
                node = self.get_node(instance_id=instance_id)
            except ironic_exceptions.HTTPNotFound:
                pass
            return node is not None

        if not tempest.test.call_until_true(
            _get_node, CONF.baremetal.association_timeout, 1):
            msg = ('Timed out waiting to get Ironic node by instance id %s'
                   % instance_id)
            raise exceptions.TimeoutException(msg)

    def get_node(self, node_id=None, instance_id=None):
        if node_id:
            return self.baremetal_client.node.get(node_id)
        elif instance_id:
            return self.baremetal_client.node.get_by_instance_uuid(instance_id)

    def get_ports(self, node_id):
        ports = []
        for port in self.baremetal_client.node.list_ports(node_id):
            ports.append(self.baremetal_client.port.get(port.uuid))
        return ports

    def add_keypair(self):
        self.keypair = self.create_keypair()

    def verify_connectivity(self, ip=None):
        if ip:
            dest = self.get_remote_client(ip)
        else:
            dest = self.get_remote_client(self.instance)
        dest.validate_authentication()

    def boot_instance(self):
        create_kwargs = {
            'key_name': self.keypair.id
        }
        self.instance = self.create_server(
            wait_on_boot=False, create_kwargs=create_kwargs)

        self.addCleanup_with_wait(self.compute_client.servers,
                                  self.instance.id,
                                  cleanup_callable=self.delete_wrapper,
                                  cleanup_args=[self.instance])

        self.wait_node(self.instance.id)
        self.node = self.get_node(instance_id=self.instance.id)

        self.wait_power_state(self.node.uuid, BaremetalPowerStates.POWER_ON)

        self.wait_provisioning_state(
            self.node.uuid,
            [BaremetalProvisionStates.DEPLOYWAIT,
             BaremetalProvisionStates.ACTIVE],
            timeout=15)

        self.wait_provisioning_state(self.node.uuid,
                                     BaremetalProvisionStates.ACTIVE,
                                     timeout=CONF.baremetal.active_timeout)

        self.status_timeout(
            self.compute_client.servers, self.instance.id, 'ACTIVE')

        self.node = self.get_node(instance_id=self.instance.id)
        self.instance = self.compute_client.servers.get(self.instance.id)

    def terminate_instance(self):
        self.instance.delete()
        self.wait_power_state(self.node.uuid, BaremetalPowerStates.POWER_OFF)
        self.wait_provisioning_state(
            self.node.uuid,
            BaremetalProvisionStates.NOSTATE,
            timeout=CONF.baremetal.unprovision_timeout)


class EncryptionScenarioTest(OfficialClientTest):
    """
    Base class for encryption scenario tests
    """

    @classmethod
    def setUpClass(cls):
        super(EncryptionScenarioTest, cls).setUpClass()

        # use admin credentials to create encrypted volume types
        admin_creds = cls.admin_credentials()
        manager = clients.OfficialClientManager(credentials=admin_creds)
        cls.admin_volume_client = manager.volume_client

    def _wait_for_volume_status(self, status):
        self.status_timeout(
            self.volume_client.volumes, self.volume.id, status)

    def nova_boot(self):
        self.keypair = self.create_keypair()
        create_kwargs = {'key_name': self.keypair.name}
        self.server = self.create_server(self.compute_client,
                                         image=self.image,
                                         create_kwargs=create_kwargs)

    def create_volume_type(self, client=None, name=None):
        if not client:
            client = self.admin_volume_client
        if not name:
            name = 'generic'
        randomized_name = data_utils.rand_name('scenario-type-' + name + '-')
        LOG.debug("Creating a volume type: %s", randomized_name)
        volume_type = client.volume_types.create(randomized_name)
        self.addCleanup(client.volume_types.delete, volume_type.id)
        return volume_type

    def create_encryption_type(self, client=None, type_id=None, provider=None,
                               key_size=None, cipher=None,
                               control_location=None):
        if not client:
            client = self.admin_volume_client
        if not type_id:
            volume_type = self.create_volume_type()
            type_id = volume_type.id
        LOG.debug("Creating an encryption type for volume type: %s", type_id)
        client.volume_encryption_types.create(type_id,
                                              {'provider': provider,
                                               'key_size': key_size,
                                               'cipher': cipher,
                                               'control_location':
                                               control_location})

    def nova_volume_attach(self):
        attach_volume_client = self.compute_client.volumes.create_server_volume
        volume = attach_volume_client(self.server.id,
                                      self.volume.id,
                                      '/dev/vdb')
        self.assertEqual(self.volume.id, volume.id)
        self._wait_for_volume_status('in-use')

    def nova_volume_detach(self):
        detach_volume_client = self.compute_client.volumes.delete_server_volume
        detach_volume_client(self.server.id, self.volume.id)
        self._wait_for_volume_status('available')

        volume = self.volume_client.volumes.get(self.volume.id)
        self.assertEqual('available', volume.status)


class NetworkScenarioTest(OfficialClientTest):
    """
    Base class for network scenario tests
    """
    _ip_version = 4

    @classmethod
    def check_preconditions(cls):
        if (CONF.service_available.neutron):
            cls.enabled = True
            # verify that neutron_available is telling the truth
            try:
                cls.network_client.list_networks()
            except exc.EndpointNotFound:
                cls.enabled = False
                raise
        else:
            cls.enabled = False
            msg = 'Neutron not available'
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(NetworkScenarioTest, cls).setUpClass()
        cls.tenant_id = cls.manager.identity_client.tenant_id

    def _create_network(self, tenant_id, namestart='network-smoke-'):
        name = data_utils.rand_name(namestart)
        body = dict(
            network=dict(
                name=name,
                tenant_id=tenant_id,
            ),
        )
        result = self.network_client.create_network(body=body)
        network = net_common.DeletableNetwork(client=self.network_client,
                                              **result['network'])
        self.assertEqual(network.name, name)
        self.addCleanup(self.delete_wrapper, network)
        return network

    def _list_networks(self, **kwargs):
        nets = self.network_client.list_networks(**kwargs)
        return nets['networks']

    def _list_subnets(self, **kwargs):
        subnets = self.network_client.list_subnets(**kwargs)
        return subnets['subnets']

    def _list_routers(self, **kwargs):
        routers = self.network_client.list_routers(**kwargs)
        return routers['routers']

    def _list_ports(self, **kwargs):
        ports = self.network_client.list_ports(**kwargs)
        return ports['ports']

    def _get_tenant_own_network_num(self, tenant_id):
        nets = self._list_networks(tenant_id=tenant_id)
        return len(nets)

    def _get_tenant_own_subnet_num(self, tenant_id):
        subnets = self._list_subnets(tenant_id=tenant_id)
        return len(subnets)

    def _get_tenant_own_port_num(self, tenant_id):
        ports = self._list_ports(tenant_id=tenant_id)
        return len(ports)

    def _create_subnet(self, network, namestart='subnet-smoke-', **kwargs):
        """
        Create a subnet for the given network within the cidr block
        configured for tenant networks.
        """

        def cidr_in_use(cidr, tenant_id):
            """
            :return True if subnet with cidr already exist in tenant
                False else
            """
            cidr_in_use = self._list_subnets(tenant_id=tenant_id, cidr=cidr)
            return len(cidr_in_use) != 0

        if self._ip_version == 6:
            tenant_cidr = netaddr.IPNetwork(CONF.network.tenant_network_v6_cidr)
            network_prefix = CONF.network.tenant_network_v6_mask_bits
        else:
            tenant_cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
            network_prefix = CONF.network.tenant_network_mask_bits
        result = None
        # Repeatedly attempt subnet creation with sequential cidr
        # blocks until an unallocated block is found.
        for subnet_cidr in tenant_cidr.subnet(network_prefix):
            str_cidr = str(subnet_cidr)
            if cidr_in_use(str_cidr, tenant_id=network.tenant_id):
                continue

            body = dict(
                subnet=dict(
                    name=data_utils.rand_name(namestart),
                    ip_version=self._ip_version,
                    network_id=network.id,
                    tenant_id=network.tenant_id,
                    cidr=str_cidr,
                ),
            )
            body['subnet'].update(kwargs)
            try:
                result = self.network_client.create_subnet(body=body)
                break
            except exc.NeutronClientException as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        self.assertIsNotNone(result, 'Unable to allocate tenant network')
        subnet = net_common.DeletableSubnet(client=self.network_client,
                                            **result['subnet'])
        self.assertEqual(subnet.cidr, str_cidr)
        self.addCleanup(self.delete_wrapper, subnet)
        return subnet

    def _create_port(self, network, namestart='port-quotatest-'):
        name = data_utils.rand_name(namestart)
        body = dict(
            port=dict(name=name,
                      network_id=network.id,
                      tenant_id=network.tenant_id))
        result = self.network_client.create_port(body=body)
        self.assertIsNotNone(result, 'Unable to allocate port')
        port = net_common.DeletablePort(client=self.network_client,
                                        **result['port'])
        self.addCleanup(self.delete_wrapper, port)
        return port

    def _get_server_port_id(self, server, ip_addr=None):
        ports = self._list_ports(device_id=server.id, fixed_ip=ip_addr)
        self.assertEqual(len(ports), 1,
                         "Unable to determine which port to target.")
        return ports[0]['id']

    def _create_floating_ip(self, thing, external_network_id, port_id=None):
        if not port_id:
            port_id = self._get_server_port_id(thing)
        body = dict(
            floatingip=dict(
                floating_network_id=external_network_id,
                port_id=port_id,
                tenant_id=thing.tenant_id,
            )
        )
        result = self.network_client.create_floatingip(body=body)
        floating_ip = net_common.DeletableFloatingIp(
            client=self.network_client,
            **result['floatingip'])
        self.addCleanup(self.delete_wrapper, floating_ip)
        return floating_ip

    def _associate_floating_ip(self, floating_ip, server):
        port_id = self._get_server_port_id(server)
        floating_ip.update(port_id=port_id)
        self.assertEqual(port_id, floating_ip.port_id)
        return floating_ip

    def _disassociate_floating_ip(self, floating_ip):
        """
        :param floating_ip: type DeletableFloatingIp
        """
        floating_ip.update(port_id=None)
        self.assertIsNone(floating_ip.port_id)
        return floating_ip

    def _ping_ip_address(self, ip_address, should_succeed=True):
        cmd = ['ping', '-c1', '-w1', ip_address]

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.wait()
            return (proc.returncode == 0) == should_succeed

        return tempest.test.call_until_true(
            ping, CONF.compute.ping_timeout, 1)

    def _create_pool(self, lb_method, protocol, subnet_id):
        """Wrapper utility that returns a test pool."""
        name = data_utils.rand_name('pool-')
        body = {
            "pool": {
                "protocol": protocol,
                "name": name,
                "subnet_id": subnet_id,
                "lb_method": lb_method
            }
        }
        resp = self.network_client.create_pool(body=body)
        pool = net_common.DeletablePool(client=self.network_client,
                                        **resp['pool'])
        self.assertEqual(pool['name'], name)
        self.addCleanup(self.delete_wrapper, pool)
        return pool

    def _create_member(self, address, protocol_port, pool_id):
        """Wrapper utility that returns a test member."""
        body = {
            "member": {
                "protocol_port": protocol_port,
                "pool_id": pool_id,
                "address": address
            }
        }
        resp = self.network_client.create_member(body)
        member = net_common.DeletableMember(client=self.network_client,
                                            **resp['member'])
        self.addCleanup(self.delete_wrapper, member)
        return member

    def _create_vip(self, protocol, protocol_port, subnet_id, pool_id):
        """Wrapper utility that returns a test vip."""
        name = data_utils.rand_name('vip-')
        body = {
            "vip": {
                "protocol": protocol,
                "name": name,
                "subnet_id": subnet_id,
                "pool_id": pool_id,
                "protocol_port": protocol_port
            }
        }
        resp = self.network_client.create_vip(body)
        vip = net_common.DeletableVip(client=self.network_client,
                                      **resp['vip'])
        self.assertEqual(vip['name'], name)
        self.addCleanup(self.delete_wrapper, vip)
        return vip

    def _check_vm_connectivity(self, ip_address,
                               username=None,
                               private_key=None,
                               should_connect=True):
        """
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
        self.assertTrue(self._ping_ip_address(ip_address,
                                              should_succeed=should_connect),
                        msg=msg)
        if should_connect:
            # no need to check ssh for negative connectivity
            self.get_remote_client(ip_address, username, private_key)

    def _check_public_network_connectivity(self, ip_address, username,
                                           private_key, should_connect=True,
                                           msg=None, servers=None):
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        LOG.debug('checking network connections to IP %s with user: %s' %
                  (ip_address, username))
        try:
            self._check_vm_connectivity(ip_address,
                                        username,
                                        private_key,
                                        should_connect=should_connect)
        except Exception as e:
            ex_msg = 'Public network connectivity check failed'
            if msg:
                ex_msg += ": " + msg
            LOG.exception(ex_msg)
            self._log_console_output(servers)
            # network debug is called as part of ssh init
            if not isinstance(e, exceptions.SSHTimeout):
                debug.log_net_debug()
            raise

    def _check_tenant_network_connectivity(self, server,
                                           username,
                                           private_key,
                                           should_connect=True,
                                           servers_for_debug=None):
        if not CONF.network.tenant_networks_reachable:
            msg = 'Tenant networks not configured to be reachable.'
            LOG.info(msg)
            return
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        try:
            for net_name, ip_addresses in server.networks.iteritems():
                for ip_address in ip_addresses:
                    self._check_vm_connectivity(ip_address,
                                                username,
                                                private_key,
                                                should_connect=should_connect)
        except Exception as e:
            LOG.exception('Tenant network connectivity check failed')
            self._log_console_output(servers_for_debug)
            # network debug is called as part of ssh init
            if not isinstance(e, exceptions.SSHTimeout):
                debug.log_net_debug()
            raise

    def _check_remote_connectivity(self, source, dest, should_succeed=True):
        """
        check ping server via source ssh connection

        :param source: RemoteClient: an ssh connection from which to ping
        :param dest: and IP to ping against
        :param should_succeed: boolean should ping succeed or not
        :returns: boolean -- should_succeed == ping
        :returns: ping is false if ping failed
        """
        def ping_remote():
            try:
                source.ping_host(dest)
            except exceptions.SSHExecCommandFailed:
                LOG.exception('Failed to ping host via ssh connection')
                return not should_succeed
            return should_succeed

        return tempest.test.call_until_true(ping_remote,
                                            CONF.compute.ping_timeout,
                                            1)

    def _create_security_group_neutron(self, tenant_id, client=None,
                                       namestart='secgroup-smoke-'):
        if client is None:
            client = self.network_client
        secgroup = self._create_empty_security_group(namestart=namestart,
                                                     client=client,
                                                     tenant_id=tenant_id)

        # Add rules to the security group
        rules = self._create_loginable_secgroup_rule_neutron(secgroup=secgroup)
        for rule in rules:
            self.assertEqual(tenant_id, rule.tenant_id)
            self.assertEqual(secgroup.id, rule.security_group_id)
        return secgroup

    def _create_empty_security_group(self, tenant_id, client=None,
                                     namestart='secgroup-smoke-'):
        """Create a security group without rules.

        Default rules will be created:
         - IPv4 egress to any
         - IPv6 egress to any

        :param tenant_id: secgroup will be created in this tenant
        :returns: DeletableSecurityGroup -- containing the secgroup created
        """
        if client is None:
            client = self.network_client
        sg_name = data_utils.rand_name(namestart)
        sg_desc = sg_name + " description"
        sg_dict = dict(name=sg_name,
                       description=sg_desc)
        sg_dict['tenant_id'] = tenant_id
        body = dict(security_group=sg_dict)
        result = client.create_security_group(body=body)
        secgroup = net_common.DeletableSecurityGroup(
            client=client,
            **result['security_group']
        )
        self.assertEqual(secgroup.name, sg_name)
        self.assertEqual(tenant_id, secgroup.tenant_id)
        self.assertEqual(secgroup.description, sg_desc)
        self.addCleanup(self.delete_wrapper, secgroup)
        return secgroup

    def _default_security_group(self, tenant_id, client=None):
        """Get default secgroup for given tenant_id.

        :returns: DeletableSecurityGroup -- default secgroup for given tenant
        """
        if client is None:
            client = self.network_client
        sgs = [
            sg for sg in client.list_security_groups().values()[0]
            if sg['tenant_id'] == tenant_id and sg['name'] == 'default'
        ]
        msg = "No default security group for tenant %s." % (tenant_id)
        self.assertTrue(len(sgs) > 0, msg)
        if len(sgs) > 1:
            msg = "Found %d default security groups" % len(sgs)
            raise exc.NeutronClientNoUniqueMatch(msg=msg)
        return net_common.DeletableSecurityGroup(client=client,
                                                 **sgs[0])

    def _create_security_group_rule(self, client=None, secgroup=None,
                                    tenant_id=None, **kwargs):
        """Create a rule from a dictionary of rule parameters.

        Create a rule in a secgroup. if secgroup not defined will search for
        default secgroup in tenant_id.

        :param secgroup: type DeletableSecurityGroup.
        :param secgroup_id: search for secgroup by id
            default -- choose default secgroup for given tenant_id
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
        if client is None:
            client = self.network_client
        if secgroup is None:
            secgroup = self._default_security_group(tenant_id)

        ruleset = dict(security_group_id=secgroup.id,
                       tenant_id=secgroup.tenant_id,
                       )
        ruleset.update(kwargs)

        body = dict(security_group_rule=dict(ruleset))
        sg_rule = client.create_security_group_rule(body=body)
        sg_rule = net_common.DeletableSecurityGroupRule(
            client=client,
            **sg_rule['security_group_rule']
        )
        self.addCleanup(self.delete_wrapper, sg_rule)
        self.assertEqual(secgroup.tenant_id, sg_rule.tenant_id)
        self.assertEqual(secgroup.id, sg_rule.security_group_id)

        return sg_rule

    def _create_loginable_secgroup_rule_neutron(self, client=None,
                                                secgroup=None):
        """These rules are intended to permit inbound ssh and icmp
        traffic from all sources, so no group_id is provided.
        Setting a group_id would only permit traffic from ports
        belonging to the same security group.
        """

        if client is None:
            client = self.network_client
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
            )
        ]
        for ruleset in rulesets:
            for r_direction in ['ingress', 'egress']:
                ruleset['direction'] = r_direction
                try:
                    sg_rule = self._create_security_group_rule(
                        client=client, secgroup=secgroup, **ruleset)
                except exc.NeutronClientException as ex:
                    # if rule already exist - skip rule and continue
                    if not (ex.status_code is 409 and 'Security group rule'
                            ' already exists' in ex.message):
                        raise ex
                else:
                    self.assertEqual(r_direction, sg_rule.direction)
                    rules.append(sg_rule)

        return rules

    def _ssh_to_server(self, server, private_key):
        ssh_login = CONF.compute.image_ssh_user
        return self.get_remote_client(server,
                                      username=ssh_login,
                                      private_key=private_key)

    def _show_quota_network(self, tenant_id):
        quota = self.network_client.show_quota(tenant_id)
        return quota['quota']['network']

    def _show_quota_subnet(self, tenant_id):
        quota = self.network_client.show_quota(tenant_id)
        return quota['quota']['subnet']

    def _show_quota_port(self, tenant_id):
        quota = self.network_client.show_quota(tenant_id)
        return quota['quota']['port']

    def _get_router(self, tenant_id):
        """Retrieve a router for the given tenant id.

        If a public router has been configured, it will be returned.

        If a public router has not been configured, but a public
        network has, a tenant router will be created and returned that
        routes traffic to the public network.
        """
        router_id = CONF.network.public_router_id
        network_id = CONF.network.public_network_id
        if router_id:
            result = self.network_client.show_router(router_id)
            return net_common.AttributeDict(**result['router'])
        elif network_id:
            router = self._create_router(tenant_id)
            router.add_gateway(network_id)
            return router
        else:
            raise Exception("Neither of 'public_router_id' or "
                            "'public_network_id' has been defined.")

    def _create_router(self, tenant_id, namestart='router-smoke-'):
        name = data_utils.rand_name(namestart)
        body = dict(
            router=dict(
                name=name,
                admin_state_up=True,
                tenant_id=tenant_id,
            ),
        )
        result = self.network_client.create_router(body=body)
        router = net_common.DeletableRouter(client=self.network_client,
                                            **result['router'])
        self.assertEqual(router.name, name)
        self.addCleanup(self.delete_wrapper, router)
        return router

    def _create_networks(self, tenant_id=None):
        """Create a network with a subnet connected to a router.

        :returns: network, subnet, router
        """
        if tenant_id is None:
            tenant_id = self.tenant_id
        network = self._create_network(tenant_id)
        router = self._get_router(tenant_id)
        subnet = self._create_subnet(network)
        subnet.add_to_router(router.id)
        return network, subnet, router


class OrchestrationScenarioTest(OfficialClientTest):
    """
    Base class for orchestration scenario tests
    """

    @classmethod
    def setUpClass(cls):
        super(OrchestrationScenarioTest, cls).setUpClass()
        if not CONF.service_available.heat:
            raise cls.skipException("Heat support is required")

    @classmethod
    def credentials(cls):
        admin_creds = auth.get_default_credentials('identity_admin')
        creds = auth.get_default_credentials('user')
        admin_creds.tenant_name = creds.tenant_name
        return admin_creds

    def _load_template(self, base_file, file_name):
        filepath = os.path.join(os.path.dirname(os.path.realpath(base_file)),
                                file_name)
        with open(filepath) as f:
            return f.read()

    @classmethod
    def _stack_rand_name(cls):
        return data_utils.rand_name(cls.__name__ + '-')

    @classmethod
    def _get_default_network(cls):
        networks = cls.network_client.list_networks()
        for net in networks['networks']:
            if net['name'] == CONF.compute.fixed_network_name:
                return net

    @staticmethod
    def _stack_output(stack, output_key):
        """Return a stack output value for a given key."""
        return next((o['output_value'] for o in stack.outputs
                    if o['output_key'] == output_key), None)

    def _ping_ip_address(self, ip_address, should_succeed=True):
        cmd = ['ping', '-c1', '-w1', ip_address]

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.wait()
            return (proc.returncode == 0) == should_succeed

        return tempest.test.call_until_true(
            ping, CONF.orchestration.build_timeout, 1)

    def _wait_for_resource_status(self, stack_identifier, resource_name,
                                  status, failure_pattern='^.*_FAILED$'):
        """Waits for a Resource to reach a given status."""
        fail_regexp = re.compile(failure_pattern)
        build_timeout = CONF.orchestration.build_timeout
        build_interval = CONF.orchestration.build_interval

        start = timeutils.utcnow()
        while timeutils.delta_seconds(start,
                                      timeutils.utcnow()) < build_timeout:
            try:
                res = self.client.resources.get(
                    stack_identifier, resource_name)
            except heat_exceptions.HTTPNotFound:
                # ignore this, as the resource may not have
                # been created yet
                pass
            else:
                if res.resource_status == status:
                    return
                if fail_regexp.search(res.resource_status):
                    raise exceptions.StackResourceBuildErrorException(
                        resource_name=res.resource_name,
                        stack_identifier=stack_identifier,
                        resource_status=res.resource_status,
                        resource_status_reason=res.resource_status_reason)
            time.sleep(build_interval)

        message = ('Resource %s failed to reach %s status within '
                   'the required time (%s s).' %
                   (res.resource_name, status, build_timeout))
        raise exceptions.TimeoutException(message)

    def _wait_for_stack_status(self, stack_identifier, status,
                               failure_pattern='^.*_FAILED$'):
        """
        Waits for a Stack to reach a given status.

        Note this compares the full $action_$status, e.g
        CREATE_COMPLETE, not just COMPLETE which is exposed
        via the status property of Stack in heatclient
        """
        fail_regexp = re.compile(failure_pattern)
        build_timeout = CONF.orchestration.build_timeout
        build_interval = CONF.orchestration.build_interval

        start = timeutils.utcnow()
        while timeutils.delta_seconds(start,
                                      timeutils.utcnow()) < build_timeout:
            try:
                stack = self.client.stacks.get(stack_identifier)
            except heat_exceptions.HTTPNotFound:
                # ignore this, as the stackource may not have
                # been created yet
                pass
            else:
                if stack.stack_status == status:
                    return
                if fail_regexp.search(stack.stack_status):
                    raise exceptions.StackBuildErrorException(
                        stack_identifier=stack_identifier,
                        stack_status=stack.stack_status,
                        stack_status_reason=stack.stack_status_reason)
            time.sleep(build_interval)

        message = ('Stack %s failed to reach %s status within '
                   'the required time (%s s).' %
                   (stack.stack_name, status, build_timeout))
        raise exceptions.TimeoutException(message)

    def _stack_delete(self, stack_identifier):
        try:
            self.client.stacks.delete(stack_identifier)
        except heat_exceptions.HTTPNotFound:
            pass
