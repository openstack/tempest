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

from tempest.api.object_storage import base
from tempest import clients
from tempest.common import custom_matchers
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class AccountTest(base.BaseObjectTest):

    containers = []

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(AccountTest, cls).setUpClass()
        for i in moves.xrange(ord('a'), ord('f') + 1):
            name = data_utils.rand_name(name='%s-' % chr(i))
            cls.container_client.create_container(name)
            cls.containers.append(name)
        cls.containers_count = len(cls.containers)

    @classmethod
    def tearDownClass(cls):
        cls.delete_containers(cls.containers)
        cls.data.teardown_all()
        super(AccountTest, cls).tearDownClass()

    @test.attr(type='smoke')
    def test_list_containers(self):
        # list of all containers should not be empty
        resp, container_list = self.account_client.list_account_containers()
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertIsNotNone(container_list)
        for container_name in self.containers:
            self.assertIn(container_name, container_list)

    @test.attr(type='smoke')
    def test_list_no_containers(self):
        # List request to empty account

        # To test listing no containers, create new user other than
        # the base user of this instance.
        self.data.setup_test_user()

        os_test_user = clients.Manager(
            self.data.test_credentials)

        # Retrieve the id of an operator role of object storage
        test_role_id = None
        swift_role = CONF.object_storage.operator_role
        try:
            _, roles = self.os_admin.identity_client.list_roles()
            test_role_id = next(r['id'] for r in roles if r['name']
                                == swift_role)
        except StopIteration:
            msg = "%s role found" % swift_role
            raise exceptions.NotFound(msg)

        # Retrieve the test_user id
        _, users = self.os_admin.identity_client.get_users()
        test_user_id = next(usr['id'] for usr in users if usr['name']
                            == self.data.test_user)

        # Retrieve the test_tenant id
        _, tenants = self.os_admin.identity_client.list_tenants()
        test_tenant_id = next(tnt['id'] for tnt in tenants if tnt['name']
                              == self.data.test_tenant)

        # Assign the newly created user the appropriate operator role
        self.os_admin.identity_client.assign_user_role(
            test_tenant_id,
            test_user_id,
            test_role_id)

        resp, container_list = \
            os_test_user.account_client.list_account_containers()
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)

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
    def test_list_containers_with_format_json(self):
        # list containers setting format parameter to 'json'
        params = {'format': 'json'}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertIsNotNone(container_list)
        self.assertTrue([c['name'] for c in container_list])
        self.assertTrue([c['count'] for c in container_list])
        self.assertTrue([c['bytes'] for c in container_list])

    @test.attr(type='smoke')
    def test_list_containers_with_format_xml(self):
        # list containers setting format parameter to 'xml'
        params = {'format': 'xml'}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertIsNotNone(container_list)
        self.assertEqual(container_list.tag, 'account')
        self.assertTrue('name' in container_list.keys())
        self.assertEqual(container_list.find(".//container").tag, 'container')
        self.assertEqual(container_list.find(".//name").tag, 'name')
        self.assertEqual(container_list.find(".//count").tag, 'count')
        self.assertEqual(container_list.find(".//bytes").tag, 'bytes')

    @test.attr(type='smoke')
    def test_list_extensions(self):
        resp, extensions = self.account_client.list_extensions()

        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

    @test.attr(type='smoke')
    def test_list_containers_with_limit(self):
        # list containers one of them, half of them then all of them
        for limit in (1, self.containers_count / 2, self.containers_count):
            params = {'limit': limit}
            resp, container_list = \
                self.account_client.list_account_containers(params=params)
            self.assertHeaders(resp, 'Account', 'GET')

            self.assertEqual(len(container_list), limit)

    @test.attr(type='smoke')
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
    def test_list_containers_with_marker_and_end_marker(self):
        # list containers combining marker and end_marker param
        params = {'marker': self.containers[0],
                  'end_marker': self.containers[self.containers_count - 1]}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list), self.containers_count - 2)

    @test.attr(type='smoke')
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
    def test_list_containers_with_limit_and_end_marker(self):
        # list containers combining limit and end_marker param
        limit = random.randint(1, self.containers_count)
        params = {'limit': limit,
                  'end_marker': self.containers[self.containers_count / 2]}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list),
                         min(limit, self.containers_count / 2))

    @test.attr(type='smoke')
    def test_list_containers_with_limit_and_marker_and_end_marker(self):
        # list containers combining limit, marker and end_marker param
        limit = random.randint(1, self.containers_count)
        params = {'limit': limit,
                  'marker': self.containers[0],
                  'end_marker': self.containers[self.containers_count - 1]}
        resp, container_list = self.account_client.list_account_containers(
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertEqual(len(container_list),
                         min(limit, self.containers_count - 2))

    @test.attr(type='smoke')
    def test_list_account_metadata(self):
        # list all account metadata

        # set metadata to account
        metadata = {'test-account-meta1': 'Meta1',
                    'test-account-meta2': 'Meta2'}
        resp, _ = self.account_client.create_account_metadata(metadata)

        resp, _ = self.account_client.list_account_metadata()
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'HEAD')
        self.assertIn('x-account-meta-test-account-meta1', resp)
        self.assertIn('x-account-meta-test-account-meta2', resp)
        self.account_client.delete_account_metadata(metadata)

    @test.attr(type='smoke')
    def test_list_no_account_metadata(self):
        # list no account metadata
        resp, _ = self.account_client.list_account_metadata()
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'HEAD')
        self.assertNotIn('x-account-meta-', str(resp))

    @test.attr(type='smoke')
    def test_update_account_metadata_with_create_metadata(self):
        # add metadata to account
        metadata = {'test-account-meta1': 'Meta1'}
        resp, _ = self.account_client.create_account_metadata(metadata)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, body = self.account_client.list_account_metadata()
        self.assertIn('x-account-meta-test-account-meta1', resp)
        self.assertEqual(resp['x-account-meta-test-account-meta1'],
                         metadata['test-account-meta1'])

        self.account_client.delete_account_metadata(metadata)

    @test.attr(type='smoke')
    def test_update_account_metadata_with_delete_matadata(self):
        # delete metadata from account
        metadata = {'test-account-meta1': 'Meta1'}
        self.account_client.create_account_metadata(metadata)
        resp, _ = self.account_client.delete_account_metadata(metadata)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)

    @test.attr(type='smoke')
    def test_update_account_metadata_with_create_matadata_key(self):
        # if the value of metadata is not set, the metadata is not
        # registered at a server
        metadata = {'test-account-meta1': ''}
        resp, _ = self.account_client.create_account_metadata(metadata)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)

    @test.attr(type='smoke')
    def test_update_account_metadata_with_delete_matadata_key(self):
        # Although the value of metadata is not set, the feature of
        # deleting metadata is valid
        metadata_1 = {'test-account-meta1': 'Meta1'}
        self.account_client.create_account_metadata(metadata_1)
        metadata_2 = {'test-account-meta1': ''}
        resp, _ = self.account_client.delete_account_metadata(metadata_2)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)

    @test.attr(type='smoke')
    def test_update_account_metadata_with_create_and_delete_metadata(self):
        # Send a request adding and deleting metadata requests simultaneously
        metadata_1 = {'test-account-meta1': 'Meta1'}
        self.account_client.create_account_metadata(metadata_1)
        metadata_2 = {'test-account-meta2': 'Meta2'}
        resp, body = self.account_client.create_and_delete_account_metadata(
            metadata_2,
            metadata_1)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertNotIn('x-account-meta-test-account-meta1', resp)
        self.assertIn('x-account-meta-test-account-meta2', resp)
        self.assertEqual(resp['x-account-meta-test-account-meta2'],
                         metadata_2['test-account-meta2'])

        self.account_client.delete_account_metadata(metadata_2)
