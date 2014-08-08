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

import six

from tempest.api.baremetal.admin import base
from tempest import exceptions as exc
from tempest import test


class TestNodes(base.BaseBaremetalTest):
    '''Tests for baremetal nodes.'''

    def setUp(self):
        super(TestNodes, self).setUp()

        _, self.chassis = self.create_chassis()
        _, self.node = self.create_node(self.chassis['uuid'])

    def _assertExpected(self, expected, actual):
        # Check if not expected keys/values exists in actual response body
        for key, value in six.iteritems(expected):
            if key not in ('created_at', 'updated_at'):
                self.assertIn(key, actual)
                self.assertEqual(value, actual[key])

    @test.attr(type='smoke')
    def test_create_node(self):
        params = {'cpu_arch': 'x86_64',
                  'cpu_num': '12',
                  'storage': '10240',
                  'memory': '1024'}

        resp, body = self.create_node(self.chassis['uuid'], **params)
        self.assertEqual('201', resp['status'])
        self._assertExpected(params, body['properties'])

    @test.attr(type='smoke')
    def test_delete_node(self):
        resp, node = self.create_node(self.chassis['uuid'])
        self.assertEqual('201', resp['status'])

        resp = self.delete_node(node['uuid'])

        self.assertEqual(resp['status'], '204')
        self.assertRaises(exc.NotFound, self.client.show_node, node['uuid'])

    @test.attr(type='smoke')
    def test_show_node(self):
        resp, loaded_node = self.client.show_node(self.node['uuid'])
        self.assertEqual('200', resp['status'])
        self._assertExpected(self.node, loaded_node)

    @test.attr(type='smoke')
    def test_list_nodes(self):
        resp, body = self.client.list_nodes()
        self.assertEqual('200', resp['status'])
        self.assertIn(self.node['uuid'],
                      [i['uuid'] for i in body['nodes']])

    @test.attr(type='smoke')
    def test_update_node(self):
        props = {'cpu_arch': 'x86_64',
                 'cpu_num': '12',
                 'storage': '10',
                 'memory': '128'}

        resp, node = self.create_node(self.chassis['uuid'], **props)
        self.assertEqual('201', resp['status'])

        new_p = {'cpu_arch': 'x86',
                 'cpu_num': '1',
                 'storage': '10000',
                 'memory': '12300'}

        resp, body = self.client.update_node(node['uuid'], properties=new_p)
        self.assertEqual('200', resp['status'])
        resp, node = self.client.show_node(node['uuid'])
        self.assertEqual('200', resp['status'])
        self._assertExpected(new_p, node['properties'])

    @test.attr(type='smoke')
    def test_validate_driver_interface(self):
        resp, body = self.client.validate_driver_interface(self.node['uuid'])
        self.assertEqual('200', resp['status'])
        core_interfaces = ['power', 'deploy']
        for interface in core_interfaces:
            self.assertIn(interface, body)
