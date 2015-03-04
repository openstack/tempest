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

from tempest.api.object_storage import base
from tempest.common import custom_matchers
from tempest import test


class CrossdomainTest(base.BaseObjectTest):

    @classmethod
    def resource_setup(cls):
        super(CrossdomainTest, cls).resource_setup()

        cls.xml_start = '<?xml version="1.0"?>\n' \
                        '<!DOCTYPE cross-domain-policy SYSTEM ' \
                        '"http://www.adobe.com/xml/dtds/cross-domain-policy.' \
                        'dtd" >\n<cross-domain-policy>\n'

        cls.xml_end = "</cross-domain-policy>"

    def setUp(self):
        super(CrossdomainTest, self).setUp()

        # Turning http://.../v1/foobar into http://.../
        self.account_client.skip_path()

    @test.attr('gate')
    @test.idempotent_id('d1b8b031-b622-4010-82f9-ff78a9e915c7')
    @test.requires_ext(extension='crossdomain', service='object')
    def test_get_crossdomain_policy(self):
        resp, body = self.account_client.get("crossdomain.xml", {})

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
