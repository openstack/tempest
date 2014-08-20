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

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import test


class ListProjectsTestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ListProjectsTestJSON, cls).setUpClass()
        cls.project_ids = list()
        cls.data.setup_test_domain()
        # Create project with domain
        cls.p1_name = data_utils.rand_name('project')
        _, cls.p1 = cls.client.create_project(
            cls.p1_name, enabled=False, domain_id=cls.data.domain['id'])
        cls.data.projects.append(cls.p1)
        cls.project_ids.append(cls.p1['id'])
        # Create default project
        p2_name = data_utils.rand_name('project')
        _, cls.p2 = cls.client.create_project(p2_name)
        cls.data.projects.append(cls.p2)
        cls.project_ids.append(cls.p2['id'])

    @test.attr(type='gate')
    def test_projects_list(self):
        # List projects
        resp, list_projects = self.client.list_projects()

        for p in self.project_ids:
            _, get_project = self.client.get_project(p)
            self.assertIn(get_project, list_projects)

    @test.attr(type='gate')
    def test_list_projects_with_domains(self):
        # List projects with domain
        self._list_projects_with_params(
            {'domain_id': self.data.domain['id']}, 'domain_id')

    @test.attr(type='gate')
    def test_list_projects_with_enabled(self):
        # List the projects with enabled
        self._list_projects_with_params({'enabled': False}, 'enabled')

    @test.attr(type='gate')
    def test_list_projects_with_name(self):
        # List projects with name
        self._list_projects_with_params({'name': self.p1_name}, 'name')

    def _list_projects_with_params(self, params, key):
        resp, body = self.client.list_projects(params)
        self.assertIn(self.p1[key], map(lambda x: x[key], body))
        self.assertNotIn(self.p2[key], map(lambda x: x[key], body))


class ListProjectsTestXML(ListProjectsTestJSON):
    _interface = 'xml'
