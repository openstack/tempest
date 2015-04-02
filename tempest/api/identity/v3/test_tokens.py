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


class TokensV3Test(base.BaseIdentityV3Test):

    @test.idempotent_id('6f8e4436-fc96-4282-8122-e41df57197a9')
    def test_create_token(self):

        creds = self.os.credentials
        user_id = creds.user_id
        username = creds.username
        password = creds.password
        resp = self.non_admin_token.auth(user_id=user_id,
                                         password=password)

        subject_name = resp['token']['user']['name']
        self.assertEqual(subject_name, username)
