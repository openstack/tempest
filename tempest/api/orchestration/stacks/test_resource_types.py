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

from tempest.api.orchestration import base
from tempest import test


class ResourceTypesTest(base.BaseOrchestrationTest):

    @test.attr(type='smoke')
    @test.idempotent_id('7123d082-3577-4a30-8f00-f805327c4ffd')
    def test_resource_type_list(self):
        """Verify it is possible to list resource types."""
        resource_types = self.client.list_resource_types()
        self.assertIsInstance(resource_types, list)
        self.assertIn('OS::Nova::Server', resource_types)

    @test.attr(type='smoke')
    @test.idempotent_id('0e85a483-828b-4a28-a0e3-f0a21809192b')
    def test_resource_type_show(self):
        """Verify it is possible to get schema about resource types."""
        resource_types = self.client.list_resource_types()
        self.assertNotEmpty(resource_types)

        for resource_type in resource_types:
            type_schema = self.client.show_resource_type(resource_type)
            self.assert_fields_in_dict(type_schema, 'properties',
                                       'attributes', 'resource_type')
            self.assertEqual(resource_type, type_schema['resource_type'])

    @test.attr(type='smoke')
    @test.idempotent_id('8401821d-65fe-4d43-9fa3-57d5ce3a35c7')
    def test_resource_type_template(self):
        """Verify it is possible to get template about resource types."""
        type_template = self.client.show_resource_type_template(
            'OS::Nova::Server')
        self.assert_fields_in_dict(
            type_template,
            'Outputs',
            'Parameters', 'Resources')
