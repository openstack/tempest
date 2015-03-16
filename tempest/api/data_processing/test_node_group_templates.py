# Copyright (c) 2014 Mirantis Inc.
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

from tempest_lib.common.utils import data_utils

from tempest.api.data_processing import base as dp_base
from tempest import test


class NodeGroupTemplateTest(dp_base.BaseDataProcessingTest):
    @classmethod
    def resource_setup(cls):
        super(NodeGroupTemplateTest, cls).resource_setup()
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

        It creates template, ensures template name and response body.
        Returns id and name of created template.
        """
        if not template_name:
            # generate random name if it's not specified
            template_name = data_utils.rand_name('sahara-ng-template')

        # create node group template
        resp_body = self.create_node_group_template(template_name,
                                                    **self.node_group_template)

        # ensure that template created successfully
        self.assertEqual(template_name, resp_body['name'])
        self.assertDictContainsSubset(self.node_group_template, resp_body)

        return resp_body['id'], template_name

    @test.attr(type='smoke')
    @test.idempotent_id('63164051-e46d-4387-9741-302ef4791cbd')
    def test_node_group_template_create(self):
        self._create_node_group_template()

    @test.attr(type='smoke')
    @test.idempotent_id('eb39801d-2612-45e5-88b1-b5d70b329185')
    def test_node_group_template_list(self):
        template_info = self._create_node_group_template()

        # check for node group template in list
        templates = self.client.list_node_group_templates()
        templates_info = [(template['id'], template['name'])
                          for template in templates]
        self.assertIn(template_info, templates_info)

    @test.attr(type='smoke')
    @test.idempotent_id('6ee31539-a708-466f-9c26-4093ce09a836')
    def test_node_group_template_get(self):
        template_id, template_name = self._create_node_group_template()

        # check node group template fetch by id
        template = self.client.get_node_group_template(template_id)
        self.assertEqual(template_name, template['name'])
        self.assertDictContainsSubset(self.node_group_template, template)

    @test.attr(type='smoke')
    @test.idempotent_id('f4f5cb82-708d-4031-81c4-b0618a706a2f')
    def test_node_group_template_delete(self):
        template_id, _ = self._create_node_group_template()

        # delete the node group template by id
        self.client.delete_node_group_template(template_id)
