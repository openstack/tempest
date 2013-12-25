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

from tempest.api.network import base
from tempest.common.utils import data_utils


class ExternalNetworksTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ExternalNetworksTestJSON, cls).setUpClass()
        cls.network = cls.create_network()

    def _create_network(self, external=True):
        post_body = {'name': data_utils.rand_name('network-')}
        if external:
            post_body['router:external'] = external
        resp, body = self.admin_client.create_network(**post_body)
        network = body['network']
        self.assertEqual('201', resp['status'])
        self.addCleanup(self.admin_client.delete_network, network['id'])
        return network

    def test_create_external_network(self):
        # Create a network as an admin user specifying the
        # external network extension attribute
        ext_network = self._create_network()
        # Verifies router:external parameter
        self.assertIsNotNone(ext_network['id'])
        self.assertTrue(ext_network['router:external'])

    def test_update_external_network(self):
        # Update a network as an admin user specifying the
        # external network extension attribute
        network = self._create_network(external=False)
        self.assertFalse(network.get('router:external', False))
        update_body = {'router:external': True}
        resp, body = self.admin_client.update_network(network['id'],
                                                      **update_body)
        self.assertEqual('200', resp['status'])
        updated_network = body['network']
        # Verify that router:external parameter was updated
        self.assertTrue(updated_network['router:external'])

    def test_list_external_networks(self):
        # Create external_net
        external_network = self._create_network()
        # List networks as a normal user and confirm the external
        # network extension attribute is returned for those networks
        # that were created as external
        resp, body = self.client.list_networks()
        self.assertEqual('200', resp['status'])
        networks_list = [net['id'] for net in body['networks']]
        self.assertIn(external_network['id'], networks_list)
        self.assertIn(self.network['id'], networks_list)
        for net in body['networks']:
            if net['id'] == self.network['id']:
                self.assertFalse(net['router:external'])
            elif net['id'] == external_network['id']:
                self.assertTrue(net['router:external'])

    def test_show_external_networks_attribute(self):
        # Create external_net
        external_network = self._create_network()
        # Show an external network as a normal user and confirm the
        # external network extension attribute is returned.
        resp, body = self.client.show_network(external_network['id'])
        self.assertEqual('200', resp['status'])
        show_ext_net = body['network']
        self.assertEqual(external_network['name'], show_ext_net['name'])
        self.assertEqual(external_network['id'], show_ext_net['id'])
        self.assertTrue(show_ext_net['router:external'])
        resp, body = self.client.show_network(self.network['id'])
        self.assertEqual('200', resp['status'])
        show_net = body['network']
        # Verify with show that router:external is False for network
        self.assertEqual(self.network['name'], show_net['name'])
        self.assertEqual(self.network['id'], show_net['id'])
        self.assertFalse(show_net['router:external'])


class ExternalNetworksTestXML(ExternalNetworksTestJSON):
    _interface = 'xml'
