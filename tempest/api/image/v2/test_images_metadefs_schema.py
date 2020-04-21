# Copyright 2016 EasyStack.
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

from tempest.api.image import base
from tempest.lib import decorators


class MetadataSchemaTest(base.BaseV2ImageTest):
    """Test to get image metadata schema"""

    @decorators.idempotent_id('e9e44891-3cb8-3b40-a532-e0a39fea3dab')
    def test_get_metadata_namespace_schema(self):
        """Test to get image namespace schema"""
        body = self.schemas_client.show_schema("metadefs/namespace")
        self.assertEqual("namespace", body['name'])

    @decorators.idempotent_id('ffe44891-678b-3ba0-a3e2-e0a3967b3aeb')
    def test_get_metadata_namespaces_schema(self):
        """Test to get image namespaces schema"""
        body = self.schemas_client.show_schema("metadefs/namespaces")
        self.assertEqual("namespaces", body['name'])

    @decorators.idempotent_id('fde34891-678b-3b40-ae32-e0a3e67b6beb')
    def test_get_metadata_resource_type_schema(self):
        """Test to get image resource_type schema"""
        body = self.schemas_client.show_schema("metadefs/resource_type")
        self.assertEqual("resource_type_association", body['name'])

    @decorators.idempotent_id('dfe4a891-b38b-3bf0-a3b2-e03ee67b3a3a')
    def test_get_metadata_resources_types_schema(self):
        """Test to get image resource_types schema"""
        body = self.schemas_client.show_schema("metadefs/resource_types")
        self.assertEqual("resource_type_associations", body['name'])

    @decorators.idempotent_id('dff4a891-b38b-3bf0-a3b2-e03ee67b3a3b')
    def test_get_metadata_object_schema(self):
        """Test to get image object schema"""
        body = self.schemas_client.show_schema("metadefs/object")
        self.assertEqual("object", body['name'])

    @decorators.idempotent_id('dee4a891-b38b-3bf0-a3b2-e03ee67b3a3c')
    def test_get_metadata_objects_schema(self):
        """Test to get image objects schema"""
        body = self.schemas_client.show_schema("metadefs/objects")
        self.assertEqual("objects", body['name'])

    @decorators.idempotent_id('dae4a891-b38b-3bf0-a3b2-e03ee67b3a3d')
    def test_get_metadata_property_schema(self):
        """Test to get image property schema"""
        body = self.schemas_client.show_schema("metadefs/property")
        self.assertEqual("property", body['name'])

    @decorators.idempotent_id('dce4a891-b38b-3bf0-a3b2-e03ee67b3a3e')
    def test_get_metadata_properties_schema(self):
        """Test to get image properties schema"""
        body = self.schemas_client.show_schema("metadefs/properties")
        self.assertEqual("properties", body['name'])

    @decorators.idempotent_id('dde4a891-b38b-3bf0-a3b2-e03ee67b3a3e')
    def test_get_metadata_tag_schema(self):
        """Test to get image tag schema"""
        body = self.schemas_client.show_schema("metadefs/tag")
        self.assertEqual("tag", body['name'])

    @decorators.idempotent_id('cde4a891-b38b-3bf0-a3b2-e03ee67b3a3a')
    def test_get_metadata_tags_schema(self):
        """Test to get image tags schema"""
        body = self.schemas_client.show_schema("metadefs/tags")
        self.assertEqual("tags", body['name'])
