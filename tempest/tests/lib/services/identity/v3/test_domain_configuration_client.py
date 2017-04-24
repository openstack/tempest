# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.lib.services.identity.v3 import domain_configuration_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestDomainConfigurationClient(base.BaseServiceTest):

    FAKE_CONFIG_SETTINGS = {
        "config": {
            "identity": {
                "driver": "ldap"
            },
            "ldap": {
                "url": "ldap://localhost",
                "user": "",
                "suffix": "cn=example,cn=com",
            }
        }
    }

    FAKE_DOMAIN_ID = '07ef7d04-2941-4bee-8551-f79f08a021de'

    def setUp(self):
        super(TestDomainConfigurationClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = domain_configuration_client.DomainConfigurationClient(
            fake_auth, 'identity', 'regionOne')

    def _test_show_default_config_settings(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_default_config_settings,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CONFIG_SETTINGS,
            bytes_body)

    def _test_show_default_group_config(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_default_group_config,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CONFIG_SETTINGS['config']['ldap'],
            bytes_body,
            group='ldap')

    def _test_show_default_group_option(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_default_group_option,
            'tempest.lib.common.rest_client.RestClient.get',
            {'driver': 'ldap'},
            bytes_body,
            group='identity',
            option='driver')

    def _test_show_domain_group_option_config(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_domain_group_option_config,
            'tempest.lib.common.rest_client.RestClient.get',
            {'driver': 'ldap'},
            bytes_body,
            domain_id=self.FAKE_DOMAIN_ID,
            group='identity',
            option='driver')

    def _test_update_domain_group_option_config(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_domain_group_option_config,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_CONFIG_SETTINGS,
            bytes_body,
            domain_id=self.FAKE_DOMAIN_ID,
            group='identity',
            option='driver',
            url='http://myldap/my_other_root')

    def _test_show_domain_group_config(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_domain_group_config,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CONFIG_SETTINGS['config']['ldap'],
            bytes_body,
            domain_id=self.FAKE_DOMAIN_ID,
            group='ldap')

    def _test_update_domain_group_config(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_domain_group_config,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_CONFIG_SETTINGS['config']['ldap'],
            bytes_body,
            domain_id=self.FAKE_DOMAIN_ID,
            group='ldap',
            **self.FAKE_CONFIG_SETTINGS['config'])

    def _test_create_domain_config(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_domain_config,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_CONFIG_SETTINGS,
            bytes_body,
            domain_id=self.FAKE_DOMAIN_ID,
            status=201)

    def _test_show_domain_config(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_domain_config,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CONFIG_SETTINGS,
            bytes_body,
            domain_id=self.FAKE_DOMAIN_ID)

    def _test_update_domain_config(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_domain_config,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_CONFIG_SETTINGS,
            bytes_body,
            domain_id=self.FAKE_DOMAIN_ID)

    def test_show_default_config_settings_with_str_body(self):
        self._test_show_default_config_settings()

    def test_show_default_config_settings_with_bytes_body(self):
        self._test_show_default_config_settings(bytes_body=True)

    def test_show_default_group_config_with_str_body(self):
        self._test_show_default_group_config()

    def test_show_default_group_config_with_bytes_body(self):
        self._test_show_default_group_config(bytes_body=True)

    def test_show_default_group_option_with_str_body(self):
        self._test_show_default_group_option()

    def test_show_default_group_option_with_bytes_body(self):
        self._test_show_default_group_option(bytes_body=True)

    def test_show_domain_group_option_config_with_str_body(self):
        self._test_show_domain_group_option_config()

    def test_show_domain_group_option_config_with_bytes_body(self):
        self._test_show_domain_group_option_config(bytes_body=True)

    def test_update_domain_group_option_config_with_str_body(self):
        self._test_update_domain_group_option_config()

    def test_update_domain_group_option_config_with_bytes_body(self):
        self._test_update_domain_group_option_config(bytes_body=True)

    def test_delete_domain_group_option_config(self):
        self.check_service_client_function(
            self.client.delete_domain_group_option_config,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            domain_id=self.FAKE_DOMAIN_ID,
            group='identity',
            option='driver')

    def test_show_domain_group_config_with_str_body(self):
        self._test_show_domain_group_config()

    def test_show_domain_group_config_with_bytes_body(self):
        self._test_show_domain_group_config(bytes_body=True)

    def test_test_update_domain_group_config_with_str_body(self):
        self._test_update_domain_group_config()

    def test_update_domain_group_config_with_bytes_body(self):
        self._test_update_domain_group_config(bytes_body=True)

    def test_delete_domain_group_config(self):
        self.check_service_client_function(
            self.client.delete_domain_group_config,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            domain_id=self.FAKE_DOMAIN_ID,
            group='identity')

    def test_create_domain_config_with_str_body(self):
        self._test_create_domain_config()

    def test_create_domain_config_with_bytes_body(self):
        self._test_create_domain_config(bytes_body=True)

    def test_show_domain_config_with_str_body(self):
        self._test_show_domain_config()

    def test_show_domain_config_with_bytes_body(self):
        self._test_show_domain_config(bytes_body=True)

    def test_update_domain_config_with_str_body(self):
        self._test_update_domain_config()

    def test_update_domain_config_with_bytes_body(self):
        self._test_update_domain_config(bytes_body=True)

    def test_delete_domain_config(self):
        self.check_service_client_function(
            self.client.delete_domain_config,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            domain_id=self.FAKE_DOMAIN_ID)
