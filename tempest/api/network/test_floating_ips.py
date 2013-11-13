# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
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

from tempest.api.network import base
from tempest.common.utils import data_utils
from tempest.test import attr


class FloatingIPTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Quantum API using the REST client for
    Neutron:

        Create a Floating IP
        Update a Floating IP
        Delete a Floating IP
        List all Floating IPs
        Show Floating IP details

    v2.0 of the Neutron API is assumed. It is also assumed that the following
    options are defined in the [network] section of etc/tempest.conf:

        public_network_id which is the id for the external network present
    """

    @classmethod
    def setUpClass(cls):
        super(FloatingIPTestJSON, cls).setUpClass()
        cls.ext_net_id = cls.config.network.public_network_id

        # Create network, subnet, router and add interface
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.router = cls.create_router(data_utils.rand_name('router-'),
                                       external_network_id=cls.ext_net_id)
        cls.create_router_interface(cls.router['id'], cls.subnet['id'])
        cls.port = list()
        # Create two ports one each for Creation and Updating of floatingIP
        for i in range(2):
            cls.create_port(cls.network)

    @attr(type='smoke')
    def test_create_list_show_update_delete_floating_ip(self):
        # Creates a floating IP
        created_floating_ip = self.create_floating_ip(
            self.ext_net_id, port_id=self.ports[0]['id'])
        self.assertIsNotNone(created_floating_ip['id'])
        self.assertIsNotNone(created_floating_ip['tenant_id'])
        self.assertIsNotNone(created_floating_ip['floating_ip_address'])
        self.assertEqual(created_floating_ip['port_id'], self.ports[0]['id'])
        self.assertEqual(created_floating_ip['floating_network_id'],
                         self.ext_net_id)
        # Verifies the details of a floating_ip
        resp, floating_ip = self.client.show_floating_ip(
            created_floating_ip['id'])
        self.assertEqual('200', resp['status'])
        shown_floating_ip = floating_ip['floatingip']
        self.assertEqual(shown_floating_ip['id'], created_floating_ip['id'])
        self.assertEqual(shown_floating_ip['floating_network_id'],
                         self.ext_net_id)
        self.assertEqual(shown_floating_ip['tenant_id'],
                         created_floating_ip['tenant_id'])
        self.assertEqual(shown_floating_ip['floating_ip_address'],
                         created_floating_ip['floating_ip_address'])
        self.assertEqual(shown_floating_ip['port_id'], self.ports[0]['id'])

        # Verify the floating ip exists in the list of all floating_ips
        resp, floating_ips = self.client.list_floatingips()
        self.assertEqual('200', resp['status'])
        floatingip_id_list = list()
        for f in floating_ips['floatingips']:
            floatingip_id_list.append(f['id'])
        self.assertIn(created_floating_ip['id'], floatingip_id_list)
        # Associate floating IP to the other port
        resp, floating_ip = self.client.update_floating_ip(
            created_floating_ip['id'], port_id=self.ports[1]['id'])
        self.assertEqual('200', resp['status'])
        updated_floating_ip = floating_ip['floatingip']
        self.assertEqual(updated_floating_ip['port_id'], self.ports[1]['id'])
        self.assertEqual(updated_floating_ip['fixed_ip_address'],
                         self.ports[1]['fixed_ips'][0]['ip_address'])
        self.assertEqual(updated_floating_ip['router_id'], self.router['id'])

        # Disassociate floating IP from the port
        resp, floating_ip = self.client.update_floating_ip(
            created_floating_ip['id'], port_id=None)
        self.assertEqual('200', resp['status'])
        updated_floating_ip = floating_ip['floatingip']
        self.assertIsNone(updated_floating_ip['port_id'])
        self.assertIsNone(updated_floating_ip['fixed_ip_address'])
        self.assertIsNone(updated_floating_ip['router_id'])


class FloatingIPTestXML(FloatingIPTestJSON):
    _interface = 'xml'
