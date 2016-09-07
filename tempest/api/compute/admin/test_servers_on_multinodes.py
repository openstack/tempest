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
from tempest import config
from tempest import test

CONF = config.CONF


class ServersOnMultiNodesTest(base.BaseV2ComputeAdminTest):

    @classmethod
    def skip_checks(cls):
        super(ServersOnMultiNodesTest, cls).skip_checks()

        if CONF.compute.min_compute_nodes < 2:
            raise cls.skipException(
                "Less than 2 compute nodes, skipping multi-nodes test.")

    def _get_host(self, server_id):
        return self.os_adm.servers_client.show_server(
            server_id)['server']['OS-EXT-SRV-ATTR:host']

    @test.idempotent_id('26a9d5df-6890-45f2-abc4-a659290cb130')
    @testtools.skipUnless(
        test.is_scheduler_filter_enabled("SameHostFilter"),
        'SameHostFilter is not available.')
    def test_create_servers_on_same_host(self):
        server01 = self.create_test_server(wait_until='ACTIVE')['id']

        hints = {'same_host': server01}
        server02 = self.create_test_server(scheduler_hints=hints,
                                           wait_until='ACTIVE')['id']
        host01 = self._get_host(server01)
        host02 = self._get_host(server02)
        self.assertEqual(host01, host02)

    @test.idempotent_id('cc7ca884-6e3e-42a3-a92f-c522fcf25e8e')
    @testtools.skipUnless(
        test.is_scheduler_filter_enabled("DifferentHostFilter"),
        'DifferentHostFilter is not available.')
    def test_create_servers_on_different_hosts(self):
        server01 = self.create_test_server(wait_until='ACTIVE')['id']

        hints = {'different_host': server01}
        server02 = self.create_test_server(scheduler_hints=hints,
                                           wait_until='ACTIVE')['id']
        host01 = self._get_host(server01)
        host02 = self._get_host(server02)
        self.assertNotEqual(host01, host02)

    @test.idempotent_id('7869cc84-d661-4e14-9f00-c18cdc89cf57')
    @testtools.skipUnless(
        test.is_scheduler_filter_enabled("DifferentHostFilter"),
        'DifferentHostFilter is not available.')
    def test_create_servers_on_different_hosts_with_list_of_servers(self):
        server01 = self.create_test_server(wait_until='ACTIVE')['id']

        # This scheduler-hint supports list of servers also.
        hints = {'different_host': [server01]}
        server02 = self.create_test_server(scheduler_hints=hints,
                                           wait_until='ACTIVE')['id']
        host01 = self._get_host(server01)
        host02 = self._get_host(server02)
        self.assertNotEqual(host01, host02)
