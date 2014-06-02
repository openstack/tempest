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
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class VPNaaSTestJSON(base.BaseNetworkTest):
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
    @test.safe_setup
    def setUpClass(cls):
        if not test.is_extension_enabled('vpnaas', 'network'):
            msg = "vpnaas extension not enabled."
            raise cls.skipException(msg)
        super(VPNaaSTestJSON, cls).setUpClass()
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.router = cls.create_router(
            data_utils.rand_name("router-"),
            external_network_id=CONF.network.public_network_id)
        cls.create_router_interface(cls.router['id'], cls.subnet['id'])
        cls.vpnservice = cls.create_vpnservice(cls.subnet['id'],
                                               cls.router['id'])
        cls.ikepolicy = cls.create_ikepolicy(
            data_utils.rand_name("ike-policy-"))
        cls.ipsecpolicy = cls.create_ipsecpolicy(
            data_utils.rand_name("ipsec-policy-"))

    def _delete_ike_policy(self, ike_policy_id):
        # Deletes a ike policy and verifies if it is deleted or not
        ike_list = list()
        resp, all_ike = self.client.list_ikepolicies()
        for ike in all_ike['ikepolicies']:
            ike_list.append(ike['id'])
        if ike_policy_id in ike_list:
            resp, _ = self.client.delete_ikepolicy(ike_policy_id)
            self.assertEqual(204, resp.status)
            # Asserting that the policy is not found in list after deletion
            resp, ikepolicies = self.client.list_ikepolicies()
            ike_id_list = list()
            for i in ikepolicies['ikepolicies']:
                ike_id_list.append(i['id'])
            self.assertNotIn(ike_policy_id, ike_id_list)

    def _delete_ipsec_policy(self, ipsec_policy_id):
        # Deletes an ike policy if it exists
        try:
            self.client.delete_ipsecpolicy(ipsec_policy_id)

        except exceptions.NotFound:
            pass

    def _assertExpected(self, expected, actual):
        # Check if not expected keys/values exists in actual response body
        for key, value in expected.iteritems():
            self.assertIn(key, actual)
            self.assertEqual(value, actual[key])

    @test.attr(type='smoke')
    def test_list_vpn_services(self):
        # Verify the VPN service exists in the list of all VPN services
        resp, body = self.client.list_vpnservices()
        self.assertEqual('200', resp['status'])
        vpnservices = body['vpnservices']
        self.assertIn(self.vpnservice['id'], [v['id'] for v in vpnservices])

    @test.attr(type='smoke')
    def test_create_update_delete_vpn_service(self):
        # Creates a VPN service
        name = data_utils.rand_name('vpn-service-')
        resp, body = self.client.create_vpnservice(subnet_id=self.subnet['id'],
                                                   router_id=self.router['id'],
                                                   name=name,
                                                   admin_state_up=True)
        self.assertEqual('201', resp['status'])
        vpnservice = body['vpnservice']
        # Assert if created vpnservices are not found in vpnservices list
        resp, body = self.client.list_vpnservices()
        vpn_services = [vs['id'] for vs in body['vpnservices']]
        self.assertIsNotNone(vpnservice['id'])
        self.assertIn(vpnservice['id'], vpn_services)

        # TODO(raies): implement logic to update  vpnservice
        # VPNaaS client function to update is implemented.
        # But precondition is that current state of vpnservice
        # should be "ACTIVE" not "PENDING*"

        # Verification of vpn service delete
        resp, body = self.client.delete_vpnservice(vpnservice['id'])
        self.assertEqual('204', resp['status'])
        # Asserting if vpn service is found in the list after deletion
        resp, body = self.client.list_vpnservices()
        vpn_services = [vs['id'] for vs in body['vpnservices']]
        self.assertNotIn(vpnservice['id'], vpn_services)

    @test.attr(type='smoke')
    def test_show_vpn_service(self):
        # Verifies the details of a vpn service
        resp, body = self.client.show_vpnservice(self.vpnservice['id'])
        self.assertEqual('200', resp['status'])
        vpnservice = body['vpnservice']
        self.assertEqual(self.vpnservice['id'], vpnservice['id'])
        self.assertEqual(self.vpnservice['name'], vpnservice['name'])
        self.assertEqual(self.vpnservice['description'],
                         vpnservice['description'])
        self.assertEqual(self.vpnservice['router_id'], vpnservice['router_id'])
        self.assertEqual(self.vpnservice['subnet_id'], vpnservice['subnet_id'])
        self.assertEqual(self.vpnservice['tenant_id'], vpnservice['tenant_id'])

    @test.attr(type='smoke')
    def test_list_ike_policies(self):
        # Verify the ike policy exists in the list of all IKE policies
        resp, body = self.client.list_ikepolicies()
        self.assertEqual('200', resp['status'])
        ikepolicies = body['ikepolicies']
        self.assertIn(self.ikepolicy['id'], [i['id'] for i in ikepolicies])

    @test.attr(type='smoke')
    def test_create_update_delete_ike_policy(self):
        # Creates a IKE policy
        name = data_utils.rand_name('ike-policy-')
        resp, body = (self.client.create_ikepolicy(
                      name=name,
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
        resp, body = self.client.update_ikepolicy(ikepolicy['id'],
                                                  **new_ike)
        self.assertEqual('200', resp['status'])
        updated_ike_policy = body['ikepolicy']
        self.assertEqual(updated_ike_policy['description'], description)
        # Verification of ike policy delete
        resp, body = self.client.delete_ikepolicy(ikepolicy['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='smoke')
    def test_show_ike_policy(self):
        # Verifies the details of a ike policy
        resp, body = self.client.show_ikepolicy(self.ikepolicy['id'])
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

    @test.attr(type='smoke')
    def test_list_ipsec_policies(self):
        # Verify the ipsec policy exists in the list of all ipsec policies
        resp, body = self.client.list_ipsecpolicies()
        self.assertEqual('200', resp['status'])
        ipsecpolicies = body['ipsecpolicies']
        self.assertIn(self.ipsecpolicy['id'], [i['id'] for i in ipsecpolicies])

    @test.attr(type='smoke')
    def test_create_update_delete_ipsec_policy(self):
        # Creates an ipsec policy
        ipsec_policy_body = {'name': data_utils.rand_name('ipsec-policy'),
                             'pfs': 'group5',
                             'encryption_algorithm': "aes-128",
                             'auth_algorithm': 'sha1'}
        resp, resp_body = self.client.create_ipsecpolicy(**ipsec_policy_body)
        self.assertEqual('201', resp['status'])
        ipsecpolicy = resp_body['ipsecpolicy']
        self.addCleanup(self._delete_ipsec_policy, ipsecpolicy['id'])
        self._assertExpected(ipsec_policy_body, ipsecpolicy)
        # Verification of ipsec policy update
        new_ipsec = {'description': 'Updated ipsec policy',
                     'pfs': 'group2',
                     'name': data_utils.rand_name("New-IPSec"),
                     'encryption_algorithm': "aes-256",
                     'lifetime': {'units': "seconds", 'value': '2000'}}
        resp, body = self.client.update_ipsecpolicy(ipsecpolicy['id'],
                                                    **new_ipsec)
        self.assertEqual('200', resp['status'])
        updated_ipsec_policy = body['ipsecpolicy']
        self._assertExpected(new_ipsec, updated_ipsec_policy)
        # Verification of ipsec policy delete
        resp, _ = self.client.delete_ipsecpolicy(ipsecpolicy['id'])
        self.assertEqual('204', resp['status'])
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_ipsecpolicy, ipsecpolicy['id'])

    @test.attr(type='smoke')
    def test_show_ipsec_policy(self):
        # Verifies the details of an ipsec policy
        resp, body = self.client.show_ipsecpolicy(self.ipsecpolicy['id'])
        self.assertEqual('200', resp['status'])
        ipsecpolicy = body['ipsecpolicy']
        self._assertExpected(self.ipsecpolicy, ipsecpolicy)


class VPNaaSTestXML(VPNaaSTestJSON):
    _interface = 'xml'
