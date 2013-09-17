# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class ServicesTestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    @attr(type='smoke')
    def test_create_get_delete_service(self):
        # GET Service
        try:
            # Creating a Service
            name = rand_name('service-')
            type = rand_name('type--')
            description = rand_name('description-')
            resp, service_data = self.client.create_service(
                name, type, description=description)
            self.assertTrue(resp['status'].startswith('2'))
            # Verifying response body of create service
            self.assertIn('id', service_data)
            self.assertFalse(service_data['id'] is None)
            self.assertIn('name', service_data)
            self.assertEqual(name, service_data['name'])
            self.assertIn('type', service_data)
            self.assertEqual(type, service_data['type'])
            self.assertIn('description', service_data)
            self.assertEqual(description, service_data['description'])
            # Get service
            resp, fetched_service = self.client.get_service(service_data['id'])
            self.assertTrue(resp['status'].startswith('2'))
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
        finally:
            if 'service_data' in locals():
                # Deleting the service created in this method
                resp, _ = self.client.delete_service(service_data['id'])
                self.assertEqual(resp['status'], '204')
                # Checking whether service is deleted successfully
                self.assertRaises(exceptions.NotFound, self.client.get_service,
                                  service_data['id'])

    @attr(type='smoke')
    def test_list_services(self):
        # Create, List, Verify and Delete Services
        services = []
        for _ in xrange(3):
            name = rand_name('service-')
            type = rand_name('type--')
            description = rand_name('description-')
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
        self.assertTrue(resp['status'].startswith('2'))
        found = [service for service in body if service['id'] in service_ids]
        self.assertEqual(len(found), len(services), 'Services not found')


class ServicesTestXML(ServicesTestJSON):
    _interface = 'xml'
