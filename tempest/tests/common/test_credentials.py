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

from tempest.common import credentials_factory as credentials
from tempest import config
from tempest import exceptions
from tempest.tests import base
from tempest.tests import fake_config


class TestLegacyCredentialsProvider(base.TestCase):

    fixed_params = {'identity_version': 'v2'}

    def setUp(self):
        super(TestLegacyCredentialsProvider, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)

    def test_get_creds_roles_legacy_invalid(self):
        test_accounts_class = credentials.LegacyCredentialProvider(
            **self.fixed_params)
        self.assertRaises(exceptions.InvalidConfiguration,
                          test_accounts_class.get_creds_by_roles,
                          ['fake_role'])
