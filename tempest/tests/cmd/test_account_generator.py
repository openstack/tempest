# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
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

import fixtures
import mock
from oslo_config import cfg

from tempest.cmd import account_generator
from tempest import config
from tempest.tests import base
from tempest.tests import fake_config


class FakeOpts(object):

    def __init__(self, version=3):
        self.os_username = 'fake_user'
        self.os_password = 'fake_password'
        self.os_project_name = 'fake_project_name'
        self.os_tenant_name = None
        self.os_domain_name = 'fake_domain'
        self.tag = 'fake'
        self.concurrency = 2
        self.with_admin = True
        self.identity_version = version
        self.accounts = 'fake_accounts.yml'


class MockHelpersMixin(object):

    def mock_config_and_opts(self, identity_version):
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)
        self.opts = FakeOpts(version=identity_version)
        self.patch('oslo_log.log.setup', autospec=True)

    def mock_resource_creation(self):
        fake_resource = dict(id='id', name='name')
        self.user_create_fixture = self.useFixture(fixtures.MockPatch(
            self.cred_client + '.create_user', return_value=fake_resource))
        self.useFixture(fixtures.MockPatch(
            self.cred_client + '.create_project',
            return_value=fake_resource))
        self.useFixture(fixtures.MockPatch(
            self.cred_client + '.assign_user_role'))
        self.useFixture(fixtures.MockPatch(
            self.cred_client + '._check_role_exists',
            return_value=fake_resource))
        self.useFixture(fixtures.MockPatch(
            self.dynamic_creds + '._create_network',
            return_value=fake_resource))
        self.useFixture(fixtures.MockPatch(
            self.dynamic_creds + '._create_subnet',
            return_value=fake_resource))
        self.useFixture(fixtures.MockPatch(
            self.dynamic_creds + '._create_router',
            return_value=fake_resource))
        self.useFixture(fixtures.MockPatch(
            self.dynamic_creds + '._add_router_interface',
            return_value=fake_resource))

    def mock_domains(self):
        fake_domain_list = {'domains': [{'id': 'fake_domain',
                                         'name': 'Fake_Domain'}]}
        self.useFixture(fixtures.MockPatch(''.join([
            'tempest.lib.services.identity.v3.domains_client.'
            'DomainsClient.list_domains']),
            return_value=fake_domain_list))
        self.useFixture(fixtures.MockPatch(
            self.cred_client + '.assign_user_role_on_domain'))


class TestAccountGeneratorV2(base.TestCase, MockHelpersMixin):

    identity_version = 2

    def setUp(self):
        super(TestAccountGeneratorV2, self).setUp()
        self.mock_config_and_opts(self.identity_version)

    def test_get_credential_provider(self):
        cp = account_generator.get_credential_provider(self.opts)
        admin_creds = cp.default_admin_creds
        self.assertEqual(self.opts.tag, cp.name)
        self.assertIn(str(self.opts.identity_version), cp.identity_version)
        self.assertEqual(self.opts.os_username, admin_creds.username)
        self.assertEqual(self.opts.os_project_name, admin_creds.tenant_name)
        self.assertEqual(self.opts.os_password, admin_creds.password)
        self.assertFalse(hasattr(admin_creds, 'domain_name'))

    def test_get_credential_provider_with_tenant(self):
        self.opts.os_project_name = None
        self.opts.os_tenant_name = 'fake_tenant'
        cp = account_generator.get_credential_provider(self.opts)
        admin_creds = cp.default_admin_creds
        self.assertEqual(self.opts.os_tenant_name, admin_creds.tenant_name)


class TestAccountGeneratorV3(TestAccountGeneratorV2):

    identity_version = 3

    def setUp(self):
        super(TestAccountGeneratorV3, self).setUp()
        fake_domain_list = {'domains': [{'id': 'fake_domain'}]}
        self.useFixture(fixtures.MockPatch(''.join([
            'tempest.lib.services.identity.v3.domains_client.'
            'DomainsClient.list_domains']),
            return_value=fake_domain_list))

    def test_get_credential_provider(self):
        cp = account_generator.get_credential_provider(self.opts)
        admin_creds = cp.default_admin_creds
        self.assertEqual(self.opts.tag, cp.name)
        self.assertIn(str(self.opts.identity_version), cp.identity_version)
        self.assertEqual(self.opts.os_username, admin_creds.username)
        self.assertEqual(self.opts.os_project_name, admin_creds.tenant_name)
        self.assertEqual(self.opts.os_password, admin_creds.password)
        self.assertEqual(self.opts.os_domain_name, admin_creds.domain_name)

    def test_get_credential_provider_without_domain(self):
        self.opts.os_domain_name = None
        cp = account_generator.get_credential_provider(self.opts)
        admin_creds = cp.default_admin_creds
        self.assertIsNotNone(admin_creds.domain_name)


class TestGenerateResourcesV2(base.TestCase, MockHelpersMixin):

    identity_version = 2
    cred_client = 'tempest.lib.common.cred_client.V2CredsClient'
    dynamic_creds = ('tempest.lib.common.dynamic_creds.'
                     'DynamicCredentialProvider')

    def setUp(self):
        super(TestGenerateResourcesV2, self).setUp()
        self.mock_config_and_opts(self.identity_version)
        self.cred_provider = account_generator.get_credential_provider(
            self.opts)
        self.mock_resource_creation()

    def test_generate_resources_no_admin(self):
        cfg.CONF.set_default('swift', False, group='service_available')
        cfg.CONF.set_default('operator_role', 'fake_operator',
                             group='object-storage')
        cfg.CONF.set_default('reseller_admin_role', 'fake_reseller',
                             group='object-storage')
        resources = account_generator.generate_resources(
            self.cred_provider, admin=False)
        resource_types = [k for k, _ in resources]
        # No admin, no swift, expect two credentials only
        self.assertEqual(2, len(resources))
        # Ensure create_user was invoked twice (two distinct users)
        self.assertEqual(2, self.user_create_fixture.mock.call_count)
        self.assertIn('primary', resource_types)
        self.assertIn('alt', resource_types)
        self.assertNotIn('admin', resource_types)
        self.assertNotIn(['fake_operator'], resource_types)
        self.assertNotIn(['fake_reseller'], resource_types)
        self.assertNotIn(['fake_owner'], resource_types)
        for resource in resources:
            self.assertIsNotNone(resource[1].network)
            self.assertIsNotNone(resource[1].router)
            self.assertIsNotNone(resource[1].subnet)

    def test_generate_resources_admin(self):
        cfg.CONF.set_default('swift', False, group='service_available')
        cfg.CONF.set_default('operator_role', 'fake_operator',
                             group='object-storage')
        cfg.CONF.set_default('reseller_admin_role', 'fake_reseller',
                             group='object-storage')
        resources = account_generator.generate_resources(
            self.cred_provider, admin=True)
        resource_types = [k for k, _ in resources]
        # Admin, no swift, expect three credentials only
        self.assertEqual(3, len(resources))
        # Ensure create_user was invoked 3 times (3 distinct users)
        self.assertEqual(3, self.user_create_fixture.mock.call_count)
        self.assertIn('primary', resource_types)
        self.assertIn('alt', resource_types)
        self.assertIn('admin', resource_types)
        self.assertNotIn(['fake_operator'], resource_types)
        self.assertNotIn(['fake_reseller'], resource_types)
        self.assertNotIn(['fake_owner'], resource_types)
        for resource in resources:
            self.assertIsNotNone(resource[1].network)
            self.assertIsNotNone(resource[1].router)
            self.assertIsNotNone(resource[1].subnet)

    def test_generate_resources_swift_admin(self):
        cfg.CONF.set_default('swift', True, group='service_available')
        cfg.CONF.set_default('operator_role', 'fake_operator',
                             group='object-storage')
        cfg.CONF.set_default('reseller_admin_role', 'fake_reseller',
                             group='object-storage')
        resources = account_generator.generate_resources(
            self.cred_provider, admin=True)
        resource_types = [k for k, _ in resources]
        # all options on, expect six credentials
        self.assertEqual(6, len(resources))
        # Ensure create_user was invoked 6 times (6 distinct users)
        self.assertEqual(5, self.user_create_fixture.mock.call_count)
        self.assertIn('primary', resource_types)
        self.assertIn('alt', resource_types)
        self.assertIn('admin', resource_types)
        self.assertIn(['fake_operator'], resource_types)
        self.assertIn(['fake_reseller'], resource_types)
        for resource in resources:
            self.assertIsNotNone(resource[1].network)
            self.assertIsNotNone(resource[1].router)
            self.assertIsNotNone(resource[1].subnet)


class TestGenerateResourcesV3(TestGenerateResourcesV2):

    identity_version = 3
    cred_client = 'tempest.lib.common.cred_client.V3CredsClient'

    def setUp(self):
        self.mock_domains()
        super(TestGenerateResourcesV3, self).setUp()


class TestDumpAccountsV2(base.TestCase, MockHelpersMixin):

    identity_version = 2
    cred_client = 'tempest.lib.common.cred_client.V2CredsClient'
    dynamic_creds = ('tempest.lib.common.dynamic_creds.'
                     'DynamicCredentialProvider')
    domain_is_in = False

    def setUp(self):
        super(TestDumpAccountsV2, self).setUp()
        self.mock_config_and_opts(self.identity_version)
        self.cred_provider = account_generator.get_credential_provider(
            self.opts)
        self.mock_resource_creation()
        cfg.CONF.set_default('swift', True, group='service_available')
        self.resources = account_generator.generate_resources(
            self.cred_provider, admin=True)

    def test_dump_accounts(self):
        self.useFixture(fixtures.MockPatch('os.path.exists',
                                           return_value=False))
        mocked_open = mock.mock_open()
        with mock.patch('{}.open'.format(account_generator.__name__),
                        mocked_open, create=True):
            with mock.patch('yaml.safe_dump') as yaml_dump_mock:
                account_generator.setup_logging()
                account_generator.dump_accounts(self.resources,
                                                self.opts.identity_version,
                                                self.opts.accounts)
        mocked_open.assert_called_once_with(self.opts.accounts, 'w')
        handle = mocked_open()
        # Ordered args in [0], keyword args in [1]
        accounts, f = yaml_dump_mock.call_args[0]
        self.assertEqual(handle, f)
        self.assertEqual(6, len(accounts))
        if self.domain_is_in:
            self.assertIn('domain_name', accounts[0].keys())
        else:
            self.assertNotIn('domain_name', accounts[0].keys())
        self.assertEqual(1, len([x for x in accounts if
                                 x.get('types') == ['admin']]))
        self.assertEqual(3, len([x for x in accounts if 'roles' in x]))
        for account in accounts:
            self.assertIn('resources', account)
            self.assertIn('network', account.get('resources'))

    def test_dump_accounts_existing_file(self):
        self.useFixture(fixtures.MockPatch('os.path.exists',
                                           return_value=True))
        rename_mock = self.useFixture(fixtures.MockPatch('os.rename')).mock
        backup_file = '.'.join((self.opts.accounts, 'bak'))
        mocked_open = mock.mock_open()
        with mock.patch('{}.open'.format(account_generator.__name__),
                        mocked_open, create=True):
            with mock.patch('yaml.safe_dump') as yaml_dump_mock:
                account_generator.setup_logging()
                account_generator.dump_accounts(self.resources,
                                                self.opts.identity_version,
                                                self.opts.accounts)
        rename_mock.assert_called_once_with(self.opts.accounts, backup_file)
        mocked_open.assert_called_once_with(self.opts.accounts, 'w')
        handle = mocked_open()
        # Ordered args in [0], keyword args in [1]
        accounts, f = yaml_dump_mock.call_args[0]
        self.assertEqual(handle, f)
        self.assertEqual(6, len(accounts))
        if self.domain_is_in:
            self.assertIn('domain_name', accounts[0].keys())
        else:
            self.assertNotIn('domain_name', accounts[0].keys())
        self.assertEqual(1, len([x for x in accounts if
                                 x.get('types') == ['admin']]))
        self.assertEqual(3, len([x for x in accounts if 'roles' in x]))
        for account in accounts:
            self.assertIn('resources', account)
            self.assertIn('network', account.get('resources'))


class TestDumpAccountsV3(TestDumpAccountsV2):

    identity_version = 3
    cred_client = 'tempest.lib.common.cred_client.V3CredsClient'
    domain_is_in = True

    def setUp(self):
        self.mock_domains()
        super(TestDumpAccountsV3, self).setUp()
