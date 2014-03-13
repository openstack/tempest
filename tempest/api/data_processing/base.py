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

from tempest import config
import tempest.test


CONF = config.CONF


class BaseDataProcessingTest(tempest.test.BaseTestCase):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(BaseDataProcessingTest, cls).setUpClass()
        os = cls.get_client_manager()
        if not CONF.service_available.sahara:
            raise cls.skipException("Sahara support is required")
        cls.client = os.data_processing_client

        # set some constants
        cls.flavor_ref = CONF.compute.flavor_ref
        cls.simple_node_group_template = {
            'plugin_name': 'vanilla',
            'hadoop_version': '1.2.1',
            'node_processes': [
                "datanode",
                "tasktracker"
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

        # add lists for watched resources
        cls._node_group_templates = []

    @classmethod
    def tearDownClass(cls):
        # cleanup node group templates
        for ngt_id in cls._node_group_templates:
            try:
                cls.client.delete_node_group_template(ngt_id)
            except Exception:
                # ignore errors while auto removing created resource
                pass
        cls.clear_isolated_creds()
        super(BaseDataProcessingTest, cls).tearDownClass()

    @classmethod
    def create_node_group_template(cls, name, plugin_name, hadoop_version,
                                   node_processes, flavor_id,
                                   node_configs=None, **kwargs):
        """Creates watched node group template with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """

        resp, body = cls.client.create_node_group_template(name, plugin_name,
                                                           hadoop_version,
                                                           node_processes,
                                                           flavor_id,
                                                           node_configs,
                                                           **kwargs)

        # store id of created node group template
        template_id = body['id']
        cls._node_group_templates.append(template_id)

        return resp, body, template_id
