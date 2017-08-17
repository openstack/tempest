# Copyright 2017 AT&T Corporation.
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


class EndPointGroupsTest(base.BaseIdentityV3AdminTest):

    @classmethod
    def setup_clients(cls):
        super(EndPointGroupsTest, cls).setup_clients()
        cls.client = cls.endpoint_groups_client

    @classmethod
    def resource_setup(cls):
        super(EndPointGroupsTest, cls).resource_setup()
        cls.service_ids = list()
        cls.endpoint_groups = list()

        # Create endpoint group so as to use it for LIST test
        service_id = cls._create_service()

        name = data_utils.rand_name('service_group')
        description = data_utils.rand_name('description')
        filters = {'service_id': service_id}

        endpoint_group = cls.client.create_endpoint_group(
            name=name,
            description=description,
            filters=filters)['endpoint_group']

        cls.endpoint_groups.append(endpoint_group)

    @classmethod
    def resource_cleanup(cls):
        for e in cls.endpoint_groups:
            cls.client.delete_endpoint_group(e['id'])
        for s in cls.service_ids:
            cls.services_client.delete_service(s)
        super(EndPointGroupsTest, cls).resource_cleanup()

    @classmethod
    def _create_service(cls):
        s_name = data_utils.rand_name('service')
        s_type = data_utils.rand_name('type')
        s_description = data_utils.rand_name('description')
        service_data = (
            cls.services_client.create_service(name=s_name,
                                               type=s_type,
                                               description=s_description))

        service_id = service_data['service']['id']
        cls.service_ids.append(service_id)
        return service_id

    @decorators.idempotent_id('7c69e7a1-f865-402d-a2ea-44493017315a')
    def test_create_list_show_check_delete_endpoint_group(self):
        service_id = self._create_service()
        name = data_utils.rand_name('service_group')
        description = data_utils.rand_name('description')
        filters = {'service_id': service_id}

        endpoint_group = self.client.create_endpoint_group(
            name=name,
            description=description,
            filters=filters)['endpoint_group']

        self.endpoint_groups.append(endpoint_group)

        # Asserting created endpoint group response body
        self.assertIn('id', endpoint_group)
        self.assertEqual(name, endpoint_group['name'])
        self.assertEqual(description, endpoint_group['description'])

        # Checking if endpoint groups are present in the list of endpoints
        # Note that there are two endpoint groups in the list, one created
        # in the resource setup, one created in this test case.
        fetched_endpoints = \
            self.client.list_endpoint_groups()['endpoint_groups']

        missing_endpoints = \
            [e for e in self.endpoint_groups if e not in fetched_endpoints]

        # Asserting LIST endpoints
        self.assertEmpty(missing_endpoints,
                         "Failed to find endpoint %s in fetched list" %
                         ', '.join(str(e) for e in missing_endpoints))

        # Show endpoint group
        fetched_endpoint = self.client.show_endpoint_group(
            endpoint_group['id'])['endpoint_group']

        # Asserting if the attributes of endpoint group are the same
        self.assertEqual(service_id,
                         fetched_endpoint['filters']['service_id'])
        for attr in ('id', 'name', 'description'):
            self.assertEqual(endpoint_group[attr], fetched_endpoint[attr])

        # Check endpoint group
        self.client.check_endpoint_group(endpoint_group['id'])

        # Deleting the endpoint group created in this method
        self.client.delete_endpoint_group(endpoint_group['id'])
        self.endpoint_groups.remove(endpoint_group)

        # Checking whether endpoint group is deleted successfully
        fetched_endpoints = \
            self.client.list_endpoint_groups()['endpoint_groups']
        fetched_endpoint_ids = [e['id'] for e in fetched_endpoints]
        self.assertNotIn(endpoint_group['id'], fetched_endpoint_ids)

    @decorators.idempotent_id('51c8fc38-fa84-4e76-b5b6-6fc37770fb26')
    def test_update_endpoint_group(self):
        # Creating an endpoint group so as to check update endpoint group
        # with new values
        service1_id = self._create_service()
        name = data_utils.rand_name('service_group')
        description = data_utils.rand_name('description')
        filters = {'service_id': service1_id}

        endpoint_group = self.client.create_endpoint_group(
            name=name,
            description=description,
            filters=filters)['endpoint_group']
        self.endpoint_groups.append(endpoint_group)

        # Creating new attr values to update endpoint group
        service2_id = self._create_service()
        name2 = data_utils.rand_name('service_group2')
        description2 = data_utils.rand_name('description2')
        filters = {'service_id': service2_id}

        # Updating endpoint group with new attr values
        updated_endpoint_group = self.client.update_endpoint_group(
            endpoint_group['id'],
            name=name2,
            description=description2,
            filters=filters)['endpoint_group']

        self.assertEqual(name2, updated_endpoint_group['name'])
        self.assertEqual(description2, updated_endpoint_group['description'])
        self.assertEqual(service2_id,
                         updated_endpoint_group['filters']['service_id'])
