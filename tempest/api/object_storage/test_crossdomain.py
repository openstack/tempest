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
from tempest import clients
from tempest.common import custom_matchers
from tempest import test


class CrossdomainTest(base.BaseObjectTest):

    @classmethod
    def setUpClass(cls):
        super(CrossdomainTest, cls).setUpClass()
        # creates a test user. The test user will set its base_url to the Swift
        # endpoint and test the healthcheck feature.
        cls.data.setup_test_user()

        cls.os_test_user = clients.Manager(cls.data.test_credentials)

        cls.xml_start = '<?xml version="1.0"?>\n' \
                        '<!DOCTYPE cross-domain-policy SYSTEM ' \
                        '"http://www.adobe.com/xml/dtds/cross-domain-policy.' \
                        'dtd" >\n<cross-domain-policy>\n'

        cls.xml_end = "</cross-domain-policy>"

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()
        super(CrossdomainTest, cls).tearDownClass()

    def setUp(self):
        super(CrossdomainTest, self).setUp()

        client = self.os_test_user.account_client
        # Turning http://.../v1/foobar into http://.../
        client.skip_path()

    def tearDown(self):
        # clear the base_url for subsequent requests
        self.os_test_user.account_client.reset_path()

        super(CrossdomainTest, self).tearDown()

    @test.attr('gate')
    @test.requires_ext(extension='crossdomain', service='object')
    def test_get_crossdomain_policy(self):
        resp, body = self.os_test_user.account_client.get("crossdomain.xml",
                                                          {})

        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertTrue(body.startswith(self.xml_start) and
                        body.endswith(self.xml_end))

        # The target of the request is not any Swift resource. Therefore, the
        # existence of response header is checked without a custom matcher.
        self.assertIn('content-length', resp)
        self.assertIn('content-type', resp)
        self.assertIn('x-trans-id', resp)
        self.assertIn('date', resp)
        # Check only the format of common headers with custom matcher
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())
