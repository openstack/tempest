# Copyright 2016 NEC Corporation.  All rights reserved.
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

import testtools

from tempest.api.compute import base
from tempest.common import compute
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class ServersOnMultiNodesTest(base.BaseV2ComputeAdminTest):
    """Test creating servers on mutiple nodes with scheduler_hints."""
    @classmethod
    def resource_setup(cls):
        super(ServersOnMultiNodesTest, cls).resource_setup()
        cls.server01 = cls.create_test_server(wait_until='ACTIVE')['id']
        cls.host01 = cls.get_host_for_server(cls.server01)

    @classmethod
    def skip_checks(cls):
        super(ServersOnMultiNodesTest, cls).skip_checks()

        if CONF.compute.min_compute_nodes < 2:
            raise cls.skipException(
                "Less than 2 compute nodes, skipping multi-nodes test.")

    def _create_servers_with_group(self, policy):
        group_id = self.create_test_server_group(policy=[policy])['id']
        hints = {'group': group_id}
        reservation_id = self.create_test_server(
            scheduler_hints=hints, wait_until='ACTIVE', min_count=2,
            return_reservation_id=True)['reservation_id']

        # Get the servers using the reservation_id.
        servers = self.servers_client.list_servers(
            detail=True, reservation_id=reservation_id)['servers']
        self.assertEqual(2, len(servers))

        # Assert the servers are in the group.
        server_group = self.server_groups_client.show_server_group(
            group_id)['server_group']
        hosts = {}
        for server in servers:
            self.assertIn(server['id'], server_group['members'])
            hosts[server['id']] = self.get_host_for_server(server['id'])

        return hosts

    @decorators.idempotent_id('26a9d5df-6890-45f2-abc4-a659290cb130')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("SameHostFilter"),
        'SameHostFilter is not available.')
    def test_create_servers_on_same_host(self):
        """Test creating servers with hints 'same_host'"""
        hints = {'same_host': self.server01}
        server02 = self.create_test_server(scheduler_hints=hints,
                                           wait_until='ACTIVE')['id']
        host02 = self.get_host_for_server(server02)
        self.assertEqual(self.host01, host02)

    @decorators.idempotent_id('cc7ca884-6e3e-42a3-a92f-c522fcf25e8e')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("DifferentHostFilter"),
        'DifferentHostFilter is not available.')
    def test_create_servers_on_different_hosts(self):
        """Test creating servers with hints of single 'different_host'"""
        hints = {'different_host': self.server01}
        server02 = self.create_test_server(scheduler_hints=hints,
                                           wait_until='ACTIVE')['id']
        host02 = self.get_host_for_server(server02)
        self.assertNotEqual(self.host01, host02)

    @decorators.idempotent_id('7869cc84-d661-4e14-9f00-c18cdc89cf57')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("DifferentHostFilter"),
        'DifferentHostFilter is not available.')
    def test_create_servers_on_different_hosts_with_list_of_servers(self):
        """Test creating servers with hints of a list of 'different_host'"""
        hints = {'different_host': [self.server01]}
        server02 = self.create_test_server(scheduler_hints=hints,
                                           wait_until='ACTIVE')['id']
        host02 = self.get_host_for_server(server02)
        self.assertNotEqual(self.host01, host02)

    @decorators.idempotent_id('f8bd0867-e459-45f5-ba53-59134552fe04')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("ServerGroupAntiAffinityFilter"),
        'ServerGroupAntiAffinityFilter is not available.')
    def test_create_server_with_scheduler_hint_group_anti_affinity(self):
        """Tests the ServerGroupAntiAffinityFilter

        Creates two servers in an anti-affinity server group and
        asserts the servers are in the group and on different hosts.
        """
        hosts = self._create_servers_with_group('anti-affinity')
        hostnames = list(hosts.values())
        self.assertNotEqual(hostnames[0], hostnames[1],
                            'Servers are on the same host: %s' % hosts)

    @decorators.idempotent_id('9d2e924a-baf4-11e7-b856-fa163e65f5ce')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("ServerGroupAffinityFilter"),
        'ServerGroupAffinityFilter is not available.')
    def test_create_server_with_scheduler_hint_group_affinity(self):
        """Tests the ServerGroupAffinityFilter

        Creates two servers in an affinity server group and
        asserts the servers are in the group and on same host.
        """
        hosts = self._create_servers_with_group('affinity')
        hostnames = list(hosts.values())
        self.assertEqual(hostnames[0], hostnames[1],
                         'Servers are on the different hosts: %s' % hosts)
