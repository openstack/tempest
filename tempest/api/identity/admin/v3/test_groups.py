# Copyright 2013 IBM Corp.
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

CONF = config.CONF


class GroupsV3TestJSON(base.BaseIdentityV3AdminTest):
    """Test keystone groups"""

    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    @classmethod
    def resource_setup(cls):
        super(GroupsV3TestJSON, cls).resource_setup()
        cls.domain = cls.create_domain()

    @decorators.idempotent_id('2e80343b-6c81-4ac3-88c7-452f3e9d5129')
    def test_group_create_update_get(self):
        """Test creating, updating and getting keystone group"""
        # Verify group creation works.
        name = data_utils.rand_name('Group')
        description = data_utils.rand_name('Description')
        group = self.setup_test_group(name=name, domain_id=self.domain['id'],
                                      description=description)
        self.assertEqual(group['name'], name)
        self.assertEqual(group['description'], description)
        self.assertEqual(self.domain['id'], group['domain_id'])

        # Verify updating name and description works.
        first_name_update = data_utils.rand_name('UpdateGroup')
        first_desc_update = data_utils.rand_name('UpdateDescription')
        updated_group = self.groups_client.update_group(
            group['id'], name=first_name_update,
            description=first_desc_update)['group']
        self.assertEqual(updated_group['name'], first_name_update)
        self.assertEqual(updated_group['description'], first_desc_update)

        # Verify that the updated values are reflected after performing show.
        new_group = self.groups_client.show_group(group['id'])['group']
        self.assertEqual(group['id'], new_group['id'])
        self.assertEqual(first_name_update, new_group['name'])
        self.assertEqual(first_desc_update, new_group['description'])

        # Verify that updating a single field for a group (name) leaves the
        # other fields (description, domain_id) unchanged.
        second_name_update = data_utils.rand_name(
            self.__class__.__name__ + 'UpdateGroup')
        updated_group = self.groups_client.update_group(
            group['id'], name=second_name_update)['group']
        self.assertEqual(second_name_update, updated_group['name'])
        # Verify that 'description' and 'domain_id' were not updated or
        # deleted.
        self.assertEqual(first_desc_update, updated_group['description'])
        self.assertEqual(self.domain['id'], updated_group['domain_id'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('1598521a-2f36-4606-8df9-30772bd51339')
    @testtools.skipIf(CONF.identity_feature_enabled.immutable_user_source,
                      'Skipped because environment has an '
                      'immutable user source and solely '
                      'provides read-only access to users.')
    def test_group_users_add_list_delete(self):
        """Test adding/listing/deleting group users"""
        group = self.setup_test_group(domain_id=self.domain['id'])
        # add user into group
        users = []
        for _ in range(3):
            user = self.create_test_user()
            users.append(user)
            self.groups_client.add_group_user(group['id'], user['id'])

        # list users in group
        group_users = self.groups_client.list_group_users(group['id'])['users']
        self.assertEqual(sorted(users, key=lambda k: k['name']),
                         sorted(group_users, key=lambda k: k['name']))
        # check and delete user in group
        for user in users:
            self.groups_client.check_group_user_existence(
                group['id'], user['id'])
            self.groups_client.delete_group_user(group['id'], user['id'])
        group_users = self.groups_client.list_group_users(group['id'])['users']
        self.assertEqual(len(group_users), 0)

    @decorators.idempotent_id('64573281-d26a-4a52-b899-503cb0f4e4ec')
    @testtools.skipIf(CONF.identity_feature_enabled.immutable_user_source,
                      'Skipped because environment has an '
                      'immutable user source and solely '
                      'provides read-only access to users.')
    def test_list_user_groups(self):
        """Test listing user groups when the user is in two groups"""
        # create a user
        user = self.create_test_user()
        # create two groups, and add user into them
        groups = []
        for _ in range(2):
            group = self.setup_test_group(domain_id=self.domain['id'])
            groups.append(group)
            self.groups_client.add_group_user(group['id'], user['id'])
        # list groups which user belongs to
        user_groups = self.users_client.list_user_groups(user['id'])['groups']
        # The `membership_expires_at` attribute is present when listing user
        # group memberships, and is not an attribute of the groups themselves.
        # Therefore we remove it from the comparison.
        for g in user_groups:
            if 'membership_expires_at' in g:
                self.assertIsNone(g['membership_expires_at'])
                del(g['membership_expires_at'])
        self.assertEqual(sorted(groups, key=lambda k: k['name']),
                         sorted(user_groups, key=lambda k: k['name']))
        self.assertEqual(2, len(user_groups))

    @decorators.idempotent_id('cc9a57a5-a9ed-4f2d-a29f-4f979a06ec71')
    def test_list_groups(self):
        """Test listing groups"""
        group_ids = list()
        fetched_ids = list()
        for _ in range(3):
            group = self.setup_test_group(domain_id=self.domain['id'])
            group_ids.append(group['id'])
        # List and Verify Groups
        # When domain specific drivers are enabled the operations
        # of listing all users and listing all groups are not supported,
        # they need a domain filter to be specified
        if CONF.identity_feature_enabled.domain_specific_drivers:
            body = self.groups_client.list_groups(
                domain_id=self.domain['id'])['groups']
        else:
            body = self.groups_client.list_groups()['groups']
        for g in body:
            fetched_ids.append(g['id'])
        missing_groups = [g for g in group_ids if g not in fetched_ids]
        self.assertEmpty(missing_groups)
