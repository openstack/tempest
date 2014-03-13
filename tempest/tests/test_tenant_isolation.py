# Copyright 2014 IBM Corp.
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

import keystoneclient.v2_0.client as keystoneclient
from mock import patch
import neutronclient.v2_0.client as neutronclient
from oslo.config import cfg

from tempest.common import isolated_creds
from tempest import config
from tempest.openstack.common.fixture import mockpatch
from tempest.services.identity.json import identity_client as json_iden_client
from tempest.services.identity.xml import identity_client as xml_iden_client
from tempest.services.network.json import network_client as json_network_client
from tempest.services.network.xml import network_client as xml_network_client
from tempest.tests import base
from tempest.tests import fake_config


class TestTenantIsolation(base.TestCase):

    def setUp(self):
        super(TestTenantIsolation, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)

    def test_tempest_client(self):
        iso_creds = isolated_creds.IsolatedCreds('test class')
        self.assertTrue(isinstance(iso_creds.identity_admin_client,
                                   json_iden_client.IdentityClientJSON))
        self.assertTrue(isinstance(iso_creds.network_admin_client,
                                   json_network_client.NetworkClientJSON))

    def test_official_client(self):
        self.useFixture(mockpatch.PatchObject(keystoneclient.Client,
                                              'authenticate'))
        iso_creds = isolated_creds.IsolatedCreds('test class',
                                                 tempest_client=False)
        self.assertTrue(isinstance(iso_creds.identity_admin_client,
                                   keystoneclient.Client))
        self.assertTrue(isinstance(iso_creds.network_admin_client,
                                   neutronclient.Client))

    def test_tempest_client_xml(self):
        iso_creds = isolated_creds.IsolatedCreds('test class', interface='xml')
        self.assertEqual(iso_creds.interface, 'xml')
        self.assertTrue(isinstance(iso_creds.identity_admin_client,
                                   xml_iden_client.IdentityClientXML))
        self.assertTrue(isinstance(iso_creds.network_admin_client,
                                   xml_network_client.NetworkClientXML))

    def _mock_user_create(self, id, name):
        user_fix = self.useFixture(mockpatch.PatchObject(
            json_iden_client.IdentityClientJSON,
            'create_user',
            return_value=({'status': 200},
                          {'id': id, 'name': name})))
        return user_fix

    def _mock_tenant_create(self, id, name):
        tenant_fix = self.useFixture(mockpatch.PatchObject(
            json_iden_client.IdentityClientJSON,
            'create_tenant',
            return_value=({'status': 200},
                          {'id': id, 'name': name})))
        return tenant_fix

    @patch('tempest.common.rest_client.RestClient')
    def test_primary_creds(self, MockRestClient):
        cfg.CONF.set_default('neutron', False, 'service_available')
        iso_creds = isolated_creds.IsolatedCreds('test class',
                                                 password='fake_password')
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        self._mock_user_create('1234', 'fake_prim_user')
        username, tenant_name, password = iso_creds.get_primary_creds()
        self.assertEqual(username, 'fake_prim_user')
        self.assertEqual(tenant_name, 'fake_prim_tenant')
        # Verify helper methods
        tenant = iso_creds.get_primary_tenant()
        user = iso_creds.get_primary_user()
        self.assertEqual(tenant['id'], '1234')
        self.assertEqual(user['id'], '1234')

    @patch('tempest.common.rest_client.RestClient')
    def test_admin_creds(self, MockRestClient):
        cfg.CONF.set_default('neutron', False, 'service_available')
        iso_creds = isolated_creds.IsolatedCreds('test class',
                                                 password='fake_password')
        self._mock_user_create('1234', 'fake_admin_user')
        self._mock_tenant_create('1234', 'fake_admin_tenant')
        self.useFixture(mockpatch.PatchObject(
            json_iden_client.IdentityClientJSON,
            'list_roles',
            return_value=({'status': 200},
                          [{'id': '1234', 'name': 'admin'}])))

        user_mock = patch.object(json_iden_client.IdentityClientJSON,
                                 'assign_user_role')
        user_mock.start()
        self.addCleanup(user_mock.stop)
        with patch.object(json_iden_client.IdentityClientJSON,
                          'assign_user_role') as user_mock:
            username, tenant_name, password = iso_creds.get_admin_creds()
        user_mock.assert_called_once_with('1234', '1234', '1234')
        self.assertEqual(username, 'fake_admin_user')
        self.assertEqual(tenant_name, 'fake_admin_tenant')
        # Verify helper methods
        tenant = iso_creds.get_admin_tenant()
        user = iso_creds.get_admin_user()
        self.assertEqual(tenant['id'], '1234')
        self.assertEqual(user['id'], '1234')

    @patch('tempest.common.rest_client.RestClient')
    def test_all_cred_cleanup(self, MockRestClient):
        cfg.CONF.set_default('neutron', False, 'service_available')
        iso_creds = isolated_creds.IsolatedCreds('test class',
                                                 password='fake_password')
        tenant_fix = self._mock_tenant_create('1234', 'fake_prim_tenant')
        user_fix = self._mock_user_create('1234', 'fake_prim_user')
        username, tenant_name, password = iso_creds.get_primary_creds()
        tenant_fix.cleanUp()
        user_fix.cleanUp()
        tenant_fix = self._mock_tenant_create('12345', 'fake_alt_tenant')
        user_fix = self._mock_user_create('12345', 'fake_alt_user')
        alt_username, alt_tenant, alt_password = iso_creds.get_alt_creds()
        tenant_fix.cleanUp()
        user_fix.cleanUp()
        tenant_fix = self._mock_tenant_create('123456', 'fake_admin_tenant')
        user_fix = self._mock_user_create('123456', 'fake_admin_user')
        self.useFixture(mockpatch.PatchObject(
            json_iden_client.IdentityClientJSON,
            'list_roles',
            return_value=({'status': 200},
                          [{'id': '123456', 'name': 'admin'}])))
        with patch.object(json_iden_client.IdentityClientJSON,
                          'assign_user_role'):
            admin_username, admin_tenant, admin_pass = \
                iso_creds.get_admin_creds()
        user_mock = self.patch(
            'tempest.services.identity.json.identity_client.'
            'IdentityClientJSON.delete_user')
        tenant_mock = self.patch(
            'tempest.services.identity.json.identity_client.'
            'IdentityClientJSON.delete_tenant')
        iso_creds.clear_isolated_creds()
        # Verify user delete calls
        calls = user_mock.mock_calls
        self.assertEqual(len(calls), 3)
        args = map(lambda x: x[1][0], calls)
        self.assertIn('1234', args)
        self.assertIn('12345', args)
        self.assertIn('123456', args)
        # Verify tenant delete calls
        calls = tenant_mock.mock_calls
        self.assertEqual(len(calls), 3)
        args = map(lambda x: x[1][0], calls)
        self.assertIn('1234', args)
        self.assertIn('12345', args)
        self.assertIn('123456', args)
