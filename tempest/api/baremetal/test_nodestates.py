# Copyright 2014 NEC Corporation.  All rights reserved.
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

from tempest.api.baremetal import base
from tempest import test


class TestNodeStates(base.BaseBaremetalTest):
    """Tests for baremetal NodeStates."""

    @classmethod
    def setUpClass(self):
        super(TestNodeStates, self).setUpClass()
        chassis = self.create_chassis()['chassis']
        self.node = self.create_node(chassis['uuid'])['node']

    @test.attr(type='smoke')
    def test_list_nodestates(self):
        resp, nodestates = self.client.list_nodestates(self.node['uuid'])
        self.assertEqual('200', resp['status'])
        for key in nodestates:
            self.assertEqual(nodestates[key], self.node[key])
