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

import copy

from tempest.lib.services.compute import baremetal_nodes_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestBareMetalNodesClient(base.BaseComputeServiceTest):

    FAKE_NODE_INFO = {'cpus': '8',
                      'disk_gb': '64',
                      'host': '10.0.2.15',
                      'id': 'Identifier',
                      'instance_uuid': "null",
                      'interfaces': [
                          {
                              "address": "20::01",
                              "datapath_id": "null",
                              "id": 1,
                              "port_no": None
                          }
                      ],
                      'memory_mb': '8192',
                      'task_state': None}

    def setUp(self):
        super(TestBareMetalNodesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.baremetal_nodes_client = (baremetal_nodes_client.
                                       BaremetalNodesClient
                                       (fake_auth, 'compute',
                                        'regionOne'))

    def _test_bareMetal_nodes(self, operation='list', bytes_body=False):
        if operation != 'list':
            expected = {"node": self.FAKE_NODE_INFO}
            function = self.baremetal_nodes_client.show_baremetal_node
        else:
            node_info = copy.deepcopy(self.FAKE_NODE_INFO)
            del node_info['instance_uuid']
            expected = {"nodes": [node_info]}
            function = self.baremetal_nodes_client.list_baremetal_nodes

        self.check_service_client_function(
            function,
            'tempest.lib.common.rest_client.RestClient.get',
            expected, bytes_body, 200,
            baremetal_node_id='Identifier')

    def test_list_bareMetal_nodes_with_str_body(self):
        self._test_bareMetal_nodes()

    def test_list_bareMetal_nodes_with_bytes_body(self):
        self._test_bareMetal_nodes(bytes_body=True)

    def test_show_bareMetal_node_with_str_body(self):
        self._test_bareMetal_nodes('show')

    def test_show_bareMetal_node_with_bytes_body(self):
        self._test_bareMetal_nodes('show', True)
