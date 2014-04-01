# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.api.data_processing import base as dp_base
from tempest.common.utils import data_utils
from tempest.test import attr


class NodeGroupTemplateTest(dp_base.BaseDataProcessingTest):
    @classmethod
    def setUpClass(cls):
        super(NodeGroupTemplateTest, cls).setUpClass()
        cls.node_group_template = {
            'description': 'Test node group template',
            'plugin_name': 'vanilla',
            'hadoop_version': '1.2.1',
            'node_processes': [
                'datanode',
                'tasktracker'
            ],
            'flavor_id': cls.flavor_ref,
            'node_configs': {
                'HDFS': {
                    'Data Node Heap Size': 1024
                },
                'MapReduce': {
                    'Task Tracker Heap Size': 1024
                }
            }
        }

    def _create_node_group_template(self, template_name=None):
        """Creates Node Group Template with optional name specified.

        It creates template and ensures response status and template name.
        Returns id and name of created template.
        """
        if template_name is None:
            # generate random name if it's not specified
            template_name = data_utils.rand_name('sahara-ng-template')

        # create node group template
        resp, body = self.create_node_group_template(
            template_name, **self.node_group_template)

        # ensure that template created successfully
        self.assertEqual(202, resp.status)
        self.assertEqual(template_name, body['name'])

        return body['id'], template_name

    @attr(type='smoke')
    def test_node_group_template_create(self):
        template_name = data_utils.rand_name('sahara-ng-template')
        resp, body = self.create_node_group_template(
            template_name, **self.node_group_template)

        # check that template created successfully
        self.assertEqual(resp.status, 202)
        self.assertEqual(template_name, body['name'])
        self.assertDictContainsSubset(self.node_group_template, body)

    @attr(type='smoke')
    def test_node_group_template_list(self):
        template_info = self._create_node_group_template()

        # check for node group template in list
        resp, templates = self.client.list_node_group_templates()

        self.assertEqual(200, resp.status)
        templates_info = [(template['id'], template['name'])
                          for template in templates]
        self.assertIn(template_info, templates_info)

    @attr(type='smoke')
    def test_node_group_template_get(self):
        template_id, template_name = self._create_node_group_template()

        # check node group template fetch by id
        resp, template = self.client.get_node_group_template(template_id)

        self.assertEqual(200, resp.status)
        self.assertEqual(template_name, template['name'])
        self.assertDictContainsSubset(self.node_group_template, template)

    @attr(type='smoke')
    def test_node_group_template_delete(self):
        template_id = self._create_node_group_template()[0]

        # delete the node group template by id
        resp = self.client.delete_node_group_template(template_id)[0]

        self.assertEqual(204, resp.status)
