# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


class TestPorts(base.BaseBaremetalTest):
    """Tests for ports."""

    def setUp(self):
        super(TestPorts, self).setUp()

        chassis = self.create_chassis()['chassis']
        self.node = self.create_node(chassis['uuid'])['node']

    @test.attr(type='smoke')
    def test_create_port(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        port = self.create_port(node_id=node_id, address=address)['port']

        self.assertEqual(port['address'], address)
        self.assertEqual(port['node_uuid'], node_id)

    @test.attr(type='smoke')
    def test_delete_port(self):
        node_id = self.node['uuid']
        port_id = self.create_port(node_id=node_id)['port']['uuid']

        resp = self.delete_port(port_id)

        self.assertEqual(resp['status'], '204')
        self.assertRaises(exc.NotFound, self.client.show_port, port_id)

    @test.attr(type='smoke')
    def test_show_port(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        port_id = self.create_port(node_id=node_id,
                                   address=address)['port']['uuid']

        resp, port = self.client.show_port(port_id)

        self.assertEqual(port['uuid'], port_id)
        self.assertEqual(port['address'], address)

    @test.attr(type='smoke')
    def test_list_ports(self):
        node_id = self.node['uuid']

        uuids = [self.create_port(node_id=node_id)['port']['uuid']
                 for i in range(0, 5)]

        resp, body = self.client.list_ports()
        loaded_uuids = [p['uuid'] for p in body['ports']]

        for u in uuids:
            self.assertIn(u, loaded_uuids)

    @test.attr(type='smoke')
    def test_update_port(self):
        node_id = self.node['uuid']
        port_id = self.create_port(node_id=node_id)['port']['uuid']

        new_address = data_utils.rand_mac_address()
        self.client.update_port(port_id, address=new_address)

        resp, body = self.client.show_port(port_id)
        self.assertEqual(body['address'], new_address)
