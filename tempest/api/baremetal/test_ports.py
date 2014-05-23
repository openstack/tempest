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

        result = self.create_port(node_id=node_id, address=address)

        port = result['port']

        resp, body = self.client.show_port(port['uuid'])

        self.assertEqual(200, resp.status)
        self.assertEqual(port['uuid'], body['uuid'])
        self.assertEqual(address, body['address'])
        self.assertEqual({}, body['extra'])
        self.assertEqual(node_id, body['node_uuid'])

    @test.attr(type='smoke')
    def test_create_port_specifying_uuid(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        uuid = data_utils.rand_uuid()

        self.create_port(node_id=node_id, address=address, uuid=uuid)

        resp, body = self.client.show_port(uuid)

        self.assertEqual(200, resp.status)
        self.assertEqual(uuid, body['uuid'])
        self.assertEqual(address, body['address'])
        self.assertEqual({}, body['extra'])
        self.assertEqual(node_id, body['node_uuid'])

    @test.attr(type='smoke')
    def test_create_port_with_extra(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key': 'value'}

        result = self.create_port(node_id=node_id, address=address,
                                  extra=extra)
        port = result['port']

        resp, body = self.client.show_port(port['uuid'])

        self.assertEqual(200, resp.status)
        self.assertEqual(port['uuid'], body['uuid'])
        self.assertEqual(address, body['address'])
        self.assertEqual(extra, body['extra'])
        self.assertEqual(node_id, body['node_uuid'])

    @test.attr(type='smoke')
    def test_delete_port(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        port_id = self.create_port(node_id=node_id, address=address)['port'][
            'uuid']

        resp = self.delete_port(port_id)

        self.assertEqual(204, resp.status)
        self.assertRaises(exc.NotFound, self.client.show_port, port_id)

    @test.attr(type='smoke')
    def test_show_port(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key': 'value'}

        port_id = self.create_port(node_id=node_id, address=address,
                                   extra=extra)['port']['uuid']

        resp, port = self.client.show_port(port_id)

        self.assertEqual(200, resp.status)
        self.assertEqual(port_id, port['uuid'])
        self.assertEqual(address, port['address'])
        self.assertEqual(extra, port['extra'])

    @test.attr(type='smoke')
    def test_show_port_with_links(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        port_id = self.create_port(node_id=node_id, address=address)['port'][
            'uuid']

        resp, body = self.client.show_port(port_id)

        self.assertEqual(200, resp.status)
        self.assertIn('links', body.keys())
        self.assertEqual(2, len(body['links']))
        self.assertIn(port_id, body['links'][0]['href'])

    @test.attr(type='smoke')
    def test_list_ports(self):
        node_id = self.node['uuid']

        uuids = [self.create_port(node_id=node_id,
                                  address=data_utils.rand_mac_address())
                 ['port']['uuid'] for i in xrange(5)]

        resp, body = self.client.list_ports()
        self.assertEqual(200, resp.status)
        loaded_uuids = [p['uuid'] for p in body['ports']]

        for uuid in uuids:
            self.assertIn(uuid, loaded_uuids)

        # Verify self links.
        for port in body['ports']:
            self.validate_self_link('ports', port['uuid'],
                                    port['links'][0]['href'])

    @test.attr(type='smoke')
    def test_list_with_limit(self):
        node_id = self.node['uuid']

        for i in xrange(5):
            self.create_port(node_id=node_id,
                             address=data_utils.rand_mac_address())

        resp, body = self.client.list_ports(limit=3)
        self.assertEqual(200, resp.status)
        self.assertEqual(3, len(body['ports']))

        next_marker = body['ports'][-1]['uuid']
        self.assertIn(next_marker, body['next'])

    def test_list_ports_details(self):
        node_id = self.node['uuid']

        uuids = [
            self.create_port(node_id=node_id,
                             address=data_utils.rand_mac_address())
            ['port']['uuid'] for i in range(0, 5)]

        resp, body = self.client.list_ports_detail()
        self.assertEqual(200, resp.status)

        ports_dict = dict((port['uuid'], port) for port in body['ports']
                          if port['uuid'] in uuids)

        for uuid in uuids:
            self.assertIn(uuid, ports_dict)
            port = ports_dict[uuid]
            self.assertIn('extra', port)
            self.assertIn('node_uuid', port)
            # never expose the node_id
            self.assertNotIn('node_id', port)
            # Verify self link.
            self.validate_self_link('ports', port['uuid'],
                                    port['links'][0]['href'])

    @test.attr(type='smoke')
    def test_update_port_replace(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}

        port_id = self.create_port(node_id=node_id, address=address,
                                   extra=extra)['port']['uuid']

        new_address = data_utils.rand_mac_address()
        new_extra = {'key1': 'new-value1', 'key2': 'new-value2',
                     'key3': 'new-value3'}

        patch = [{'path': '/address',
                  'op': 'replace',
                  'value': new_address},
                 {'path': '/extra/key1',
                  'op': 'replace',
                  'value': new_extra['key1']},
                 {'path': '/extra/key2',
                  'op': 'replace',
                  'value': new_extra['key2']},
                 {'path': '/extra/key3',
                  'op': 'replace',
                  'value': new_extra['key3']}]

        self.client.update_port(port_id, patch)

        resp, body = self.client.show_port(port_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(new_address, body['address'])
        self.assertEqual(new_extra, body['extra'])

    @test.attr(type='smoke')
    def test_update_port_remove(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}

        port_id = self.create_port(node_id=node_id, address=address,
                                   extra=extra)['port']['uuid']

        # Removing one item from the collection
        resp, _ = self.client.update_port(port_id, [{'path': '/extra/key2',
                                                     'op': 'remove'}])
        self.assertEqual(200, resp.status)
        extra.pop('key2')
        resp, body = self.client.show_port(port_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(extra, body['extra'])

        # Removing the collection
        resp, _ = self.client.update_port(port_id, [{'path': '/extra',
                                                     'op': 'remove'}])
        self.assertEqual(200, resp.status)
        resp, body = self.client.show_port(port_id)
        self.assertEqual(200, resp.status)
        self.assertEqual({}, body['extra'])

        # Assert nothing else was changed
        self.assertEqual(node_id, body['node_uuid'])
        self.assertEqual(address, body['address'])

    @test.attr(type='smoke')
    def test_update_port_add(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        port_id = self.create_port(node_id=node_id, address=address)['port'][
            'uuid']

        extra = {'key1': 'value1', 'key2': 'value2'}

        patch = [{'path': '/extra/key1',
                  'op': 'add',
                  'value': extra['key1']},
                 {'path': '/extra/key2',
                  'op': 'add',
                  'value': extra['key2']}]

        self.client.update_port(port_id, patch)

        resp, body = self.client.show_port(port_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(extra, body['extra'])

    @test.attr(type='smoke')
    def test_update_port_mixed_ops(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key1': 'value1', 'key2': 'value2'}

        port_id = self.create_port(node_id=node_id, address=address,
                                   extra=extra)['port']['uuid']

        new_address = data_utils.rand_mac_address()
        new_extra = {'key1': 'new-value1', 'key3': 'new-value3'}

        patch = [{'path': '/address',
                  'op': 'replace',
                  'value': new_address},
                 {'path': '/extra/key1',
                  'op': 'replace',
                  'value': new_extra['key1']},
                 {'path': '/extra/key2',
                  'op': 'remove'},
                 {'path': '/extra/key3',
                  'op': 'add',
                  'value': new_extra['key3']}]

        self.client.update_port(port_id, patch)

        resp, body = self.client.show_port(port_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(new_address, body['address'])
        self.assertEqual(new_extra, body['extra'])
