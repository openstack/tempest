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
from oslo_serialization import jsonutils as json

from tempest.api.identity import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class CredentialsTestJSON(base.BaseIdentityV3AdminTest):
    """Test keystone credentials"""

    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    @classmethod
    def resource_setup(cls):
        super(CredentialsTestJSON, cls).resource_setup()
        cls.projects = list()
        cls.creds_list = [['project_id', 'user_id', 'id'],
                          ['access', 'secret']]
        for _ in range(2):
            project = cls.projects_client.create_project(
                data_utils.rand_name('project'),
                description=data_utils.rand_name('project-desc'))['project']
            cls.addClassResourceCleanup(
                cls.projects_client.delete_project, project['id'])
            cls.projects.append(project['id'])
        cls.user_body = cls.users_client.show_user(
            cls.os_primary.credentials.user_id)['user']

    def _delete_credential(self, cred_id):
        self.creds_client.delete_credential(cred_id)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('7cd59bf9-bda4-4c72-9467-d21cab278355')
    def test_credentials_create_get_update_delete(self):
        """Test creating, getting, updating, deleting of credentials"""
        blob = '{"access": "%s", "secret": "%s"}' % (
            data_utils.rand_name('Access'), data_utils.rand_name('Secret'))
        cred = self.creds_client.create_credential(
            user_id=self.user_body['id'], project_id=self.projects[0],
            blob=blob, type='ec2')['credential']
        self.addCleanup(self._delete_credential, cred['id'])
        for value1 in self.creds_list[0]:
            self.assertIn(value1, cred)
        for value2 in self.creds_list[1]:
            self.assertIn(value2, cred['blob'])

        new_keys = [data_utils.rand_name('NewAccess'),
                    data_utils.rand_name('NewSecret')]
        blob = '{"access": "%s", "secret": "%s"}' % (new_keys[0], new_keys[1])
        update_body = self.creds_client.update_credential(
            cred['id'], blob=blob, project_id=self.projects[1],
            type='ec2')['credential']
        update_body['blob'] = json.loads(update_body['blob'])
        self.assertEqual(cred['id'], update_body['id'])
        self.assertEqual(self.projects[1], update_body['project_id'])
        self.assertEqual(self.user_body['id'], update_body['user_id'])
        self.assertEqual(update_body['blob']['access'], new_keys[0])
        self.assertEqual(update_body['blob']['secret'], new_keys[1])

        get_body = self.creds_client.show_credential(cred['id'])['credential']
        get_body['blob'] = json.loads(get_body['blob'])
        for value1 in self.creds_list[0]:
            self.assertEqual(update_body[value1],
                             get_body[value1])
        for value2 in self.creds_list[1]:
            self.assertEqual(update_body['blob'][value2],
                             get_body['blob'][value2])

    @decorators.idempotent_id('13202c00-0021-42a1-88d4-81b44d448aab')
    def test_credentials_list_delete(self):
        """Test listing credentials"""
        created_cred_ids = list()
        fetched_cred_ids = list()

        for _ in range(2):
            blob = '{"access": "%s", "secret": "%s"}' % (
                data_utils.rand_name('Access'), data_utils.rand_name('Secret'))
            cred = self.creds_client.create_credential(
                user_id=self.user_body['id'], project_id=self.projects[0],
                blob=blob, type='ec2')['credential']
            created_cred_ids.append(cred['id'])
            self.addCleanup(self._delete_credential, cred['id'])

        creds = self.creds_client.list_credentials()['credentials']

        for i in creds:
            fetched_cred_ids.append(i['id'])
        missing_creds = [c for c in created_cred_ids
                         if c not in fetched_cred_ids]
        self.assertEmpty(missing_creds,
                         "Failed to find cred %s in fetched list" %
                         ', '.join(m_cred for m_cred in missing_creds))
