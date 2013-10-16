# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

from tempest.api.network import base
from tempest.test import attr


class ServiceTypeManagementTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    @attr(type='smoke')
    def test_service_provider_list(self):
        resp, body = self.client.list_service_providers()
        self.assertEqual(resp['status'], '200')
        self.assertIsInstance(body['service_providers'], list)


class ServiceTypeManagementTestXML(ServiceTypeManagementTestJSON):
    _interface = 'xml'
