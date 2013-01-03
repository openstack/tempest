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

from nose.plugins.attrib import attr

from tempest.tests.compute import base


class ExtensionsTestBase(object):

    @attr(type='positive')
    def test_list_extensions(self):
        # List of all extensions
        resp, extensions = self.client.list_extensions()
        self.assertTrue("extensions" in extensions)
        self.assertEqual(200, resp.status)


class ExtensionsTestJSON(base.BaseComputeTest, ExtensionsTestBase):

    @classmethod
    def setUpClass(cls):
        super(ExtensionsTestJSON, cls).setUpClass()
        cls.client = cls.extensions_client


class ExtensionsTestXML(base.BaseComputeTestXML, ExtensionsTestBase):

    @classmethod
    def setUpClass(cls):
        super(ExtensionsTestXML, cls).setUpClass()
        cls.client = cls.extensions_client
