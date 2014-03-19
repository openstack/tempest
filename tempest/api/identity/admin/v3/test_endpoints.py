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


class EndPointsTestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(EndPointsTestJSON, cls).setUpClass()
        cls.identity_client = cls.client
        cls.client = cls.endpoints_client
        cls.service_ids = list()
        s_name = data_utils.rand_name('service-')
        s_type = data_utils.rand_name('type--')
        s_description = data_utils.rand_name('description-')
        resp, cls.service_data =\
            cls.service_client.create_service(s_name, s_type,
                                              description=s_description)
        cls.service_id = cls.service_data['id']
        cls.service_ids.append(cls.service_id)
        # Create endpoints so as to use for LIST and GET test cases
        cls.setup_endpoints = list()
        for i in range(2):
            region = data_utils.rand_name('region')
            url = data_utils.rand_name('url')
            interface = 'public'
            resp, endpoint = cls.client.create_endpoint(
                cls.service_id, interface, url, region=region, enabled=True)
            cls.setup_endpoints.append(endpoint)

    @classmethod
    def tearDownClass(cls):
        for e in cls.setup_endpoints:
            cls.client.delete_endpoint(e['id'])
        for s in cls.service_ids:
            cls.service_client.delete_service(s)
        super(EndPointsTestJSON, cls).tearDownClass()

    @test.attr(type='gate')
    def test_list_endpoints(self):
        # Get a list of endpoints
        resp, fetched_endpoints = self.client.list_endpoints()
        # Asserting LIST endpoints
        self.assertEqual(resp['status'], '200')
        missing_endpoints =\
            [e for e in self.setup_endpoints if e not in fetched_endpoints]
        self.assertEqual(0, len(missing_endpoints),
                         "Failed to find endpoint %s in fetched list" %
                         ', '.join(str(e) for e in missing_endpoints))

    @test.attr(type='gate')
    def test_create_list_delete_endpoint(self):
        region = data_utils.rand_name('region')
        url = data_utils.rand_name('url')
        interface = 'public'
        resp, endpoint =\
            self.client.create_endpoint(self.service_id, interface, url,
                                        region=region, enabled=True)
        # Asserting Create Endpoint response body
        self.assertEqual(resp['status'], '201')
        self.assertIn('id', endpoint)
        self.assertEqual(region, endpoint['region'])
        self.assertEqual(url, endpoint['url'])
        # Checking if created endpoint is present in the list of endpoints
        resp, fetched_endpoints = self.client.list_endpoints()
        fetched_endpoints_id = [e['id'] for e in fetched_endpoints]
        self.assertIn(endpoint['id'], fetched_endpoints_id)
        # Deleting the endpoint created in this method
        resp, body = self.client.delete_endpoint(endpoint['id'])
        self.assertEqual(resp['status'], '204')
        self.assertEqual(body, '')
        # Checking whether endpoint is deleted successfully
        resp, fetched_endpoints = self.client.list_endpoints()
        fetched_endpoints_id = [e['id'] for e in fetched_endpoints]
        self.assertNotIn(endpoint['id'], fetched_endpoints_id)

    @test.attr(type='smoke')
    def test_update_endpoint(self):
        # Creating an endpoint so as to check update endpoint
        # with new values
        region1 = data_utils.rand_name('region')
        url1 = data_utils.rand_name('url')
        interface1 = 'public'
        resp, endpoint_for_update =\
            self.client.create_endpoint(self.service_id, interface1,
                                        url1, region=region1,
                                        enabled=True)
        self.addCleanup(self.client.delete_endpoint, endpoint_for_update['id'])
        # Creating service so as update endpoint with new service ID
        s_name = data_utils.rand_name('service-')
        s_type = data_utils.rand_name('type--')
        s_description = data_utils.rand_name('description-')
        resp, self.service2 =\
            self.service_client.create_service(s_name, s_type,
                                               description=s_description)
        self.service_ids.append(self.service2['id'])
        # Updating endpoint with new values
        region2 = data_utils.rand_name('region')
        url2 = data_utils.rand_name('url')
        interface2 = 'internal'
        resp, endpoint = \
            self.client.update_endpoint(endpoint_for_update['id'],
                                        service_id=self.service2['id'],
                                        interface=interface2, url=url2,
                                        region=region2, enabled=False)
        self.assertEqual(resp['status'], '200')
        # Asserting if the attributes of endpoint are updated
        self.assertEqual(self.service2['id'], endpoint['service_id'])
        self.assertEqual(interface2, endpoint['interface'])
        self.assertEqual(url2, endpoint['url'])
        self.assertEqual(region2, endpoint['region'])
        self.assertEqual('false', str(endpoint['enabled']).lower())


class EndPointsTestXML(EndPointsTestJSON):
    _interface = 'xml'
