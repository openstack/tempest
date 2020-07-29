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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class UsersNegativeTest(base.BaseIdentityV3AdminTest):
    """Negative tests of keystone users"""

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e75f006c-89cc-477b-874d-588e4eab4b17')
    def test_create_user_for_non_existent_domain(self):
        """Attempt to create a user in a non-existent domain should fail"""
        u_name = data_utils.rand_name('user')
        u_email = u_name + '@testmail.tm'
        u_password = data_utils.rand_password()
        self.assertRaises(lib_exc.NotFound, self.users_client.create_user,
                          name=u_name, password=u_password,
                          email=u_email,
                          domain_id=data_utils.rand_uuid_hex())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b3c9fccc-4134-46f5-b600-1da6fb0a3b1f')
    def test_authentication_for_disabled_user(self):
        """Attempt to authenticate for disabled user should fail"""
        password = data_utils.rand_password()
        user = self.setup_test_user(password)
        self.disable_user(user['name'], user['domain_id'])
        self.assertRaises(lib_exc.Unauthorized, self.token.auth,
                          username=user['name'],
                          password=password,
                          user_domain_id=CONF.identity.default_domain_id)
