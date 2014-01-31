# Copyright 2013 Huawei Technologies Co.,LTD.
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
from tempest.common.utils import data_utils
from tempest.test import attr


class TokensTestJSON(base.BaseIdentityV2AdminTest):
    _interface = 'json'

    @attr(type='gate')
    def test_create_delete_token(self):
        # get a token by username and password
        user_name = data_utils.rand_name(name='user-')
        user_password = data_utils.rand_name(name='pass-')
        # first:create a tenant
        tenant_name = data_utils.rand_name(name='tenant-')
        resp, tenant = self.client.create_tenant(tenant_name)
        self.assertEqual(200, resp.status)
        self.data.tenants.append(tenant)
        # second:create a user
        resp, user = self.client.create_user(user_name, user_password,
                                             tenant['id'], '')
        self.assertEqual(200, resp.status)
        self.data.users.append(user)
        # then get a token for the user
        rsp, body = self.token_client.auth(user_name,
                                           user_password,
                                           tenant['name'])
        self.assertEqual(rsp['status'], '200')
        self.assertEqual(body['token']['tenant']['name'],
                         tenant['name'])
        # then delete the token
        token_id = body['token']['id']
        resp, body = self.client.delete_token(token_id)
        self.assertEqual(resp['status'], '204')


class TokensTestXML(TokensTestJSON):
    _interface = 'xml'
