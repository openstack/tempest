# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 IBM Corp.
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


from tempest.api.volume import base
from tempest.test import attr


class ExtensionsTestJSON(base.BaseVolumeTest):
    _interface = 'json'

    @attr(type='gate')
    def test_list_extensions(self):
        # List of all extensions
        resp, extensions = self.volumes_extension_client.list_extensions()
        self.assertEqual(200, resp.status)
        if len(self.config.volume_feature_enabled.api_extensions) == 0:
            raise self.skipException('There are not any extensions configured')
        ext = self.config.volume_feature_enabled.api_extensions[0]
        if ext == 'all':
            self.assertIn('Hosts', map(lambda x: x['name'], extensions))
        elif ext:
            self.assertIn(ext, map(lambda x: x['name'], extensions))
        else:
            raise self.skipException('There are not any extensions configured')


class ExtensionsTestXML(ExtensionsTestJSON):
    _interface = 'xml'
