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

from six import moves
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.identity import base
from tempest import test


class ServicesTestJSON(base.BaseIdentityV2AdminTest):

    def _del_service(self, service_id):
        # Deleting the service created in this method
        self.client.delete_service(service_id)
        # Checking whether service is deleted successfully
        self.assertRaises(lib_exc.NotFound, self.client.get_service,
                          service_id)

    @test.attr(type='smoke')
    @test.idempotent_id('84521085-c6e6-491c-9a08-ec9f70f90110')
    def test_create_get_delete_service(self):
        # GET Service
        # Creating a Service
        name = data_utils.rand_name('service')
        type = data_utils.rand_name('type')
        description = data_utils.rand_name('description')
        service_data = self.client.create_service(
            name, type, description=description)
        self.assertFalse(service_data['id'] is None)
        self.addCleanup(self._del_service, service_data['id'])
        # Verifying response body of create service
        self.assertIn('id', service_data)
        self.assertIn('name', service_data)
        self.assertEqual(name, service_data['name'])
        self.assertIn('type', service_data)
        self.assertEqual(type, service_data['type'])
        self.assertIn('description', service_data)
        self.assertEqual(description, service_data['description'])
        # Get service
        fetched_service = self.client.get_service(service_data['id'])
        # verifying the existence of service created
        self.assertIn('id', fetched_service)
        self.assertEqual(fetched_service['id'], service_data['id'])
        self.assertIn('name', fetched_service)
        self.assertEqual(fetched_service['name'], service_data['name'])
        self.assertIn('type', fetched_service)
        self.assertEqual(fetched_service['type'], service_data['type'])
        self.assertIn('description', fetched_service)
        self.assertEqual(fetched_service['description'],
                         service_data['description'])

    @test.attr(type='gate')
    @test.idempotent_id('5d3252c8-e555-494b-a6c8-e11d7335da42')
    def test_create_service_without_description(self):
        # Create a service only with name and type
        name = data_utils.rand_name('service')
        type = data_utils.rand_name('type')
        service = self.client.create_service(name, type)
        self.assertIn('id', service)
        self.addCleanup(self._del_service, service['id'])
        self.assertIn('name', service)
        self.assertEqual(name, service['name'])
        self.assertIn('type', service)
        self.assertEqual(type, service['type'])

    @test.attr(type='smoke')
    @test.idempotent_id('34ea6489-012d-4a86-9038-1287cadd5eca')
    def test_list_services(self):
        # Create, List, Verify and Delete Services
        services = []
        for _ in moves.xrange(3):
            name = data_utils.rand_name('service')
            type = data_utils.rand_name('type')
            description = data_utils.rand_name('description')
            service = self.client.create_service(
                name, type, description=description)
            services.append(service)
        service_ids = map(lambda x: x['id'], services)

        def delete_services():
            for service_id in service_ids:
                self.client.delete_service(service_id)

        self.addCleanup(delete_services)
        # List and Verify Services
        body = self.client.list_services()
        found = [serv for serv in body if serv['id'] in service_ids]
        self.assertEqual(len(found), len(services), 'Services not found')
