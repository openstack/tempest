# Copyright 2016 Ericsson India Global Services Private Limited
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


class MetadataResourceTypesTest(base.BaseV2ImageTest):
    """Test the Metadata definition resource types basic functionality"""

    @decorators.idempotent_id('6f358a4e-5ef0-11e6-a795-080027d0d606')
    def test_basic_meta_def_resource_type_association(self):
        """Test image resource type associations"""
        # Get the available resource types and use one resource_type
        body = self.resource_types_client.list_resource_types()
        resource_name = body['resource_types'][0]['name']
        # Create a namespace
        namespace = self.create_namespace()
        # Create resource type association
        body = self.resource_types_client.create_resource_type_association(
            namespace['namespace'], name=resource_name)
        self.assertEqual(body['name'], resource_name)
        # NOTE(raiesmh08): Here intentionally I have not added addcleanup
        # method for resource type dissociation because its a metadata add and
        # being cleaned as soon as namespace is cleaned at test case level.
        # When namespace cleans, resource type association will automatically
        # clean without any error or dependency.

        # List resource type associations and validate creation
        rs_type_associations = [
            rs_type_association['name'] for rs_type_association in
            self.resource_types_client.list_resource_type_association(
                namespace['namespace'])['resource_type_associations']]
        self.assertIn(resource_name, rs_type_associations)
        # Delete resource type association
        self.resource_types_client.delete_resource_type_association(
            namespace['namespace'], resource_name)
        # List resource type associations and validate deletion
        rs_type_associations = [
            rs_type_association['name'] for rs_type_association in
            self.resource_types_client.list_resource_type_association(
                namespace['namespace'])['resource_type_associations']]
        self.assertNotIn(resource_name, rs_type_associations)
