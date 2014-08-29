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

import netaddr

from tempest.api.network import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class VPNaaSTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:
        List, Show, Create, Delete, and Update VPN Service
        List, Show, Create, Delete, and Update IKE policy
        List, Show, Create, Delete, and Update IPSec policy
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
            data_utils.rand_name("router"),
            external_network_id=CONF.network.public_network_id)
        cls.create_router_interface(cls.router['id'], cls.subnet['id'])
        cls.vpnservice = cls.create_vpnservice(cls.subnet['id'],
                                               cls.router['id'])

        cls.ikepolicy = cls.create_ikepolicy(
            data_utils.rand_name("ike-policy-"))
        cls.ipsecpolicy = cls.create_ipsecpolicy(
            data_utils.rand_name("ipsec-policy-"))

        cidr = CONF.network.tenant_network_cidr
        net = netaddr.IPNetwork(cidr)
        ip = str(netaddr.IPAddress(net.first + 1))
        ipsec_site_conn_body = {
            'name': data_utils.rand_name('ipsec-site-conn'),
            'psk': 'secret',
            'ipsecpolicy_id': cls.ipsecpolicy['id'],
            'ikepolicy_id': cls.ikepolicy['id'],
            'vpnservice_id': cls.vpnservice['id'],
            'peer_cidrs': [cidr],
            'peer_address': ip,
            'peer_id': ip}
        cls.ipsec_site_connection = cls.create_ipsec_site_connection(
            ipsec_site_conn_body)

    def _delete_ike_policy(self, ike_policy_id):
        # Deletes a ike policy and verifies if it is deleted or not
        ike_list = list()
        resp, all_ike = self.client.list_ikepolicies()
        for ike in all_ike['ikepolicies']:
            ike_list.append(ike['id'])
        if ike_policy_id in ike_list:
            self.client.delete_ikepolicy(ike_policy_id)
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

    def _delete_ipsec_site_connection(self, ipsec_site_connection_id):
        # Deletes an ipsec policy if it exists
        try:
            self.client.delete_ipsec_site_connection(ipsec_site_connection_id)

        except exceptions.NotFound:
            pass

    def _assertExpected(self, expected, actual):
        # Check if not expected keys/values exists in actual response body
        for key, value in expected.iteritems():
            self.assertIn(key, actual)
            self.assertEqual(value, actual[key])

    def _delete_vpn_service(self, vpn_service_id):
        self.client.delete_vpnservice(vpn_service_id)
        # Asserting if vpn service is found in the list after deletion
        _, body = self.client.list_vpnservices()
        vpn_services = [vs['id'] for vs in body['vpnservices']]
        self.assertNotIn(vpn_service_id, vpn_services)

    def _get_tenant_id(self):
        """
        Returns the tenant_id of the client current user
        """
        # TODO(jroovers) This is a temporary workaround to get the tenant_id
        # of the the current client. Replace this once tenant_isolation for
        # neutron is fixed.
        _, body = self.client.show_network(self.network['id'])
        return body['network']['tenant_id']

    @test.attr(type='smoke')
    def test_admin_create_ipsec_policy_for_tenant(self):
        tenant_id = self._get_tenant_id()
        # Create IPSec policy for the newly created tenant
        name = data_utils.rand_name('ipsec-policy')
        _, body = (self.admin_client.
                   create_ipsecpolicy(name=name, tenant_id=tenant_id))
        ipsecpolicy = body['ipsecpolicy']
        self.assertIsNotNone(ipsecpolicy['id'])
        self.addCleanup(self.admin_client.delete_ipsecpolicy,
                        ipsecpolicy['id'])

        # Assert that created ipsec policy is found in API list call
        _, body = self.client.list_ipsecpolicies()
        ipsecpolicies = [policy['id'] for policy in body['ipsecpolicies']]
        self.assertIn(ipsecpolicy['id'], ipsecpolicies)

    @test.attr(type='smoke')
    def test_admin_create_vpn_service_for_tenant(self):
        tenant_id = self._get_tenant_id()

        # Create vpn service for the newly created tenant
        name = data_utils.rand_name('vpn-service')
        _, body = self.admin_client.create_vpnservice(
            subnet_id=self.subnet['id'],
            router_id=self.router['id'],
            name=name,
            admin_state_up=True,
            tenant_id=tenant_id)
        vpnservice = body['vpnservice']
        self.assertIsNotNone(vpnservice['id'])
        self.addCleanup(self.admin_client.delete_vpnservice, vpnservice['id'])

        # Assert that created vpnservice is found in API list call
        _, body = self.client.list_vpnservices()
        vpn_services = [vs['id'] for vs in body['vpnservices']]
        self.assertIn(vpnservice['id'], vpn_services)

    @test.attr(type='smoke')
    def test_admin_create_ike_policy_for_tenant(self):
        tenant_id = self._get_tenant_id()

        # Create IKE policy for the newly created tenant
        name = data_utils.rand_name('ike-policy')
        _, body = (self.admin_client.
                   create_ikepolicy(name=name, ike_version="v1",
                                    encryption_algorithm="aes-128",
                                    auth_algorithm="sha1",
                                    tenant_id=tenant_id))
        ikepolicy = body['ikepolicy']
        self.assertIsNotNone(ikepolicy['id'])
        self.addCleanup(self.admin_client.delete_ikepolicy, ikepolicy['id'])

        # Assert that created ike policy is found in API list call
        _, body = self.client.list_ikepolicies()
        ikepolicies = [ikp['id'] for ikp in body['ikepolicies']]
        self.assertIn(ikepolicy['id'], ikepolicies)

    @test.attr(type='smoke')
    def test_list_vpn_services(self):
        # Verify the VPN service exists in the list of all VPN services
        _, body = self.client.list_vpnservices()
        vpnservices = body['vpnservices']
        self.assertIn(self.vpnservice['id'], [v['id'] for v in vpnservices])

    @test.attr(type='smoke')
    def test_create_update_delete_vpn_service(self):
        # Creates a VPN service and sets up deletion
        name = data_utils.rand_name('vpn-service')
        _, body = self.client.create_vpnservice(subnet_id=self.subnet['id'],
                                                router_id=self.router['id'],
                                                name=name,
                                                admin_state_up=True)
        vpnservice = body['vpnservice']
        self.addCleanup(self._delete_vpn_service, vpnservice['id'])
        # Assert if created vpnservices are not found in vpnservices list
        resp, body = self.client.list_vpnservices()
        vpn_services = [vs['id'] for vs in body['vpnservices']]
        self.assertIsNotNone(vpnservice['id'])
        self.assertIn(vpnservice['id'], vpn_services)

        # TODO(raies): implement logic to update  vpnservice
        # VPNaaS client function to update is implemented.
        # But precondition is that current state of vpnservice
        # should be "ACTIVE" not "PENDING*"

    @test.attr(type='smoke')
    def test_show_vpn_service(self):
        # Verifies the details of a vpn service
        _, body = self.client.show_vpnservice(self.vpnservice['id'])
        vpnservice = body['vpnservice']
        self.assertEqual(self.vpnservice['id'], vpnservice['id'])
        self.assertEqual(self.vpnservice['name'], vpnservice['name'])
        self.assertEqual(self.vpnservice['description'],
                         vpnservice['description'])
        self.assertEqual(self.vpnservice['router_id'], vpnservice['router_id'])
        self.assertEqual(self.vpnservice['subnet_id'], vpnservice['subnet_id'])
        self.assertEqual(self.vpnservice['tenant_id'], vpnservice['tenant_id'])
        valid_status = ["ACTIVE", "DOWN", "BUILD", "ERROR", "PENDING_CREATE",
                        "PENDING_UPDATE", "PENDING_DELETE"]
        self.assertIn(vpnservice['status'], valid_status)

    @test.attr(type='smoke')
    def test_list_ike_policies(self):
        # Verify the ike policy exists in the list of all IKE policies
        _, body = self.client.list_ikepolicies()
        ikepolicies = body['ikepolicies']
        self.assertIn(self.ikepolicy['id'], [i['id'] for i in ikepolicies])

    @test.attr(type='smoke')
    def test_create_update_delete_ike_policy(self):
        # Creates a IKE policy
        name = data_utils.rand_name('ike-policy')
        _, body = (self.client.create_ikepolicy(
                   name=name,
                   ike_version="v1",
                   encryption_algorithm="aes-128",
                   auth_algorithm="sha1"))
        ikepolicy = body['ikepolicy']
        self.assertIsNotNone(ikepolicy['id'])
        self.addCleanup(self._delete_ike_policy, ikepolicy['id'])

        # Update IKE Policy
        new_ike = {'name': data_utils.rand_name("New-IKE"),
                   'description': "Updated ike policy",
                   'encryption_algorithm': "aes-256",
                   'ike_version': "v2",
                   'pfs': "group14",
                   'lifetime': {'units': "seconds", 'value': 2000}}
        self.client.update_ikepolicy(ikepolicy['id'], **new_ike)
        # Confirm that update was successful by verifying using 'show'
        _, body = self.client.show_ikepolicy(ikepolicy['id'])
        ike_policy = body['ikepolicy']
        for key, value in new_ike.iteritems():
            self.assertIn(key, ike_policy)
            self.assertEqual(value, ike_policy[key])

        # Verification of ike policy delete
        self.client.delete_ikepolicy(ikepolicy['id'])
        _, body = self.client.list_ikepolicies()
        ikepolicies = [ikp['id'] for ikp in body['ikepolicies']]
        self.assertNotIn(ike_policy['id'], ikepolicies)

    @test.attr(type='smoke')
    def test_show_ike_policy(self):
        # Verifies the details of a ike policy
        _, body = self.client.show_ikepolicy(self.ikepolicy['id'])
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
        _, body = self.client.list_ipsecpolicies()
        ipsecpolicies = body['ipsecpolicies']
        self.assertIn(self.ipsecpolicy['id'], [i['id'] for i in ipsecpolicies])

    @test.attr(type='smoke')
    def test_create_update_delete_ipsec_policy(self):
        # Creates an ipsec policy
        ipsec_policy_body = {'name': data_utils.rand_name('ipsec-policy'),
                             'pfs': 'group5',
                             'encryption_algorithm': "aes-128",
                             'auth_algorithm': 'sha1'}
        _, resp_body = self.client.create_ipsecpolicy(**ipsec_policy_body)
        ipsecpolicy = resp_body['ipsecpolicy']
        self.addCleanup(self._delete_ipsec_policy, ipsecpolicy['id'])
        self._assertExpected(ipsec_policy_body, ipsecpolicy)
        # Verification of ipsec policy update
        new_ipsec = {'description': 'Updated ipsec policy',
                     'pfs': 'group2',
                     'name': data_utils.rand_name("New-IPSec"),
                     'encryption_algorithm': "aes-256",
                     'lifetime': {'units': "seconds", 'value': '2000'}}
        _, body = self.client.update_ipsecpolicy(ipsecpolicy['id'],
                                                 **new_ipsec)
        updated_ipsec_policy = body['ipsecpolicy']
        self._assertExpected(new_ipsec, updated_ipsec_policy)
        # Verification of ipsec policy delete
        self.client.delete_ipsecpolicy(ipsecpolicy['id'])
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_ipsecpolicy, ipsecpolicy['id'])

    @test.attr(type='smoke')
    def test_show_ipsec_policy(self):
        # Verifies the details of an ipsec policy
        _, body = self.client.show_ipsecpolicy(self.ipsecpolicy['id'])
        ipsecpolicy = body['ipsecpolicy']
        self._assertExpected(self.ipsecpolicy, ipsecpolicy)

    @test.attr(type='smoke')
    def test_list_ipsec_site_connections(self):
        # Verify the ipsec site connection exists in the list of all ipsec site
        # connections
        resp, body = self.client.list_ipsec_site_connections()
        self.assertEqual('200', resp['status'])
        ipsec_site_connections = body['ipsec_site_connections']
        self.assertIn(self.ipsec_site_connection['id'],
                      [i['id'] for i in ipsec_site_connections])

    @test.skip_because(bug="1331502")
    @test.attr(type='smoke')
    def test_create_update_delete_ipsec_site_connection(self):
        # Creates an ipsec site connection
        cidr = CONF.network.tenant_network_cidr
        net = netaddr.IPNetwork(cidr)
        ip = str(netaddr.IPAddress(net.first + 1))
        ipsec_site_conn_body = {
            'name': data_utils.rand_name('ipsec-site-conn'),
            'psk': 'secret',
            'ipsecpolicy_id': self.ipsecpolicy['id'],
            'ikepolicy_id': self.ikepolicy['id'],
            'vpnservice_id': self.vpnservice['id'],
            'peer_cidrs': [cidr],
            'peer_address': ip,
            'peer_id': ip}
        resp, resp_body = self.client.create_ipsec_site_connection(
            **ipsec_site_conn_body)
        self.assertEqual('201', resp['status'])
        ipsec_site_connection = resp_body['ipsec_site_connection']
        self.addCleanup(self._delete_ipsec_site_connection,
                        ipsec_site_connection['id'])
        self._assertExpected(ipsec_site_conn_body, ipsec_site_connection)
        # Verification of ipsec site connection update
        self.client.wait_for_resource_status('ipsec_site_connection',
                                             ipsec_site_connection['id'],
                                             'ACTIVE')
        new_ipsec = {'name': data_utils.rand_name("New-ipsec-site-connection"),
                     'mtu': 2000}
        resp, body = self.client.update_ipsec_site_connection(
            ipsec_site_connection['id'],
            **new_ipsec)
        self.assertEqual('200', resp['status'])
        updated_ipsec_site_connection = body['ipsec_site_connection']
        self._assertExpected(new_ipsec, updated_ipsec_site_connection)
        # Verification of ipsec site connection delete
        resp, _ = self.client.delete_ipsec_site_connection(
            ipsec_site_connection['id'])
        self.assertEqual('204', resp['status'])
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_ipsec_site_connection,
                          ipsec_site_connection['id'])

    @test.attr(type='smoke')
    def test_show_ipsec_site_connection(self):
        # Verifies the details of an ipsec site connection
        resp, body = self.client.show_ipsec_site_connection(
            self.ipsec_site_connection['id'])
        self.assertEqual('200', resp['status'])
        ipsec_site_connection = body['ipsec_site_connection']
        self._assertExpected(self.ipsec_site_connection, ipsec_site_connection)


class VPNaaSTestXML(VPNaaSTestJSON):
    _interface = 'xml'
