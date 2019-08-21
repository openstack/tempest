# Copyright 2014 Hewlett-Packard Development Company, L.P
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

from oslo_log import log as logging

from tempest.api.identity import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

LOG = logging.getLogger(__name__)
CONF = config.CONF


class BaseListProjectsTestJSON(base.BaseIdentityV3AdminTest):

    def _list_projects_with_params(self, included, excluded, params, key):
        # Validate that projects in ``included`` belongs to the projects
        # returned that match ``params`` but not projects in ``excluded``
        all_projects = self.projects_client.list_projects()['projects']
        LOG.debug("Complete list of projects available in keystone: %s",
                  all_projects)
        body = self.projects_client.list_projects(params)['projects']
        for p in included:
            self.assertIn(p[key], map(lambda x: x[key], body))
        for p in excluded:
            self.assertNotIn(p[key], map(lambda x: x[key], body))


class ListProjectsTestJSON(BaseListProjectsTestJSON):

    @classmethod
    def resource_setup(cls):
        super(ListProjectsTestJSON, cls).resource_setup()
        domain_id = cls.os_admin.credentials.domain_id
        # Create project with domain
        p1_name = data_utils.rand_name(cls.__name__)
        cls.p1 = cls.projects_client.create_project(
            p1_name, enabled=False, domain_id=domain_id)['project']
        cls.addClassResourceCleanup(cls.projects_client.delete_project,
                                    cls.p1['id'])
        # Create default project
        p2_name = data_utils.rand_name(cls.__name__)
        cls.p2 = cls.projects_client.create_project(p2_name)['project']
        cls.addClassResourceCleanup(cls.projects_client.delete_project,
                                    cls.p2['id'])
        # Create a new project (p3) using p2 as parent project
        p3_name = data_utils.rand_name(cls.__name__)
        cls.p3 = cls.projects_client.create_project(
            p3_name, parent_id=cls.p2['id'])['project']
        cls.addClassResourceCleanup(cls.projects_client.delete_project,
                                    cls.p3['id'])

    @decorators.idempotent_id('0fe7a334-675a-4509-b00e-1c4b95d5dae8')
    def test_list_projects_with_enabled(self):
        # List the projects with enabled
        self._list_projects_with_params(
            [self.p1], [self.p2, self.p3], {'enabled': False}, 'enabled')

    @decorators.idempotent_id('6edc66f5-2941-4a17-9526-4073311c1fac')
    def test_list_projects_with_parent(self):
        # List projects with parent
        params = {'parent_id': self.p3['parent_id']}
        fetched_projects = self.projects_client.list_projects(
            params)['projects']
        self.assertNotEmpty(fetched_projects)
        for project in fetched_projects:
            self.assertEqual(self.p3['parent_id'], project['parent_id'])


class ListProjectsStaticTestJSON(BaseListProjectsTestJSON):
    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    @classmethod
    def resource_setup(cls):
        super(ListProjectsStaticTestJSON, cls).resource_setup()
        # Fetch an existing project from os_primary
        cls.p1 = cls.projects_client.show_project(
            cls.os_primary.credentials.project_id)['project']
        # Create a test project
        p2_name = data_utils.rand_name(cls.__name__)
        p2_domain_id = CONF.identity.default_domain_id
        cls.p2 = cls.projects_client.create_project(
            p2_name, domain_id=p2_domain_id)['project']
        cls.addClassResourceCleanup(cls.projects_client.delete_project,
                                    cls.p2['id'])

    @decorators.idempotent_id('1d830662-22ad-427c-8c3e-4ec854b0af44')
    def test_list_projects(self):
        # List projects
        list_projects = self.projects_client.list_projects()['projects']

        for p in [self.p1, self.p2]:
            show_project = self.projects_client.show_project(p['id'])[
                'project']
            self.assertIn(show_project, list_projects)

    @decorators.idempotent_id('fa178524-4e6d-4925-907c-7ab9f42c7e26')
    def test_list_projects_with_name(self):
        # List projects with name
        self._list_projects_with_params(
            [self.p1], [self.p2], {'name': self.p1['name']}, 'name')

    @decorators.idempotent_id('fab13f3c-f6a6-4b9f-829b-d32fd44fdf10')
    def test_list_projects_with_domains(self):
        # Verify project list filtered by domain
        key = 'domain_id'
        for p in [self.p1, self.p2]:
            params = {key: p[key]}
            # Verify filter shows both projects in their respective domains
            self._list_projects_with_params([p], [], params, key)
        # Verify filter excludes projects that are filtered out
        if self.p1[key] != self.p2[key]:
            exclude = [self.p2]
            params = {key: self.p1[key]}
            self._list_projects_with_params([self.p1], exclude, params, key)
