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


class VPNaaSJSON(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        List VPN Services
        Show VPN Services
        Create VPN Services
        Update VPN Services
        Delete VPN Services
    """

    @classmethod
    def setUpClass(cls):
        super(VPNaaSJSON, cls).setUpClass()
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.router = cls.create_router(rand_name("router-"))
        cls.create_router_interface(cls.router['id'], cls.subnet['id'])
        cls.vpnservice = cls.create_vpnservice(cls.subnet['id'],
                                               cls.router['id'])

    @attr(type='smoke')
    def test_list_vpn_services(self):
        # Verify the VPN service exists in the list of all VPN services
        resp, body = self.client.list_vpn_services()
        self.assertEqual('200', resp['status'])
        vpnservices = body['vpnservices']
        self.assertIn(self.vpnservice['id'], [v['id'] for v in vpnservices])

    @attr(type='smoke')
    def test_create_update_delete_vpn_service(self):
        # Creates a VPN service
        name = rand_name('vpn-service-')
        resp, body = self.client.create_vpn_service(self.subnet['id'],
                                                    self.router['id'],
                                                    name=name,
                                                    admin_state_up=True)
        self.assertEqual('201', resp['status'])
        vpnservice = body['vpnservice']
        # Assert if created vpnservices are not found in vpnservices list
        resp, body = self.client.list_vpn_services()
        vpn_services = [vs['id'] for vs in body['vpnservices']]
        self.assertIsNotNone(vpnservice['id'])
        self.assertIn(vpnservice['id'], vpn_services)

        # TODO(raies): implement logic to update  vpnservice
        # VPNaaS client function to update is implemented.
        # But precondition is that current state of vpnservice
        # should be "ACTIVE" not "PENDING*"

        # Verification of vpn service delete
        resp, body = self.client.delete_vpn_service(vpnservice['id'])
        self.assertEqual('204', resp['status'])
        # Asserting if vpn service is found in the list after deletion
        resp, body = self.client.list_vpn_services()
        vpn_services = [vs['id'] for vs in body['vpnservices']]
        self.assertNotIn(vpnservice['id'], vpn_services)

    @attr(type='smoke')
    def test_show_vpn_service(self):
        # Verifies the details of a vpn service
        resp, body = self.client.show_vpn_service(self.vpnservice['id'])
        self.assertEqual('200', resp['status'])
        vpnservice = body['vpnservice']
        self.assertEqual(self.vpnservice['id'], vpnservice['id'])
        self.assertEqual(self.vpnservice['name'], vpnservice['name'])
        self.assertEqual(self.vpnservice['description'],
                         vpnservice['description'])
        self.assertEqual(self.vpnservice['router_id'], vpnservice['router_id'])
        self.assertEqual(self.vpnservice['subnet_id'], vpnservice['subnet_id'])
        self.assertEqual(self.vpnservice['tenant_id'], vpnservice['tenant_id'])
