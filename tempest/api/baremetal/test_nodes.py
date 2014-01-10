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

import six

from tempest.api.baremetal import base
from tempest import exceptions as exc
from tempest import test


class TestNodes(base.BaseBaremetalTest):
    '''Tests for baremetal nodes.'''

    def setUp(self):
        super(TestNodes, self).setUp()

        self.chassis = self.create_chassis()['chassis']

    @test.attr(type='smoke')
    def test_create_node(self):
        params = {'cpu_arch': 'x86_64',
                  'cpu_num': '12',
                  'storage': '10240',
                  'memory': '1024'}

        node = self.create_node(self.chassis['uuid'], **params)['node']

        for key in params:
            self.assertEqual(node['properties'][key], params[key])

    @test.attr(type='smoke')
    def test_delete_node(self):
        node = self.create_node(self.chassis['uuid'])['node']
        node_id = node['uuid']

        resp = self.delete_node(node_id)

        self.assertEqual(resp['status'], '204')
        self.assertRaises(exc.NotFound, self.client.show_node, node_id)

    @test.attr(type='smoke')
    def test_show_node(self):
        params = {'cpu_arch': 'x86_64',
                  'cpu_num': '4',
                  'storage': '100',
                  'memory': '512'}

        created_node = self.create_node(self.chassis['uuid'], **params)['node']
        resp, loaded_node = self.client.show_node(created_node['uuid'])

        for key, val in created_node.iteritems():
            if key not in ('created_at', 'updated_at'):
                self.assertEqual(loaded_node[key], val)

    @test.attr(type='smoke')
    def test_list_nodes(self):
        uuids = [self.create_node(self.chassis['uuid'])['node']['uuid']
                 for i in range(0, 5)]

        resp, body = self.client.list_nodes()
        loaded_uuids = [n['uuid'] for n in body['nodes']]

        for u in uuids:
            self.assertIn(u, loaded_uuids)

    @test.attr(type='smoke')
    def test_update_node(self):
        props = {'cpu_arch': 'x86_64',
                 'cpu_num': '12',
                 'storage': '10',
                 'memory': '128'}

        node = self.create_node(self.chassis['uuid'], **props)['node']
        node_id = node['uuid']

        new_props = {'cpu_arch': 'x86',
                     'cpu_num': '1',
                     'storage': '10000',
                     'memory': '12300'}

        self.client.update_node(node_id, properties=new_props)
        resp, node = self.client.show_node(node_id)

        for name, value in six.iteritems(new_props):
            if name not in ('created_at', 'updated_at'):
                self.assertEqual(node['properties'][name], value)
