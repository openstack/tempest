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

from tempest_lib.common.utils import data_utils

from tempest.api.identity import base
from tempest import test


class EndPointsTestJSON(base.BaseIdentityV3AdminTest):

    @classmethod
    def setup_clients(cls):
        super(EndPointsTestJSON, cls).setup_clients()
        cls.identity_client = cls.client
        cls.client = cls.endpoints_client

    @classmethod
    def resource_setup(cls):
        super(EndPointsTestJSON, cls).resource_setup()
        cls.service_ids = list()
        s_name = data_utils.rand_name('service')
        s_type = data_utils.rand_name('type')
        s_description = data_utils.rand_name('description')
        cls.service_data =\
            cls.service_client.create_service(s_name, s_type,
                                              description=s_description)
        cls.service_id = cls.service_data['id']
        cls.service_ids.append(cls.service_id)
        # Create endpoints so as to use for LIST and GET test cases
        cls.setup_endpoints = list()
        for i in range(2):
            region = data_utils.rand_name('region')
            url = data_utils.rand_url()
            interface = 'public'
            endpoint = cls.client.create_endpoint(
                cls.service_id, interface, url, region=region, enabled=True)
            cls.setup_endpoints.append(endpoint)

    @classmethod
    def resource_cleanup(cls):
        for e in cls.setup_endpoints:
            cls.client.delete_endpoint(e['id'])
        for s in cls.service_ids:
            cls.service_client.delete_service(s)
        super(EndPointsTestJSON, cls).resource_cleanup()

    @test.attr(type='gate')
    @test.idempotent_id('c19ecf90-240e-4e23-9966-21cee3f6a618')
    def test_list_endpoints(self):
        # Get a list of endpoints
        fetched_endpoints = self.client.list_endpoints()
        # Asserting LIST endpoints
        missing_endpoints =\
            [e for e in self.setup_endpoints if e not in fetched_endpoints]
        self.assertEqual(0, len(missing_endpoints),
                         "Failed to find endpoint %s in fetched list" %
                         ', '.join(str(e) for e in missing_endpoints))

    @test.attr(type='gate')
    @test.idempotent_id('0e2446d2-c1fd-461b-a729-b9e73e3e3b37')
    def test_create_list_delete_endpoint(self):
        region = data_utils.rand_name('region')
        url = data_utils.rand_url()
        interface = 'public'
        endpoint =\
            self.client.create_endpoint(self.service_id, interface, url,
                                        region=region, enabled=True)
        # Asserting Create Endpoint response body
        self.assertIn('id', endpoint)
        self.assertEqual(region, endpoint['region'])
        self.assertEqual(url, endpoint['url'])
        # Checking if created endpoint is present in the list of endpoints
        fetched_endpoints = self.client.list_endpoints()
        fetched_endpoints_id = [e['id'] for e in fetched_endpoints]
        self.assertIn(endpoint['id'], fetched_endpoints_id)
        # Deleting the endpoint created in this method
        self.client.delete_endpoint(endpoint['id'])
        # Checking whether endpoint is deleted successfully
        fetched_endpoints = self.client.list_endpoints()
        fetched_endpoints_id = [e['id'] for e in fetched_endpoints]
        self.assertNotIn(endpoint['id'], fetched_endpoints_id)

    @test.attr(type='smoke')
    @test.idempotent_id('37e8f15e-ee7c-4657-a1e7-f6b61e375eff')
    def test_update_endpoint(self):
        # Creating an endpoint so as to check update endpoint
        # with new values
        region1 = data_utils.rand_name('region')
        url1 = data_utils.rand_url()
        interface1 = 'public'
        endpoint_for_update =\
            self.client.create_endpoint(self.service_id, interface1,
                                        url1, region=region1,
                                        enabled=True)
        self.addCleanup(self.client.delete_endpoint, endpoint_for_update['id'])
        # Creating service so as update endpoint with new service ID
        s_name = data_utils.rand_name('service')
        s_type = data_utils.rand_name('type')
        s_description = data_utils.rand_name('description')
        service2 =\
            self.service_client.create_service(s_name, s_type,
                                               description=s_description)
        self.service_ids.append(service2['id'])
        # Updating endpoint with new values
        region2 = data_utils.rand_name('region')
        url2 = data_utils.rand_url()
        interface2 = 'internal'
        endpoint = \
            self.client.update_endpoint(endpoint_for_update['id'],
                                        service_id=service2['id'],
                                        interface=interface2, url=url2,
                                        region=region2, enabled=False)
        # Asserting if the attributes of endpoint are updated
        self.assertEqual(service2['id'], endpoint['service_id'])
        self.assertEqual(interface2, endpoint['interface'])
        self.assertEqual(url2, endpoint['url'])
        self.assertEqual(region2, endpoint['region'])
        self.assertEqual('false', str(endpoint['enabled']).lower())
