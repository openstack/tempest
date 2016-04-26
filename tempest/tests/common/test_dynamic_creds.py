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

import mock
from oslo_config import cfg
from oslotest import mockpatch

from tempest.common import credentials_factory as credentials
from tempest.common import dynamic_creds
from tempest import config
from tempest import exceptions
from tempest.lib.common import rest_client
from tempest.lib.services.identity.v2 import token_client as json_token_client
from tempest.services.identity.v2.json import identity_client as \
    json_iden_client
from tempest.services.identity.v2.json import roles_client as \
    json_roles_client
from tempest.services.identity.v2.json import tenants_client as \
    json_tenants_client
from tempest.services.identity.v2.json import users_client as \
    json_users_client
from tempest.services.network.json import routers_client
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests.lib import fake_http
from tempest.tests.lib import fake_identity


class TestDynamicCredentialProvider(base.TestCase):

    fixed_params = {'name': 'test class',
                    'identity_version': 'v2',
                    'admin_role': 'admin'}

    def setUp(self):
        super(TestDynamicCredentialProvider, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)
        self.patchobject(json_token_client.TokenClient, 'raw_request',
                         fake_identity._fake_v2_response)
        cfg.CONF.set_default('operator_role', 'FakeRole',
                             group='object-storage')
        self._mock_list_ec2_credentials('fake_user_id', 'fake_tenant_id')
        self.fixed_params.update(
            admin_creds=self._get_fake_admin_creds())

    def test_tempest_client(self):
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self.assertIsInstance(creds.identity_admin_client,
                              json_iden_client.IdentityClient)

    def _get_fake_admin_creds(self):
        return credentials.get_credentials(
            fill_in=False,
            identity_version=self.fixed_params['identity_version'],
            username='fake_username', password='fake_password',
            tenant_name='fake_tenant')

    def _mock_user_create(self, id, name):
        user_fix = self.useFixture(mockpatch.PatchObject(
            json_users_client.UsersClient,
            'create_user',
            return_value=(rest_client.ResponseBody
                          (200, {'user': {'id': id, 'name': name}}))))
        return user_fix

    def _mock_tenant_create(self, id, name):
        tenant_fix = self.useFixture(mockpatch.PatchObject(
            json_tenants_client.TenantsClient,
            'create_tenant',
            return_value=(rest_client.ResponseBody
                          (200, {'tenant': {'id': id, 'name': name}}))))
        return tenant_fix

    def _mock_list_roles(self, id, name):
        roles_fix = self.useFixture(mockpatch.PatchObject(
            json_roles_client.RolesClient,
            'list_roles',
            return_value=(rest_client.ResponseBody
                          (200,
                           {'roles': [{'id': id, 'name': name},
                            {'id': '1', 'name': 'FakeRole'},
                            {'id': '2', 'name': 'Member'}]}))))
        return roles_fix

    def _mock_list_2_roles(self):
        roles_fix = self.useFixture(mockpatch.PatchObject(
            json_roles_client.RolesClient,
            'list_roles',
            return_value=(rest_client.ResponseBody
                          (200,
                           {'roles': [{'id': '1234', 'name': 'role1'},
                            {'id': '1', 'name': 'FakeRole'},
                            {'id': '12345', 'name': 'role2'}]}))))
        return roles_fix

    def _mock_assign_user_role(self):
        tenant_fix = self.useFixture(mockpatch.PatchObject(
            json_roles_client.RolesClient,
            'assign_user_role',
            return_value=(rest_client.ResponseBody
                          (200, {}))))
        return tenant_fix

    def _mock_list_role(self):
        roles_fix = self.useFixture(mockpatch.PatchObject(
            json_roles_client.RolesClient,
            'list_roles',
            return_value=(rest_client.ResponseBody
                          (200, {'roles': [{'id': '1',
                                 'name': 'FakeRole'}]}))))
        return roles_fix

    def _mock_list_ec2_credentials(self, user_id, tenant_id):
        ec2_creds_fix = self.useFixture(mockpatch.PatchObject(
            json_users_client.UsersClient,
            'list_user_ec2_credentials',
            return_value=(rest_client.ResponseBody
                          (200, {'credentials': [{
                                 'access': 'fake_access',
                                 'secret': 'fake_secret',
                                 'tenant_id': tenant_id,
                                 'user_id': user_id,
                                 'trust_id': None}]}))))
        return ec2_creds_fix

    def _mock_network_create(self, iso_creds, id, name):
        net_fix = self.useFixture(mockpatch.PatchObject(
            iso_creds.networks_admin_client,
            'create_network',
            return_value={'network': {'id': id, 'name': name}}))
        return net_fix

    def _mock_subnet_create(self, iso_creds, id, name):
        subnet_fix = self.useFixture(mockpatch.PatchObject(
            iso_creds.subnets_admin_client,
            'create_subnet',
            return_value={'subnet': {'id': id, 'name': name}}))
        return subnet_fix

    def _mock_router_create(self, id, name):
        router_fix = self.useFixture(mockpatch.PatchObject(
            routers_client.RoutersClient,
            'create_router',
            return_value={'router': {'id': id, 'name': name}}))
        return router_fix

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_primary_creds(self, MockRestClient):
        cfg.CONF.set_default('neutron', False, 'service_available')
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        self._mock_user_create('1234', 'fake_prim_user')
        primary_creds = creds.get_primary_creds()
        self.assertEqual(primary_creds.username, 'fake_prim_user')
        self.assertEqual(primary_creds.tenant_name, 'fake_prim_tenant')
        # Verify IDs
        self.assertEqual(primary_creds.tenant_id, '1234')
        self.assertEqual(primary_creds.user_id, '1234')

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_admin_creds(self, MockRestClient):
        cfg.CONF.set_default('neutron', False, 'service_available')
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self._mock_list_roles('1234', 'admin')
        self._mock_user_create('1234', 'fake_admin_user')
        self._mock_tenant_create('1234', 'fake_admin_tenant')

        user_mock = mock.patch.object(json_roles_client.RolesClient,
                                      'assign_user_role')
        user_mock.start()
        self.addCleanup(user_mock.stop)
        with mock.patch.object(json_roles_client.RolesClient,
                               'assign_user_role') as user_mock:
            admin_creds = creds.get_admin_creds()
        user_mock.assert_has_calls([
            mock.call('1234', '1234', '1234')])
        self.assertEqual(admin_creds.username, 'fake_admin_user')
        self.assertEqual(admin_creds.tenant_name, 'fake_admin_tenant')
        # Verify IDs
        self.assertEqual(admin_creds.tenant_id, '1234')
        self.assertEqual(admin_creds.user_id, '1234')

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_role_creds(self, MockRestClient):
        cfg.CONF.set_default('neutron', False, 'service_available')
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self._mock_list_2_roles()
        self._mock_user_create('1234', 'fake_role_user')
        self._mock_tenant_create('1234', 'fake_role_tenant')

        user_mock = mock.patch.object(json_roles_client.RolesClient,
                                      'assign_user_role')
        user_mock.start()
        self.addCleanup(user_mock.stop)
        with mock.patch.object(json_roles_client.RolesClient,
                               'assign_user_role') as user_mock:
            role_creds = creds.get_creds_by_roles(
                roles=['role1', 'role2'])
        calls = user_mock.mock_calls
        # Assert that the role creation is called with the 2 specified roles
        self.assertEqual(len(calls), 2)
        args = map(lambda x: x[1], calls)
        args = list(args)
        self.assertIn(('1234', '1234', '1234'), args)
        self.assertIn(('1234', '1234', '12345'), args)
        self.assertEqual(role_creds.username, 'fake_role_user')
        self.assertEqual(role_creds.tenant_name, 'fake_role_tenant')
        # Verify IDs
        self.assertEqual(role_creds.tenant_id, '1234')
        self.assertEqual(role_creds.user_id, '1234')

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_all_cred_cleanup(self, MockRestClient):
        cfg.CONF.set_default('neutron', False, 'service_available')
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        self._mock_user_create('1234', 'fake_prim_user')
        creds.get_primary_creds()
        self._mock_tenant_create('12345', 'fake_alt_tenant')
        self._mock_user_create('12345', 'fake_alt_user')
        creds.get_alt_creds()
        self._mock_tenant_create('123456', 'fake_admin_tenant')
        self._mock_user_create('123456', 'fake_admin_user')
        self._mock_list_roles('123456', 'admin')
        creds.get_admin_creds()
        user_mock = self.patch(
            'tempest.services.identity.v2.json.users_client.'
            'UsersClient.delete_user')
        tenant_mock = self.patch(
            'tempest.services.identity.v2.json.tenants_client.'
            'TenantsClient.delete_tenant')
        creds.clear_creds()
        # Verify user delete calls
        calls = user_mock.mock_calls
        self.assertEqual(len(calls), 3)
        args = map(lambda x: x[1][0], calls)
        args = list(args)
        self.assertIn('1234', args)
        self.assertIn('12345', args)
        self.assertIn('123456', args)
        # Verify tenant delete calls
        calls = tenant_mock.mock_calls
        self.assertEqual(len(calls), 3)
        args = map(lambda x: x[1][0], calls)
        args = list(args)
        self.assertIn('1234', args)
        self.assertIn('12345', args)
        self.assertIn('123456', args)

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_alt_creds(self, MockRestClient):
        cfg.CONF.set_default('neutron', False, 'service_available')
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_user_create('1234', 'fake_alt_user')
        self._mock_tenant_create('1234', 'fake_alt_tenant')
        alt_creds = creds.get_alt_creds()
        self.assertEqual(alt_creds.username, 'fake_alt_user')
        self.assertEqual(alt_creds.tenant_name, 'fake_alt_tenant')
        # Verify IDs
        self.assertEqual(alt_creds.tenant_id, '1234')
        self.assertEqual(alt_creds.user_id, '1234')

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_no_network_creation_with_config_set(self, MockRestClient):
        cfg.CONF.set_default('create_isolated_networks', False, group='auth')
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_user_create('1234', 'fake_prim_user')
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        net = mock.patch.object(creds.networks_admin_client,
                                'delete_network')
        net_mock = net.start()
        subnet = mock.patch.object(creds.subnets_admin_client,
                                   'delete_subnet')
        subnet_mock = subnet.start()
        router = mock.patch.object(creds.routers_admin_client,
                                   'delete_router')
        router_mock = router.start()

        primary_creds = creds.get_primary_creds()
        self.assertEqual(net_mock.mock_calls, [])
        self.assertEqual(subnet_mock.mock_calls, [])
        self.assertEqual(router_mock.mock_calls, [])
        network = primary_creds.network
        subnet = primary_creds.subnet
        router = primary_creds.router
        self.assertIsNone(network)
        self.assertIsNone(subnet)
        self.assertIsNone(router)

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_network_creation(self, MockRestClient):
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_user_create('1234', 'fake_prim_user')
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        self._mock_network_create(creds, '1234', 'fake_net')
        self._mock_subnet_create(creds, '1234', 'fake_subnet')
        self._mock_router_create('1234', 'fake_router')
        router_interface_mock = self.patch(
            'tempest.services.network.json.routers_client.RoutersClient.'
            'add_router_interface')
        primary_creds = creds.get_primary_creds()
        router_interface_mock.assert_called_once_with('1234', subnet_id='1234')
        network = primary_creds.network
        subnet = primary_creds.subnet
        router = primary_creds.router
        self.assertEqual(network['id'], '1234')
        self.assertEqual(network['name'], 'fake_net')
        self.assertEqual(subnet['id'], '1234')
        self.assertEqual(subnet['name'], 'fake_subnet')
        self.assertEqual(router['id'], '1234')
        self.assertEqual(router['name'], 'fake_router')

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_network_cleanup(self, MockRestClient):
        def side_effect(**args):
            return {"security_groups": [{"tenant_id": args['tenant_id'],
                                         "name": args['name'],
                                         "description": args['name'],
                                         "security_group_rules": [],
                                         "id": "sg-%s" % args['tenant_id']}]}
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        # Create primary tenant and network
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_user_create('1234', 'fake_prim_user')
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        self._mock_network_create(creds, '1234', 'fake_net')
        self._mock_subnet_create(creds, '1234', 'fake_subnet')
        self._mock_router_create('1234', 'fake_router')
        router_interface_mock = self.patch(
            'tempest.services.network.json.routers_client.RoutersClient.'
            'add_router_interface')
        creds.get_primary_creds()
        router_interface_mock.assert_called_once_with('1234', subnet_id='1234')
        router_interface_mock.reset_mock()
        # Create alternate tenant and network
        self._mock_user_create('12345', 'fake_alt_user')
        self._mock_tenant_create('12345', 'fake_alt_tenant')
        self._mock_network_create(creds, '12345', 'fake_alt_net')
        self._mock_subnet_create(creds, '12345', 'fake_alt_subnet')
        self._mock_router_create('12345', 'fake_alt_router')
        creds.get_alt_creds()
        router_interface_mock.assert_called_once_with('12345',
                                                      subnet_id='12345')
        router_interface_mock.reset_mock()
        # Create admin tenant and networks
        self._mock_user_create('123456', 'fake_admin_user')
        self._mock_tenant_create('123456', 'fake_admin_tenant')
        self._mock_network_create(creds, '123456', 'fake_admin_net')
        self._mock_subnet_create(creds, '123456', 'fake_admin_subnet')
        self._mock_router_create('123456', 'fake_admin_router')
        self._mock_list_roles('123456', 'admin')
        creds.get_admin_creds()
        self.patch('tempest.services.identity.v2.json.users_client.'
                   'UsersClient.delete_user')
        self.patch('tempest.services.identity.v2.json.tenants_client.'
                   'TenantsClient.delete_tenant')
        net = mock.patch.object(creds.networks_admin_client,
                                'delete_network')
        net_mock = net.start()
        subnet = mock.patch.object(creds.subnets_admin_client,
                                   'delete_subnet')
        subnet_mock = subnet.start()
        router = mock.patch.object(creds.routers_admin_client,
                                   'delete_router')
        router_mock = router.start()
        remove_router_interface_mock = self.patch(
            'tempest.services.network.json.routers_client.RoutersClient.'
            'remove_router_interface')
        return_values = ({'status': 200}, {'ports': []})
        port_list_mock = mock.patch.object(creds.ports_admin_client,
                                           'list_ports',
                                           return_value=return_values)

        port_list_mock.start()
        secgroup_list_mock = mock.patch.object(
            creds.security_groups_admin_client,
            'list_security_groups',
            side_effect=side_effect)
        secgroup_list_mock.start()

        return_values = fake_http.fake_http_response({}, status=204), ''
        remove_secgroup_mock = self.patch(
            'tempest.lib.services.network.security_groups_client.'
            'SecurityGroupsClient.delete', return_value=return_values)
        creds.clear_creds()
        # Verify default security group delete
        calls = remove_secgroup_mock.mock_calls
        self.assertEqual(len(calls), 3)
        args = map(lambda x: x[1][0], calls)
        args = list(args)
        self.assertIn('v2.0/security-groups/sg-1234', args)
        self.assertIn('v2.0/security-groups/sg-12345', args)
        self.assertIn('v2.0/security-groups/sg-123456', args)
        # Verify remove router interface calls
        calls = remove_router_interface_mock.mock_calls
        self.assertEqual(len(calls), 3)
        args = map(lambda x: (x[1][0], x[2]), calls)
        args = list(args)
        self.assertIn(('1234', {'subnet_id': '1234'}), args)
        self.assertIn(('12345', {'subnet_id': '12345'}), args)
        self.assertIn(('123456', {'subnet_id': '123456'}), args)
        # Verify network delete calls
        calls = net_mock.mock_calls
        self.assertEqual(len(calls), 3)
        args = map(lambda x: x[1][0], calls)
        args = list(args)
        self.assertIn('1234', args)
        self.assertIn('12345', args)
        self.assertIn('123456', args)
        # Verify subnet delete calls
        calls = subnet_mock.mock_calls
        self.assertEqual(len(calls), 3)
        args = map(lambda x: x[1][0], calls)
        args = list(args)
        self.assertIn('1234', args)
        self.assertIn('12345', args)
        self.assertIn('123456', args)
        # Verify router delete calls
        calls = router_mock.mock_calls
        self.assertEqual(len(calls), 3)
        args = map(lambda x: x[1][0], calls)
        args = list(args)
        self.assertIn('1234', args)
        self.assertIn('12345', args)
        self.assertIn('123456', args)

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_network_alt_creation(self, MockRestClient):
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_user_create('1234', 'fake_alt_user')
        self._mock_tenant_create('1234', 'fake_alt_tenant')
        self._mock_network_create(creds, '1234', 'fake_alt_net')
        self._mock_subnet_create(creds, '1234', 'fake_alt_subnet')
        self._mock_router_create('1234', 'fake_alt_router')
        router_interface_mock = self.patch(
            'tempest.services.network.json.routers_client.RoutersClient.'
            'add_router_interface')
        alt_creds = creds.get_alt_creds()
        router_interface_mock.assert_called_once_with('1234', subnet_id='1234')
        network = alt_creds.network
        subnet = alt_creds.subnet
        router = alt_creds.router
        self.assertEqual(network['id'], '1234')
        self.assertEqual(network['name'], 'fake_alt_net')
        self.assertEqual(subnet['id'], '1234')
        self.assertEqual(subnet['name'], 'fake_alt_subnet')
        self.assertEqual(router['id'], '1234')
        self.assertEqual(router['name'], 'fake_alt_router')

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_network_admin_creation(self, MockRestClient):
        creds = dynamic_creds.DynamicCredentialProvider(**self.fixed_params)
        self._mock_assign_user_role()
        self._mock_user_create('1234', 'fake_admin_user')
        self._mock_tenant_create('1234', 'fake_admin_tenant')
        self._mock_network_create(creds, '1234', 'fake_admin_net')
        self._mock_subnet_create(creds, '1234', 'fake_admin_subnet')
        self._mock_router_create('1234', 'fake_admin_router')
        router_interface_mock = self.patch(
            'tempest.services.network.json.routers_client.RoutersClient.'
            'add_router_interface')
        self._mock_list_roles('123456', 'admin')
        admin_creds = creds.get_admin_creds()
        router_interface_mock.assert_called_once_with('1234', subnet_id='1234')
        network = admin_creds.network
        subnet = admin_creds.subnet
        router = admin_creds.router
        self.assertEqual(network['id'], '1234')
        self.assertEqual(network['name'], 'fake_admin_net')
        self.assertEqual(subnet['id'], '1234')
        self.assertEqual(subnet['name'], 'fake_admin_subnet')
        self.assertEqual(router['id'], '1234')
        self.assertEqual(router['name'], 'fake_admin_router')

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_no_network_resources(self, MockRestClient):
        net_dict = {
            'network': False,
            'router': False,
            'subnet': False,
            'dhcp': False,
        }
        creds = dynamic_creds.DynamicCredentialProvider(
            network_resources=net_dict,
            **self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_user_create('1234', 'fake_prim_user')
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        net = mock.patch.object(creds.networks_admin_client,
                                'delete_network')
        net_mock = net.start()
        subnet = mock.patch.object(creds.subnets_admin_client,
                                   'delete_subnet')
        subnet_mock = subnet.start()
        router = mock.patch.object(creds.routers_admin_client,
                                   'delete_router')
        router_mock = router.start()

        primary_creds = creds.get_primary_creds()
        self.assertEqual(net_mock.mock_calls, [])
        self.assertEqual(subnet_mock.mock_calls, [])
        self.assertEqual(router_mock.mock_calls, [])
        network = primary_creds.network
        subnet = primary_creds.subnet
        router = primary_creds.router
        self.assertIsNone(network)
        self.assertIsNone(subnet)
        self.assertIsNone(router)

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_router_without_network(self, MockRestClient):
        net_dict = {
            'network': False,
            'router': True,
            'subnet': False,
            'dhcp': False,
        }
        creds = dynamic_creds.DynamicCredentialProvider(
            network_resources=net_dict,
            **self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_user_create('1234', 'fake_prim_user')
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        self.assertRaises(exceptions.InvalidConfiguration,
                          creds.get_primary_creds)

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_subnet_without_network(self, MockRestClient):
        net_dict = {
            'network': False,
            'router': False,
            'subnet': True,
            'dhcp': False,
        }
        creds = dynamic_creds.DynamicCredentialProvider(
            network_resources=net_dict,
            **self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_user_create('1234', 'fake_prim_user')
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        self.assertRaises(exceptions.InvalidConfiguration,
                          creds.get_primary_creds)

    @mock.patch('tempest.lib.common.rest_client.RestClient')
    def test_dhcp_without_subnet(self, MockRestClient):
        net_dict = {
            'network': False,
            'router': False,
            'subnet': False,
            'dhcp': True,
        }
        creds = dynamic_creds.DynamicCredentialProvider(
            network_resources=net_dict,
            **self.fixed_params)
        self._mock_assign_user_role()
        self._mock_list_role()
        self._mock_user_create('1234', 'fake_prim_user')
        self._mock_tenant_create('1234', 'fake_prim_tenant')
        self.assertRaises(exceptions.InvalidConfiguration,
                          creds.get_primary_creds)
