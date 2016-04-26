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

from tempest.common import credentials_factory as common_creds
from tempest.common import tempest_fixtures as fixtures
from tempest import config
from tempest.lib import auth
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.identity.v2 import token_client as v2_client
from tempest.lib.services.identity.v3 import token_client as v3_client
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests.lib import fake_identity


class ConfiguredV2CredentialsTests(base.TestCase):
    attributes = {
        'username': 'fake_username',
        'password': 'fake_password',
        'tenant_name': 'fake_tenant_name'
    }

    identity_response = fake_identity._fake_v2_response
    credentials_class = auth.KeystoneV2Credentials
    tokenclient_class = v2_client.TokenClient
    identity_version = 'v2'

    def setUp(self):
        super(ConfiguredV2CredentialsTests, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)
        self.patchobject(self.tokenclient_class, 'raw_request',
                         self.identity_response)

    def _get_credentials(self, attributes=None):
        if attributes is None:
            attributes = self.attributes
        return self.credentials_class(**attributes)

    def _check(self, credentials, credentials_class, filled):
        # Check the right version of credentials has been returned
        self.assertIsInstance(credentials, credentials_class)
        # Check the id attributes are filled in
        attributes = [x for x in credentials.ATTRIBUTES if (
            '_id' in x and x != 'domain_id')]
        for attr in attributes:
            if filled:
                self.assertIsNotNone(getattr(credentials, attr))
            else:
                self.assertIsNone(getattr(credentials, attr))

    def _verify_credentials(self, credentials_class, filled=True,
                            identity_version=None):
        for ctype in common_creds.CREDENTIAL_TYPES:
            if identity_version is None:
                creds = common_creds.get_configured_credentials(
                    credential_type=ctype, fill_in=filled)
            else:
                creds = common_creds.get_configured_credentials(
                    credential_type=ctype, fill_in=filled,
                    identity_version=identity_version)
            self._check(creds, credentials_class, filled)

    def test_create(self):
        creds = self._get_credentials()
        self.assertEqual(self.attributes, creds._initial)

    def test_create_invalid_attr(self):
        self.assertRaises(lib_exc.InvalidCredentials,
                          self._get_credentials,
                          attributes=dict(invalid='fake'))

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
    tokenclient_class = v3_client.V3TokenClient
    identity_version = 'v3'

    def setUp(self):
        super(ConfiguredV3CredentialsTests, self).setUp()
        # Additional config items reset by cfg fixture after each test
        cfg.CONF.set_default('auth_version', 'v3', group='identity')
        # Identity group items
        for prefix in ['', 'alt_', 'admin_']:
            if prefix == 'admin_':
                group = 'auth'
            else:
                group = 'identity'
            cfg.CONF.set_default(prefix + 'domain_name', 'fake_domain_name',
                                 group=group)
