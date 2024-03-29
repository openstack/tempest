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

from tempest.api.network import base
from tempest.common import utils
from tempest.lib import decorators


class ServiceProvidersTest(base.BaseNetworkTest):
    """Test network service providers"""

    @classmethod
    def skip_checks(cls):
        super(ServiceProvidersTest, cls).skip_checks()
        if not utils.is_extension_enabled('service-type', 'network'):
            skip_msg = ("service-type extension not enabled.")
            raise cls.skipException(skip_msg)

    @decorators.idempotent_id('2cbbeea9-f010-40f6-8df5-4eaa0c918ea6')
    def test_service_providers_list(self):
        """Test listing network service providers"""
        body = self.service_providers_client.list_service_providers()
        self.assertIn('service_providers', body)
        self.assertIsInstance(body['service_providers'], list)
