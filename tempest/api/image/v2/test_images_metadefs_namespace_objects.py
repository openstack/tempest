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
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators


class MetadataNamespaceObjectsTest(base.BaseV2ImageTest):
    """Test the Metadata definition namespace objects basic functionality"""

    def _create_namespace_object(self, namespace):
        object_name = data_utils.rand_name(self.__class__.__name__ + '-object')
        namespace_object = self.namespace_objects_client.\
            create_namespace_object(namespace['namespace'], name=object_name)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.namespace_objects_client.delete_namespace_object,
                        namespace['namespace'], object_name)
        return namespace_object

    @decorators.idempotent_id('b1a3775e-3b5c-4f6a-a3b4-1ba3574ae718')
    def test_create_update_delete_meta_namespace_objects(self):
        # Create a namespace
        namespace = self.create_namespace()
        # Create a namespace object
        body = self._create_namespace_object(namespace)
        # Update a namespace object
        up_object_name = data_utils.rand_name('update-object')
        body = self.namespace_objects_client.update_namespace_object(
            namespace['namespace'], body['name'],
            name=up_object_name)
        self.assertEqual(up_object_name, body['name'])
        # Delete a namespace object
        self.namespace_objects_client.delete_namespace_object(
            namespace['namespace'], up_object_name)
        # List namespace objects and validate deletion
        namespace_objects = [
            namespace_object['name'] for namespace_object in
            self.namespace_objects_client.list_namespace_objects(
                namespace['namespace'])['objects']]
        self.assertNotIn(up_object_name, namespace_objects)

    @decorators.idempotent_id('a2a3615e-3b5c-3f6a-a2b1-1ba3574ae738')
    def test_list_meta_namespace_objects(self):
        # Create a namespace object
        namespace = self.create_namespace()
        meta_namespace_object = self._create_namespace_object(namespace)
        # List namespace objects
        namespace_objects = [
            namespace_object['name'] for namespace_object in
            self.namespace_objects_client.list_namespace_objects(
                namespace['namespace'])['objects']]
        self.assertIn(meta_namespace_object['name'], namespace_objects)

    @decorators.idempotent_id('b1a3674e-3b4c-3f6a-a3b4-1ba3573ca768')
    def test_show_meta_namespace_objects(self):
        # Create a namespace object
        namespace = self.create_namespace()
        namespace_object = self._create_namespace_object(namespace)
        # Show a namespace object
        body = self.namespace_objects_client.show_namespace_object(
            namespace['namespace'], namespace_object['name'])
        self.assertEqual(namespace_object['name'], body['name'])
