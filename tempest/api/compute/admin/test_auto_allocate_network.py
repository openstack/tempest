# Copyright 2016 IBM Corp.
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

from oslo_log import log

from tempest.api.compute import base
from tempest.common import compute
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_excs

CONF = config.CONF
LOG = log.getLogger(__name__)


# NOTE(mriedem): This is in the admin directory only because it requires
# force_tenant_isolation=True, but doesn't extend BaseV2ComputeAdminTest
# because it doesn't actually use any admin credentials in the tests.
class AutoAllocateNetworkTest(base.BaseV2ComputeTest):
    """Tests auto-allocating networks with the v2.37 microversion.

    These tests rely on Neutron being enabled. Also, the tenant must not have
    any network resources available to it so we can make sure that Nova
    calls to Neutron to automatically allocate the network topology.
    """

    force_tenant_isolation = True

    min_microversion = '2.37'
    max_microversion = 'latest'

    @classmethod
    def skip_checks(cls):
        super(AutoAllocateNetworkTest, cls).skip_checks()
        if not CONF.service_available.neutron:
            raise cls.skipException('Neutron is required')
        if not utils.is_extension_enabled('auto-allocated-topology',
                                          'network'):
            raise cls.skipException(
                'auto-allocated-topology extension is not available')

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these tests.
        cls.set_network_resources()
        super(AutoAllocateNetworkTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(AutoAllocateNetworkTest, cls).setup_clients()
        cls.networks_client = cls.os_primary.networks_client
        cls.routers_client = cls.os_primary.routers_client
        cls.subnets_client = cls.os_primary.subnets_client
        cls.ports_client = cls.os_primary.ports_client

    @classmethod
    def resource_setup(cls):
        super(AutoAllocateNetworkTest, cls).resource_setup()
        # Sanity check that there are no networks available to the tenant.
        # This is essentially what Nova does for getting available networks.
        tenant_id = cls.networks_client.tenant_id
        # (1) Retrieve non-public network list owned by the tenant.
        search_opts = {'tenant_id': tenant_id, 'shared': False}
        nets = cls.networks_client.list_networks(
            **search_opts).get('networks', [])
        if nets:
            raise lib_excs.TempestException(
                'Found tenant networks: %s' % nets)
        # (2) Retrieve shared network list.
        search_opts = {'shared': True}
        nets = cls.networks_client.list_networks(
            **search_opts).get('networks', [])
        if nets:
            raise cls.skipException('Found shared networks: %s' % nets)

    @classmethod
    def resource_cleanup(cls):
        """Deletes any auto_allocated_network and it's associated resources."""

        # Find the auto-allocated router for the tenant.
        # This is a bit hacky since we don't have a great way to find the
        # auto-allocated router given the private tenant network we have.
        routers = cls.routers_client.list_routers().get('routers', [])
        if len(routers) > 1:
            # This indicates a race where nova is concurrently calling the
            # neutron auto-allocated-topology API for multiple server builds
            # at the same time (it's called from nova-compute when setting up
            # networking for a server). Neutron will detect duplicates and
            # automatically clean them up, but there is a window where the API
            # can return multiple and we don't have a good way to filter those
            # out right now, so we'll just handle them.
            LOG.info('(%s) Found more than one router for tenant.',
                     test_utils.find_test_caller())

        # Remove any networks, duplicate or otherwise, that these tests
        # created. All such networks will be in the current tenant. Neutron
        # will cleanup duplicate resources automatically, so ignore 404s.
        search_opts = {'tenant_id': cls.networks_client.tenant_id}
        networks = cls.networks_client.list_networks(
            **search_opts).get('networks', [])

        for router in routers:
            # Disassociate the subnets from the router. Because of the race
            # mentioned above the subnets might not be associated with the
            # router so ignore any 404.
            for network in networks:
                for subnet_id in network['subnets']:
                    test_utils.call_and_ignore_notfound_exc(
                        cls.routers_client.remove_router_interface,
                        router['id'], subnet_id=subnet_id)

            # Delete the router.
            cls.routers_client.delete_router(router['id'])

        for network in networks:
            # Get and delete the ports for the given network.
            ports = cls.ports_client.list_ports(
                network_id=network['id']).get('ports', [])
            for port in ports:
                test_utils.call_and_ignore_notfound_exc(
                    cls.ports_client.delete_port, port['id'])

            # Delete the subnets.
            for subnet_id in network['subnets']:
                test_utils.call_and_ignore_notfound_exc(
                    cls.subnets_client.delete_subnet, subnet_id)

            # Delete the network.
            test_utils.call_and_ignore_notfound_exc(
                cls.networks_client.delete_network, network['id'])

        super(AutoAllocateNetworkTest, cls).resource_cleanup()

    @decorators.idempotent_id('5eb7b8fa-9c23-47a2-9d7d-02ed5809dd34')
    def test_server_create_no_allocate(self):
        """Tests that no networking is allocated for the server."""
        # create the server with no networking
        server, _ = compute.create_test_server(
            self.os_primary, networks='none', wait_until='ACTIVE')
        self.addCleanup(self.delete_server, server['id'])
        # get the server ips
        addresses = self.servers_client.list_addresses(
            server['id'])['addresses']
        # assert that there is no networking
        self.assertEqual({}, addresses)

    @decorators.idempotent_id('2e6cf129-9e28-4e8a-aaaa-045ea826b2a6')
    def test_server_multi_create_auto_allocate(self):
        """Tests that networking is auto-allocated for multiple servers."""

        # Create multiple servers with auto networking to make sure the
        # automatic network allocation is atomic. Using a minimum of three
        # servers is essential for this scenario because:
        #
        # - First request sees no networks for the tenant so it auto-allocates
        #   one from Neutron, let's call that net1.
        # - Second request sees no networks for the tenant so it auto-allocates
        #   one from Neutron. Neutron creates net2 but sees it's a duplicate
        #   so it queues net2 for deletion and returns net1 from the API and
        #   Nova uses that for the second server request.
        # - Third request sees net1 and net2 for the tenant and fails with a
        #   NetworkAmbiguous 400 error.
        _, servers = compute.create_test_server(
            self.os_primary, networks='auto', wait_until='ACTIVE',
            min_count=3)
        for server in servers:
            self.addCleanup(self.delete_server, server['id'])

        server_nets = set()
        for server in servers:
            # get the server ips
            addresses = self.servers_client.list_addresses(
                server['id'])['addresses']
            # assert that there is networking (should only be one)
            self.assertEqual(1, len(addresses))
            server_nets.add(list(addresses.keys())[0])
        # all servers should be on the same network
        self.assertEqual(1, len(server_nets))

        # List the networks for the tenant; we filter on admin_state_up=True
        # because the auto-allocated-topology code in Neutron won't set that
        # to True until the network is ready and is returned from the API.
        # Duplicate networks created from a race should have
        # admin_state_up=False.
        search_opts = {'tenant_id': self.networks_client.tenant_id,
                       'shared': False,
                       'admin_state_up': True}
        nets = self.networks_client.list_networks(
            **search_opts).get('networks', [])
        self.assertEqual(1, len(nets))
        # verify the single private tenant network is the one that the servers
        # are using also
        self.assertIn(nets[0]['name'], server_nets)
