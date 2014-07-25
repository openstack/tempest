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

        resp, self.chassis = self.create_chassis()
        self.assertEqual('201', resp['status'])

        resp, self.node = self.create_node(self.chassis['uuid'])
        self.assertEqual('201', resp['status'])

    @test.attr(type=['negative', 'smoke'])
    def test_create_port_malformed_mac(self):
        node_id = self.node['uuid']
        address = 'malformed:mac'

        self.assertRaises(exc.BadRequest,
                          self.create_port, node_id=node_id, address=address)

    @test.attr(type=['negative', 'smoke'])
    def test_create_port_malformed_extra(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key': 0.123}
        self.assertRaises(exc.BadRequest,
                          self.create_port, node_id=node_id,
                          address=address, extra=extra)

    @test.attr(type=['negative', 'smoke'])
    def test_create_port_nonexsistent_node_id(self):
        node_id = str(data_utils.rand_uuid())
        address = data_utils.rand_mac_address()
        self.assertRaises(exc.BadRequest, self.create_port, node_id=node_id,
                          address=address)

    @test.attr(type=['negative', 'smoke'])
    def test_show_port_malformed_uuid(self):
        self.assertRaises(exc.BadRequest, self.client.show_port,
                          'malformed:uuid')

    @test.attr(type=['negative', 'smoke'])
    def test_show_port_nonexistent_uuid(self):
        self.assertRaises(exc.NotFound, self.client.show_port,
                          data_utils.rand_uuid())

    @test.attr(type=['negative', 'smoke'])
    def test_show_port_by_mac_not_allowed(self):
        self.assertRaises(exc.BadRequest, self.client.show_port,
                          data_utils.rand_mac_address())

    @test.attr(type=['negative', 'smoke'])
    def test_create_port_duplicated_port_uuid(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        uuid = data_utils.rand_uuid()

        self.create_port(node_id=node_id, address=address, uuid=uuid)
        self.assertRaises(exc.Conflict, self.create_port, node_id=node_id,
                          address=address, uuid=uuid)

    @test.attr(type=['negative', 'smoke'])
    def test_create_port_no_mandatory_field_node_id(self):
        address = data_utils.rand_mac_address()

        self.assertRaises(exc.BadRequest, self.create_port, node_id=None,
                          address=address)

    @test.attr(type=['negative', 'smoke'])
    def test_create_port_no_mandatory_field_mac(self):
        node_id = self.node['uuid']

        self.assertRaises(exc.BadRequest, self.create_port, node_id=node_id,
                          address=None)

    @test.attr(type=['negative', 'smoke'])
    def test_create_port_malformed_port_uuid(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        uuid = 'malformed:uuid'

        self.assertRaises(exc.BadRequest, self.create_port, node_id=node_id,
                          address=address, uuid=uuid)

    @test.attr(type=['negative', 'smoke'])
    def test_create_port_malformed_node_id(self):
        address = data_utils.rand_mac_address()
        self.assertRaises(exc.BadRequest, self.create_port,
                          node_id='malformed:nodeid', address=address)

    @test.attr(type=['negative', 'smoke'])
    def test_create_port_duplicated_mac(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        self.create_port(node_id=node_id, address=address)
        self.assertRaises(exc.Conflict,
                          self.create_port, node_id=node_id,
                          address=address)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_by_mac_not_allowed(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key': 'value'}

        self.create_port(node_id=node_id, address=address, extra=extra)

        patch = [{'path': '/extra/key',
                  'op': 'replace',
                  'value': 'new-value'}]

        self.assertRaises(exc.BadRequest,
                          self.client.update_port, address,
                          patch)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_nonexistent(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key': 'value'}

        resp, port = self.create_port(node_id=node_id, address=address,
                                      extra=extra)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        resp, body = self.client.delete_port(port_id)
        self.assertEqual('204', resp['status'])

        patch = [{'path': '/extra/key',
                  'op': 'replace',
                  'value': 'new-value'}]
        self.assertRaises(exc.NotFound,
                          self.client.update_port, port_id, patch)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_malformed_port_uuid(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        self.create_port(node_id=node_id, address=address)

        new_address = data_utils.rand_mac_address()
        self.assertRaises(exc.BadRequest, self.client.update_port,
                          uuid='malformed:uuid',
                          patch=[{'path': '/address', 'op': 'replace',
                                  'value': new_address}])

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_add_malformed_extra(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        self.assertRaises(exc.BadRequest, self.client.update_port, port_id,
                          [{'path': '/extra/key', ' op': 'add',
                            'value': 0.123}])

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_add_whole_malformed_extra(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        self.assertRaises(exc.BadRequest, self.client.update_port, port_id,
                          [{'path': '/extra',
                            'op': 'add',
                            'value': [1, 2, 3, 4, 'a']}])

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_add_nonexistent_property(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        self.assertRaises(exc.BadRequest, self.client.update_port, port_id,
                          [{'path': '/nonexistent', ' op': 'add',
                            'value': 'value'}])

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_replace_node_id_with_malformed(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        patch = [{'path': '/node_uuid',
                  'op': 'replace',
                  'value': 'malformed:node_uuid'}]
        self.assertRaises(exc.BadRequest,
                          self.client.update_port, port_id, patch)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_replace_mac_with_duplicated(self):
        node_id = self.node['uuid']
        address1 = data_utils.rand_mac_address()
        address2 = data_utils.rand_mac_address()

        resp, port1 = self.create_port(node_id=node_id, address=address1)
        self.assertEqual('201', resp['status'])

        resp, port2 = self.create_port(node_id=node_id, address=address2)
        self.assertEqual('201', resp['status'])
        port_id = port2['uuid']

        patch = [{'path': '/address',
                  'op': 'replace',
                  'value': address1}]
        self.assertRaises(exc.Conflict,
                          self.client.update_port, port_id, patch)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_replace_node_id_with_nonexistent(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        patch = [{'path': '/node_uuid',
                  'op': 'replace',
                  'value': data_utils.rand_uuid()}]
        self.assertRaises(exc.BadRequest,
                          self.client.update_port, port_id, patch)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_replace_mac_with_malformed(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        patch = [{'path': '/address',
                  'op': 'replace',
                  'value': 'malformed:mac'}]

        self.assertRaises(exc.BadRequest,
                          self.client.update_port, port_id, patch)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_replace_extra_item_with_malformed(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key': 'value'}

        resp, port = self.create_port(node_id=node_id, address=address,
                                      extra=extra)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        patch = [{'path': '/extra/key',
                  'op': 'replace',
                  'value': 0.123}]
        self.assertRaises(exc.BadRequest,
                          self.client.update_port, port_id, patch)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_replace_whole_extra_with_malformed(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        patch = [{'path': '/extra',
                  'op': 'replace',
                  'value': [1, 2, 3, 4, 'a']}]

        self.assertRaises(exc.BadRequest,
                          self.client.update_port, port_id, patch)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_replace_nonexistent_property(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        patch = [{'path': '/nonexistent', ' op': 'replace', 'value': 'value'}]

        self.assertRaises(exc.BadRequest,
                          self.client.update_port, port_id, patch)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_remove_mandatory_field_mac(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        self.assertRaises(exc.BadRequest, self.client.update_port, port_id,
                          [{'path': '/address', 'op': 'remove'}])

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_remove_mandatory_field_port_uuid(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        self.assertRaises(exc.BadRequest, self.client.update_port, port_id,
                          [{'path': '/uuid', 'op': 'remove'}])

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_remove_nonexistent_property(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        resp, port = self.create_port(node_id=node_id, address=address)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

        self.assertRaises(exc.BadRequest, self.client.update_port, port_id,
                          [{'path': '/nonexistent', 'op': 'remove'}])

    @test.attr(type=['negative', 'smoke'])
    def test_delete_port_by_mac_not_allowed(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()

        self.create_port(node_id=node_id, address=address)
        self.assertRaises(exc.BadRequest, self.client.delete_port, address)

    @test.attr(type=['negative', 'smoke'])
    def test_update_port_mixed_ops_integrity(self):
        node_id = self.node['uuid']
        address = data_utils.rand_mac_address()
        extra = {'key1': 'value1', 'key2': 'value2'}

        resp, port = self.create_port(node_id=node_id, address=address,
                                      extra=extra)
        self.assertEqual('201', resp['status'])
        port_id = port['uuid']

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
                  'value': new_extra['key3']},
                 {'path': '/nonexistent',
                  'op': 'replace',
                  'value': 'value'}]

        self.assertRaises(exc.BadRequest, self.client.update_port, port_id,
                          patch)

        # patch should not be applied
        resp, body = self.client.show_port(port_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(address, body['address'])
        self.assertEqual(extra, body['extra'])
