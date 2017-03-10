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

from tempest.api.image import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class MetadataNamespacePropertiesTest(base.BaseV2ImageTest):
    """Test the Metadata definition namespace property basic functionality"""

    @decorators.idempotent_id('b1a3765e-3a5d-4f6d-a3a7-3ca3476ae768')
    def test_basic_meta_def_namespace_property(self):
        # Get the available resource types and use one resource_type
        body = self.resource_types_client.list_resource_types()
        resource_name = body['resource_types'][0]['name']
        enum = ["xen", "qemu", "kvm", "lxc", "uml", "vmware", "hyperv"]
        # Create a namespace
        namespace = self.create_namespace()
        # Create resource type association
        body = self.resource_types_client.create_resource_type_association(
            namespace['namespace'], name=resource_name)
        # Create a property
        property_title = data_utils.rand_name('property')
        body = self.namespace_properties_client.create_namespace_property(
            namespace=namespace['namespace'], title=property_title,
            name=resource_name, type="string", enum=enum)
        self.assertEqual(property_title, body['title'])
        # Show namespace property
        body = self.namespace_properties_client.show_namespace_properties(
            namespace['namespace'], resource_name)
        self.assertEqual(resource_name, body['name'])
        # Update namespace property
        update_property_title = data_utils.rand_name('update-property')
        body = self.namespace_properties_client.update_namespace_properties(
            namespace['namespace'], resource_name,
            title=update_property_title, type="string",
            enum=enum, name=resource_name)
        self.assertEqual(update_property_title, body['title'])
        # Delete namespace property
        self.namespace_properties_client.delete_namespace_property(
            namespace['namespace'], resource_name)
        # List namespace properties and validate deletion
        namespace_property = [
            namespace_property['title'] for namespace_property in
            self.namespace_properties_client.list_namespace_properties(
                namespace['namespace'])['properties']]
        self.assertNotIn(update_property_title, namespace_property)
