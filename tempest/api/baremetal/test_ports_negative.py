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
from tempest.common.utils import data_utils
from tempest import exceptions as exc
from tempest import test


class TestPortsNegative(base.BaseBaremetalTest):
    """Negative tests for ports."""

    def setUp(self):
        super(TestPortsNegative, self).setUp()

        chassis = self.create_chassis()['chassis']
        self.node = self.create_node(chassis['uuid'])['node']

    @test.attr(type='negative')
    def test_create_port_invalid_mac(self):
        node_id = self.node['uuid']
        address = 'not an uuid'

        self.assertRaises(exc.BadRequest,
                          self.create_port, node_id=node_id, address=address)

    @test.attr(type='negative')
    def test_create_port_wrong_node_id(self):
        node_id = str(data_utils.rand_uuid())

        self.assertRaises(exc.BadRequest, self.create_port, node_id=node_id)
