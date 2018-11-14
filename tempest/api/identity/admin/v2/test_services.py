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

from tempest.api.identity import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class ServicesTestJSON(base.BaseIdentityV2AdminTest):

    def _del_service(self, service_id):
        # Deleting the service created in this method
        self.services_client.delete_service(service_id)
        # Checking whether service is deleted successfully
        self.assertRaises(lib_exc.NotFound, self.services_client.show_service,
                          service_id)

    @decorators.idempotent_id('84521085-c6e6-491c-9a08-ec9f70f90110')
    def test_create_get_delete_service(self):
        # GET Service
        # Creating a Service
        name = data_utils.rand_name('service')
        s_type = data_utils.rand_name('type')
        description = data_utils.rand_name('description')
        service_data = self.services_client.create_service(
            name=name, type=s_type,
            description=description)['OS-KSADM:service']
        self.assertIsNotNone(service_data['id'])
        self.addCleanup(self._del_service, service_data['id'])
        # Verifying response body of create service
        self.assertIn('name', service_data)
        self.assertEqual(name, service_data['name'])
        self.assertIn('type', service_data)
        self.assertEqual(s_type, service_data['type'])
        self.assertIn('description', service_data)
        self.assertEqual(description, service_data['description'])
        # Get service
        fetched_service = (
            self.services_client.show_service(service_data['id'])
            ['OS-KSADM:service'])
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

    @decorators.idempotent_id('5d3252c8-e555-494b-a6c8-e11d7335da42')
    def test_create_service_without_description(self):
        # Create a service only with name and type
        name = data_utils.rand_name('service')
        s_type = data_utils.rand_name('type')
        service = self.services_client.create_service(
            name=name, type=s_type)['OS-KSADM:service']
        self.assertIn('id', service)
        self.addCleanup(self._del_service, service['id'])
        self.assertIn('name', service)
        self.assertEqual(name, service['name'])
        self.assertIn('type', service)
        self.assertEqual(s_type, service['type'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('34ea6489-012d-4a86-9038-1287cadd5eca')
    def test_list_services(self):
        # Create, List, Verify and Delete Services
        services = []
        for _ in range(3):
            name = data_utils.rand_name('service')
            s_type = data_utils.rand_name('type')
            description = data_utils.rand_name('description')

            service = self.services_client.create_service(
                name=name, type=s_type,
                description=description)['OS-KSADM:service']
            self.addCleanup(self.services_client.delete_service, service['id'])
            services.append(service)
        service_ids = [svc['id'] for svc in services]

        # List and Verify Services
        body = self.services_client.list_services()['OS-KSADM:services']
        found = [serv for serv in body if serv['id'] in service_ids]
        self.assertEqual(len(found), len(services), 'Services not found')
