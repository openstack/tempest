# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.object_storage import base
from tempest.common import custom_matchers
from tempest import test


class StaticWebTest(base.BaseObjectTest):

    @classmethod
    def resource_setup(cls):
        super(StaticWebTest, cls).resource_setup()
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
    def resource_cleanup(cls):
        if hasattr(cls, "container_name"):
            cls.delete_containers([cls.container_name])
        super(StaticWebTest, cls).resource_cleanup()

    @test.idempotent_id('c1f055ab-621d-4a6a-831f-846fcb578b8b')
    @test.requires_ext(extension='staticweb', service='object')
    @test.attr('gate')
    def test_web_index(self):
        headers = {'web-index': self.object_name}

        self.container_client.update_container_metadata(
            self.container_name, metadata=headers)

        # Maintain original headers, no auth added
        self.account_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )

        # test GET on http://account_url/container_name
        # we should retrieve the self.object_name file
        resp, body = self.account_client.request("GET",
                                                 self.container_name,
                                                 headers={})
        # This request is equivalent to GET object
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, self.object_data)

        # clean up before exiting
        self.container_client.update_container_metadata(self.container_name,
                                                        {'web-index': ""})

        _, body = self.container_client.list_container_metadata(
            self.container_name)
        self.assertNotIn('x-container-meta-web-index', body)

    @test.idempotent_id('941814cf-db9e-4b21-8112-2b6d0af10ee5')
    @test.requires_ext(extension='staticweb', service='object')
    @test.attr('gate')
    def test_web_listing(self):
        headers = {'web-listings': 'true'}

        self.container_client.update_container_metadata(
            self.container_name, metadata=headers)

        # test GET on http://account_url/container_name
        # we should retrieve a listing of objects
        resp, body = self.account_client.request("GET",
                                                 self.container_name,
                                                 headers={})
        # The target of the request is not any Swift resource. Therefore, the
        # existence of response header is checked without a custom matcher.
        self.assertIn('content-length', resp)
        self.assertIn('content-type', resp)
        self.assertIn('x-trans-id', resp)
        self.assertIn('date', resp)
        # Check only the format of common headers with custom matcher
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

        self.assertIn(self.object_name, body)

        # clean up before exiting
        self.container_client.update_container_metadata(self.container_name,
                                                        {'web-listings': ""})

        _, body = self.container_client.list_container_metadata(
            self.container_name)
        self.assertNotIn('x-container-meta-web-listings', body)

    @test.idempotent_id('bc37ec94-43c8-4990-842e-0e5e02fc8926')
    @test.requires_ext(extension='staticweb', service='object')
    @test.attr('gate')
    def test_web_listing_css(self):
        headers = {'web-listings': 'true',
                   'web-listings-css': 'listings.css'}

        self.container_client.update_container_metadata(
            self.container_name, metadata=headers)

        # Maintain original headers, no auth added
        self.account_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )

        # test GET on http://account_url/container_name
        # we should retrieve a listing of objects
        resp, body = self.account_client.request("GET",
                                                 self.container_name,
                                                 headers={})
        self.assertIn(self.object_name, body)
        css = '<link rel="stylesheet" type="text/css" href="listings.css" />'
        self.assertIn(css, body)

    @test.idempotent_id('f18b4bef-212e-45e7-b3ca-59af3a465f82')
    @test.requires_ext(extension='staticweb', service='object')
    @test.attr('gate')
    def test_web_error(self):
        headers = {'web-listings': 'true',
                   'web-error': self.object_name}

        self.container_client.update_container_metadata(
            self.container_name, metadata=headers)

        # Create object to return when requested object not found
        object_name_404 = "404" + self.object_name
        object_data_404 = data_utils.arbitrary_string()
        self.object_client.create_object(self.container_name,
                                         object_name_404,
                                         object_data_404)

        # Do not set auth in HTTP headers for next request
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )

        # Request non-existing object
        self.assertRaises(
            lib_exc.NotFound, self.object_client.get_object,
            self.container_name, "notexisting")
