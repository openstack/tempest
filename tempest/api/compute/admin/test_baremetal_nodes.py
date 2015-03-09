# Copyright 2015 NEC Corporation.  All rights reserved.
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

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class BaremetalNodesAdminTestJSON(base.BaseV2ComputeAdminTest):
    """
    Tests Baremetal API
    """

    @classmethod
    def resource_setup(cls):
        super(BaremetalNodesAdminTestJSON, cls).resource_setup()
        if not CONF.service_available.ironic:
            skip_msg = ('%s skipped as Ironic is not available' % cls.__name__)
            raise cls.skipException(skip_msg)
        cls.client = cls.os_adm.baremetal_nodes_client
        cls.ironic_client = cls.os_adm.baremetal_client

    @test.attr(type=['smoke', 'baremetal'])
    @test.idempotent_id('e475aa6e-416d-4fa4-b3af-28d5e84250fb')
    def test_list_get_baremetal_nodes(self):
        # Create some test nodes in Ironic directly
        test_nodes = []
        for i in range(0, 3):
            _, node = self.ironic_client.create_node()
            test_nodes.append(node)
            self.addCleanup(self.ironic_client.delete_node, node['uuid'])

        # List all baremetal nodes and ensure our created test nodes are
        # listed
        bm_node_ids = set([n['id'] for n in
                           self.client.list_baremetal_nodes()])
        test_node_ids = set([n['uuid'] for n in test_nodes])
        self.assertTrue(test_node_ids.issubset(bm_node_ids))

        # Test getting each individually
        for node in test_nodes:
            baremetal_node = self.client.get_baremetal_node(node['uuid'])
            self.assertEqual(node['uuid'], baremetal_node['id'])
