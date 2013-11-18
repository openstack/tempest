# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


from tempest.api.compute import base
from tempest import test
import testtools


class ExtensionsTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @testtools.skipIf(not test.is_extension_enabled('os-consoles', 'compute'),
                      'os-consoles extension not enabled.')
    @test.attr(type='gate')
    def test_list_extensions(self):
        # List of all extensions
        resp, extensions = self.extensions_client.list_extensions()
        self.assertIn("extensions", extensions)
        self.assertEqual(200, resp.status)
        self.assertTrue(self.extensions_client.is_enabled("Consoles"))

    @testtools.skipIf(not test.is_extension_enabled('os-consoles', 'compute'),
                      'os-consoles extension not enabled.')
    @test.attr(type='gate')
    def test_get_extension(self):
        # get the specified extensions
        resp, extension = self.extensions_client.get_extension('os-consoles')
        self.assertEqual(200, resp.status)
        self.assertEqual('os-consoles', extension['alias'])


class ExtensionsTestXML(ExtensionsTestJSON):
    _interface = 'xml'
