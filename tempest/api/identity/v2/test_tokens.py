# Copyright 2015 OpenStack Foundation
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
from tempest import test


class TokensTest(base.BaseIdentityV2Test):

    @test.idempotent_id('65ae3b78-91ff-467b-a705-f6678863b8ec')
    def test_create_token(self):

        token_client = self.non_admin_token_client

        # get a token for the user
        creds = self.os.credentials
        username = creds.username
        password = creds.password
        tenant_name = creds.tenant_name

        body = token_client.auth(username,
                                 password,
                                 tenant_name)

        self.assertEqual(body['token']['tenant']['name'],
                         tenant_name)
