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
        List, Show, Create, Delete, and Update IKE policy
    """

    @classmethod
    def setUpClass(cls):
        super(VPNaaSJSON, cls).setUpClass()
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.router = cls.create_router(
            data_utils.rand_name("router-"),
            external_network_id=cls.network_cfg.public_network_id)
        cls.create_router_interface(cls.router['id'], cls.subnet['id'])
        cls.vpnservice = cls.create_vpnservice(cls.subnet['id'],
                                               cls.router['id'])
        cls.ikepolicy = cls.create_ike_policy(data_utils.rand_name(
                                              "ike-policy-"))

    def _delete_ike_policy(self, ike_policy_id):
        # Deletes a ike policy and verifies if it is deleted or not
        ike_list = list()
        resp, all_ike = self.client.list_ike_policies()
        for ike in all_ike['ikepolicies']:
            ike_list.append(ike['id'])
        if ike_policy_id in ike_list:
            resp, _ = self.client.delete_ike_policy(ike_policy_id)
            self.assertEqual(204, resp.status)
            # Asserting that the policy is not found in list after deletion
            resp, ikepolicies = self.client.list_ike_policies()
            ike_id_list = list()
            for i in ikepolicies['ikepolicies']:
                ike_id_list.append(i['id'])
            self.assertNotIn(ike_policy_id, ike_id_list)

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
        name = data_utils.rand_name('vpn-service-')
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

    @attr(type='smoke')
    def test_list_ike_policies(self):
        # Verify the ike policy exists in the list of all IKE policies
        resp, body = self.client.list_ike_policies()
        self.assertEqual('200', resp['status'])
        ikepolicies = body['ikepolicies']
        self.assertIn(self.ikepolicy['id'], [i['id'] for i in ikepolicies])

    @attr(type='smoke')
    def test_create_update_delete_ike_policy(self):
        # Creates a IKE policy
        name = data_utils.rand_name('ike-policy-')
        resp, body = (self.client.create_ike_policy(
                      name,
                      ike_version="v1",
                      encryption_algorithm="aes-128",
                      auth_algorithm="sha1"))
        self.assertEqual('201', resp['status'])
        ikepolicy = body['ikepolicy']
        self.addCleanup(self._delete_ike_policy, ikepolicy['id'])
        # Verification of ike policy update
        description = "Updated ike policy"
        new_ike = {'description': description, 'pfs': 'group5',
                   'name': data_utils.rand_name("New-IKE-")}
        resp, body = self.client.update_ike_policy(ikepolicy['id'],
                                                   **new_ike)
        self.assertEqual('200', resp['status'])
        updated_ike_policy = body['ikepolicy']
        self.assertEqual(updated_ike_policy['description'], description)
        # Verification of ike policy delete
        resp, body = self.client.delete_ike_policy(ikepolicy['id'])
        self.assertEqual('204', resp['status'])

    @attr(type='smoke')
    def test_show_ike_policy(self):
        # Verifies the details of a ike policy
        resp, body = self.client.show_ike_policy(self.ikepolicy['id'])
        self.assertEqual('200', resp['status'])
        ikepolicy = body['ikepolicy']
        self.assertEqual(self.ikepolicy['id'], ikepolicy['id'])
        self.assertEqual(self.ikepolicy['name'], ikepolicy['name'])
        self.assertEqual(self.ikepolicy['description'],
                         ikepolicy['description'])
        self.assertEqual(self.ikepolicy['encryption_algorithm'],
                         ikepolicy['encryption_algorithm'])
        self.assertEqual(self.ikepolicy['auth_algorithm'],
                         ikepolicy['auth_algorithm'])
        self.assertEqual(self.ikepolicy['tenant_id'],
                         ikepolicy['tenant_id'])
        self.assertEqual(self.ikepolicy['pfs'],
                         ikepolicy['pfs'])
        self.assertEqual(self.ikepolicy['phase1_negotiation_mode'],
                         ikepolicy['phase1_negotiation_mode'])
        self.assertEqual(self.ikepolicy['ike_version'],
                         ikepolicy['ike_version'])
