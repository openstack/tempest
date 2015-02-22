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

    @test.attr(type='smoke')
    def test_list_baremetal_nodes(self):
        # List all baremetal nodes.
        baremetal_nodes = self.client.list_baremetal_nodes()
        self.assertNotEmpty(baremetal_nodes, "No baremetal nodes found.")

        for node in baremetal_nodes:
            baremetal_node = self.client.get_baremetal_node(node['id'])
            self.assertEqual(node['id'], baremetal_node['id'])
