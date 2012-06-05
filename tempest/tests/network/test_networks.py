# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# All Rights Reserved.
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

from nose.plugins.attrib import attr

from tempest.common.utils.data_utils import rand_name
from tempest.tests.network import base


class NetworksTest(base.BaseNetworkTest):

    @classmethod
    def setUpClass(cls):
        super(NetworksTest, cls).setUpClass()
        cls.network = cls.create_network()
        cls.name = cls.network['name']

    @attr(type='positive')
    def test_create_delete_network(self):
        """Creates and deletes a network for a tenant"""
        name = rand_name('network')
        resp, body = self.client.create_network(name)
        self.assertEqual('202', resp['status'])
        network = body['network']
        self.assertTrue(network['id'] is not None)
        resp, body = self.client.delete_network(network['id'])
        self.assertEqual('204', resp['status'])

    @attr(type='positive')
    def test_show_network(self):
        """Verifies the details of a network"""
        resp, body = self.client.get_network(self.network['id'])
        self.assertEqual('200', resp['status'])
        network = body['network']
        self.assertEqual(self.network['id'], network['id'])
        self.assertEqual(self.name, network['name'])

    @attr(type='positive')
    def test_show_network_details(self):
        """Verifies the full details of a network"""
        resp, body = self.client.get_network_details(self.network['id'])
        self.assertEqual('200', resp['status'])
        network = body['network']
        self.assertEqual(self.network['id'], network['id'])
        self.assertEqual(self.name, network['name'])
        self.assertEqual(len(network['ports']), 0)

    @attr(type='positive')
    def test_list_networks(self):
        """Verify the network exists in the list of all networks"""
        resp, body = self.client.list_networks()
        networks = body['networks']
        found = any(n for n in networks if n['id'] == self.network['id'])
        self.assertTrue(found)

    @attr(type='positive')
    def test_list_networks_with_detail(self):
        """Verify the network exists in the detailed list of all networks"""
        resp, body = self.client.list_networks_details()
        networks = body['networks']
        found = any(n for n in networks if n['id'] == self.network['id'])
        self.assertTrue(found)
