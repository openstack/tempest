# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest import config
from tempest.test import attr
from tempest.test import HTTP_SUCCESS


class CrossdomainTest(base.BaseObjectTest):
    crossdomain_available = \
        config.TempestConfig().object_storage_feature_enabled.crossdomain

    @classmethod
    def setUpClass(cls):
        super(CrossdomainTest, cls).setUpClass()

        # skip this test if CORS isn't enabled in the conf file.
        if not cls.crossdomain_available:
            skip_msg = ("%s skipped as Crossdomain middleware not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

        # creates a test user. The test user will set its base_url to the Swift
        # endpoint and test the healthcheck feature.
        cls.data.setup_test_user()

        cls.os_test_user = clients.Manager(
            cls.data.test_user,
            cls.data.test_password,
            cls.data.test_tenant)

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
        client._set_auth()
        # Turning http://.../v1/foobar into http://.../
        client.base_url = "/".join(client.base_url.split("/")[:-2])

    def tearDown(self):
        # clear the base_url for subsequent requests
        self.os_test_user.account_client.base_url = None

        super(CrossdomainTest, self).tearDown()

    @attr('gate')
    def test_get_crossdomain_policy(self):
        resp, body = self.os_test_user.account_client.get("crossdomain.xml",
                                                          {})

        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        self.assertTrue(body.startswith(self.xml_start) and
                        body.endswith(self.xml_end))
