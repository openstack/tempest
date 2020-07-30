# Copyright 2017 AT&T Corporation
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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class TokensAdminTestNegative(base.BaseIdentityV2AdminTest):
    """Negative tests of keystone tokens via v2 API"""

    credentials = ['primary', 'admin', 'alt']

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a0a0a600-4292-4364-99c5-922c834fdf05')
    def test_check_token_existence_negative(self):
        """Test checking other tenant's token existence via v2 API

        Checking other tenant's token existence via v2 API should fail.
        """
        creds = self.os_primary.credentials
        creds_alt = self.os_alt.credentials
        username = creds.username
        password = creds.password
        tenant_name = creds.tenant_name
        alt_tenant_name = creds_alt.tenant_name
        body = self.token_client.auth(username, password, tenant_name)
        self.assertRaises(lib_exc.Unauthorized,
                          self.client.check_token_existence,
                          body['token']['id'],
                          belongsTo=alt_tenant_name)
