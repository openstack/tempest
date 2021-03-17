# Copyright 2015 Red Hat, Inc.
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
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class MetadataNamespacesTest(base.BaseV2ImageAdminTest):
    """Test the Metadata definition Namespaces basic functionality"""

    @decorators.idempotent_id('319b765e-7f3d-4b3d-8b37-3ca3876ee768')
    def test_basic_metadata_definition_namespaces(self):
        """Test operations of image metadata definition namespaces"""
        # get the available resource types and use one resource_type
        body = self.resource_types_client.list_resource_types()
        resource_name = body['resource_types'][0]['name']
        name = [{'name': resource_name}]
        namespace_name = data_utils.rand_name('namespace')
        # create the metadef namespace
        body = self.namespaces_client.create_namespace(
            namespace=namespace_name,
            visibility='public',
            description='Tempest',
            display_name=namespace_name,
            resource_type_associations=name,
            protected=True)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self._cleanup_namespace, namespace_name)
        # list namespaces
        bodys = self.namespaces_client.list_namespaces()['namespaces']
        body = [namespace['namespace'] for namespace in bodys]
        self.assertIn(namespace_name, body)
        # get namespace details
        body = self.namespaces_client.show_namespace(namespace_name)
        self.assertEqual(namespace_name, body['namespace'])
        self.assertEqual('public', body['visibility'])
        # unable to delete protected namespace
        self.assertRaises(lib_exc.Forbidden,
                          self.namespaces_client.delete_namespace,
                          namespace_name)
        # update the visibility to private and protected to False
        body = self.namespaces_client.update_namespace(
            namespace=namespace_name,
            description='Tempest',
            visibility='private',
            display_name=namespace_name,
            protected=False)
        self.assertEqual('private', body['visibility'])
        self.assertEqual(False, body['protected'])
        # now able to delete the non-protected namespace
        self.namespaces_client.delete_namespace(namespace_name)

    def _cleanup_namespace(self, namespace_name):
        body = self.namespaces_client.show_namespace(namespace_name)
        self.assertEqual(namespace_name, body['namespace'])
        body = self.namespaces_client.update_namespace(
            namespace=namespace_name,
            description='Tempest',
            visibility='private',
            display_name=namespace_name,
            protected=False)
        self.namespaces_client.delete_namespace(namespace_name)
