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
from tempest.common import custom_matchers
from tempest.common.utils import data_utils
from tempest import test


class AccountTest(base.BaseObjectTest):
    @classmethod
    def setUpClass(cls):
        super(AccountTest, cls).setUpClass()
        cls.containers = []
        for i in moves.xrange(ord('a'), ord('f') + 1):
            name = data_utils.rand_name(name='%s-' % chr(i))
            cls.container_client.create_container(name)
            cls.containers.append(name)
        cls.containers_count = len(cls.containers)

    @classmethod
    def tearDownClass(cls):
        cls.delete_containers(cls.containers)
        super(AccountTest, cls).tearDownClass()

    @test.attr(type='smoke')
    def test_list_containers(self):
        # list of all containers should not be empty
        params = {'format': 'json'}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertIsNotNone(container_list)
        container_names = [c['name'] for c in container_list]
        for container_name in self.containers:
            self.assertIn(container_name, container_names)

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
    def test_list_account_metadata(self):
        # list all account metadata
        resp, metadata = self.account_client.list_account_metadata()
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'HEAD')

    @test.attr(type='smoke')
    def test_create_and_delete_account_metadata(self):
        header = 'test-account-meta'
        data = 'Meta!'
        # add metadata to account
        resp, _ = self.account_client.create_account_metadata(
            metadata={header: data})
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertHeaders(resp, 'Account', 'HEAD')

        self.assertIn('x-account-meta-' + header, resp)
        self.assertEqual(resp['x-account-meta-' + header], data)

        # delete metadata from account
        resp, _ = \
            self.account_client.delete_account_metadata(metadata=[header])
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'POST')

        resp, _ = self.account_client.list_account_metadata()
        self.assertHeaders(resp, 'Account', 'HEAD')
        self.assertNotIn('x-account-meta-' + header, resp)
