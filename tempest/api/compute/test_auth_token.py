# Copyright 2013 IBM Corp
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.


import testtools

from tempest.api.compute import base
import tempest.config as config

CONF = config.CONF


class AuthTokenTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(AuthTokenTestJSON, cls).setUpClass()

        cls.servers_v2 = cls.os.servers_client
        cls.servers_v3 = cls.os.servers_client_v3_auth

    def test_v2_token(self):
        # Can get a token using v2 of the identity API and use that to perform
        # an operation on the compute service.

        # Doesn't matter which compute API is used,
        # picking list_servers because it's easy.
        self.servers_v2.list_servers()

    @testtools.skipIf(not CONF.identity.uri_v3,
                      'v3 auth client not configured')
    def test_v3_token(self):
        # Can get a token using v3 of the identity API and use that to perform
        # an operation on the compute service.

        # Doesn't matter which compute API is used,
        # picking list_servers because it's easy.
        self.servers_v3.list_servers()


class AuthTokenTestXML(AuthTokenTestJSON):
    _interface = 'xml'
