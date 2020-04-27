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
from tempest.lib import decorators


class TokensTest(base.BaseIdentityV2Test):
    """Test tokens in identity v2 API"""

    @decorators.idempotent_id('65ae3b78-91ff-467b-a705-f6678863b8ec')
    def test_create_token(self):
        """Test creating token for user via v2 API"""
        token_client = self.non_admin_token_client

        # get a token for the user
        creds = self.os_primary.credentials
        username = creds.username
        password = creds.password
        tenant_name = creds.tenant_name

        body = token_client.auth(username, password, tenant_name)

        self.assertNotEmpty(body['token']['id'])
        self.assertIsInstance(body['token']['id'], six.string_types)

        now = timeutils.utcnow()
        expires_at = timeutils.normalize_time(
            timeutils.parse_isotime(body['token']['expires']))
        self.assertGreater(expires_at, now)

        self.assertEqual(body['token']['tenant']['id'],
                         creds.tenant_id)
        self.assertEqual(body['token']['tenant']['name'],
                         tenant_name)

        self.assertEqual(body['user']['id'], creds.user_id)
