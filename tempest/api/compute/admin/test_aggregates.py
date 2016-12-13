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

import testtools

from tempest.api.compute import base
from tempest.common import tempest_fixtures as fixtures
from tempest.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest import test


class AggregatesAdminTestJSON(base.BaseV2ComputeAdminTest):
    """Tests Aggregates API that require admin privileges"""

    _host_key = 'OS-EXT-SRV-ATTR:host'

    @classmethod
    def setup_clients(cls):
        super(AggregatesAdminTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.aggregates_client

    @classmethod
    def resource_setup(cls):
        super(AggregatesAdminTestJSON, cls).resource_setup()
        cls.aggregate_name_prefix = 'test_aggregate'
        cls.az_name_prefix = 'test_az'
        print("Hello")

        cls.host = None
        hypers = cls.os_adm.hypervisor_client.list_hypervisors(
            detail=True)['hypervisors']
        hosts_available = [hyper['service']['host'] for hyper in hypers
                           if (hyper['state'] == 'up' and
                               hyper['status'] == 'enabled')]
        if hosts_available:
            cls.host = hosts_available[0]
        else:
            raise testtools.TestCase.failureException(
                "no available compute node found")

    @test.idempotent_id('0d148aa3-d54c-4317-aa8d-42040a475e20')
    def test_aggregate_create_delete(self):
        # Create and delete an aggregate.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = (self.client.create_aggregate(name=aggregate_name)
                     ['aggregate'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.client.delete_aggregate, aggregate['id'])
        self.assertEqual(aggregate_name, aggregate['name'])
        self.assertIsNone(aggregate['availability_zone'])

        self.client.delete_aggregate(aggregate['id'])
        self.client.wait_for_resource_deletion(aggregate['id'])

    @test.idempotent_id('5873a6f8-671a-43ff-8838-7ce430bb6d0b')
    def test_aggregate_create_delete_with_az(self):
        # Create and delete an aggregate.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        az_name = data_utils.rand_name(self.az_name_prefix)
        aggregate = self.client.create_aggregate(
            name=aggregate_name, availability_zone=az_name)['aggregate']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.client.delete_aggregate, aggregate['id'])
        self.assertEqual(aggregate_name, aggregate['name'])
        self.assertEqual(az_name, aggregate['availability_zone'])

        self.client.delete_aggregate(aggregate['id'])
        self.client.wait_for_resource_deletion(aggregate['id'])

    @test.idempotent_id('68089c38-04b1-4758-bdf0-cf0daec4defd')
    def test_aggregate_create_verify_entry_in_list(self):
        # Create an aggregate and ensure it is listed.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = (self.client.create_aggregate(name=aggregate_name)
                     ['aggregate'])
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        aggregates = self.client.list_aggregates()['aggregates']
        self.assertIn((aggregate['id'], aggregate['availability_zone']),
                      map(lambda x: (x['id'], x['availability_zone']),
                          aggregates))

    @test.idempotent_id('36ec92ca-7a73-43bc-b920-7531809e8540')
    def test_aggregate_create_update_metadata_get_details(self):
        # Create an aggregate and ensure its details are returned.
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = (self.client.create_aggregate(name=aggregate_name)
                     ['aggregate'])
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        body = self.client.show_aggregate(aggregate['id'])['aggregate']
        self.assertEqual(aggregate['name'], body['name'])
        self.assertEqual(aggregate['availability_zone'],
                         body['availability_zone'])
        self.assertEqual({}, body["metadata"])

        # set the metadata of the aggregate
        meta = {"key": "value"}
        body = self.client.set_metadata(aggregate['id'], metadata=meta)
        self.assertEqual(meta, body['aggregate']["metadata"])

        # verify the metadata has been set
        body = self.client.show_aggregate(aggregate['id'])['aggregate']
        self.assertEqual(meta, body["metadata"])

    @test.idempotent_id('4d2b2004-40fa-40a1-aab2-66f4dab81beb')
    def test_aggregate_create_update_with_az(self):
        # Update an aggregate and ensure properties are updated correctly
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        az_name = data_utils.rand_name(self.az_name_prefix)
        aggregate = self.client.create_aggregate(
            name=aggregate_name, availability_zone=az_name)['aggregate']
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        self.assertEqual(aggregate_name, aggregate['name'])
        self.assertEqual(az_name, aggregate['availability_zone'])
        self.assertIsNotNone(aggregate['id'])

        aggregate_id = aggregate['id']
        new_aggregate_name = aggregate_name + '_new'
        new_az_name = az_name + '_new'

        resp_aggregate = self.client.update_aggregate(
            aggregate_id,
            name=new_aggregate_name,
            availability_zone=new_az_name)['aggregate']
        self.assertEqual(new_aggregate_name, resp_aggregate['name'])
        self.assertEqual(new_az_name, resp_aggregate['availability_zone'])

        aggregates = self.client.list_aggregates()['aggregates']
        self.assertIn((aggregate_id, new_aggregate_name, new_az_name),
                      map(lambda x:
                          (x['id'], x['name'], x['availability_zone']),
                          aggregates))

    @test.idempotent_id('c8e85064-e79b-4906-9931-c11c24294d02')
    def test_aggregate_add_remove_host(self):
        # Add a host to the given aggregate and remove.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = (self.client.create_aggregate(name=aggregate_name)
                     ['aggregate'])
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])

        body = (self.client.add_host(aggregate['id'], host=self.host)
                ['aggregate'])
        self.assertEqual(aggregate_name, body['name'])
        self.assertEqual(aggregate['availability_zone'],
                         body['availability_zone'])
        self.assertIn(self.host, body['hosts'])

        body = (self.client.remove_host(aggregate['id'], host=self.host)
                ['aggregate'])
        self.assertEqual(aggregate_name, body['name'])
        self.assertEqual(aggregate['availability_zone'],
                         body['availability_zone'])
        self.assertNotIn(self.host, body['hosts'])

    @test.idempotent_id('7f6a1cc5-2446-4cdb-9baa-b6ae0a919b72')
    def test_aggregate_add_host_list(self):
        # Add a host to the given aggregate and list.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = (self.client.create_aggregate(name=aggregate_name)
                     ['aggregate'])
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])
        self.client.add_host(aggregate['id'], host=self.host)
        self.addCleanup(self.client.remove_host, aggregate['id'],
                        host=self.host)

        aggregates = self.client.list_aggregates()['aggregates']
        aggs = [agg for agg in aggregates if agg['id'] == aggregate['id']]
        self.assertEqual(1, len(aggs))
        agg = aggs[0]
        self.assertEqual(aggregate_name, agg['name'])
        self.assertIsNone(agg['availability_zone'])
        self.assertIn(self.host, agg['hosts'])

    @test.idempotent_id('eeef473c-7c52-494d-9f09-2ed7fc8fc036')
    def test_aggregate_add_host_get_details(self):
        # Add a host to the given aggregate and get details.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = (self.client.create_aggregate(name=aggregate_name)
                     ['aggregate'])
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])
        self.client.add_host(aggregate['id'], host=self.host)
        self.addCleanup(self.client.remove_host, aggregate['id'],
                        host=self.host)

        body = self.client.show_aggregate(aggregate['id'])['aggregate']
        self.assertEqual(aggregate_name, body['name'])
        self.assertIsNone(body['availability_zone'])
        self.assertIn(self.host, body['hosts'])

    @test.idempotent_id('96be03c7-570d-409c-90f8-e4db3c646996')
    def test_aggregate_add_host_create_server_with_az(self):
        # Add a host to the given aggregate and create a server.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        az_name = data_utils.rand_name(self.az_name_prefix)
        aggregate = self.client.create_aggregate(
            name=aggregate_name, availability_zone=az_name)['aggregate']
        self.addCleanup(self.client.delete_aggregate, aggregate['id'])
        self.client.add_host(aggregate['id'], host=self.host)
        self.addCleanup(self.client.remove_host, aggregate['id'],
                        host=self.host)
        server_name = data_utils.rand_name('test_server')
        admin_servers_client = self.os_adm.servers_client
        server = self.create_test_server(name=server_name,
                                         availability_zone=az_name,
                                         wait_until='ACTIVE')
        body = admin_servers_client.show_server(server['id'])['server']
        self.assertEqual(self.host, body[self._host_key])
