# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import testtools

from tempest.lib import auth
from tempest.lib import exceptions
from tempest import service_clients
from tempest.tests import base
from tempest.tests.lib import fake_credentials


class TestServiceClients(base.TestCase):

    def test__init__creds_v2_uri(self):
        # Verify that no API request is made, since no mock
        # is required to run the test successfully
        creds = fake_credentials.FakeKeystoneV2Credentials()
        uri = 'fake_uri'
        _manager = service_clients.ServiceClients(creds, identity_uri=uri)
        self.assertIsInstance(_manager.auth_provider,
                              auth.KeystoneV2AuthProvider)

    def test__init__creds_v3_uri(self):
        # Verify that no API request is made, since no mock
        # is required to run the test successfully
        creds = fake_credentials.FakeKeystoneV3Credentials()
        uri = 'fake_uri'
        _manager = service_clients.ServiceClients(creds, identity_uri=uri)
        self.assertIsInstance(_manager.auth_provider,
                              auth.KeystoneV3AuthProvider)

    def test__init__base_creds_uri(self):
        creds = fake_credentials.FakeCredentials()
        uri = 'fake_uri'
        with testtools.ExpectedException(exceptions.InvalidCredentials):
            service_clients.ServiceClients(creds, identity_uri=uri)

    def test__init__invalid_creds_uri(self):
        creds = fake_credentials.FakeKeystoneV2Credentials()
        delattr(creds, 'username')
        uri = 'fake_uri'
        with testtools.ExpectedException(exceptions.InvalidCredentials):
            service_clients.ServiceClients(creds, identity_uri=uri)

    def test__init__creds_uri_none(self):
        creds = fake_credentials.FakeKeystoneV2Credentials()
        msg = "Invalid Credentials\nDetails: Manager requires a non-empty"
        with testtools.ExpectedException(exceptions.InvalidCredentials,
                                         value_re=msg):
            service_clients.ServiceClients(creds, None)
