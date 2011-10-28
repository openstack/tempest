# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack, LLC
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

"""Functional test case against the OpenStack Nova API server"""

import httplib2
import json
import os
import time
import uuid

from kong import keystone
from kong import tests


class TestKeystoneAuth(tests.FunctionalTest):

    def setUp(self):
        super(TestKeystoneAuth, self).setUp()

        api_version = self.keystone['apiver']
        if api_version != 'v2.0':
            raise ValueError("Must use Identity API v2.0")

        args = (self.keystone['service_host'],
            self.keystone['service_port'],
                api_version)

        self.base_url = "http://%s:%s/%s/tokens" % args

        self.user = self.keystone['user']
        self.password = self.keystone['password']
        self.tenant_id = self.keystone['tenant_id']

    def test_can_get_token(self):
        headers = {'content-type': 'application/json'}

        body = {
            "auth": {
                "passwordCredentials":{
                    "username": self.user,
                    "password": self.password,
                },
                "tenantId": self.tenant_id,
            },
        }

        http = httplib2.Http()
        response, content = http.request(self.base_url, 'POST',
                                         headers=headers,
                                         body=json.dumps(body))

        self.assertEqual(response.status, 200)
        res_body = json.loads(content)
        self.assertTrue(res_body['access']['token']['id'])
    test_can_get_token.tags = ['auth']

    def test_bad_user(self):
        headers = {'content-type': 'application/json'}

        body = {
            "auth": {
                "passwordCredentials": {
                    "username": str(uuid.uuid4()),
                    "password": self.password,
                },
                "tenantId": self.tenant_id,
            },
        }

        http = httplib2.Http()
        response, content = http.request(self.base_url, 'POST',
                                         headers=headers,
                                         body=json.dumps(body))

        self.assertEqual(response.status, 401)
    test_bad_user.tags = ['auth']

    def test_bad_password(self):
        headers = {'content-type': 'application/json'}

        body = {
            "auth": {
                "passwordCredentials": {
                    "username": self.user,
                    "password": str(uuid.uuid4()),
                },
                "tenantId": self.tenant_id,
            },
        }

        http = httplib2.Http()
        response, content = http.request(self.base_url, 'POST',
                                         headers=headers,
                                         body=json.dumps(body))

        self.assertEqual(response.status, 401)
    test_bad_password.tags = ['auth']

    def test_bad_tenant_id(self):
        headers = {'content-type': 'application/json'}

        body = {
            "auth": {
                "passwordCredentials": {
                    "username": self.user,
                    "password": self.password,
                },
                "tenantId": str(uuid.uuid4()),
            },
        }

        http = httplib2.Http()
        response, content = http.request(self.base_url, 'POST',
                                         headers=headers,
                                         body=json.dumps(body))

        self.assertEqual(response.status, 401)
    test_bad_tenant_id.tags = ['auth']



class TestKeystoneAuthWithNova(tests.FunctionalTest):

    def setUp(self):
        super(TestKeystoneAuthWithNova, self).setUp()
        args = (self.nova['host'], self.nova['port'],
                self.nova['ver'], self.nova['project'])
        self.base_url = "http://%s:%s/%s/%s" % args

        self.keystone_api = keystone.API(self.keystone['service_host'],
                                         self.keystone['service_port'])

    def _get_token(self):
        user = self.keystone['user']
        password = self.keystone['password']
        tenant_id = self.keystone['tenant_id']
        return self.keystone_api.get_token(user, password, tenant_id)

    def test_good_token(self):
        http = httplib2.Http()
        url = '%s/flavors' % self.base_url
        headers = {'x-auth-token': self._get_token()}
        response, content = http.request(url, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
    test_good_token.tags = ['nova', 'auth']

    def test_bad_token(self):
        http = httplib2.Http()
        url = '%s/flavors' % self.base_url
        headers = {'x-auth-token': str(uuid.uuid4())}
        response, content = http.request(url, 'GET', headers=headers)
        self.assertEqual(response.status, 401)
    test_bad_token.tags = ['nova', 'auth']

    def test_no_token(self):
        http = httplib2.Http()
        url = '%s/flavors' % self.base_url
        headers = {'x-auth-token': str(uuid.uuid4())}
        response, content = http.request(url, 'GET', headers=headers)
        self.assertEqual(response.status, 401)
    test_no_token.tags = ['nova', 'auth']

    def test_no_header(self):
        http = httplib2.Http()
        url = '%s/flavors' % self.base_url
        response, content = http.request(url, 'GET')
        self.assertEqual(response.status, 401)
    test_no_header.tags = ['nova', 'auth']
