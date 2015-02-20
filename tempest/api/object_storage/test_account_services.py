# Copyright 2012 OpenStack Foundation
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

import random

from six import moves
from tempest_lib.common.utils import data_utils
import testtools

from tempest.api.object_storage import base
from tempest import clients
from tempest.common import custom_matchers
from tempest import config
from tempest import test

CONF = config.CONF


class AccountTest(base.BaseObjectTest):

    containers = []

    @classmethod
    def setup_credentials(cls):
        super(AccountTest, cls).setup_credentials()
        cls.os_operator = clients.Manager(
            cls.isolated_creds.get_creds_by_roles(
                roles=[CONF.object_storage.operator_role], force_new=True))

    @classmethod
    def resource_setup(cls):
        super(AccountTest, cls).resource_setup()
        for i in moves.xrange(ord('a'), ord('f') + 1):
            name = data_utils.rand_name(name='%s-' % chr(i))
            cls.container_client.create_container(name)
            cls.containers.append(name)
        cls.containers_count = len(cls.containers)

    @classmethod
    def resource_cleanup(cls):
        cls.delete_containers(cls.containers)
        super(AccountTest, cls).resource_cleanup()

    @test.attr(type='smoke')
    @test.idempotent_id('3499406a-ae53-4f8c-b43a-133d4dc6fe3f')
    def test_list_containers(self):
        # list of all containers should not be empty
        resp, container_list = self.account_client.list_account_containers()
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertIsNotNone(container_list)
        for container_name in self.containers:
            self.assertIn(container_name, container_list)

    @test.attr(type='smoke')
    @test.idempotent_id('884ec421-fbad-4fcc-916b-0580f2699565')
    def test_list_no_containers(self):
        # List request to empty account

        # To test listing no containers, create new user other than
        # the base user of this instance.

        resp, container_list = \
            self.os_operator.account_client.list_account_containers()

        # When sending a request to an account which has not received a PUT
        # container request, the response does not contain 'accept-ranges'
        # header. This is a special case, therefore the existence of response
        # headers is checked without custom matcher.
        self.assertIn('content-length', resp)
        self.assertIn('x-timestamp', resp)
        self.assertIn('x-account-bytes-used', resp)
        self.assertIn('x-account-container-count', resp)
        self.assertIn('x-account-object-count', resp)
        self.assertIn('content-type', resp)
        self.assertIn('x-trans-id', resp)
        self.assertIn('date', resp)

        # Check only the format of common headers with custom matcher
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

        self.assertEqual(len(container_list), 0)

    @test.attr(type='smoke')
    @test.idempotent_id('1c7efa35-e8a2-4b0b-b5ff-862c7fd83704')
    def test_list_containers_with_format_json(self):
        # list containers setting format parameter to 'json'
        params = {'format': 'json'}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertIsNotNone(container_list)
        self.assertTrue([c['name'] for c in container_list])
        self.assertTrue([c['count'] for c in container_list])
        self.assertTrue([c['bytes'] for c in container_list])

    @test.attr(type='smoke')
    @test.idempotent_id('4477b609-1ca6-4d4b-b25d-ad3f01086089')
    def test_list_containers_with_format_xml(self):
        # list containers setting format parameter to 'xml'
        params = {'format': 'xml'}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertIsNotNone(container_list)
        self.assertEqual(container_list.tag, 'account')
        self.assertTrue('name' in container_list.keys())
        self.assertEqual(container_list.find(".//container").tag, 'container')
        self.assertEqual(container_list.find(".//name").tag, 'name')
        self.assertEqual(container_list.find(".//count").tag, 'count')
        self.assertEqual(container_list.find(".//bytes").tag, 'bytes')

    @test.attr(type='smoke')
    @test.idempotent_id('6eb04a6a-4860-4e31-ba91-ea3347d76b58')
    @testtools.skipIf(
        not CONF.object_storage_feature_enabled.discoverability,
        'Discoverability function is disabled')
    def test_list_extensions(self):
        resp, extensions = self.account_client.list_extensions()

        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

    @test.attr(type='smoke')
    @test.idempotent_id('5cfa4ab2-4373-48dd-a41f-a532b12b08b2')
    def test_list_containers_with_limit(self):
        # list containers one of them, half of them then all of them
        for limit in (1, self.containers_count / 2, self.containers_count):
            params = {'limit': limit}
            resp, container_list = \
                self.account_client.list_account_containers(params=params)
            self.assertHeaders(resp, 'Account', 'GET')

            self.assertEqual(len(container_list), limit)

    @test.attr(type='smoke')
    @test.idempotent_id('638f876d-6a43-482a-bbb3-0840bca101c6')
    def test_list_containers_with_marker(self):
        # list containers using marker param
        # first expect to get 0 container as we specified last
        # the container as marker
        # second expect to get the bottom half of the containers
        params = {'marker': self.containers[-1]}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertEqual(len(container_list), 0)

        params = {'marker': self.containers[self.containers_count / 2]}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertEqual(len(container_list), self.containers_count / 2 - 1)

    @test.attr(type='smoke')
    @test.idempotent_id('5ca164e4-7bde-43fa-bafb-913b53b9e786')
    def test_list_containers_with_end_marker(self):
        # list containers using end_marker param
        # first expect to get 0 container as we specified first container as
        # end_marker
        # second expect to get the top half of the containers
        params = {'end_marker': self.containers[0]}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list), 0)

        params = {'end_marker': self.containers[self.containers_count / 2]}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list), self.containers_count / 2)

    @test.attr(type='smoke')
    @test.idempotent_id('ac8502c2-d4e4-4f68-85a6-40befea2ef5e')
    def test_list_containers_with_marker_and_end_marker(self):
        # list containers combining marker and end_marker param
        params = {'marker': self.containers[0],
                  'end_marker': self.containers[self.containers_count - 1]}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list), self.containers_count - 2)

    @test.attr(type='smoke')
    @test.idempotent_id('f7064ae8-dbcc-48da-b594-82feef6ea5af')
    def test_list_containers_with_limit_and_marker(self):
        # list containers combining marker and limit param
        # result are always limitated by the limit whatever the marker
        for marker in random.choice(self.containers):
            limit = random.randint(0, self.containers_count - 1)
            params = {'marker': marker,
                      'limit': limit}
            resp, container_list = \
                self.account_client.list_account_containers(params=params)
            self.assertHeaders(resp, 'Account', 'GET')

            self.assertTrue(len(container_list) <= limit, str(container_list))

    @test.attr(type='smoke')
    @test.idempotent_id('888a3f0e-7214-4806-8e50-5e0c9a69bb5e')
    def test_list_containers_with_limit_and_end_marker(self):
        # list containers combining limit and end_marker param
        limit = random.randint(1, self.containers_count)
        params = {'limit': limit,
                  'end_marker': self.containers[self.containers_count / 2]}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list),
                         min(limit, self.containers_count / 2))

    @test.attr(type='smoke')
    @test.idempotent_id('8cf98d9c-e3a0-4e44-971b-c87656fdddbd')
    def test_list_containers_with_limit_and_marker_and_end_marker(self):
        # list containers combining limit, marker and end_marker param
        limit = random.randint(1, self.containers_count)
        params = {'limit': limit,
                  'marker': self.containers[0],
                  'end_marker': self.containers[self.containers_count - 1]}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list),
                         min(limit, self.containers_count - 2))

    @test.attr(type='smoke')
    @test.idempotent_id('4894c312-6056-4587-8d6f-86ffbf861f80')
    def test_list_account_metadata(self):
        # list all account metadata

        # set metadata to account
        metadata = {'test-account-meta1': 'Meta1',
                    'test-account-meta2': 'Meta2'}
        resp, _ = self.account_client.create_account_metadata(metadata)

        resp, _ = self.account_client.list_account_metadata()
        self.assertHeaders(resp, 'Account', 'HEAD')
        self.assertIn('x-account-meta-test-account-meta1', resp)
        self.assertIn('x-account-meta-test-account-meta2', resp)
        self.account_client.delete_account_metadata(metadata)

    @test.attr(type='smoke')
    @test.idempotent_id('b904c2e3-24c2-4dba-ad7d-04e90a761be5')
    def test_list_no_account_metadata(self):
        # list no account metadata
        resp, _ = self.account_client.list_account_metadata()
        self.assertHeaders(resp, 'Account', 'HEAD')
        self.assertNotIn('x-account-meta-', str(resp))

    @test.attr(type='smoke')
    @test.idempotent_id('e2a08b5f-3115-4768-a3ee-d4287acd6c08')
    def test_update_account_metadata_with_create_metadata(self):
        # add metadata to account
        metadata = {'test-account-meta1': 'Meta1'}
        resp, _ = self.account_client.create_account_metadata(metadata)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, body = self.account_client.list_account_metadata()
        self.assertIn('x-account-meta-test-account-meta1', resp)
        self.assertEqual(resp['x-account-meta-test-account-meta1'],
                         metadata['test-account-meta1'])

        self.account_client.delete_account_metadata(metadata)

    @test.attr(type='smoke')
    @test.idempotent_id('9f60348d-c46f-4465-ae06-d51dbd470953')
    def test_update_account_metadata_with_delete_matadata(self):
        # delete metadata from account
        metadata = {'test-account-meta1': 'Meta1'}
        self.account_client.create_account_metadata(metadata)
        resp, _ = self.account_client.delete_account_metadata(metadata)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('64fd53f3-adbd-4639-af54-436e4982dbfb')
    def test_update_account_metadata_with_create_matadata_key(self):
        # if the value of metadata is not set, the metadata is not
        # registered at a server
        metadata = {'test-account-meta1': ''}
        resp, _ = self.account_client.create_account_metadata(metadata)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('d4d884d3-4696-4b85-bc98-4f57c4dd2bf1')
    def test_update_account_metadata_with_delete_matadata_key(self):
        # Although the value of metadata is not set, the feature of
        # deleting metadata is valid
        metadata_1 = {'test-account-meta1': 'Meta1'}
        self.account_client.create_account_metadata(metadata_1)
        metadata_2 = {'test-account-meta1': ''}
        resp, _ = self.account_client.delete_account_metadata(metadata_2)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('8e5fc073-59b9-42ee-984a-29ed11b2c749')
    def test_update_account_metadata_with_create_and_delete_metadata(self):
        # Send a request adding and deleting metadata requests simultaneously
        metadata_1 = {'test-account-meta1': 'Meta1'}
        self.account_client.create_account_metadata(metadata_1)
        metadata_2 = {'test-account-meta2': 'Meta2'}
        resp, body = self.account_client.create_and_delete_account_metadata(
            metadata_2,
            metadata_1)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)
        self.assertIn('x-account-meta-test-account-meta2', resp)
        self.assertEqual(resp['x-account-meta-test-account-meta2'],
                         metadata_2['test-account-meta2'])

        self.account_client.delete_account_metadata(metadata_2)
