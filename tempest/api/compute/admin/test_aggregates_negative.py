# Copyright 2013 Huawei Technologies Co.,LTD.
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

from tempest.api.compute import base
from tempest.common import tempest_fixtures as fixtures
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class AggregatesAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Aggregates API that require admin privileges
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(AggregatesAdminNegativeTestJSON, cls).setUpClass()
        cls.client = cls.os_adm.aggregates_client
        cls.user_client = cls.aggregates_client
        cls.aggregate_name_prefix = 'test_aggregate_'
        cls.az_name_prefix = 'test_az_'

        resp, hosts_all = cls.os_adm.hosts_client.list_hosts()
        hosts = map(lambda x: x['host_name'],
                    filter(lambda y: y['service'] == 'compute', hosts_all))
        cls.host = hosts[0]

    @attr(type=['negative', 'gate'])
    def test_aggregate_create_as_user(self):
        # Regular user is not allowed to create an aggregate.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        self.assertRaises(exceptions.Unauthorized,
                          self.user_client.create_aggregate,
                          name=aggregate_name)

    @attr(type=['negative', 'gate'])
    def test_aggregate_create_aggregate_name_length_less_than_1(self):
        # the length of aggregate name should >= 1 and <=255
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_aggregate,
                          name='')

    @attr(type=['negative', 'gate'])
    def test_aggregate_create_aggregate_name_length_exceeds_255(self):
        # the length of aggregate name should >= 1 and <=255
        aggregate_name = 'a' * 256
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_aggregate,
                          name=aggregate_name)

    @attr(type=['negative', 'gate'])
    def test_aggregate_create_with_existent_aggregate_name(self):
        # creating an aggregate with existent aggregate name is forbidden
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        self.assertRaises(exceptions.Conflict,
                          self.client.create_aggregate,
                          name=aggregate_name)

    @attr(type=['negative', 'gate'])
    def test_aggregate_delete_as_user(self):
        # Regular user is not allowed to delete an aggregate.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        self.assertRaises(exceptions.Unauthorized,
                          self.user_client.delete_aggregate,
                          aggregate['id'])

    @attr(type=['negative', 'gate'])
    def test_aggregate_list_as_user(self):
        # Regular user is not allowed to list aggregates.
        self.assertRaises(exceptions.Unauthorized,
                          self.user_client.list_aggregates)

    @attr(type=['negative', 'gate'])
    def test_aggregate_get_details_as_user(self):
        # Regular user is not allowed to get aggregate details.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        self.assertRaises(exceptions.Unauthorized,
                          self.user_client.get_aggregate,
                          aggregate['id'])

    @attr(type=['negative', 'gate'])
    def test_aggregate_delete_with_invalid_id(self):
        # Delete an aggregate with invalid id should raise exceptions.
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_aggregate, -1)

    @attr(type=['negative', 'gate'])
    def test_aggregate_get_details_with_invalid_id(self):
        # Get aggregate details with invalid id should raise exceptions.
        self.assertRaises(exceptions.NotFound,
                          self.client.get_aggregate, -1)

    @attr(type=['negative', 'gate'])
    def test_aggregate_add_non_exist_host(self):
        # Adding a non-exist host to an aggregate should raise exceptions.
        resp, hosts_all = self.os_adm.hosts_client.list_hosts()
        hosts = map(lambda x: x['host_name'], hosts_all)
        while True:
            non_exist_host = data_utils.rand_name('nonexist_host_')
            if non_exist_host not in hosts:
                break

        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        self.assertRaises(exceptions.NotFound, self.client.add_host,
                          aggregate['id'], non_exist_host)

    @attr(type=['negative', 'gate'])
    def test_aggregate_add_host_as_user(self):
        # Regular user is not allowed to add a host to an aggregate.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        self.assertRaises(exceptions.Unauthorized,
                          self.user_client.add_host,
                          aggregate['id'], self.host)

    @attr(type=['negative', 'gate'])
    def test_aggregate_add_existent_host(self):
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        resp, body = self.client.add_host(aggregate['id'], self.host)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.remove_host, aggregate['id'], self.host)

        self.assertRaises(exceptions.Conflict, self.client.add_host,
                          aggregate['id'], self.host)

    @attr(type=['negative', 'gate'])
    def test_aggregate_remove_host_as_user(self):
        # Regular user is not allowed to remove a host from an aggregate.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])
        resp, body = self.client.add_host(aggregate['id'], self.host)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.remove_host, aggregate['id'], self.host)

        self.assertRaises(exceptions.Unauthorized,
                          self.user_client.remove_host,
                          aggregate['id'], self.host)

    @attr(type=['negative', 'gate'])
    def test_aggregate_remove_nonexistent_host(self):
        non_exist_host = data_utils.rand_name('nonexist_host_')
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        self.assertRaises(exceptions.NotFound, self.client.remove_host,
                          aggregate['id'], non_exist_host)


class AggregatesAdminNegativeTestXML(AggregatesAdminNegativeTestJSON):
    _interface = 'xml'
