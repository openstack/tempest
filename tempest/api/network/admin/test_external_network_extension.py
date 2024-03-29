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

import testtools

from tempest.api.network import base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators

CONF = config.CONF


class ExternalNetworksTestJSON(base.BaseAdminNetworkTest):
    """Test external networks"""

    @classmethod
    def resource_setup(cls):
        super(ExternalNetworksTestJSON, cls).resource_setup()
        cls.network = cls.create_network()

    def _create_network(self, external=True):
        post_body = {'name': data_utils.rand_name(
            name='network-', prefix=CONF.resource_name_prefix)}
        if external:
            post_body['router:external'] = external
        body = self.admin_networks_client.create_network(**post_body)
        network = body['network']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.admin_networks_client.delete_network, network['id'])
        return network

    @decorators.idempotent_id('462be770-b310-4df9-9c42-773217e4c8b1')
    def test_create_external_network(self):
        """Test creating external network

        Create a network as an admin user specifying the
        external network extension attribute
        """
        ext_network = self._create_network()
        # Verifies router:external parameter
        self.assertIsNotNone(ext_network['id'])
        self.assertTrue(ext_network['router:external'])

    @decorators.idempotent_id('4db5417a-e11c-474d-a361-af00ebef57c5')
    def test_update_external_network(self):
        """Test updating external network

        Update a network as an admin user specifying the
        external network extension attribute
        """
        network = self._create_network(external=False)
        self.assertFalse(network.get('router:external', False))
        update_body = {'router:external': True}
        body = self.admin_networks_client.update_network(network['id'],
                                                         **update_body)
        updated_network = body['network']
        # Verify that router:external parameter was updated
        self.assertTrue(updated_network['router:external'])

    @decorators.idempotent_id('39be4c9b-a57e-4ff9-b7c7-b218e209dfcc')
    def test_list_external_networks(self):
        """Test listing external networks"""
        # Create external_net
        external_network = self._create_network()
        # List networks as a normal user and confirm the external
        # network extension attribute is returned for those networks
        # that were created as external
        body = self.networks_client.list_networks()
        networks_list = [net['id'] for net in body['networks']]
        self.assertIn(external_network['id'], networks_list)
        self.assertIn(self.network['id'], networks_list)
        for net in body['networks']:
            if net['id'] == self.network['id']:
                self.assertFalse(net['router:external'])
            elif net['id'] == external_network['id']:
                self.assertTrue(net['router:external'])

    @decorators.idempotent_id('2ac50ab2-7ebd-4e27-b3ce-a9e399faaea2')
    def test_show_external_networks_attribute(self):
        """Test showing external network attribute"""
        # Create external_net
        external_network = self._create_network()
        # Show an external network as a normal user and confirm the
        # external network extension attribute is returned.
        body = self.networks_client.show_network(external_network['id'])
        show_ext_net = body['network']
        self.assertEqual(external_network['name'], show_ext_net['name'])
        self.assertEqual(external_network['id'], show_ext_net['id'])
        self.assertTrue(show_ext_net['router:external'])
        body = self.networks_client.show_network(self.network['id'])
        show_net = body['network']
        # Verify with show that router:external is False for network
        self.assertEqual(self.network['name'], show_net['name'])
        self.assertEqual(self.network['id'], show_net['id'])
        self.assertFalse(show_net['router:external'])

    @decorators.idempotent_id('82068503-2cf2-4ed4-b3be-ecb89432e4bb')
    @testtools.skipUnless(CONF.network_feature_enabled.floating_ips,
                          'Floating ips are not availabled')
    def test_delete_external_networks_with_floating_ip(self):
        """Test deleting external network with unassociated floating ips

        Verifies external network can be deleted while still holding
        (unassociated) floating IPs
        """
        body = self.admin_networks_client.create_network(
            **{'router:external': True})
        external_network = body['network']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_networks_client.delete_network,
                        external_network['id'])
        subnet = self.create_subnet(
            external_network, client=self.admin_subnets_client,
            enable_dhcp=False)
        body = self.admin_floating_ips_client.create_floatingip(
            floating_network_id=external_network['id'])
        created_floating_ip = body['floatingip']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_floating_ips_client.delete_floatingip,
                        created_floating_ip['id'])
        if utils.is_extension_enabled('filter-validation', 'network'):
            floatingip_list = self.admin_floating_ips_client.list_floatingips(
                floating_network_id=external_network['id'])
        else:
            # NOTE(hongbin): This is for testing the backward-compatibility
            # of neutron API although the parameter is a wrong filter
            # for listing floating IPs.
            floatingip_list = self.admin_floating_ips_client.list_floatingips(
                invalid_filter=external_network['id'])
        self.assertIn(created_floating_ip['id'],
                      (f['id'] for f in floatingip_list['floatingips']))
        self.admin_networks_client.delete_network(external_network['id'])
        # Verifies floating ip is deleted
        floatingip_list = self.admin_floating_ips_client.list_floatingips()
        self.assertNotIn(created_floating_ip['id'],
                         (f['id'] for f in floatingip_list['floatingips']))
        # Verifies subnet is deleted
        subnet_list = self.admin_subnets_client.list_subnets()
        self.assertNotIn(subnet['id'],
                         (s['id'] for s in subnet_list))
