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
from tempest.common import waiters
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

    @decorators.attr(type='multinode')
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

    @decorators.attr(type='multinode')
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

    @decorators.attr(type='multinode')
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

    @decorators.attr(type='multinode')
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

    @decorators.attr(type='multinode')
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


class UnshelveToHostMultiNodesTest(base.BaseV2ComputeAdminTest):
    """Test to unshelve server in between hosts."""
    min_microversion = '2.91'
    max_microversion = 'latest'

    @classmethod
    def skip_checks(cls):
        super(UnshelveToHostMultiNodesTest, cls).skip_checks()

        if CONF.compute.min_compute_nodes < 2:
            raise cls.skipException(
                "Less than 2 compute nodes, skipping multi-nodes test.")

    def _shelve_offload_then_unshelve_to_host(self, server, host):
        compute.shelve_server(self.servers_client, server['id'],
                              force_shelve_offload=True)

        self.os_admin.servers_client.unshelve_server(
            server['id'],
            body={'unshelve': {'host': host}}
            )
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('b5cc0889-50c2-46a0-b8ff-b5fb4c3a6e20')
    def test_unshelve_to_specific_host(self):
        """Test unshelve to a specific host, new behavior introduced in
        microversion 2.91.
        1. Shelve offload server.
        2. Request unshelve to original host and verify server land on it.
        3. Shelve offload server again.
        4. Request unshelve to the other host and verify server land on it.
        """
        server = self.create_test_server(wait_until='ACTIVE')
        host = self.get_host_for_server(server['id'])
        otherhost = self.get_host_other_than(server['id'])

        self._shelve_offload_then_unshelve_to_host(server, host)
        self.assertEqual(host, self.get_host_for_server(server['id']))

        self._shelve_offload_then_unshelve_to_host(server, otherhost)
        self.assertEqual(otherhost, self.get_host_for_server(server['id']))
