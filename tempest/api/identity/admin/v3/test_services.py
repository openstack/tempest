# Copyright 2013 OpenStack Foundation
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

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class ServicesTestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    def _del_service(self, service_id):
        # Used for deleting the services created in this class
        self.service_client.delete_service(service_id)
        # Checking whether service is deleted successfully
        self.assertRaises(exceptions.NotFound, self.service_client.get_service,
                          service_id)

    @test.attr(type='smoke')
    def test_create_update_get_service(self):
        # Creating a Service
        name = data_utils.rand_name('service')
        serv_type = data_utils.rand_name('type')
        desc = data_utils.rand_name('description')
        _, create_service = self.service_client.create_service(
            serv_type, name=name, description=desc)
        self.addCleanup(self._del_service, create_service['id'])
        self.assertIsNotNone(create_service['id'])

        # Verifying response body of create service
        expected_data = {'name': name, 'type': serv_type, 'description': desc}
        self.assertDictContainsSubset(expected_data, create_service)

        # Update description
        s_id = create_service['id']
        resp1_desc = create_service['description']
        s_desc2 = data_utils.rand_name('desc2')
        _, update_service = self.service_client.update_service(
            s_id, description=s_desc2)
        resp2_desc = update_service['description']

        self.assertNotEqual(resp1_desc, resp2_desc)

        # Get service
        _, fetched_service = self.service_client.get_service(s_id)
        resp3_desc = fetched_service['description']

        self.assertEqual(resp2_desc, resp3_desc)
        self.assertDictContainsSubset(update_service, fetched_service)

    @test.attr(type='smoke')
    def test_create_service_without_description(self):
        # Create a service only with name and type
        name = data_utils.rand_name('service')
        serv_type = data_utils.rand_name('type')
        _, service = self.service_client.create_service(
            serv_type, name=name)
        self.addCleanup(self.service_client.delete_service, service['id'])
        self.assertIn('id', service)
        expected_data = {'name': name, 'type': serv_type}
        self.assertDictContainsSubset(expected_data, service)

    @test.attr(type='smoke')
    def test_list_services(self):
        # Create, List, Verify and Delete Services
        service_ids = list()
        for _ in range(3):
            name = data_utils.rand_name('service')
            serv_type = data_utils.rand_name('type')
            _, create_service = self.service_client.create_service(
                serv_type, name=name)
            self.addCleanup(self.service_client.delete_service,
                            create_service['id'])
            service_ids.append(create_service['id'])

        # List and Verify Services
        _, services = self.service_client.list_services()
        fetched_ids = [service['id'] for service in services]
        found = [s for s in fetched_ids if s in service_ids]
        self.assertEqual(len(found), len(service_ids))


class ServicesTestXML(ServicesTestJSON):
    _interface = 'xml'
