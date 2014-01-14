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
from tempest.openstack.common import log as logging
from tempest import test


LOG = logging.getLogger(__name__)


class ExtensionsTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @test.attr(type='gate')
    def test_list_extensions(self):
        # List of all extensions
        if len(self.config.compute_feature_enabled.api_extensions) == 0:
            raise self.skipException('There are not any extensions configured')
        resp, extensions = self.extensions_client.list_extensions()
        self.assertEqual(200, resp.status)
        ext = self.config.compute_feature_enabled.api_extensions[0]
        if ext == 'all':
            self.assertIn('Hosts', map(lambda x: x['name'], extensions))
        elif ext:
            self.assertIn(ext, map(lambda x: x['name'], extensions))
        else:
            raise self.skipException('There are not any extensions configured')
        # Log extensions list
        extension_list = map(lambda x: x['name'], extensions)
        LOG.debug("Nova extensions: %s" % ','.join(extension_list))

    @test.requires_ext(extension='os-consoles', service='compute')
    @test.attr(type='gate')
    def test_get_extension(self):
        # get the specified extensions
        resp, extension = self.extensions_client.get_extension('os-consoles')
        self.assertEqual(200, resp.status)
        self.assertEqual('os-consoles', extension['alias'])


class ExtensionsTestXML(ExtensionsTestJSON):
    _interface = 'xml'
