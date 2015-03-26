# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

from tempest import auth
from tempest.common import cred_provider
from tempest.common import tempest_fixtures as fixtures
from tempest import config
from tempest.services.identity.v2.json import token_client as v2_client
from tempest.services.identity.v3.json import token_client as v3_client
from tempest.tests import fake_config
from tempest.tests import fake_identity
# Note(andreaf): once credentials tests move to tempest-lib, I will copy the
# parts of them required by these here.
from tempest.tests import test_credentials as test_creds


class ConfiguredV2CredentialsTests(test_creds.CredentialsTests):
    attributes = {
        'username': 'fake_username',
        'password': 'fake_password',
        'tenant_name': 'fake_tenant_name'
    }

    identity_response = fake_identity._fake_v2_response
    credentials_class = auth.KeystoneV2Credentials
    tokenclient_class = v2_client.TokenClientJSON
    identity_version = 'v2'

    def setUp(self):
        super(ConfiguredV2CredentialsTests, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)
        self.stubs.Set(self.tokenclient_class, 'raw_request',
                       self.identity_response)

    def _verify_credentials(self, credentials_class, filled=True,
                            identity_version=None):
        for ctype in cred_provider.CREDENTIAL_TYPES:
            if identity_version is None:
                creds = cred_provider.get_configured_credentials(
                    credential_type=ctype, fill_in=filled)
            else:
                creds = cred_provider.get_configured_credentials(
                    credential_type=ctype, fill_in=filled,
                    identity_version=identity_version)
            self._check(creds, credentials_class, filled)

    def test_get_configured_credentials(self):
        self.useFixture(fixtures.LockFixture('auth_version'))
        self._verify_credentials(credentials_class=self.credentials_class)

    def test_get_configured_credentials_unfilled(self):
        self.useFixture(fixtures.LockFixture('auth_version'))
        self._verify_credentials(credentials_class=self.credentials_class,
                                 filled=False)

    def test_get_configured_credentials_version(self):
        # version specified and not loaded from config
        self.useFixture(fixtures.LockFixture('auth_version'))
        self._verify_credentials(credentials_class=self.credentials_class,
                                 identity_version=self.identity_version)

    def test_is_valid(self):
        creds = self._get_credentials()
        self.assertTrue(creds.is_valid())


class ConfiguredV3CredentialsTests(ConfiguredV2CredentialsTests):
    attributes = {
        'username': 'fake_username',
        'password': 'fake_password',
        'project_name': 'fake_project_name',
        'user_domain_name': 'fake_domain_name'
    }

    credentials_class = auth.KeystoneV3Credentials
    identity_response = fake_identity._fake_v3_response
    tokenclient_class = v3_client.V3TokenClientJSON
    identity_version = 'v3'

    def setUp(self):
        super(ConfiguredV3CredentialsTests, self).setUp()
        # Additional config items reset by cfg fixture after each test
        cfg.CONF.set_default('auth_version', 'v3', group='identity')
        # Identity group items
        for prefix in ['', 'alt_', 'admin_']:
            cfg.CONF.set_default(prefix + 'domain_name', 'fake_domain_name',
                                 group='identity')
