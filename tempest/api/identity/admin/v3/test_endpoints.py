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
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators


class EndPointsTestJSON(base.BaseIdentityV3AdminTest):
    """Test keystone endpoints"""

    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    @classmethod
    def setup_clients(cls):
        super(EndPointsTestJSON, cls).setup_clients()
        cls.client = cls.endpoints_client

    @classmethod
    def resource_setup(cls):
        super(EndPointsTestJSON, cls).resource_setup()
        cls.service_ids = list()

        # Create endpoints so as to use for LIST and GET test cases
        interfaces = ['public', 'internal']
        cls.setup_endpoint_ids = list()
        for i in range(2):
            service = cls._create_service()
            cls.service_ids.append(service['id'])
            cls.addClassResourceCleanup(
                cls.services_client.delete_service, service['id'])

            region_name = data_utils.rand_name('region')
            url = data_utils.rand_url()
            endpoint = cls.client.create_endpoint(
                service_id=cls.service_ids[i], interface=interfaces[i],
                url=url, region=region_name, enabled=True)['endpoint']
            region = cls.regions_client.show_region(region_name)['region']
            cls.addClassResourceCleanup(
                cls.regions_client.delete_region, region['id'])
            cls.addClassResourceCleanup(
                cls.client.delete_endpoint, endpoint['id'])
            cls.setup_endpoint_ids.append(endpoint['id'])

    @classmethod
    def _create_service(cls, s_name=None, s_type=None, s_description=None):
        if s_name is None:
            s_name = data_utils.rand_name('service')
        if s_type is None:
            s_type = data_utils.rand_name('type')
        if s_description is None:
            s_description = data_utils.rand_name('description')
        service_data = (
            cls.services_client.create_service(name=s_name, type=s_type,
                                               description=s_description))
        return service_data['service']

    @decorators.idempotent_id('c19ecf90-240e-4e23-9966-21cee3f6a618')
    def test_list_endpoints(self):
        """Test listing keystone endpoints by filters"""
        # Get the list of all the endpoints.
        fetched_endpoints = self.client.list_endpoints()['endpoints']
        fetched_endpoint_ids = [e['id'] for e in fetched_endpoints]
        # Check that all the created endpoints are present in
        # "fetched_endpoints".
        missing_endpoints =\
            [e for e in self.setup_endpoint_ids
             if e not in fetched_endpoint_ids]
        self.assertEqual(0, len(missing_endpoints),
                         "Failed to find endpoint %s in fetched list" %
                         ', '.join(str(e) for e in missing_endpoints))

        # Check that filtering endpoints by service_id works.
        fetched_endpoints_for_service = self.client.list_endpoints(
            service_id=self.service_ids[0])['endpoints']
        fetched_endpoints_for_alt_service = self.client.list_endpoints(
            service_id=self.service_ids[1])['endpoints']

        # Assert that both filters returned the correct result.
        self.assertEqual(1, len(fetched_endpoints_for_service))
        self.assertEqual(1, len(fetched_endpoints_for_alt_service))
        self.assertEqual(set(self.setup_endpoint_ids),
                         set([fetched_endpoints_for_service[0]['id'],
                              fetched_endpoints_for_alt_service[0]['id']]))

        # Check that filtering endpoints by interface works.
        fetched_public_endpoints = self.client.list_endpoints(
            interface='public')['endpoints']
        fetched_internal_endpoints = self.client.list_endpoints(
            interface='internal')['endpoints']

        # Check that the expected endpoint_id is present per filter. [0] is
        # public and [1] is internal.
        self.assertIn(self.setup_endpoint_ids[0],
                      [e['id'] for e in fetched_public_endpoints])
        self.assertIn(self.setup_endpoint_ids[1],
                      [e['id'] for e in fetched_internal_endpoints])

    @decorators.idempotent_id('0e2446d2-c1fd-461b-a729-b9e73e3e3b37')
    def test_create_list_show_delete_endpoint(self):
        """Test creating, listing, showing and deleting keystone endpoint"""
        region_name = data_utils.rand_name('region')
        url = data_utils.rand_url()
        interface = 'public'
        endpoint = self.client.create_endpoint(service_id=self.service_ids[0],
                                               interface=interface,
                                               url=url, region=region_name,
                                               enabled=True)['endpoint']
        region = self.regions_client.show_region(region_name)['region']
        self.addCleanup(self.regions_client.delete_region, region['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.client.delete_endpoint, endpoint['id'])
        # Asserting Create Endpoint response body
        self.assertEqual(region_name, endpoint['region'])
        self.assertEqual(url, endpoint['url'])

        # Checking if created endpoint is present in the list of endpoints
        fetched_endpoints = self.client.list_endpoints()['endpoints']
        fetched_endpoints_id = [e['id'] for e in fetched_endpoints]
        self.assertIn(endpoint['id'], fetched_endpoints_id)

        # Show endpoint
        fetched_endpoint = (
            self.client.show_endpoint(endpoint['id'])['endpoint'])
        # Asserting if the attributes of endpoint are the same
        self.assertEqual(self.service_ids[0], fetched_endpoint['service_id'])
        self.assertEqual(interface, fetched_endpoint['interface'])
        self.assertEqual(url, fetched_endpoint['url'])
        self.assertEqual(region_name, fetched_endpoint['region'])
        self.assertEqual(True, fetched_endpoint['enabled'])

        # Deleting the endpoint created in this method
        self.client.delete_endpoint(endpoint['id'])

        # Checking whether endpoint is deleted successfully
        fetched_endpoints = self.client.list_endpoints()['endpoints']
        fetched_endpoints_id = [e['id'] for e in fetched_endpoints]
        self.assertNotIn(endpoint['id'], fetched_endpoints_id)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('37e8f15e-ee7c-4657-a1e7-f6b61e375eff')
    def test_update_endpoint(self):
        """Test updating keystone endpoint"""
        # NOTE(zhufl) Service2 should be created before endpoint_for_update
        # is created, because Service2 must be deleted after
        # endpoint_for_update is deleted, otherwise we will get a 404 error
        # when deleting endpoint_for_update if endpoint's service is deleted.

        # Creating service for updating endpoint with new service ID
        s_name = data_utils.rand_name('service')
        s_type = data_utils.rand_name('type')
        s_description = data_utils.rand_name('description')
        service2 = self._create_service(s_name=s_name, s_type=s_type,
                                        s_description=s_description)
        self.addCleanup(self.services_client.delete_service, service2['id'])

        # Creating an endpoint so as to check update endpoint with new values
        region1_name = data_utils.rand_name('region')
        url1 = data_utils.rand_url()
        interface1 = 'public'
        endpoint_for_update = (
            self.client.create_endpoint(service_id=self.service_ids[0],
                                        interface=interface1,
                                        url=url1, region=region1_name,
                                        enabled=True)['endpoint'])
        region1 = self.regions_client.show_region(region1_name)['region']
        self.addCleanup(self.regions_client.delete_region, region1['id'])

        # Updating endpoint with new values
        region2_name = data_utils.rand_name('region')
        url2 = data_utils.rand_url()
        interface2 = 'internal'
        endpoint = self.client.update_endpoint(endpoint_for_update['id'],
                                               service_id=service2['id'],
                                               interface=interface2,
                                               url=url2, region=region2_name,
                                               enabled=False)['endpoint']
        region2 = self.regions_client.show_region(region2_name)['region']
        self.addCleanup(self.regions_client.delete_region, region2['id'])
        self.addCleanup(self.client.delete_endpoint, endpoint_for_update['id'])

        # Asserting if the attributes of endpoint are updated
        self.assertEqual(service2['id'], endpoint['service_id'])
        self.assertEqual(interface2, endpoint['interface'])
        self.assertEqual(url2, endpoint['url'])
        self.assertEqual(region2_name, endpoint['region'])
        self.assertEqual(False, endpoint['enabled'])
