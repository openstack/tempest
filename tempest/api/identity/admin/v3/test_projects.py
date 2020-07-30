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
import testtools

from tempest.api.identity import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ProjectsTestJSON(base.BaseIdentityV3AdminTest):
    """Test identity projects"""

    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    @decorators.idempotent_id('0ecf465c-0dc4-4532-ab53-91ffeb74d12d')
    def test_project_create_with_description(self):
        """Test creating project with a description"""
        project_desc = data_utils.rand_name('desc')
        project = self.setup_test_project(description=project_desc)
        project_id = project['id']
        desc1 = project['description']
        self.assertEqual(desc1, project_desc, 'Description should have '
                         'been sent in response for create')
        body = self.projects_client.show_project(project_id)['project']
        desc2 = body['description']
        self.assertEqual(desc2, project_desc, 'Description does not appear '
                         'to be set')

    @decorators.idempotent_id('5f50fe07-8166-430b-a882-3b2ee0abe26f')
    def test_project_create_with_domain(self):
        """Test creating project with a domain"""
        domain = self.setup_test_domain()
        project_name = data_utils.rand_name('project')
        project = self.setup_test_project(
            name=project_name, domain_id=domain['id'])
        project_id = project['id']
        self.assertEqual(project_name, project['name'])
        self.assertEqual(domain['id'], project['domain_id'])
        body = self.projects_client.show_project(project_id)['project']
        self.assertEqual(project_name, body['name'])
        self.assertEqual(domain['id'], body['domain_id'])

    @decorators.idempotent_id('1854f9c0-70bc-4d11-a08a-1c789d339e3d')
    def test_project_create_with_parent(self):
        """Test creating root project without providing a parent_id"""
        domain = self.setup_test_domain()
        domain_id = domain['id']

        root_project_name = data_utils.rand_name('root_project')
        root_project = self.setup_test_project(
            name=root_project_name, domain_id=domain_id)

        root_project_id = root_project['id']
        parent_id = root_project['parent_id']
        self.assertEqual(root_project_name, root_project['name'])
        # If not provided, the parent_id must point to the top level
        # project in the hierarchy, i.e. its domain
        self.assertEqual(domain_id, parent_id)

        # Create a project using root_project_id as parent_id
        project_name = data_utils.rand_name('project')
        project = self.setup_test_project(
            name=project_name, domain_id=domain_id, parent_id=root_project_id)
        parent_id = project['parent_id']
        self.assertEqual(project_name, project['name'])
        self.assertEqual(root_project_id, parent_id)

    @decorators.idempotent_id('a7eb9416-6f9b-4dbb-b71b-7f73aaef59d5')
    def test_create_is_domain_project(self):
        """Test creating is_domain project"""
        project = self.setup_test_project(domain_id=None, is_domain=True)
        # To delete a domain, we need to disable it first
        self.addCleanup(self.projects_client.update_project, project['id'],
                        enabled=False)

        # Check if the is_domain project is correctly returned by both
        # project and domain APIs
        projects_list = self.projects_client.list_projects(
            params={'is_domain': True})['projects']
        project_ids = [p['id'] for p in projects_list]
        self.assertIn(project['id'], project_ids)

        # The domains API return different attributes for the entity, so we
        # compare the entities IDs
        domains_ids = [d['id'] for d in self.domains_client.list_domains()[
            'domains']]
        self.assertIn(project['id'], domains_ids)

    @decorators.idempotent_id('1f66dc76-50cc-4741-a200-af984509e480')
    def test_project_create_enabled(self):
        """Test creating a project that is enabled"""
        project = self.setup_test_project(enabled=True)
        project_id = project['id']
        self.assertTrue(project['enabled'],
                        'Enable should be True in response')
        body = self.projects_client.show_project(project_id)['project']
        self.assertTrue(body['enabled'], 'Enable should be True in lookup')

    @decorators.idempotent_id('78f96a9c-e0e0-4ee6-a3ba-fbf6dfd03207')
    def test_project_create_not_enabled(self):
        """Test creating a project that is not enabled"""
        project = self.setup_test_project(enabled=False)
        self.assertFalse(project['enabled'],
                         'Enable should be False in response')
        body = self.projects_client.show_project(project['id'])['project']
        self.assertFalse(body['enabled'],
                         'Enable should be False in lookup')

    @decorators.idempotent_id('f608f368-048c-496b-ad63-d286c26dab6b')
    def test_project_update_name(self):
        """Test updating name attribute of a project"""
        p_name1 = data_utils.rand_name('project')
        project = self.setup_test_project(name=p_name1)

        resp1_name = project['name']

        p_name2 = data_utils.rand_name('project2')
        body = self.projects_client.update_project(project['id'],
                                                   name=p_name2)['project']
        resp2_name = body['name']
        self.assertNotEqual(resp1_name, resp2_name)

        body = self.projects_client.show_project(project['id'])['project']
        resp3_name = body['name']

        self.assertNotEqual(resp1_name, resp3_name)
        self.assertEqual(p_name1, resp1_name)
        self.assertEqual(resp2_name, resp3_name)

    @decorators.idempotent_id('f138b715-255e-4a7d-871d-351e1ef2e153')
    def test_project_update_desc(self):
        """Test updating description attribute of a project"""
        p_desc = data_utils.rand_name('desc')
        project = self.setup_test_project(description=p_desc)
        resp1_desc = project['description']

        p_desc2 = data_utils.rand_name('desc2')
        body = self.projects_client.update_project(
            project['id'], description=p_desc2)['project']
        resp2_desc = body['description']
        self.assertNotEqual(resp1_desc, resp2_desc)

        body = self.projects_client.show_project(project['id'])['project']
        resp3_desc = body['description']

        self.assertNotEqual(resp1_desc, resp3_desc)
        self.assertEqual(p_desc, resp1_desc)
        self.assertEqual(resp2_desc, resp3_desc)

    @decorators.idempotent_id('b6b25683-c97f-474d-a595-55d410b68100')
    def test_project_update_enable(self):
        """Test updating the enabled attribute of a project"""
        p_en = False
        project = self.setup_test_project(enabled=p_en)

        resp1_en = project['enabled']

        p_en2 = True
        body = self.projects_client.update_project(project['id'],
                                                   enabled=p_en2)['project']
        resp2_en = body['enabled']
        self.assertNotEqual(resp1_en, resp2_en)

        body = self.projects_client.show_project(project['id'])['project']
        resp3_en = body['enabled']

        self.assertNotEqual(resp1_en, resp3_en)
        self.assertFalse(project['enabled'])
        self.assertEqual(resp2_en, resp3_en)

    @decorators.idempotent_id('59398d4a-5dc5-4f86-9a4c-c26cc804d6c6')
    @testtools.skipIf(CONF.identity_feature_enabled.immutable_user_source,
                      'Skipped because environment has an '
                      'immutable user source and solely '
                      'provides read-only access to users.')
    def test_associate_user_to_project(self):
        """Test associating a user to a project"""
        # Create a Project
        project = self.setup_test_project()

        # Create a User
        u_name = data_utils.rand_name('user')
        u_desc = u_name + 'description'
        u_email = u_name + '@testmail.tm'
        u_password = data_utils.rand_password()
        user = self.users_client.create_user(
            name=u_name, description=u_desc, password=u_password,
            email=u_email, project_id=project['id'])['user']
        # Delete the User at the end of this method
        self.addCleanup(self.users_client.delete_user, user['id'])

        # Get User To validate the user details
        new_user_get = self.users_client.show_user(user['id'])['user']
        # Assert response body of GET
        self.assertEqual(u_name, new_user_get['name'])
        self.assertEqual(u_desc, new_user_get['description'])
        self.assertEqual(project['id'],
                         new_user_get['project_id'])
        self.assertEqual(u_email, new_user_get['email'])

    @decorators.idempotent_id('d1db68b6-aebe-4fa0-b79d-d724d2e21162')
    def test_project_get_equals_list(self):
        """Test the result of getting project equals that of listing"""
        fields = ['parent_id', 'is_domain', 'description', 'links',
                  'name', 'enabled', 'domain_id', 'id', 'tags']

        # Tags must be unique, keystone API will reject duplicates
        tags = ['a', 'c', 'b', 'd']

        # Create a Project, cleanup is handled in the helper
        project = self.setup_test_project(tags=tags)

        # Show and list for the project
        project_get = self.projects_client.show_project(
            project['id'])['project']
        _projects = self.projects_client.list_projects()['projects']
        project_list = next(x for x in _projects if x['id'] == project['id'])

        # Assert the expected fields exist. More fields than expected may
        # be in this list. This is for future proofind as keystone does not
        # and has no plans to support microservices. Any fields in the future
        # that are added to the response of the API should eventually be added
        # to the expected fields. The expected fields must be a subset of
        # the project_get fields (all keys in fields must exist in project_get,
        # but project_get.keys() may have additional fields)
        self.assertTrue(set(fields).issubset(project_get.keys()))

        # Ensure the set of tags is identical and match the expected one
        get_tags = set(project_get.pop("tags"))
        self.assertSetEqual(get_tags, set(project_list.pop("tags")))
        self.assertSetEqual(get_tags, set(tags))

        # Ensure all other fields are identical
        self.assertDictEqual(project_get, project_list)
