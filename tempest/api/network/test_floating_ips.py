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
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr


class FloatingIPTest(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Quantum API using the REST client for
    Quantum:

        Create a Floating IP
        Update a Floating IP
        Delete a Floating IP
        List all Floating IPs
        Show Floating IP details

    v2.0 of the Quantum API is assumed. It is also assumed that the following
    options are defined in the [network] section of etc/tempest.conf:

        public_network_id which is the id for the external network present
    """

    @classmethod
    def setUpClass(cls):
        super(FloatingIPTest, cls).setUpClass()
        cls.ext_net_id = cls.config.network.public_network_id

        # Create network, subnet, router and add interface
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        resp, router = cls.client.create_router(
            rand_name('router-'),
            external_gateway_info={"network_id":
                                   cls.network_cfg.public_network_id})
        cls.router = router['router']
        resp, _ = cls.client.add_router_interface_with_subnet_id(
            cls.router['id'], cls.subnet['id'])
        cls.port = list()
        # Create two ports one each for Creation and Updating of floatingIP
        for i in range(2):
            resp, port = cls.client.create_port(cls.network['id'])
            cls.port.append(port['port'])

    @classmethod
    def tearDownClass(cls):
        cls.client.remove_router_interface_with_subnet_id(cls.router['id'],
                                                          cls.subnet['id'])
        for i in range(2):
            cls.client.delete_port(cls.port[i]['id'])
        cls.client.delete_router(cls.router['id'])
        super(FloatingIPTest, cls).tearDownClass()

    def _delete_floating_ip(self, floating_ip_id):
        # Deletes a floating IP and verifies if it is deleted or not
        resp, _ = self.client.delete_floating_ip(floating_ip_id)
        self.assertEqual(204, resp.status)
        # Asserting that the floating_ip is not found in list after deletion
        resp, floating_ips = self.client.list_floating_ips()
        floatingip_id_list = list()
        for f in floating_ips['floatingips']:
            floatingip_id_list.append(f['id'])
        self.assertNotIn(floating_ip_id, floatingip_id_list)

    @attr(type='smoke')
    def test_create_list_show_update_delete_floating_ip(self):
        # Creates a floating IP
        resp, floating_ip = self.client.create_floating_ip(
            self.ext_net_id, port_id=self.port[0]['id'])
        self.assertEqual('201', resp['status'])
        create_floating_ip = floating_ip['floatingip']
        self.assertIsNotNone(create_floating_ip['id'])
        self.assertIsNotNone(create_floating_ip['tenant_id'])
        self.assertIsNotNone(create_floating_ip['floating_ip_address'])
        self.assertEqual(create_floating_ip['port_id'], self.port[0]['id'])
        self.assertEqual(create_floating_ip['floating_network_id'],
                         self.ext_net_id)
        self.addCleanup(self._delete_floating_ip, create_floating_ip['id'])
        # Verifies the details of a floating_ip
        resp, floating_ip = self.client.show_floating_ip(
            create_floating_ip['id'])
        self.assertEqual('200', resp['status'])
        show_floating_ip = floating_ip['floatingip']
        self.assertEqual(show_floating_ip['id'], create_floating_ip['id'])
        self.assertEqual(show_floating_ip['floating_network_id'],
                         self.ext_net_id)
        self.assertEqual(show_floating_ip['tenant_id'],
                         create_floating_ip['tenant_id'])
        self.assertEqual(show_floating_ip['floating_ip_address'],
                         create_floating_ip['floating_ip_address'])
        self.assertEqual(show_floating_ip['port_id'], self.port[0]['id'])

        # Verify the floating ip exists in the list of all floating_ips
        resp, floating_ips = self.client.list_floating_ips()
        self.assertEqual('200', resp['status'])
        floatingip_id_list = list()
        for f in floating_ips['floatingips']:
            floatingip_id_list.append(f['id'])
        self.assertIn(create_floating_ip['id'], floatingip_id_list)

        # Associate floating IP to the other port
        resp, floating_ip = self.client.update_floating_ip(
            create_floating_ip['id'], port_id=self.port[1]['id'])
        self.assertEqual('200', resp['status'])
        update_floating_ip = floating_ip['floatingip']
        self.assertEqual(update_floating_ip['port_id'], self.port[1]['id'])
        self.assertIsNotNone(update_floating_ip['fixed_ip_address'])
        self.assertEqual(update_floating_ip['router_id'], self.router['id'])

        # Disassociate floating IP from the port
        resp, floating_ip = self.client.update_floating_ip(
            create_floating_ip['id'], port_id=None)
        self.assertEqual('200', resp['status'])
        update_floating_ip = floating_ip['floatingip']
        self.assertIsNone(update_floating_ip['port_id'])
        self.assertIsNone(update_floating_ip['fixed_ip_address'])
        self.assertIsNone(update_floating_ip['router_id'])
