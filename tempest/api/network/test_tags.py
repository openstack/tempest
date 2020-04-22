# Copyright 2017 AT&T Corporation.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.api.network import base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class TagsTest(base.BaseNetworkTest):
    """Tests the following operations in the tags API:

        Update all tags.
        Delete all tags.
        Check tag existence.
        Create a tag.
        List tags.
        Remove a tag.

    v2.0 of the Neutron API is assumed. The tag extension allows users to set
    tags on their networks. The extension supports networks only.
    """

    @classmethod
    def skip_checks(cls):
        super(TagsTest, cls).skip_checks()
        if not utils.is_extension_enabled('tag', 'network'):
            msg = "tag extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        super(TagsTest, cls).resource_setup()
        cls.network = cls.create_network()

    @decorators.idempotent_id('ee76bfaf-ac94-4d74-9ecc-4bbd4c583cb1')
    def test_create_list_show_update_delete_tags(self):
        """Validate that creating a tag on a network resource works"""
        tag_name = data_utils.rand_name(self.__class__.__name__ + '-Tag')
        self.tags_client.create_tag('networks', self.network['id'], tag_name)
        self.addCleanup(self.tags_client.delete_all_tags, 'networks',
                        self.network['id'])
        self.tags_client.check_tag_existence('networks', self.network['id'],
                                             tag_name)

        # Validate that listing tags on a network resource works.
        retrieved_tags = self.tags_client.list_tags(
            'networks', self.network['id'])['tags']
        self.assertEqual([tag_name], retrieved_tags)

        # Generate 3 new tag names.
        replace_tags = [data_utils.rand_name(
            self.__class__.__name__ + '-Tag') for _ in range(3)]

        # Replace the current tag with the 3 new tags and validate that the
        # network resource has the 3 new tags.
        updated_tags = self.tags_client.update_all_tags(
            'networks', self.network['id'], replace_tags)['tags']
        self.assertEqual(3, len(updated_tags))
        self.assertEqual(set(replace_tags), set(updated_tags))

        # Delete the first tag and check that it has been removed.
        self.tags_client.delete_tag(
            'networks', self.network['id'], replace_tags[0])
        self.assertRaises(lib_exc.NotFound,
                          self.tags_client.check_tag_existence, 'networks',
                          self.network['id'], replace_tags[0])
        for i in range(1, 3):
            self.tags_client.check_tag_existence(
                'networks', self.network['id'], replace_tags[i])

        # Delete all the remaining tags and check that they have been removed.
        self.tags_client.delete_all_tags('networks', self.network['id'])
        for i in range(1, 3):
            self.assertRaises(lib_exc.NotFound,
                              self.tags_client.check_tag_existence, 'networks',
                              self.network['id'], replace_tags[i])


class TagsExtTest(base.BaseNetworkTest):
    """Tests the following operations in the tags API:

        Update all tags.
        Delete all tags.
        Check tag existence.
        Create a tag.
        List tags.
        Remove a tag.

    v2.0 of the Neutron API is assumed. The tag-ext or standard-attr-tag
    extension allows users to set tags on the following resources: subnets,
    ports, routers and subnetpools.
    from stein release the tag-ext has been renamed to standard-attr-tag
    """

    # NOTE(felipemonteiro): The supported resource names are plural. Use
    # the singular case for the corresponding class resource object.
    SUPPORTED_RESOURCES = ['subnets', 'ports', 'routers', 'subnetpools']

    @classmethod
    def skip_checks(cls):
        super(TagsExtTest, cls).skip_checks()
        # Added condition to support backward compatiblity since
        # tag-ext has been renamed to standard-attr-tag
        if not (utils.is_extension_enabled('tag-ext', 'network') or
                utils.is_extension_enabled('standard-attr-tag', 'network')):
            msg = ("neither tag-ext nor standard-attr-tag extensions "
                   "are enabled.")
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        super(TagsExtTest, cls).resource_setup()
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.port = cls.create_port(cls.network)
        cls.router = cls.create_router()

        subnetpool_name = data_utils.rand_name(cls.__name__ + '-Subnetpool')
        prefix = CONF.network.default_network
        cls.subnetpool = cls.subnetpools_client.create_subnetpool(
            name=subnetpool_name, prefixes=prefix)['subnetpool']
        cls.addClassResourceCleanup(cls.subnetpools_client.delete_subnetpool,
                                    cls.subnetpool['id'])

    def _create_tags_for_each_resource(self):
        # Create a tag for each resource in `SUPPORTED_RESOURCES` and return
        # the list of tag names.
        tag_names = []

        for resource in self.SUPPORTED_RESOURCES:
            tag_name = data_utils.rand_name(self.__class__.__name__ + '-Tag')
            tag_names.append(tag_name)
            resource_object = getattr(self, resource[:-1])

            self.tags_client.create_tag(resource, resource_object['id'],
                                        tag_name)
            self.addCleanup(self.tags_client.delete_all_tags, resource,
                            resource_object['id'])

        return tag_names

    @decorators.idempotent_id('c6231efa-9a89-4adf-b050-2a3156b8a1d9')
    def test_create_check_list_and_delete_tags(self):
        """Test tag operations on subnets/ports/routers/subnetpools"""
        tag_names = self._create_tags_for_each_resource()

        for i, resource in enumerate(self.SUPPORTED_RESOURCES):
            # Ensure that a tag was created for each resource.
            resource_object = getattr(self, resource[:-1])
            retrieved_tags = self.tags_client.list_tags(
                resource, resource_object['id'])['tags']
            self.assertEqual(1, len(retrieved_tags))
            self.assertEqual(tag_names[i], retrieved_tags[0])

            # Check that the expected tag exists for each resource.
            self.tags_client.check_tag_existence(
                resource, resource_object['id'], tag_names[i])

            # Delete the tag and ensure it was deleted.
            self.tags_client.delete_tag(
                resource, resource_object['id'], tag_names[i])
            retrieved_tags = self.tags_client.list_tags(
                resource, resource_object['id'])['tags']
            self.assertEmpty(retrieved_tags)

    @decorators.idempotent_id('663a90f5-f334-4b44-afe0-c5fc1d408791')
    def test_update_and_delete_all_tags(self):
        """Test update/delete all tags on subnets/ports/routers/subnetpools"""
        self._create_tags_for_each_resource()

        for resource in self.SUPPORTED_RESOURCES:
            # Generate 3 new tag names.
            replace_tags = [data_utils.rand_name(
                self.__class__.__name__ + '-Tag') for _ in range(3)]

            # Replace the current tag with the 3 new tags and validate that the
            # current resource has the 3 new tags.
            resource_object = getattr(self, resource[:-1])
            updated_tags = self.tags_client.update_all_tags(
                resource, resource_object['id'], replace_tags)['tags']
            self.assertEqual(3, len(updated_tags))
            self.assertEqual(set(replace_tags), set(updated_tags))

            # Delete all the tags and check that they have been removed.
            self.tags_client.delete_all_tags(resource, resource_object['id'])
            for i in range(3):
                self.assertRaises(
                    lib_exc.NotFound, self.tags_client.check_tag_existence,
                    resource, resource_object['id'], replace_tags[i])
