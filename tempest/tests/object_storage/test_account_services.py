# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import unittest2 as unittest
import tempest.config
import re

from nose.plugins.attrib import attr
from tempest import exceptions
from tempest import openstack
from tempest.common.utils.data_utils import rand_name
from tempest.tests.object_storage import base


class AccountTest(base.BaseObjectTest):

    @classmethod
    def setUpClass(cls):
        super(AccountTest, cls).setUpClass()

        #Create a container
        cls.container_name = rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)

    @classmethod
    def tearDownClass(cls):
        cls.container_client.delete_container(cls.container_name)

    @attr(type='smoke')
    def test_list_containers(self):
        """List of all containers should not be empty"""

        params = {'format': 'json'}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)

        self.assertIsNotNone(container_list)
        container_names = [c['name'] for c in container_list]
        self.assertTrue(self.container_name in container_names)

    @attr(type='smoke')
    def test_list_account_metadata(self):
        """List all account metadata"""

        resp, metadata = self.account_client.list_account_metadata()
        self.assertEqual(resp['status'], '204')
        self.assertIn('x-account-object-count', resp)
        self.assertIn('x-account-container-count', resp)
        self.assertIn('x-account-bytes-used', resp)

    @attr(type='smoke')
    def test_create_account_metadata(self):
        """Add metadata to account"""

        metadata = {'test-account-meta': 'Meta!'}
        resp, _ = \
            self.account_client.create_account_metadata(metadata=metadata)
        self.assertEqual(resp['status'], '204')

        resp, metadata = self.account_client.list_account_metadata()
        self.assertIn('x-account-meta-test-account-meta', resp)
        self.assertEqual(resp['x-account-meta-test-account-meta'], 'Meta!')
