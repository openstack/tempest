# Copyright 2013 OpenStack Foundation
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


class CredentialsTestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(CredentialsTestJSON, cls).setUpClass()
        cls.projects = list()
        cls.creds_list = [['project_id', 'user_id', 'id'],
                          ['access', 'secret']]
        u_name = data_utils.rand_name('user-')
        u_desc = '%s description' % u_name
        u_email = '%s@testmail.tm' % u_name
        u_password = data_utils.rand_name('pass-')
        for i in range(2):
            resp, cls.project = cls.v3_client.create_project(
                data_utils.rand_name('project-'),
                description=data_utils.rand_name('project-desc-'))
            assert resp['status'] == '201', "Expected %s" % resp['status']
            cls.projects.append(cls.project['id'])

        resp, cls.user_body = cls.v3_client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email, project_id=cls.projects[0])
        assert resp['status'] == '201', "Expected: %s" % resp['status']

    @classmethod
    def tearDownClass(cls):
        resp, _ = cls.v3_client.delete_user(cls.user_body['id'])
        assert resp['status'] == '204', "Expected: %s" % resp['status']
        for p in cls.projects:
            resp, _ = cls.v3_client.delete_project(p)
            assert resp['status'] == '204', "Expected: %s" % resp['status']
        super(CredentialsTestJSON, cls).tearDownClass()

    def _delete_credential(self, cred_id):
        resp, body = self.creds_client.delete_credential(cred_id)
        self.assertEqual(resp['status'], '204')

    @attr(type='smoke')
    def test_credentials_create_get_update_delete(self):
        keys = [data_utils.rand_name('Access-'),
                data_utils.rand_name('Secret-')]
        resp, cred = self.creds_client.create_credential(
            keys[0], keys[1], self.user_body['id'],
            self.projects[0])
        self.addCleanup(self._delete_credential, cred['id'])
        self.assertEqual(resp['status'], '201')
        for value1 in self.creds_list[0]:
            self.assertIn(value1, cred)
        for value2 in self.creds_list[1]:
            self.assertIn(value2, cred['blob'])

        new_keys = [data_utils.rand_name('NewAccess-'),
                    data_utils.rand_name('NewSecret-')]
        resp, update_body = self.creds_client.update_credential(
            cred['id'], access_key=new_keys[0], secret_key=new_keys[1],
            project_id=self.projects[1])
        self.assertEqual(resp['status'], '200')
        self.assertEqual(cred['id'], update_body['id'])
        self.assertEqual(self.projects[1], update_body['project_id'])
        self.assertEqual(self.user_body['id'], update_body['user_id'])
        self.assertEqual(update_body['blob']['access'], new_keys[0])
        self.assertEqual(update_body['blob']['secret'], new_keys[1])

        resp, get_body = self.creds_client.get_credential(cred['id'])
        self.assertEqual(resp['status'], '200')
        for value1 in self.creds_list[0]:
            self.assertEqual(update_body[value1],
                             get_body[value1])
        for value2 in self.creds_list[1]:
            self.assertEqual(update_body['blob'][value2],
                             get_body['blob'][value2])

    @attr(type='smoke')
    def test_credentials_list_delete(self):
        created_cred_ids = list()
        fetched_cred_ids = list()

        for i in range(2):
            resp, cred = self.creds_client.create_credential(
                data_utils.rand_name('Access-'),
                data_utils.rand_name('Secret-'),
                self.user_body['id'], self.projects[0])
            self.assertEqual(resp['status'], '201')
            created_cred_ids.append(cred['id'])
            self.addCleanup(self._delete_credential, cred['id'])

        resp, creds = self.creds_client.list_credentials()
        self.assertEqual(resp['status'], '200')

        for i in creds:
            fetched_cred_ids.append(i['id'])
        missing_creds = [c for c in created_cred_ids
                         if c not in fetched_cred_ids]
        self.assertEqual(0, len(missing_creds),
                         "Failed to find cred %s in fetched list" %
                         ', '.join(m_cred for m_cred in missing_creds))


class CredentialsTestXML(CredentialsTestJSON):
    _interface = 'xml'
