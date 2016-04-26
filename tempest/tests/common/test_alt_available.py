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

from oslo_config import cfg
from oslotest import mockpatch

from tempest.common import credentials_factory as credentials
from tempest import config
from tempest.tests import base
from tempest.tests import fake_config


class TestAltAvailable(base.TestCase):

    identity_version = 'v2'

    def setUp(self):
        super(TestAltAvailable, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)

    def run_test(self, dynamic_creds, use_accounts_file, creds):

        cfg.CONF.set_default('use_dynamic_credentials',
                             dynamic_creds, group='auth')
        if use_accounts_file:
            accounts = [dict(username="u%s" % ii,
                             project_name="t%s" % ii,
                             password="p") for ii in creds]
            self.useFixture(mockpatch.Patch(
                'tempest.common.preprov_creds.read_accounts_yaml',
                return_value=accounts))
            cfg.CONF.set_default('test_accounts_file',
                                 use_accounts_file, group='auth')
            self.useFixture(mockpatch.Patch('os.path.isfile',
                                            return_value=True))
        else:
            self.useFixture(mockpatch.Patch('os.path.isfile',
                                            return_value=False))
            cred_prefix = ['', 'alt_']
            for ii in range(0, 2):
                if len(creds) > ii:
                    username = 'u%s' % creds[ii]
                    project = 't%s' % creds[ii]
                    password = 'p'
                    domain = 'd'
                else:
                    username = None
                    project = None
                    password = None
                    domain = None

                cfg.CONF.set_default('%susername' % cred_prefix[ii], username,
                                     group='identity')
                cfg.CONF.set_default('%sproject_name' % cred_prefix[ii],
                                     project, group='identity')
                cfg.CONF.set_default('%spassword' % cred_prefix[ii], password,
                                     group='identity')
                cfg.CONF.set_default('%sdomain_name' % cred_prefix[ii], domain,
                                     group='identity')

        expected = len(set(creds)) > 1 or dynamic_creds
        observed = credentials.is_alt_available(
            identity_version=self.identity_version)
        self.assertEqual(expected, observed)

    # Dynamic credentials implies alt so only one test case for True
    def test__dynamic_creds__accounts_file__one_user(self):
        self.run_test(dynamic_creds=True,
                      use_accounts_file=False,
                      creds=['1', '2'])

    def test__no_dynamic_creds__accounts_file__one_user(self):
        self.run_test(dynamic_creds=False,
                      use_accounts_file=True,
                      creds=['1'])

    def test__no_dynamic_creds__accounts_file__two_users(self):
        self.run_test(dynamic_creds=False,
                      use_accounts_file=True,
                      creds=['1', '2'])

    def test__no_dynamic_creds__accounts_file__two_users_identical(self):
        self.run_test(dynamic_creds=False,
                      use_accounts_file=True,
                      creds=['1', '1'])

    def test__no_dynamic_creds__no_accounts_file__one_user(self):
        self.run_test(dynamic_creds=False,
                      use_accounts_file=False,
                      creds=['1'])

    def test__no_dynamic_creds__no_accounts_file__two_users(self):
        self.run_test(dynamic_creds=False,
                      use_accounts_file=False,
                      creds=['1', '2'])

    def test__no_dynamic_creds__no_accounts_file__two_users_identical(self):
        self.run_test(dynamic_creds=False,
                      use_accounts_file=False,
                      creds=['1', '1'])


class TestAltAvailableV3(TestAltAvailable):

    identity_version = 'v3'
