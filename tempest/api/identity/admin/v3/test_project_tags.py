# Copyright 2018 AT&T Corporation.
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

import testtools

from tempest.api.identity import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class IdentityV3ProjectTagsTest(base.BaseIdentityV3AdminTest):
    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    @decorators.idempotent_id('7c123aac-999d-416a-a0fb-84b915ab10de')
    @testtools.skipUnless(CONF.identity_feature_enabled.project_tags,
                          'Project tags not available.')
    def test_list_update_delete_project_tags(self):
        project = self.setup_test_project()

        # Create a tag for testing.
        tag = data_utils.rand_name('tag')
        # NOTE(felipemonteiro): The response body for create is empty.
        self.project_tags_client.update_project_tag(project['id'], tag)

        # Verify that the tag was created.
        self.project_tags_client.check_project_tag_existence(
            project['id'], tag)

        # Verify that updating the project tags works.
        tags_to_update = [data_utils.rand_name('tag') for _ in range(3)]
        updated_tags = self.project_tags_client.update_all_project_tags(
            project['id'], tags_to_update)['tags']
        self.assertEqual(sorted(tags_to_update), sorted(updated_tags))

        # Verify that listing project tags works.
        retrieved_tags = self.project_tags_client.list_project_tags(
            project['id'])['tags']
        self.assertEqual(sorted(tags_to_update), sorted(retrieved_tags))

        # Verify that deleting a project tag works.
        self.project_tags_client.delete_project_tag(
            project['id'], tags_to_update[0])
        self.assertRaises(lib_exc.NotFound,
                          self.project_tags_client.check_project_tag_existence,
                          project['id'], tags_to_update[0])

        # Verify that deleting all project tags works.
        self.project_tags_client.delete_all_project_tags(project['id'])
        retrieved_tags = self.project_tags_client.list_project_tags(
            project['id'])['tags']
        self.assertEmpty(retrieved_tags)
