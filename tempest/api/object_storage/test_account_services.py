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

import six
import testtools

from tempest.api.object_storage import base
from tempest.common import custom_matchers
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class AccountTest(base.BaseObjectTest):

    credentials = [['operator', CONF.object_storage.operator_role],
                   ['operator_alt', CONF.object_storage.operator_role]]
    containers = []

    @classmethod
    def setup_credentials(cls):
        super(AccountTest, cls).setup_credentials()
        cls.os_operator = cls.os_roles_operator_alt

    @classmethod
    def resource_setup(cls):
        super(AccountTest, cls).resource_setup()
        for i in range(ord('a'), ord('f') + 1):
            name = data_utils.rand_name(name='%s-' % six.int2byte(i))
            cls.container_client.update_container(name)
            cls.addClassResourceCleanup(base.delete_containers,
                                        [name],
                                        cls.container_client,
                                        cls.object_client)
            cls.containers.append(name)
        cls.containers_count = len(cls.containers)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('3499406a-ae53-4f8c-b43a-133d4dc6fe3f')
    def test_list_containers(self):
        # list of all containers should not be empty
        resp, container_list = self.account_client.list_account_containers()
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertIsNotNone(container_list)

        for container_name in self.containers:
            self.assertIn(six.text_type(container_name).encode('utf-8'),
                          container_list)

    @decorators.idempotent_id('884ec421-fbad-4fcc-916b-0580f2699565')
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
        #
        # As the expected response is 204 No Content, Content-Length presence
        # is not checked here intentionally. According to RFC 7230 a server
        # MUST NOT send the header in such responses. Thus, clients should not
        # depend on this header. However, the standard does not require them
        # to validate the server's behavior. We leverage that to not refuse
        # any implementation violating it like Swift [1] or some versions of
        # Ceph RadosGW [2].
        # [1] https://bugs.launchpad.net/swift/+bug/1537811
        # [2] http://tracker.ceph.com/issues/13582
        self.assertIn('x-timestamp', resp)
        self.assertIn('x-account-bytes-used', resp)
        self.assertIn('x-account-container-count', resp)
        self.assertIn('x-account-object-count', resp)
        self.assertIn('content-type', resp)
        self.assertIn('x-trans-id', resp)
        self.assertIn('date', resp)

        # Check only the format of common headers with custom matcher
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

        self.assertEmpty(container_list)

    @decorators.idempotent_id('1c7efa35-e8a2-4b0b-b5ff-862c7fd83704')
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

    @decorators.idempotent_id('4477b609-1ca6-4d4b-b25d-ad3f01086089')
    def test_list_containers_with_format_xml(self):
        # list containers setting format parameter to 'xml'
        params = {'format': 'xml'}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertIsNotNone(container_list)
        self.assertEqual(container_list.tag, 'account')
        self.assertIn('name', container_list.keys())
        self.assertEqual(container_list.find(".//container").tag, 'container')
        self.assertEqual(container_list.find(".//name").tag, 'name')
        self.assertEqual(container_list.find(".//count").tag, 'count')
        self.assertEqual(container_list.find(".//bytes").tag, 'bytes')

    @decorators.idempotent_id('6eb04a6a-4860-4e31-ba91-ea3347d76b58')
    @testtools.skipIf(
        not CONF.object_storage_feature_enabled.discoverability,
        'Discoverability function is disabled')
    def test_list_extensions(self):
        resp = self.capabilities_client.list_capabilities()

        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

    @decorators.idempotent_id('5cfa4ab2-4373-48dd-a41f-a532b12b08b2')
    def test_list_containers_with_limit(self):
        # list containers one of them, half of them then all of them
        for limit in (1, self.containers_count // 2,
                      self.containers_count):
            params = {'limit': limit}
            resp, container_list = \
                self.account_client.list_account_containers(params=params)
            self.assertHeaders(resp, 'Account', 'GET')

            self.assertEqual(len(container_list), limit)

    @decorators.idempotent_id('638f876d-6a43-482a-bbb3-0840bca101c6')
    def test_list_containers_with_marker(self):
        # list containers using marker param
        # first expect to get 0 container as we specified last
        # the container as marker
        # second expect to get the bottom half of the containers
        params = {'marker': self.containers[-1]}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertEmpty(container_list)

        params = {'marker': self.containers[self.containers_count // 2]}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertEqual(len(container_list),
                         self.containers_count // 2 - 1)

    @decorators.idempotent_id('5ca164e4-7bde-43fa-bafb-913b53b9e786')
    def test_list_containers_with_end_marker(self):
        # list containers using end_marker param
        # first expect to get 0 container as we specified first container as
        # end_marker
        # second expect to get the top half of the containers
        params = {'end_marker': self.containers[0]}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEmpty(container_list)

        params = {'end_marker': self.containers[self.containers_count // 2]}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list), self.containers_count // 2)

    @decorators.idempotent_id('ac8502c2-d4e4-4f68-85a6-40befea2ef5e')
    def test_list_containers_with_marker_and_end_marker(self):
        # list containers combining marker and end_marker param
        params = {'marker': self.containers[0],
                  'end_marker': self.containers[self.containers_count - 1]}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list), self.containers_count - 2)

    @decorators.idempotent_id('f7064ae8-dbcc-48da-b594-82feef6ea5af')
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

            self.assertLessEqual(len(container_list), limit,
                                 str(container_list))

    @decorators.idempotent_id('888a3f0e-7214-4806-8e50-5e0c9a69bb5e')
    def test_list_containers_with_limit_and_end_marker(self):
        # list containers combining limit and end_marker param
        limit = random.randint(1, self.containers_count)
        params = {'limit': limit,
                  'end_marker': self.containers[self.containers_count // 2]}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list),
                         min(limit, self.containers_count // 2))

    @decorators.idempotent_id('8cf98d9c-e3a0-4e44-971b-c87656fdddbd')
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

    @decorators.idempotent_id('365e6fc7-1cfe-463b-a37c-8bd08d47b6aa')
    def test_list_containers_with_prefix(self):
        # list containers that have a name that starts with a prefix
        prefix = 'tempest-a'
        params = {'prefix': prefix}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        for container in container_list:
            self.assertEqual(True, container.decode(
                'utf-8').startswith(prefix))

    @decorators.idempotent_id('b1811cff-d1ed-4c15-a52e-efd8de41cf34')
    def test_list_containers_reverse_order(self):
        # list containers in reverse order
        _, orig_container_list = self.account_client.list_account_containers()

        params = {'reverse': True}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(sorted(orig_container_list, reverse=True),
                         container_list)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('4894c312-6056-4587-8d6f-86ffbf861f80')
    def test_list_account_metadata(self):
        # list all account metadata

        # set metadata to account
        metadata = {'test-account-meta1': 'Meta1',
                    'test-account-meta2': 'Meta2'}
        resp, _ = self.account_client.create_update_or_delete_account_metadata(
            create_update_metadata=metadata)

        resp, _ = self.account_client.list_account_metadata()
        self.assertHeaders(resp, 'Account', 'HEAD')
        self.assertIn('x-account-meta-test-account-meta1', resp)
        self.assertIn('x-account-meta-test-account-meta2', resp)
        self.account_client.create_update_or_delete_account_metadata(
            delete_metadata=metadata)

    @decorators.idempotent_id('b904c2e3-24c2-4dba-ad7d-04e90a761be5')
    def test_list_no_account_metadata(self):
        # list no account metadata
        resp, _ = self.account_client.list_account_metadata()
        self.assertHeaders(resp, 'Account', 'HEAD')
        self.assertNotIn('x-account-meta-', str(resp))

    @decorators.idempotent_id('e2a08b5f-3115-4768-a3ee-d4287acd6c08')
    def test_update_account_metadata_with_create_metadata(self):
        # add metadata to account
        metadata = {'test-account-meta1': 'Meta1'}
        resp, _ = self.account_client.create_update_or_delete_account_metadata(
            create_update_metadata=metadata)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertIn('x-account-meta-test-account-meta1', resp)
        self.assertEqual(resp['x-account-meta-test-account-meta1'],
                         metadata['test-account-meta1'])

        self.account_client.create_update_or_delete_account_metadata(
            delete_metadata=metadata)

    @decorators.idempotent_id('9f60348d-c46f-4465-ae06-d51dbd470953')
    def test_update_account_metadata_with_delete_metadata(self):
        # delete metadata from account
        metadata = {'test-account-meta1': 'Meta1'}
        self.account_client.create_update_or_delete_account_metadata(
            create_update_metadata=metadata)
        resp, _ = self.account_client.create_update_or_delete_account_metadata(
            delete_metadata=metadata)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)

    @decorators.idempotent_id('64fd53f3-adbd-4639-af54-436e4982dbfb')
    def test_update_account_metadata_with_create_metadata_key(self):
        # if the value of metadata is not set, the metadata is not
        # registered at a server
        metadata = {'test-account-meta1': ''}
        resp, _ = self.account_client.create_update_or_delete_account_metadata(
            create_update_metadata=metadata)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)

    @decorators.idempotent_id('d4d884d3-4696-4b85-bc98-4f57c4dd2bf1')
    def test_update_account_metadata_with_delete_metadata_key(self):
        # Although the value of metadata is not set, the feature of
        # deleting metadata is valid
        metadata_1 = {'test-account-meta1': 'Meta1'}
        self.account_client.create_update_or_delete_account_metadata(
            create_update_metadata=metadata_1)
        metadata_2 = {'test-account-meta1': ''}
        resp, _ = self.account_client.create_update_or_delete_account_metadata(
            delete_metadata=metadata_2)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)

    @decorators.idempotent_id('8e5fc073-59b9-42ee-984a-29ed11b2c749')
    def test_update_account_metadata_with_create_and_delete_metadata(self):
        # Send a request adding and deleting metadata requests simultaneously
        metadata_1 = {'test-account-meta1': 'Meta1'}
        self.account_client.create_update_or_delete_account_metadata(
            create_update_metadata=metadata_1)
        metadata_2 = {'test-account-meta2': 'Meta2'}
        resp, _ = (
            self.account_client.create_update_or_delete_account_metadata(
                create_update_metadata=metadata_2,
                delete_metadata=metadata_1))
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)
        self.assertIn('x-account-meta-test-account-meta2', resp)
        self.assertEqual(resp['x-account-meta-test-account-meta2'],
                         metadata_2['test-account-meta2'])

        self.account_client.create_update_or_delete_account_metadata(
            delete_metadata=metadata_2)
