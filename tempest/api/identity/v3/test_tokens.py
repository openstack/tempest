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

from oslo_utils import timeutils
import six
from tempest.api.identity import base
from tempest import test


class TokensV3Test(base.BaseIdentityV3Test):

    @test.idempotent_id('6f8e4436-fc96-4282-8122-e41df57197a9')
    def test_create_token(self):

        creds = self.os.credentials
        user_id = creds.user_id
        username = creds.username
        password = creds.password
        user_domain_id = creds.user_domain_id

        # 'user_domain_id' needs to be specified otherwise tempest.lib assumes
        # it to be 'default'
        token_id, resp = self.non_admin_token.get_token(
            user_id=user_id,
            user_domain_id=user_domain_id,
            password=password,
            auth_data=True)

        self.assertNotEmpty(token_id)
        self.assertIsInstance(token_id, six.string_types)

        now = timeutils.utcnow()
        expires_at = timeutils.normalize_time(
            timeutils.parse_isotime(resp['expires_at']))
        self.assertGreater(resp['expires_at'],
                           resp['issued_at'])
        self.assertGreater(expires_at, now)

        subject_id = resp['user']['id']
        self.assertEqual(subject_id, user_id)

        subject_name = resp['user']['name']
        self.assertEqual(subject_name, username)

        self.assertEqual(resp['methods'][0], 'password')
