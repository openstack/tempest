# Copyright 2017 AT&T Corp.
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

import six

from tempest.api.compute import base
from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class ServerTagsTestJSON(base.BaseV2ComputeTest):
    """Test server tags with compute microversion greater than 2.25"""

    min_microversion = '2.26'
    max_microversion = 'latest'

    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(ServerTagsTestJSON, cls).skip_checks()
        if not utils.is_extension_enabled('os-server-tags', 'compute'):
            msg = "os-server-tags extension is not enabled."
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(ServerTagsTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServerTagsTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until='ACTIVE')

    def _update_server_tags(self, server_id, tags):
        if not isinstance(tags, (list, tuple)):
            tags = [tags]
        for tag in tags:
            self.client.update_tag(server_id, tag)
        self.addCleanup(self.client.delete_all_tags, server_id)

    @decorators.idempotent_id('8d95abe2-c658-4c42-9a44-c0258500306b')
    def test_create_delete_tag(self):
        """Test creating and deleting server tag"""
        # Check that no tags exist.
        fetched_tags = self.client.list_tags(self.server['id'])['tags']
        self.assertEmpty(fetched_tags)

        # Add server tag to the server.
        assigned_tag = data_utils.rand_name('tag')
        self._update_server_tags(self.server['id'], assigned_tag)

        # Check that added tag exists.
        fetched_tags = self.client.list_tags(self.server['id'])['tags']
        self.assertEqual([assigned_tag], fetched_tags)

        # Remove assigned tag from server and check that it was removed.
        self.client.delete_tag(self.server['id'], assigned_tag)
        fetched_tags = self.client.list_tags(self.server['id'])['tags']
        self.assertEmpty(fetched_tags)

    @decorators.idempotent_id('a2c1af8c-127d-417d-974b-8115f7e3d831')
    def test_update_all_tags(self):
        """Test updating all server tags"""
        # Add server tags to the server.
        tags = [data_utils.rand_name('tag'), data_utils.rand_name('tag')]
        self._update_server_tags(self.server['id'], tags)

        # Replace tags with new tags and check that they are present.
        new_tags = [data_utils.rand_name('tag'), data_utils.rand_name('tag')]
        replaced_tags = self.client.update_all_tags(
            self.server['id'], new_tags)['tags']
        six.assertCountEqual(self, new_tags, replaced_tags)

        # List the tags and check that the tags were replaced.
        fetched_tags = self.client.list_tags(self.server['id'])['tags']
        six.assertCountEqual(self, new_tags, fetched_tags)

    @decorators.idempotent_id('a63b2a74-e918-4b7c-bcab-10c855f3a57e')
    def test_delete_all_tags(self):
        """Test deleting all server tags"""
        # Add server tags to the server.
        assigned_tags = [data_utils.rand_name('tag'),
                         data_utils.rand_name('tag')]
        self._update_server_tags(self.server['id'], assigned_tags)

        # Delete tags from the server and check that they were deleted.
        self.client.delete_all_tags(self.server['id'])
        fetched_tags = self.client.list_tags(self.server['id'])['tags']
        self.assertEmpty(fetched_tags)

    @decorators.idempotent_id('81279a66-61c3-4759-b830-a2dbe64cbe08')
    def test_check_tag_existence(self):
        """Test checking server tag existence"""
        # Add server tag to the server.
        assigned_tag = data_utils.rand_name('tag')
        self._update_server_tags(self.server['id'], assigned_tag)

        # Check that added tag exists. Throws a 404 if not found, else a 204,
        # which was already checked by the schema validation.
        self.client.check_tag_existence(self.server['id'], assigned_tag)
