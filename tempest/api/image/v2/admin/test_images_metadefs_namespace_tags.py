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


class MetadataNamespaceTagsTest(base.BaseV2ImageAdminTest):
    """Test the Metadata definition namespace tags basic functionality"""

    tags = [
        {
            "name": "sample-tag1"
        },
        {
            "name": "sample-tag2"
        },
        {
            "name": "sample-tag3"
        }
    ]
    tag_list = ["sample-tag1", "sample-tag2", "sample-tag3"]

    def _create_namespace_tags(self, namespace):
        # Create a namespace
        namespace_tags = self.namespace_tags_client.create_namespace_tags(
            namespace['namespace'], tags=self.tags)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.namespace_tags_client.delete_namespace_tags,
                        namespace['namespace'])
        return namespace_tags

    @decorators.idempotent_id('a2a3765e-3a6d-4f6d-a3a7-3cc3476aa876')
    def test_create_list_delete_namespace_tags(self):
        """Test creating/listing/deleting image metadata namespace tags"""
        # Create a namespace
        namespace = self.create_namespace()
        self._create_namespace_tags(namespace)
        # List namespace tags
        body = self.namespace_tags_client.list_namespace_tags(
            namespace['namespace'])
        self.assertEqual(3, len(body['tags']))
        self.assertIn(body['tags'][0]['name'], self.tag_list)
        self.assertIn(body['tags'][1]['name'], self.tag_list)
        self.assertIn(body['tags'][2]['name'], self.tag_list)
        # Delete all tag definitions
        self.namespace_tags_client.delete_namespace_tags(
            namespace['namespace'])
        body = self.namespace_tags_client.list_namespace_tags(
            namespace['namespace'])
        self.assertEmpty(body['tags'])

    @decorators.idempotent_id('a2a3765e-1a2c-3f6d-a3a7-3cc3466ab875')
    def test_create_update_delete_tag(self):
        """Test creating/updating/deleting image metadata namespace tag"""
        # Create a namespace
        namespace = self.create_namespace()
        self._create_namespace_tags(namespace)
        # Create a tag
        tag_name = data_utils.rand_name('tag_name')
        self.namespace_tags_client.create_namespace_tag(
            namespace=namespace['namespace'], tag_name=tag_name)

        body = self.namespace_tags_client.show_namespace_tag(
            namespace['namespace'], tag_name)
        self.assertEqual(tag_name, body['name'])
        # Update tag definition
        update_tag_definition = data_utils.rand_name('update-tag')
        body = self.namespace_tags_client.update_namespace_tag(
            namespace['namespace'], tag_name=tag_name,
            name=update_tag_definition)
        self.assertEqual(update_tag_definition, body['name'])
        # Delete tag definition
        self.namespace_tags_client.delete_namespace_tag(
            namespace['namespace'], update_tag_definition)
        # List namespace tags and validate deletion
        namespace_tags = [
            namespace_tag['name'] for namespace_tag in
            self.namespace_tags_client.list_namespace_tags(
                namespace['namespace'])['tags']]
        self.assertNotIn(update_tag_definition, namespace_tags)
