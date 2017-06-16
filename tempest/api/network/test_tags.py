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
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest import test


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
        if not test.is_extension_enabled('tag', 'network'):
            msg = "tag extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        super(TagsTest, cls).resource_setup()
        cls.network = cls.create_network()

    @decorators.idempotent_id('ee76bfaf-ac94-4d74-9ecc-4bbd4c583cb1')
    def test_create_list_show_update_delete_tags(self):
        # Validate that creating a tag on a network resource works.
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
