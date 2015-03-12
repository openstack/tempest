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

from oslo_log import log as logging

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


LOG = logging.getLogger(__name__)


class ExtensionsTestJSON(base.BaseV2ComputeTest):

    @test.attr(type='gate')
    @test.idempotent_id('3bb27738-b759-4e0d-a5fa-37d7a6df07d1')
    def test_list_extensions(self):
        # List of all extensions
        if len(CONF.compute_feature_enabled.api_extensions) == 0:
            raise self.skipException('There are not any extensions configured')
        extensions = self.extensions_client.list_extensions()
        ext = CONF.compute_feature_enabled.api_extensions[0]
        if ext == 'all':
            self.assertIn('Hosts', map(lambda x: x['name'], extensions))
        elif ext:
            self.assertIn(ext, map(lambda x: x['alias'], extensions))
        else:
            raise self.skipException('There are not any extensions configured')
        # Log extensions list
        extension_list = map(lambda x: x['alias'], extensions)
        LOG.debug("Nova extensions: %s" % ','.join(extension_list))

    @test.idempotent_id('05762f39-bdfa-4cdb-9b46-b78f8e78e2fd')
    @test.requires_ext(extension='os-consoles', service='compute')
    @test.attr(type='gate')
    def test_get_extension(self):
        # get the specified extensions
        extension = self.extensions_client.get_extension('os-consoles')
        self.assertEqual('os-consoles', extension['alias'])
