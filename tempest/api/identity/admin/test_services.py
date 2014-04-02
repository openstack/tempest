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

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class ServicesTestJSON(base.BaseIdentityV2AdminTest):
    _interface = 'json'

    def _del_service(self, service_id):
        # Deleting the service created in this method
        resp, _ = self.client.delete_service(service_id)
        self.assertEqual(204, resp.status)
        # Checking whether service is deleted successfully
        self.assertRaises(exceptions.NotFound, self.client.get_service,
                          service_id)

    @attr(type='smoke')
    def test_create_get_delete_service(self):
        # GET Service
        # Creating a Service
        name = data_utils.rand_name('service-')
        type = data_utils.rand_name('type--')
        description = data_utils.rand_name('description-')
        resp, service_data = self.client.create_service(
            name, type, description=description)
        self.assertFalse(service_data['id'] is None)
        self.addCleanup(self._del_service, service_data['id'])
        self.assertEqual(200, resp.status)
        # Verifying response body of create service
        self.assertIn('id', service_data)
        self.assertIn('name', service_data)
        self.assertEqual(name, service_data['name'])
        self.assertIn('type', service_data)
        self.assertEqual(type, service_data['type'])
        self.assertIn('description', service_data)
        self.assertEqual(description, service_data['description'])
        # Get service
        resp, fetched_service = self.client.get_service(service_data['id'])
        self.assertEqual(200, resp.status)
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

    @attr(type='gate')
    def test_create_service_without_description(self):
        # Create a service only with name and type
        name = data_utils.rand_name('service-')
        type = data_utils.rand_name('type--')
        resp, service = self.client.create_service(name, type)
        self.assertIn('id', service)
        self.assertTrue('200', resp['status'])
        self.addCleanup(self._del_service, service['id'])
        self.assertIn('name', service)
        self.assertEqual(name, service['name'])
        self.assertIn('type', service)
        self.assertEqual(type, service['type'])

    @attr(type='smoke')
    def test_list_services(self):
        # Create, List, Verify and Delete Services
        services = []
        for _ in moves.xrange(3):
            name = data_utils.rand_name('service-')
            type = data_utils.rand_name('type--')
            description = data_utils.rand_name('description-')
            resp, service = self.client.create_service(
                name, type, description=description)
            services.append(service)
        service_ids = map(lambda x: x['id'], services)

        def delete_services():
            for service_id in service_ids:
                self.client.delete_service(service_id)

        self.addCleanup(delete_services)
        # List and Verify Services
        resp, body = self.client.list_services()
        self.assertEqual(200, resp.status)
        found = [service for service in body if service['id'] in service_ids]
        self.assertEqual(len(found), len(services), 'Services not found')


class ServicesTestXML(ServicesTestJSON):
    _interface = 'xml'
