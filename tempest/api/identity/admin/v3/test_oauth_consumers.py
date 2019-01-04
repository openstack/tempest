# Copyright 2017 AT&T Corporation.
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

from tempest.api.identity import base
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions


class OAUTHConsumersV3Test(base.BaseIdentityV3AdminTest):
    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    def _create_consumer(self):
        """Creates a consumer with a random description."""
        description = data_utils.rand_name('test_create_consumer')
        consumer = self.oauth_consumers_client.create_consumer(
            description)['consumer']
        # cleans up created consumers after tests
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.oauth_consumers_client.delete_consumer,
                        consumer['id'])
        return consumer

    @decorators.idempotent_id('c8307ea6-a86c-47fd-ae7b-5b3b2caca76d')
    def test_create_and_show_consumer(self):
        """Tests to make sure that a consumer with parameters is made"""
        consumer = self._create_consumer()
        # fetch created consumer from client
        fetched_consumer = self.oauth_consumers_client.show_consumer(
            consumer['id'])['consumer']
        # assert that the fetched consumer matches the created one and
        # has all parameters
        for key in ['description', 'id', 'links']:
            self.assertEqual(consumer[key], fetched_consumer[key])

    @decorators.idempotent_id('fdfa1b7f-2a31-4354-b2c7-f6ae20554f93')
    def test_delete_consumer(self):
        """Tests the delete function."""
        consumer = self._create_consumer()
        # fetch consumer from client to confirm it exists
        fetched_consumer = self.oauth_consumers_client.show_consumer(
            consumer['id'])['consumer']
        self.assertEqual(consumer['id'], fetched_consumer['id'])
        # delete existing consumer
        self.oauth_consumers_client.delete_consumer(consumer['id'])
        # check that consumer no longer exists
        self.assertRaises(exceptions.NotFound,
                          self.oauth_consumers_client.show_consumer,
                          consumer['id'])

    @decorators.idempotent_id('080a9b1a-c009-47c0-9979-5305bf72e3dc')
    def test_update_consumer(self):
        """Tests the update functionality"""
        # create a new consumer to update
        consumer = self._create_consumer()
        # create new description
        new_description = data_utils.rand_name('test_update_consumer')
        # update consumer
        self.oauth_consumers_client.update_consumer(consumer['id'],
                                                    new_description)
        # check that the same consumer now has the new description
        updated_consumer = self.oauth_consumers_client.show_consumer(
            consumer['id'])['consumer']
        self.assertEqual(new_description, updated_consumer['description'])

    @decorators.idempotent_id('09ca50de-78f2-4ffb-ac71-f2254036b2b8')
    def test_list_consumers(self):
        """Test for listing consumers"""
        # create two consumers to populate list
        new_consumer_one = self._create_consumer()
        new_consumer_two = self._create_consumer()
        # fetch the list of consumers
        consumer_list = self.oauth_consumers_client \
                            .list_consumers()['consumers']
        # add fetched consumer ids to a list
        id_list = [consumer['id'] for consumer in consumer_list]
        # check if created consumers are in the list
        self.assertIn(new_consumer_one['id'], id_list)
        self.assertIn(new_consumer_two['id'], id_list)
