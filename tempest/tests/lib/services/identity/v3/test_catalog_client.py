# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.lib.services.identity.v3 import catalog_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestCatalogClient(base.BaseServiceTest):
    FAKE_CATALOG_INFO = {
        'catalog': [
            {
                'endpoints': [
                    {
                        'id': '39dc322ce86c4111b4f06c2eeae0841b',
                        'interface': 'public',
                        'region': 'RegionOne',
                        'url': 'http://localhost:5000'
                    },
                ],
                'id': 'ac58672276f848a7b1727850b3ebe826',
                'type': 'compute',
                'name': 'nova'
            },
            {
                'endpoints': [
                    {
                        'id': '39dc322ce86c4111b4f06c2eeae0841b',
                        'interface': 'public',
                        'region': 'RegionOne',
                        'url': 'http://localhost:5000'
                    },
                ],
                'id': 'b7c5ed2b486a46dbb4c221499d22991c',
                'type': 'image',
                'name': 'glance'
            },
            {
                'endpoints': [
                    {
                        'id': '39dc322ce86c4111b4f06c2eeae0841b',
                        'interface': 'public',
                        'region': 'RegionOne',
                        'url': 'http://localhost:5000'
                    },
                ],
                'id': '4363ae44bdf34a3981fde3b823cb9aa2',
                'type': 'identity',
                'name': 'keystone'
            }

        ],
        'links': {
            'self': 'http://localhost/identity/v3/catalog',
            'previous': None,
            'next': None
        }
    }

    def setUp(self):
        super(TestCatalogClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = catalog_client.CatalogClient(fake_auth, 'identity',
                                                   'RegionOne')

    def test_show_catalog_with_bytes_body(self):
        self._test_show_catalog(bytes_body=True)

    def test_show_catalog_with_str_body(self):
        self._test_show_catalog()

    def _test_show_catalog(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_catalog,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CATALOG_INFO,
            bytes_body)
