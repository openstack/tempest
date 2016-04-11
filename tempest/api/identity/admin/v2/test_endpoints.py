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
from tempest import test


class EndPointsTestJSON(base.BaseIdentityV2AdminTest):

    @classmethod
    def resource_setup(cls):
        super(EndPointsTestJSON, cls).resource_setup()
        cls.service_ids = list()
        s_name = data_utils.rand_name('service')
        s_type = data_utils.rand_name('type')
        s_description = data_utils.rand_name('description')
        cls.service_data = cls.services_client.create_service(
            s_name, s_type, description=s_description)['OS-KSADM:service']
        cls.service_id = cls.service_data['id']
        cls.service_ids.append(cls.service_id)
        # Create endpoints so as to use for LIST and GET test cases
        cls.setup_endpoints = list()
        for i in range(2):
            region = data_utils.rand_name('region')
            url = data_utils.rand_url()
            endpoint = cls.endpoints_client.create_endpoint(
                cls.service_id,
                region,
                publicurl=url,
                adminurl=url,
                internalurl=url)['endpoint']
            # list_endpoints() will return 'enabled' field
            endpoint['enabled'] = True
            cls.setup_endpoints.append(endpoint)

    @classmethod
    def resource_cleanup(cls):
        for e in cls.setup_endpoints:
            cls.endpoints_client.delete_endpoint(e['id'])
        for s in cls.service_ids:
            cls.services_client.delete_service(s)
        super(EndPointsTestJSON, cls).resource_cleanup()

    @test.idempotent_id('11f590eb-59d8-4067-8b2b-980c7f387f51')
    def test_list_endpoints(self):
        # Get a list of endpoints
        fetched_endpoints = self.endpoints_client.list_endpoints()['endpoints']
        # Asserting LIST endpoints
        missing_endpoints =\
            [e for e in self.setup_endpoints if e not in fetched_endpoints]
        self.assertEqual(0, len(missing_endpoints),
                         "Failed to find endpoint %s in fetched list" %
                         ', '.join(str(e) for e in missing_endpoints))

    @test.idempotent_id('9974530a-aa28-4362-8403-f06db02b26c1')
    def test_create_list_delete_endpoint(self):
        region = data_utils.rand_name('region')
        url = data_utils.rand_url()
        endpoint = self.endpoints_client.create_endpoint(
            self.service_id,
            region,
            publicurl=url,
            adminurl=url,
            internalurl=url)['endpoint']
        # Asserting Create Endpoint response body
        self.assertIn('id', endpoint)
        self.assertEqual(region, endpoint['region'])
        self.assertEqual(url, endpoint['publicurl'])
        # Checking if created endpoint is present in the list of endpoints
        fetched_endpoints = self.endpoints_client.list_endpoints()['endpoints']
        fetched_endpoints_id = [e['id'] for e in fetched_endpoints]
        self.assertIn(endpoint['id'], fetched_endpoints_id)
        # Deleting the endpoint created in this method
        self.endpoints_client.delete_endpoint(endpoint['id'])
        # Checking whether endpoint is deleted successfully
        fetched_endpoints = self.endpoints_client.list_endpoints()['endpoints']
        fetched_endpoints_id = [e['id'] for e in fetched_endpoints]
        self.assertNotIn(endpoint['id'], fetched_endpoints_id)
