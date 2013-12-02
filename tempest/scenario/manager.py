# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import subprocess

# Default client libs
import cinderclient.client
import glanceclient
import heatclient.client
import keystoneclient.v2_0.client
import netaddr
from neutronclient.common import exceptions as exc
import neutronclient.v2_0.client
import novaclient.client
from novaclient import exceptions as nova_exceptions

from tempest.api.network import common as net_common
from tempest.common import isolated_creds
from tempest.common import ssh
from tempest.common.utils.data_utils import rand_name
from tempest.common.utils.linux.remote_client import RemoteClient
from tempest import exceptions
import tempest.manager
from tempest.openstack.common import log
import tempest.test


LOG = log.getLogger(__name__)

# NOTE(afazekas): Workaround for the stdout logging
LOG_nova_client = logging.getLogger('novaclient.client')
LOG_nova_client.addHandler(log.NullHandler())

LOG_cinder_client = logging.getLogger('cinderclient.client')
LOG_cinder_client.addHandler(log.NullHandler())


class OfficialClientManager(tempest.manager.Manager):
    """
    Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """

    NOVACLIENT_VERSION = '2'
    CINDERCLIENT_VERSION = '1'
    HEATCLIENT_VERSION = '1'

    def __init__(self, username, password, tenant_name):
        super(OfficialClientManager, self).__init__()
        self.compute_client = self._get_compute_client(username,
                                                       password,
                                                       tenant_name)
        self.identity_client = self._get_identity_client(username,
                                                         password,
                                                         tenant_name)
        self.image_client = self._get_image_client()
        self.network_client = self._get_network_client()
        self.volume_client = self._get_volume_client(username,
                                                     password,
                                                     tenant_name)
        self.orchestration_client = self._get_orchestration_client(
            username,
            password,
            tenant_name)

    def _get_compute_client(self, username, password, tenant_name):
        # Novaclient will not execute operations for anyone but the
        # identified user, so a new client needs to be created for
        # each user that operations need to be performed for.
        self._validate_credentials(username, password, tenant_name)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        client_args = (username, password, tenant_name, auth_url)

        # Create our default Nova client to use in testing
        service_type = self.config.compute.catalog_type
        return novaclient.client.Client(self.NOVACLIENT_VERSION,
                                        *client_args,
                                        service_type=service_type,
                                        no_cache=True,
                                        insecure=dscv,
                                        http_log_debug=True)

    def _get_image_client(self):
        token = self.identity_client.auth_token
        endpoint = self.identity_client.service_catalog.url_for(
            service_type='image', endpoint_type='publicURL')
        dscv = self.config.identity.disable_ssl_certificate_validation
        return glanceclient.Client('1', endpoint=endpoint, token=token,
                                   insecure=dscv)

    def _get_volume_client(self, username, password, tenant_name):
        auth_url = self.config.identity.uri
        return cinderclient.client.Client(self.CINDERCLIENT_VERSION,
                                          username,
                                          password,
                                          tenant_name,
                                          auth_url,
                                          http_log_debug=True)

    def _get_orchestration_client(self, username=None, password=None,
                                  tenant_name=None):
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        if not tenant_name:
            tenant_name = self.config.identity.tenant_name

        self._validate_credentials(username, password, tenant_name)

        keystone = self._get_identity_client(username, password, tenant_name)
        token = keystone.auth_token
        try:
            endpoint = keystone.service_catalog.url_for(
                service_type='orchestration',
                endpoint_type='publicURL')
        except keystoneclient.exceptions.EndpointNotFound:
            return None
        else:
            return heatclient.client.Client(self.HEATCLIENT_VERSION,
                                            endpoint,
                                            token=token,
                                            username=username,
                                            password=password)

    def _get_identity_client(self, username, password, tenant_name):
        # This identity client is not intended to check the security
        # of the identity service, so use admin credentials by default.
        self._validate_credentials(username, password, tenant_name)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        return keystoneclient.v2_0.client.Client(username=username,
                                                 password=password,
                                                 tenant_name=tenant_name,
                                                 auth_url=auth_url,
                                                 insecure=dscv)

    def _get_network_client(self):
        # The intended configuration is for the network client to have
        # admin privileges and indicate for whom resources are being
        # created via a 'tenant_id' parameter.  This will often be
        # preferable to authenticating as a specific user because
        # working with certain resources (public routers and networks)
        # often requires admin privileges anyway.
        username = self.config.identity.admin_username
        password = self.config.identity.admin_password
        tenant_name = self.config.identity.admin_tenant_name

        self._validate_credentials(username, password, tenant_name)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        return neutronclient.v2_0.client.Client(username=username,
                                                password=password,
                                                tenant_name=tenant_name,
                                                auth_url=auth_url,
                                                insecure=dscv)


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
            __name__, tempest_client=False)

        username, tenant_name, password = cls.credentials()

        cls.manager = OfficialClientManager(username, password, tenant_name)
        cls.compute_client = cls.manager.compute_client
        cls.image_client = cls.manager.image_client
        cls.identity_client = cls.manager.identity_client
        cls.network_client = cls.manager.network_client
        cls.volume_client = cls.manager.volume_client
        cls.orchestration_client = cls.manager.orchestration_client
        cls.resource_keys = {}
        cls.os_resources = []

    @classmethod
    def credentials(cls):
        if cls.config.compute.allow_tenant_isolation:
            return cls.isolated_creds.get_primary_creds()

        username = cls.config.identity.username
        password = cls.config.identity.password
        tenant_name = cls.config.identity.tenant_name
        return username, tenant_name, password

    @classmethod
    def tearDownClass(cls):
        # NOTE(jaypipes): Because scenario tests are typically run in a
        # specific order, and because test methods in scenario tests
        # generally create resources in a particular order, we destroy
        # resources in the reverse order in which resources are added to
        # the scenario test class object
        while cls.os_resources:
            thing = cls.os_resources.pop()
            LOG.debug("Deleting %r from shared resources of %s" %
                      (thing, cls.__name__))

            try:
                # OpenStack resources are assumed to have a delete()
                # method which destroys the resource...
                thing.delete()
            except Exception as e:
                # If the resource is already missing, mission accomplished.
                if e.__class__.__name__ == 'NotFound':
                    continue
                raise

            def is_deletion_complete():
                # Deletion testing is only required for objects whose
                # existence cannot be checked via retrieval.
                if isinstance(thing, dict):
                    return True
                try:
                    thing.get()
                except Exception as e:
                    # Clients are expected to return an exception
                    # called 'NotFound' if retrieval fails.
                    if e.__class__.__name__ == 'NotFound':
                        return True
                    raise
                return False

            # Block until resource deletion has completed or timed-out
            tempest.test.call_until_true(is_deletion_complete, 10, 1)
        cls.isolated_creds.clear_isolated_creds()
        super(OfficialClientTest, cls).tearDownClass()

    @classmethod
    def set_resource(cls, key, thing):
        LOG.debug("Adding %r to shared resources of %s" %
                  (thing, cls.__name__))
        cls.resource_keys[key] = thing
        cls.os_resources.append(thing)

    @classmethod
    def get_resource(cls, key):
        return cls.resource_keys[key]

    @classmethod
    def remove_resource(cls, key):
        thing = cls.resource_keys[key]
        cls.os_resources.remove(thing)
        del cls.resource_keys[key]

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
                else:
                    raise

            new_status = thing.status

            # Some components are reporting error status in lower case
            # so case sensitive comparisons can really mess things
            # up.
            if new_status.lower() == error_status.lower():
                message = "%s failed to get to expected status. \
                          In %s state." % (thing, new_status)
                raise exceptions.BuildErrorException(message)
            elif new_status == expected_status and expected_status is not None:
                return True  # All good.
            LOG.debug("Waiting for %s to get to %s status. "
                      "Currently in %s status",
                      thing, log_status, new_status)
        if not tempest.test.call_until_true(
            check_status,
            self.config.compute.build_timeout,
            self.config.compute.build_interval):
            message = "Timed out waiting for thing %s \
                      to become %s" % (thing_id, log_status)
            raise exceptions.TimeoutException(message)

    def create_loginable_secgroup_rule(self, client=None, secgroup_id=None):
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
        for ruleset in rulesets:
            sg_rule = client.security_group_rules.create(secgroup_id,
                                                         **ruleset)
            self.set_resource(sg_rule.id, sg_rule)

    def create_server(self, client=None, name=None, image=None, flavor=None,
                      create_kwargs={}):
        if client is None:
            client = self.compute_client
        if name is None:
            name = rand_name('scenario-server-')
        if image is None:
            image = self.config.compute.image_ref
        if flavor is None:
            flavor = self.config.compute.flavor_ref
        LOG.debug("Creating a server (name: %s, image: %s, flavor: %s)",
                  name, image, flavor)
        server = client.servers.create(name, image, flavor, **create_kwargs)
        self.assertEqual(server.name, name)
        self.set_resource(name, server)
        self.status_timeout(client.servers, server.id, 'ACTIVE')
        # The instance retrieved on creation is missing network
        # details, necessitating retrieval after it becomes active to
        # ensure correct details.
        server = client.servers.get(server.id)
        self.set_resource(name, server)
        LOG.debug("Created server: %s", server)
        return server

    def create_volume(self, client=None, size=1, name=None,
                      snapshot_id=None, imageRef=None):
        if client is None:
            client = self.volume_client
        if name is None:
            name = rand_name('scenario-volume-')
        LOG.debug("Creating a volume (size: %s, name: %s)", size, name)
        volume = client.volumes.create(size=size, display_name=name,
                                       snapshot_id=snapshot_id,
                                       imageRef=imageRef)
        self.set_resource(name, volume)
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
            name = rand_name('scenario-snapshot-')
        LOG.debug("Creating a snapshot image for server: %s", server.name)
        image_id = compute_client.servers.create_image(server, name)
        self.addCleanup(image_client.images.delete, image_id)
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
            name = rand_name('scenario-keypair-')
        keypair = client.keypairs.create(name)
        self.assertEqual(keypair.name, name)
        self.set_resource(name, keypair)
        return keypair

    def get_remote_client(self, server_or_ip, username=None, private_key=None):
        if isinstance(server_or_ip, basestring):
            ip = server_or_ip
        else:
            network_name_for_ssh = self.config.compute.network_for_ssh
            ip = server_or_ip.networks[network_name_for_ssh][0]
        if username is None:
            username = self.config.scenario.ssh_user
        if private_key is None:
            private_key = self.keypair.private_key
        return RemoteClient(ip, username, pkey=private_key)


class NetworkScenarioTest(OfficialClientTest):
    """
    Base class for network scenario tests
    """

    @classmethod
    def check_preconditions(cls):
        if (cls.config.service_available.neutron):
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
        if cls.config.compute.allow_tenant_isolation:
            cls.tenant_id = cls.isolated_creds.get_primary_tenant().id
        else:
            cls.tenant_id = cls.manager._get_identity_client(
                cls.config.identity.username,
                cls.config.identity.password,
                cls.config.identity.tenant_name).tenant_id

    def _create_security_group(self, client=None, namestart='secgroup-smoke-'):
        if client is None:
            client = self.compute_client
        # Create security group
        sg_name = rand_name(namestart)
        sg_desc = sg_name + " description"
        secgroup = client.security_groups.create(sg_name, sg_desc)
        self.assertEqual(secgroup.name, sg_name)
        self.assertEqual(secgroup.description, sg_desc)
        self.set_resource(sg_name, secgroup)

        # Add rules to the security group
        self.create_loginable_secgroup_rule(client, secgroup.id)

        return secgroup

    def _create_network(self, tenant_id, namestart='network-smoke-'):
        name = rand_name(namestart)
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
        self.set_resource(name, network)
        return network

    def _list_networks(self):
        nets = self.network_client.list_networks()
        return nets['networks']

    def _list_subnets(self):
        subnets = self.network_client.list_subnets()
        return subnets['subnets']

    def _list_routers(self):
        routers = self.network_client.list_routers()
        return routers['routers']

    def _create_subnet(self, network, namestart='subnet-smoke-'):
        """
        Create a subnet for the given network within the cidr block
        configured for tenant networks.
        """
        cfg = self.config.network
        tenant_cidr = netaddr.IPNetwork(cfg.tenant_network_cidr)
        result = None
        # Repeatedly attempt subnet creation with sequential cidr
        # blocks until an unallocated block is found.
        for subnet_cidr in tenant_cidr.subnet(cfg.tenant_network_mask_bits):
            body = dict(
                subnet=dict(
                    ip_version=4,
                    network_id=network.id,
                    tenant_id=network.tenant_id,
                    cidr=str(subnet_cidr),
                ),
            )
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
        self.assertEqual(subnet.cidr, str(subnet_cidr))
        self.set_resource(rand_name(namestart), subnet)
        return subnet

    def _create_port(self, network, namestart='port-quotatest-'):
        name = rand_name(namestart)
        body = dict(
            port=dict(name=name,
                      network_id=network.id,
                      tenant_id=network.tenant_id))
        result = self.network_client.create_port(body=body)
        self.assertIsNotNone(result, 'Unable to allocate port')
        port = net_common.DeletablePort(client=self.network_client,
                                        **result['port'])
        self.set_resource(name, port)
        return port

    def _create_floating_ip(self, server, external_network_id):
        result = self.network_client.list_ports(device_id=server.id)
        ports = result.get('ports', [])
        self.assertEqual(len(ports), 1,
                         "Unable to determine which port to target.")
        port_id = ports[0]['id']
        body = dict(
            floatingip=dict(
                floating_network_id=external_network_id,
                port_id=port_id,
                tenant_id=server.tenant_id,
            )
        )
        result = self.network_client.create_floatingip(body=body)
        floating_ip = net_common.DeletableFloatingIp(
            client=self.network_client,
            **result['floatingip'])
        self.set_resource(rand_name('floatingip-'), floating_ip)
        return floating_ip

    def _ping_ip_address(self, ip_address):
        cmd = ['ping', '-c1', '-w1', ip_address]

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.wait()
            if proc.returncode == 0:
                return True

        return tempest.test.call_until_true(
            ping, self.config.compute.ping_timeout, 1)

    def _is_reachable_via_ssh(self, ip_address, username, private_key,
                              timeout):
        ssh_client = ssh.Client(ip_address, username,
                                pkey=private_key,
                                timeout=timeout)
        return ssh_client.test_connection_auth()

    def _check_vm_connectivity(self, ip_address, username, private_key):
        self.assertTrue(self._ping_ip_address(ip_address),
                        "Timed out waiting for %s to become "
                        "reachable" % ip_address)
        self.assertTrue(self._is_reachable_via_ssh(
            ip_address,
            username,
            private_key,
            timeout=self.config.compute.ssh_timeout),
            'Auth failure in connecting to %s@%s via ssh' %
            (username, ip_address))


class OrchestrationScenarioTest(OfficialClientTest):
    """
    Base class for orchestration scenario tests
    """

    @classmethod
    def setUpClass(cls):
        super(OrchestrationScenarioTest, cls).setUpClass()
        if not cls.config.service_available.heat:
            raise cls.skipException("Heat support is required")

    @classmethod
    def credentials(cls):
        username = cls.config.identity.admin_username
        password = cls.config.identity.admin_password
        tenant_name = cls.config.identity.tenant_name
        return username, tenant_name, password

    def _load_template(self, base_file, file_name):
        filepath = os.path.join(os.path.dirname(os.path.realpath(base_file)),
                                file_name)
        with open(filepath) as f:
            return f.read()

    @classmethod
    def _stack_rand_name(cls):
        return rand_name(cls.__name__ + '-')

    @classmethod
    def _get_default_network(cls):
        networks = cls.network_client.list_networks()
        for net in networks['networks']:
            if net['name'] == cls.config.compute.fixed_network_name:
                return net
