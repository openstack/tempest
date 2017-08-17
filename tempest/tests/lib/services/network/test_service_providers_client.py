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


from tempest.lib.services.network import service_providers_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestServiceProvidersClient(base.BaseServiceTest):
    def setUp(self):
        super(TestServiceProvidersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = service_providers_client.ServiceProvidersClient(
            fake_auth, 'network', 'regionOne')

    def _test_list_service_providers(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_service_providers,
            'tempest.lib.common.rest_client.RestClient.get',
            {"service_providers": []},
            bytes_body)

    def test_list_service_providers_with_str_body(self):
        self._test_list_service_providers()

    def test_list_service_providers_with_bytes_body(self):
        self._test_list_service_providers(bytes_body=True)
