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
from tempest import test


class RolesV3TestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(RolesV3TestJSON, cls).setUpClass()
        cls.fetched_role_ids = list()
        u_name = data_utils.rand_name('user-')
        u_desc = '%s description' % u_name
        u_email = '%s@testmail.tm' % u_name
        cls.u_password = data_utils.rand_name('pass-')
        resp = [None] * 5
        resp[0], cls.domain = cls.client.create_domain(
            data_utils.rand_name('domain-'),
            description=data_utils.rand_name('domain-desc-'))
        resp[1], cls.project = cls.client.create_project(
            data_utils.rand_name('project-'),
            description=data_utils.rand_name('project-desc-'),
            domain_id=cls.domain['id'])
        resp[2], cls.group_body = cls.client.create_group(
            data_utils.rand_name('Group-'), project_id=cls.project['id'],
            domain_id=cls.domain['id'])
        resp[3], cls.user_body = cls.client.create_user(
            u_name, description=u_desc, password=cls.u_password,
            email=u_email, project_id=cls.project['id'],
            domain_id=cls.domain['id'])
        resp[4], cls.role = cls.client.create_role(
            data_utils.rand_name('Role-'))
        for r in resp:
            assert r['status'] == '201', (
                "Expected 201, but got: %s" % r['status'])

    @classmethod
    def tearDownClass(cls):
        resp = [None] * 5
        resp[0], _ = cls.client.delete_role(cls.role['id'])
        resp[1], _ = cls.client.delete_group(cls.group_body['id'])
        resp[2], _ = cls.client.delete_user(cls.user_body['id'])
        resp[3], _ = cls.client.delete_project(cls.project['id'])
        # NOTE(harika-vakadi): It is necessary to disable the domain
        # before deleting,or else it would result in unauthorized error
        cls.client.update_domain(cls.domain['id'], enabled=False)
        resp[4], _ = cls.client.delete_domain(cls.domain['id'])
        for r in resp:
            assert r['status'] == '204', (
                "Expected 204, but got: %s" % r['status'])
        super(RolesV3TestJSON, cls).tearDownClass()

    def _list_assertions(self, resp, body, fetched_role_ids, role_id):
        self.assertEqual(resp['status'], '200')
        self.assertEqual(len(body), 1)
        self.assertIn(role_id, fetched_role_ids)

    @test.attr(type='smoke')
    def test_role_create_update_get(self):
        r_name = data_utils.rand_name('Role-')
        resp, role = self.client.create_role(r_name)
        self.addCleanup(self.client.delete_role, role['id'])
        self.assertEqual(resp['status'], '201')
        self.assertIn('name', role)
        self.assertEqual(role['name'], r_name)

        new_name = data_utils.rand_name('NewRole-')
        resp, updated_role = self.client.update_role(new_name, role['id'])
        self.assertEqual(resp['status'], '200')
        self.assertIn('name', updated_role)
        self.assertIn('id', updated_role)
        self.assertIn('links', updated_role)
        self.assertNotEqual(r_name, updated_role['name'])

        resp, new_role = self.client.get_role(role['id'])
        self.assertEqual(resp['status'], '200')
        self.assertEqual(new_name, new_role['name'])
        self.assertEqual(updated_role['id'], new_role['id'])

    @test.attr(type='smoke')
    def test_grant_list_revoke_role_to_user_on_project(self):
        resp, _ = self.client.assign_user_role_on_project(
            self.project['id'], self.user_body['id'], self.role['id'])
        self.assertEqual(resp['status'], '204')

        resp, roles = self.client.list_user_roles_on_project(
            self.project['id'], self.user_body['id'])

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(resp, roles, self.fetched_role_ids,
                              self.role['id'])

        resp, _ = self.client.revoke_role_from_user_on_project(
            self.project['id'], self.user_body['id'], self.role['id'])
        self.assertEqual(resp['status'], '204')

    @test.attr(type='smoke')
    def test_grant_list_revoke_role_to_user_on_domain(self):
        resp, _ = self.client.assign_user_role_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])
        self.assertEqual(resp['status'], '204')

        resp, roles = self.client.list_user_roles_on_domain(
            self.domain['id'], self.user_body['id'])

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(resp, roles, self.fetched_role_ids,
                              self.role['id'])

        resp, _ = self.client.revoke_role_from_user_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])
        self.assertEqual(resp['status'], '204')

    @test.attr(type='smoke')
    def test_grant_list_revoke_role_to_group_on_project(self):
        # Grant role to group on project
        resp, _ = self.client.assign_group_role_on_project(
            self.project['id'], self.group_body['id'], self.role['id'])
        self.assertEqual(resp['status'], '204')
        # List group roles on project
        resp, roles = self.client.list_group_roles_on_project(
            self.project['id'], self.group_body['id'])

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(resp, roles, self.fetched_role_ids,
                              self.role['id'])
        # Add user to group, and insure user has role on project
        self.client.add_group_user(self.group_body['id'], self.user_body['id'])
        self.addCleanup(self.client.delete_group_user,
                        self.group_body['id'], self.user_body['id'])
        resp, body = self.token.auth(self.user_body['id'], self.u_password,
                                     self.project['name'],
                                     domain=self.domain['name'])
        roles = body['token']['roles']
        self.assertEqual(resp['status'], '201')
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0]['id'], self.role['id'])
        # Revoke role to group on project
        resp, _ = self.client.revoke_role_from_group_on_project(
            self.project['id'], self.group_body['id'], self.role['id'])
        self.assertEqual(resp['status'], '204')

    @test.attr(type='smoke')
    def test_grant_list_revoke_role_to_group_on_domain(self):
        resp, _ = self.client.assign_group_role_on_domain(
            self.domain['id'], self.group_body['id'], self.role['id'])
        self.assertEqual(resp['status'], '204')

        resp, roles = self.client.list_group_roles_on_domain(
            self.domain['id'], self.group_body['id'])

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(resp, roles, self.fetched_role_ids,
                              self.role['id'])

        resp, _ = self.client.revoke_role_from_group_on_domain(
            self.domain['id'], self.group_body['id'], self.role['id'])
        self.assertEqual(resp['status'], '204')


class RolesV3TestXML(RolesV3TestJSON):
    _interface = 'xml'
