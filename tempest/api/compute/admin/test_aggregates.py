# Copyright 2013 NEC Corporation.
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
from tempest import test


class AggregatesAdminTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Aggregates API that require admin privileges
    """

    _host_key = 'OS-EXT-SRV-ATTR:host'

    @classmethod
    def setUpClass(cls):
        super(AggregatesAdminTestJSON, cls).setUpClass()
        cls.client = cls.os_adm.aggregates_client
        cls.aggregate_name_prefix = 'test_aggregate_'
        cls.az_name_prefix = 'test_az_'

        resp, hosts_all = cls.os_adm.hosts_client.list_hosts()
        hosts = map(lambda x: x['host_name'],
                    filter(lambda y: y['service'] == 'compute', hosts_all))
        cls.host = hosts[0]

    def _try_delete_aggregate(self, aggregate_id):
        # delete aggregate, if it exists
        try:
            self.client.delete_aggregate(aggregate_id)
        # if aggregate not found, it depict it was deleted in the test
        except exceptions.NotFound:
            pass

    @test.attr(type='gate')
    def test_aggregate_create_delete(self):
        # Create and delete an aggregate.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.addCleanup(self._try_delete_aggregate, aggregate['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(aggregate_name, aggregate['name'])
        self.assertIsNone(aggregate['availability_zone'])

        resp, _ = self.client.delete_aggregate(aggregate['id'])
        self.assertEqual(200, resp.status)
        self.client.wait_for_resource_deletion(aggregate['id'])

    @test.attr(type='gate')
    def test_aggregate_create_delete_with_az(self):
        # Create and delete an aggregate.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        az_name = data_utils.rand_name(self.az_name_prefix)
        resp, aggregate = self.client.create_aggregate(
            name=aggregate_name, availability_zone=az_name)
        self.addCleanup(self._try_delete_aggregate, aggregate['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(aggregate_name, aggregate['name'])
        self.assertEqual(az_name, aggregate['availability_zone'])

        resp, _ = self.client.delete_aggregate(aggregate['id'])
        self.assertEqual(200, resp.status)
        self.client.wait_for_resource_deletion(aggregate['id'])

    @test.attr(type='gate')
    def test_aggregate_create_verify_entry_in_list(self):
        # Create an aggregate and ensure it is listed.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        resp, aggregates = self.client.list_aggregates()
        self.assertEqual(200, resp.status)
        self.assertIn((aggregate['id'], aggregate['availability_zone']),
                      map(lambda x: (x['id'], x['availability_zone']),
                          aggregates))

    @test.attr(type='gate')
    def test_aggregate_create_update_metadata_get_details(self):
        # Create an aggregate and ensure its details are returned.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        resp, body = self.client.get_aggregate(aggregate['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(aggregate['name'], body['name'])
        self.assertEqual(aggregate['availability_zone'],
                         body['availability_zone'])
        self.assertEqual({}, body["metadata"])

        # set the metadata of the aggregate
        meta = {"key": "value"}
        resp, body = self.client.set_metadata(aggregate['id'], meta)
        self.assertEqual(200, resp.status)
        self.assertEqual(meta, body["metadata"])

        # verify the metadata has been set
        resp, body = self.client.get_aggregate(aggregate['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(meta, body["metadata"])

    @test.attr(type='gate')
    def test_aggregate_create_update_with_az(self):
        # Update an aggregate and ensure properties are updated correctly
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        az_name = data_utils.rand_name(self.az_name_prefix)
        resp, aggregate = self.client.create_aggregate(
            name=aggregate_name, availability_zone=az_name)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        self.assertEqual(200, resp.status)
        self.assertEqual(aggregate_name, aggregate['name'])
        self.assertEqual(az_name, aggregate['availability_zone'])
        self.assertIsNotNone(aggregate['id'])

        aggregate_id = aggregate['id']
        new_aggregate_name = aggregate_name + '_new'
        new_az_name = az_name + '_new'

        resp, resp_aggregate = self.client.update_aggregate(aggregate_id,
                                                            new_aggregate_name,
                                                            new_az_name)
        self.assertEqual(200, resp.status)
        self.assertEqual(new_aggregate_name, resp_aggregate['name'])
        self.assertEqual(new_az_name, resp_aggregate['availability_zone'])

        resp, aggregates = self.client.list_aggregates()
        self.assertEqual(200, resp.status)
        self.assertIn((aggregate_id, new_aggregate_name, new_az_name),
                      map(lambda x:
                          (x['id'], x['name'], x['availability_zone']),
                          aggregates))

    @test.attr(type='gate')
    def test_aggregate_add_remove_host(self):
        # Add an host to the given aggregate and remove.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        resp, body = self.client.add_host(aggregate['id'], self.host)
        self.assertEqual(200, resp.status)
        self.assertEqual(aggregate_name, body['name'])
        self.assertEqual(aggregate['availability_zone'],
                         body['availability_zone'])
        self.assertIn(self.host, body['hosts'])

        resp, body = self.client.remove_host(aggregate['id'], self.host)
        self.assertEqual(200, resp.status)
        self.assertEqual(aggregate_name, body['name'])
        self.assertEqual(aggregate['availability_zone'],
                         body['availability_zone'])
        self.assertNotIn(self.host, body['hosts'])

    @test.attr(type='gate')
    def test_aggregate_add_host_list(self):
        # Add an host to the given aggregate and list.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])
        self.client.add_host(aggregate['id'], self.host)
        self.addCleanup(self.client.remove_host, aggregate['id'], self.host)

        resp, aggregates = self.client.list_aggregates()
        aggs = filter(lambda x: x['id'] == aggregate['id'], aggregates)
        self.assertEqual(1, len(aggs))
        agg = aggs[0]
        self.assertEqual(aggregate_name, agg['name'])
        self.assertIsNone(agg['availability_zone'])
        self.assertIn(self.host, agg['hosts'])

    @test.attr(type='gate')
    def test_aggregate_add_host_get_details(self):
        # Add an host to the given aggregate and get details.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        resp, aggregate = self.client.create_aggregate(name=aggregate_name)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])
        self.client.add_host(aggregate['id'], self.host)
        self.addCleanup(self.client.remove_host, aggregate['id'], self.host)

        resp, body = self.client.get_aggregate(aggregate['id'])
        self.assertEqual(aggregate_name, body['name'])
        self.assertIsNone(body['availability_zone'])
        self.assertIn(self.host, body['hosts'])

    @test.attr(type='gate')
    def test_aggregate_add_host_create_server_with_az(self):
        # Add an host to the given aggregate and create a server.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        az_name = data_utils.rand_name(self.az_name_prefix)
        resp, aggregate = self.client.create_aggregate(
            name=aggregate_name, availability_zone=az_name)
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])
        self.client.add_host(aggregate['id'], self.host)
        self.addCleanup(self.client.remove_host, aggregate['id'], self.host)
        server_name = data_utils.rand_name('test_server_')
        admin_servers_client = self.os_adm.servers_client
        resp, server = self.create_test_server(name=server_name,
                                               availability_zone=az_name,
                                               wait_until='ACTIVE')
        resp, body = admin_servers_client.get_server(server['id'])
        self.assertEqual(self.host, body[self._host_key])


class AggregatesAdminTestXML(AggregatesAdminTestJSON):
    _host_key = (
        '{http://docs.openstack.org/compute/ext/extended_status/api/v1.1}host')
    _interface = 'xml'
