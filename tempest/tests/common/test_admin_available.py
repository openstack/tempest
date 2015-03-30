# Copyright 2015 Red Hat, Inc.
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

from oslo.config import cfg
from oslotest import mockpatch

from tempest.common import credentials
from tempest import config
from tempest.tests import base
from tempest.tests import fake_config


class TestAdminAvailable(base.TestCase):

    def setUp(self):
        super(TestAdminAvailable, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)

    def run_test(self, tenant_isolation, use_accounts_file, admin_creds):

        cfg.CONF.set_default('allow_tenant_isolation',
                             tenant_isolation, group='auth')
        if use_accounts_file:
            accounts = [{'username': 'u1',
                         'tenant_name': 't1',
                         'password': 'p'},
                        {'username': 'u2',
                         'tenant_name': 't2',
                         'password': 'p'}]
            if admin_creds == 'role':
                accounts.append({'username': 'admin',
                                 'tenant_name': 'admin',
                                 'password': 'p',
                                 'roles': ['admin']})
            elif admin_creds == 'type':
                accounts.append({'username': 'admin',
                                 'tenant_name': 'admin',
                                 'password': 'p',
                                 'types': ['admin']})
            self.useFixture(mockpatch.Patch(
                'tempest.common.accounts.read_accounts_yaml',
                return_value=accounts))
            cfg.CONF.set_default('test_accounts_file',
                                 use_accounts_file, group='auth')
            self.useFixture(mockpatch.Patch('os.path.isfile',
                                            return_value=True))
        else:
            self.useFixture(mockpatch.Patch('os.path.isfile',
                                            return_value=False))
            if admin_creds:
                (u, t, p) = ('u', 't', 'p')
            else:
                (u, t, p) = (None, None, None)

            cfg.CONF.set_default('admin_username', u, group='identity')
            cfg.CONF.set_default('admin_tenant_name', t, group='identity')
            cfg.CONF.set_default('admin_password', p, group='identity')

        expected = admin_creds is not None or tenant_isolation
        observed = credentials.is_admin_available()
        self.assertEqual(expected, observed)

    # Tenant isolation implies admin so only one test case for True
    def test__tenant_isolation__accounts_file__no_admin(self):
        self.run_test(tenant_isolation=True,
                      use_accounts_file=True,
                      admin_creds=None)

    def test__no_tenant_isolation__accounts_file__no_admin(self):
        self.run_test(tenant_isolation=False,
                      use_accounts_file=True,
                      admin_creds=None)

    def test__no_tenant_isolation__accounts_file__admin_role(self):
        self.run_test(tenant_isolation=False,
                      use_accounts_file=True,
                      admin_creds='role')

    def test__no_tenant_isolation__accounts_file__admin_type(self):
        self.run_test(tenant_isolation=False,
                      use_accounts_file=True,
                      admin_creds='type')

    def test__no_tenant_isolation__no_accounts_file__no_admin(self):
        self.run_test(tenant_isolation=False,
                      use_accounts_file=False,
                      admin_creds=None)

    def test__no_tenant_isolation__no_accounts_file__admin(self):
        self.run_test(tenant_isolation=False,
                      use_accounts_file=False,
                      admin_creds='role')
