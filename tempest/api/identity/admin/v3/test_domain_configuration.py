# Copyright 2017 AT&T Corporation
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

from tempest.api.identity import base
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class DomainConfigurationTestJSON(base.BaseIdentityV3AdminTest):
    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    custom_config = {
        "identity": {
            "driver": "ldap"
        },
        "ldap": {
            "url": "ldap://myldap.com:389/",
            "user_tree_dn": "ou=Users,dc=my_new_root,dc=org"
        }
    }

    @classmethod
    def setup_clients(cls):
        super(DomainConfigurationTestJSON, cls).setup_clients()
        cls.client = cls.domain_config_client

    def _create_domain_and_config(self, config):
        domain = self.setup_test_domain()
        config = self.client.create_domain_config(domain['id'], **config)[
            'config']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.client.delete_domain_config, domain['id'])
        return domain, config

    @decorators.idempotent_id('11a02bf0-6f94-4380-b3b0-c8dc18fc0d22')
    def test_show_default_group_config_and_options(self):
        # The API supports only the identity and ldap groups. For the ldap
        # group, a valid value is url or user_tree_dn. For the identity group,
        # a valid value is driver.

        # Check that the default config has the identity and ldap groups.
        config = self.client.show_default_config_settings()['config']
        self.assertIsInstance(config, dict)
        self.assertIn('identity', config)
        self.assertIn('ldap', config)

        # Check that the identity group is correct.
        identity_config = self.client.show_default_group_config('identity')[
            'config']

        self.assertIsInstance(identity_config, dict)
        self.assertIn('identity', identity_config)
        self.assertIn('driver', identity_config['identity'])
        self.assertIn('list_limit', identity_config['identity'])

        # Show each option for the default domain and identity group.
        for config_opt_name in ['driver', 'list_limit']:
            retrieved_config_opt = self.client.show_default_group_option(
                'identity', config_opt_name)['config']
            self.assertIn(config_opt_name, retrieved_config_opt)

        # Check that the ldap group is correct.
        ldap_config = self.client.show_default_group_config('ldap')['config']

        self.assertIsInstance(ldap_config, dict)
        self.assertIn('ldap', ldap_config)

        # Several valid options exist for ldap group.
        valid_options = ldap_config['ldap'].keys()

        # Show each option for the default domain and ldap group.
        for config_opt_name in valid_options:
            retrieved_config_opt = self.client.show_default_group_option(
                'ldap', config_opt_name)['config']
            self.assertIn(config_opt_name, retrieved_config_opt)

    @decorators.idempotent_id('9e3ff13c-f597-4f01-9377-d6c06c2a1477')
    def test_create_domain_config_and_show_config_groups_and_options(self):
        domain, created_config = self._create_domain_and_config(
            self.custom_config)

        # Check that the entire configuration is correct.
        self.assertEqual(self.custom_config, created_config)

        # Check that each configuration group is correct.
        for group_name in self.custom_config.keys():
            group_cfg = self.client.show_domain_group_config(
                domain['id'], group_name)['config']
            self.assertIn(group_name, group_cfg)
            self.assertEqual(self.custom_config[group_name],
                             group_cfg[group_name])

            # Check that each configuration option is correct.
            for opt_name in self.custom_config[group_name].keys():
                group_opt = self.client.show_domain_group_option_config(
                    domain['id'], group_name, opt_name)['config']
                self.assertIn(opt_name, group_opt)
                self.assertEqual(self.custom_config[group_name][opt_name],
                                 group_opt[opt_name])

    @decorators.idempotent_id('7161023e-5dd0-4612-9da0-1bac6ac30b63')
    def test_create_update_and_delete_domain_config(self):
        domain, created_config = self._create_domain_and_config(
            self.custom_config)

        new_config = created_config
        new_config['ldap']['url'] = data_utils.rand_url()

        # Check that the altered configuration is reflected in updated_config.
        updated_config = self.client.update_domain_config(
            domain['id'], **new_config)['config']
        self.assertEqual(new_config, updated_config)

        # Check that showing the domain config shows the altered configuration.
        retrieved_config = self.client.show_domain_config(domain['id'])[
            'config']
        self.assertEqual(new_config, retrieved_config)

        # Check that deleting a configuration works.
        self.client.delete_domain_config(domain['id'])
        self.assertRaises(lib_exc.NotFound, self.client.show_domain_config,
                          domain['id'])

    @decorators.idempotent_id('c7510fa2-6661-4170-9c6b-4783a80651e9')
    def test_create_update_and_delete_domain_config_groups_and_opts(self):
        domain, _ = self._create_domain_and_config(self.custom_config)

        # Check that updating configuration groups work.
        new_driver = data_utils.rand_name('driver')
        new_limit = data_utils.rand_int_id(0, 100)
        new_group_config = {'identity': {'driver': new_driver,
                                         'list_limit': new_limit}}

        updated_config = self.client.update_domain_group_config(
            domain['id'], 'identity', **new_group_config)['config']

        self.assertEqual(new_driver, updated_config['identity']['driver'])
        self.assertEqual(new_limit, updated_config['identity']['list_limit'])

        # Check that updating individual configuration group options work.
        new_driver = data_utils.rand_name('driver')

        updated_config = self.client.update_domain_group_option_config(
            domain['id'], 'identity', 'driver', driver=new_driver)['config']

        self.assertEqual(new_driver, updated_config['identity']['driver'])

        # Check that deleting individual configuration group options work.
        self.client.delete_domain_group_option_config(
            domain['id'], 'identity', 'driver')
        self.assertRaises(lib_exc.NotFound,
                          self.client.show_domain_group_option_config,
                          domain['id'], 'identity', 'driver')

        # Check that deleting configuration groups work.
        self.client.delete_domain_group_config(domain['id'], 'identity')
        self.assertRaises(lib_exc.NotFound,
                          self.client.show_domain_group_config,
                          domain['id'], 'identity')
