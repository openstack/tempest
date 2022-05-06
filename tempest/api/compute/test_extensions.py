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
from tempest.lib import decorators

CONF = config.CONF


LOG = logging.getLogger(__name__)


class ExtensionsTest(base.BaseV2ComputeTest):
    """Tests Compute Extensions API"""

    @decorators.idempotent_id('3bb27738-b759-4e0d-a5fa-37d7a6df07d1')
    def test_list_extensions(self):
        """Test listing compute extensions"""
        extensions = self.extensions_client.list_extensions()['extensions']
        # Log extensions list
        extension_list = [x['alias'] for x in extensions]
        LOG.debug("Nova extensions: %s", ','.join(extension_list))

        self.assertIn('Hosts', map(lambda x: x['name'], extensions))

    @decorators.idempotent_id('05762f39-bdfa-4cdb-9b46-b78f8e78e2fd')
    def test_get_extension(self):
        """Test getting specified compute extension details"""
        extension = self.extensions_client.show_extension('os-consoles')
        self.assertEqual('os-consoles', extension['extension']['alias'])
