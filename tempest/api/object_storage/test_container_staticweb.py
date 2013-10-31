# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Joe H. Rahme <joe.hakim.rahme@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.api.object_storage import base
from tempest.common.utils import data_utils
from tempest.test import attr


class StaticWebTest(base.BaseObjectTest):

    @classmethod
    def setUpClass(cls):
        super(StaticWebTest, cls).setUpClass()
        cls.container_name = data_utils.rand_name(name="TestContainer")

        # This header should be posted on the container before every test
        cls.headers_public_read_acl = {'Read': '.r:*'}

        # Create test container and create one object in it
        cls.container_client.create_container(cls.container_name)
        cls.object_name = data_utils.rand_name(name="TestObject")
        cls.object_data = data_utils.arbitrary_string()
        cls.object_client.create_object(cls.container_name,
                                        cls.object_name,
                                        cls.object_data)

        cls.container_client.update_container_metadata(
            cls.container_name,
            metadata=cls.headers_public_read_acl,
            metadata_prefix="X-Container-")

    @classmethod
    def tearDownClass(cls):
        cls.delete_containers([cls.container_name])
        cls.data.teardown_all()
        super(StaticWebTest, cls).tearDownClass()

    @attr('gate')
    def test_web_index(self):
        headers = {'web-index': self.object_name}

        self.container_client.update_container_metadata(
            self.container_name, metadata=headers)

        # test GET on http://account_url/container_name
        # we should retrieve the self.object_name file
        resp, body = self.custom_account_client.request("GET",
                                                        self.container_name)
        self.assertEqual(resp['status'], '200')
        self.assertEqual(body, self.object_data)

        # clean up before exiting
        self.container_client.update_container_metadata(self.container_name,
                                                        {'web-index': ""})

        _, body = self.container_client.list_container_metadata(
            self.container_name)
        self.assertNotIn('x-container-meta-web-index', body)

    @attr('gate')
    def test_web_listing(self):
        headers = {'web-listings': 'true'}

        self.container_client.update_container_metadata(
            self.container_name, metadata=headers)

        # test GET on http://account_url/container_name
        # we should retrieve a listing of objects
        resp, body = self.custom_account_client.request("GET",
                                                        self.container_name)
        self.assertEqual(resp['status'], '200')
        self.assertIn(self.object_name, body)

        # clean up before exiting
        self.container_client.update_container_metadata(self.container_name,
                                                        {'web-listings': ""})

        _, body = self.container_client.list_container_metadata(
            self.container_name)
        self.assertNotIn('x-container-meta-web-listings', body)
