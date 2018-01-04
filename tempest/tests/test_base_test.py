# Copyright 2016 IBM Corp.
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

from tempest import clients
from tempest.common import credentials_factory as credentials
from tempest import config
from tempest.lib.common import fixed_network
from tempest import test
from tempest.tests import base
from tempest.tests import fake_config


class TestBaseTestCase(base.TestCase):
    def setUp(self):
        super(TestBaseTestCase, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)
        self.fixed_network_name = 'fixed-net'
        cfg.CONF.set_default('fixed_network_name', self.fixed_network_name,
                             'compute')
        cfg.CONF.set_default('neutron', True, 'service_available')

    @mock.patch.object(test.BaseTestCase, 'get_client_manager')
    @mock.patch.object(test.BaseTestCase, '_get_credentials_provider')
    @mock.patch.object(fixed_network, 'get_tenant_network')
    def test_get_tenant_network(self, mock_gtn, mock_gprov, mock_gcm):
        net_client = mock.Mock()
        mock_prov = mock.Mock()
        mock_gcm.return_value.networks_client = net_client
        mock_gprov.return_value = mock_prov

        test.BaseTestCase.get_tenant_network()

        mock_gcm.assert_called_once_with(credential_type='primary')
        mock_gprov.assert_called_once_with()
        mock_gtn.assert_called_once_with(mock_prov, net_client,
                                         self.fixed_network_name)

    @mock.patch.object(test.BaseTestCase, 'get_client_manager')
    @mock.patch.object(test.BaseTestCase, '_get_credentials_provider')
    @mock.patch.object(fixed_network, 'get_tenant_network')
    @mock.patch.object(test.BaseTestCase, 'get_identity_version')
    @mock.patch.object(credentials, 'is_admin_available')
    @mock.patch.object(clients, 'Manager')
    def test_get_tenant_network_with_nova_net(self, mock_man, mock_iaa,
                                              mock_giv, mock_gtn, mock_gcp,
                                              mock_gcm):
        cfg.CONF.set_default('neutron', False, 'service_available')
        mock_prov = mock.Mock()
        mock_admin_man = mock.Mock()
        mock_iaa.return_value = True
        mock_gcp.return_value = mock_prov
        mock_man.return_value = mock_admin_man

        test.BaseTestCase.get_tenant_network()

        mock_man.assert_called_once_with(
            mock_prov.get_admin_creds.return_value.credentials)
        mock_iaa.assert_called_once_with(
            identity_version=mock_giv.return_value)
        mock_gcp.assert_called_once_with()
        mock_gtn.assert_called_once_with(
            mock_prov, mock_admin_man.compute_networks_client,
            self.fixed_network_name)

    @mock.patch.object(test.BaseTestCase, 'get_client_manager')
    @mock.patch.object(test.BaseTestCase, '_get_credentials_provider')
    @mock.patch.object(fixed_network, 'get_tenant_network')
    def test_get_tenant_network_with_alt_creds(self, mock_gtn, mock_gprov,
                                               mock_gcm):
        net_client = mock.Mock()
        mock_prov = mock.Mock()
        mock_gcm.return_value.networks_client = net_client
        mock_gprov.return_value = mock_prov

        test.BaseTestCase.get_tenant_network(credentials_type='alt')

        mock_gcm.assert_called_once_with(credential_type='alt')
        mock_gprov.assert_called_once_with()
        mock_gtn.assert_called_once_with(mock_prov, net_client,
                                         self.fixed_network_name)

    @mock.patch.object(test.BaseTestCase, 'get_client_manager')
    @mock.patch.object(test.BaseTestCase, '_get_credentials_provider')
    @mock.patch.object(fixed_network, 'get_tenant_network')
    def test_get_tenant_network_with_role_creds(self, mock_gtn, mock_gprov,
                                                mock_gcm):
        net_client = mock.Mock()
        mock_prov = mock.Mock()
        mock_gcm.return_value.networks_client = net_client
        mock_gprov.return_value = mock_prov
        creds = ['foo_type', 'role1']

        test.BaseTestCase.get_tenant_network(credentials_type=creds)

        mock_gcm.assert_called_once_with(roles=['role1'])
        mock_gprov.assert_called_once_with()
        mock_gtn.assert_called_once_with(mock_prov, net_client,
                                         self.fixed_network_name)
