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

import testtools

from tempest.api.compute import base
from tempest.common import compute
from tempest import config
from tempest import exceptions
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


@decorators.serial
class ServersAffinityTest(base.BaseV2ComputeAdminTest):
    """Test creating servers without multi-create with scheduler_hints.

    The server affinity tests in ServersOnMultiNodesTest use the /servers
    multi-create API and therefore do not test affinity behavior when server
    group members already exist on hosts.

    These tests must be run in serial because they will be disabling compute
    hosts in order to verify affinity behavior.
    """
    # 2.64 added 'policy' and 'rules' fields to POST /os-server-groups
    min_microversion = '2.64'

    @classmethod
    def resource_setup(cls):
        super().resource_setup()

        # Disable all compute hosts except two.
        services = cls.os_admin.services_client.list_services(
            binary='nova-compute')['services']
        num_extra = len(services) - 2
        for i in range(num_extra):
            service = services.pop()
            cls.os_admin.services_client.update_service(
                service['id'], status='disabled')
        cls.services = {
            service['host']: service['id'] for service in services}

    @classmethod
    def skip_checks(cls):
        super().skip_checks()

        if CONF.compute.min_compute_nodes < 2:
            raise cls.skipException(
                "Less than 2 compute nodes, skipping affinity tests.")

    def _disable_compute_host(self, hostname):
        service_id = self.services[hostname]
        self.os_admin.services_client.update_service(
            service_id, status='disabled')
        self.addCleanup(
            self.os_admin.services_client.update_service, service_id,
            status='enabled')

    def _create_server(self, **kwargs):
        body, servers = compute.create_test_server(
            self.os_primary, networks='none', **kwargs)
        for server in servers:
            self.addCleanup(self.delete_server, server['id'])
        return body

    def _create_server_group(self, **kwargs):
        name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=self.__class__.__name__ + "-Server-Group")
        group_id = self.server_groups_client.create_server_group(
            name=name, **kwargs)['server_group']['id']
        self.addCleanup(
            self.server_groups_client.delete_server_group, group_id)
        return group_id

    def _create_server_in_group(self, group_id):
        hints = {'group': group_id}
        server = self._create_server(
            scheduler_hints=hints, wait_until='ACTIVE')
        # Assert the server is in the group.
        server_group = self.server_groups_client.show_server_group(
            group_id)['server_group']
        self.assertIn(server['id'], server_group['members'])
        return server

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('28ef4c29-09db-40a8-aacd-dc5fa321f35e')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("ServerGroupAffinityFilter"),
        'ServerGroupAffinityFilter is not available.')
    def test_create_server_with_affinity(self):
        group_id = self._create_server_group(policy='affinity')

        # Create server1 in the group.
        server1 = self._create_server_in_group(group_id)

        # Create server2 in the group.
        server2 = self._create_server_in_group(group_id)

        # Servers should be on the same host.
        self.assertEqual(
            self.get_host_for_server(server1['id']),
            self.get_host_for_server(server2['id']))

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('3ac1ff4e-0fa2-4069-ae59-695cf829275b')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("ServerGroupAffinityFilter"),
        'ServerGroupAffinityFilter is not available.')
    def test_create_server_with_affinity_negative(self):
        group_id = self._create_server_group(policy='affinity')

        # Create server1 in the group.
        server1 = self._create_server_in_group(group_id)

        # Disable the compute host server1 is on.
        self._disable_compute_host(self.get_host_for_server(server1['id']))

        # Create server2 in the group. This should fail because affinity policy
        # cannot be honored.
        self.assertRaises(
            exceptions.BuildErrorException,
            self._create_server_in_group, group_id)

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('99cf4819-479c-4176-a9a6-ad501f6fc4b7')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("ServerGroupAffinityFilter"),
        'ServerGroupAffinityFilter is not available.')
    def test_create_server_with_soft_affinity(self):
        group_id = self._create_server_group(policy='soft-affinity')

        # Create server1 in the group.
        server1 = self._create_server_in_group(group_id)

        # Disable the compute host server1 is on.
        self._disable_compute_host(self.get_host_for_server(server1['id']))

        # Create server2 in the group. This should succeed because soft
        # affinity is best effort and scheduling should go ahead even if the
        # policy cannot be honored.
        server2 = self._create_server_in_group(group_id)

        # Servers should be on different hosts.
        self.assertNotEqual(
            self.get_host_for_server(server1['id']),
            self.get_host_for_server(server2['id']))

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('475e9db0-5512-41cb-a6b2-4bd6fb3c7603')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("ServerGroupAntiAffinityFilter"),
        'ServerGroupAntiAffinityFilter is not available.')
    def test_create_server_with_anti_affinity(self):
        group_id = self._create_server_group(policy='anti-affinity')

        # Create server1 in the group.
        server1 = self._create_server_in_group(group_id)

        # Create server2 in the group.
        server2 = self._create_server_in_group(group_id)

        # Servers should be on different hosts.
        self.assertNotEqual(
            self.get_host_for_server(server1['id']),
            self.get_host_for_server(server2['id']))

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('c5e43585-0fdd-42a9-a525-2b99465c28df')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("ServerGroupAntiAffinityFilter"),
        'ServerGroupAntiAffinityFilter is not available.')
    def test_create_server_with_anti_affinity_negative(self):
        group_id = self._create_server_group(policy='anti-affinity')

        # Create server1 in the group.
        server1 = self._create_server_in_group(group_id)

        # Disable the compute host server1 is not on.
        self._disable_compute_host(self.get_host_other_than(server1['id']))

        # Create server2 in the group. This should fail because anti-affinity
        # policy cannot be honored.
        self.assertRaises(
            exceptions.BuildErrorException,
            self._create_server_in_group, group_id)

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('88a8c3d4-c0e8-4873-ba6f-006004779f29')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("ServerGroupAntiAffinityFilter"),
        'ServerGroupAntiAffinityFilter is not available.')
    def test_create_server_with_anti_affinity_max_server_per_host(self):
        group_id = self._create_server_group(
            policy='anti-affinity', rules={'max_server_per_host': 2})

        # Create server1 in the group.
        server1 = self._create_server_in_group(group_id)

        # Disable the compute host server1 is not on.
        self._disable_compute_host(self.get_host_other_than(server1['id']))

        # Create server2 in the group. This should succeed because we are
        # allowing a maximum of two servers per compute host for anti-affinity.
        server2 = self._create_server_in_group(group_id)

        # Servers should be on the same host.
        self.assertEqual(
            self.get_host_for_server(server1['id']),
            self.get_host_for_server(server2['id']))

        # A attempt to create a third server in the group should fail because
        # we have already reached our maximum allowed servers per compute host
        # for anti-affinity.
        self.assertRaises(
            exceptions.BuildErrorException,
            self._create_server_in_group, group_id)

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('ef2bc189-5ecc-4a23-8c1b-0d70a9138a77')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("ServerGroupAntiAffinityFilter"),
        'ServerGroupAntiAffinityFilter is not available.')
    def test_create_server_with_soft_anti_affinity(self):
        group_id = self._create_server_group(policy='soft-anti-affinity')

        # Create server1 in the group.
        server1 = self._create_server_in_group(group_id)

        # Disable the compute host server1 is not on.
        self._disable_compute_host(self.get_host_other_than(server1['id']))

        # Create server2 in the group. This should succeed because soft
        # anti-affinity is best effort and scheduling should go ahead even if
        # the policy cannot be honored.
        server2 = self._create_server_in_group(group_id)

        # Servers should be on the same host.
        self.assertEqual(
            self.get_host_for_server(server1['id']),
            self.get_host_for_server(server2['id']))
