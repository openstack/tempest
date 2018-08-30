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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators

CONF = config.CONF


class AggregatesAdminTestBase(base.BaseV2ComputeAdminTest):
    """Tests Aggregates API that require admin privileges"""

    @classmethod
    def setup_clients(cls):
        super(AggregatesAdminTestBase, cls).setup_clients()
        cls.client = cls.os_admin.aggregates_client

    @classmethod
    def resource_setup(cls):
        super(AggregatesAdminTestBase, cls).resource_setup()
        cls.aggregate_name_prefix = 'test_aggregate'
        cls.az_name_prefix = 'test_az'

        cls.host = None
        hypers = cls.os_admin.hypervisor_client.list_hypervisors(
            detail=True)['hypervisors']

        if CONF.compute.hypervisor_type:
            hypers = [hyper for hyper in hypers
                      if (hyper['hypervisor_type'] ==
                          CONF.compute.hypervisor_type)]

        cls.hosts_available = [hyper['service']['host'] for hyper in hypers
                               if (hyper['state'] == 'up' and
                                   hyper['status'] == 'enabled')]
        if cls.hosts_available:
            cls.host = cls.hosts_available[0]
        else:
            msg = "no available compute node found"
            if CONF.compute.hypervisor_type:
                msg += " for hypervisor_type %s" % CONF.compute.hypervisor_type
            raise testtools.TestCase.failureException(msg)

    def _create_test_aggregate(self, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = self.client.create_aggregate(**kwargs)['aggregate']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.client.delete_aggregate, aggregate['id'])
        self.assertEqual(kwargs['name'], aggregate['name'])

        return aggregate


class AggregatesAdminTestJSON(AggregatesAdminTestBase):

    @decorators.idempotent_id('0d148aa3-d54c-4317-aa8d-42040a475e20')
    def test_aggregate_create_delete(self):
        # Create and delete an aggregate.
        aggregate = self._create_test_aggregate()
        self.assertIsNone(aggregate['availability_zone'])

        self.client.delete_aggregate(aggregate['id'])
        self.client.wait_for_resource_deletion(aggregate['id'])

    @decorators.idempotent_id('5873a6f8-671a-43ff-8838-7ce430bb6d0b')
    def test_aggregate_create_delete_with_az(self):
        # Create and delete an aggregate.
        az_name = data_utils.rand_name(self.az_name_prefix)
        aggregate = self._create_test_aggregate(availability_zone=az_name)
        self.assertEqual(az_name, aggregate['availability_zone'])

        self.client.delete_aggregate(aggregate['id'])
        self.client.wait_for_resource_deletion(aggregate['id'])

    @decorators.idempotent_id('68089c38-04b1-4758-bdf0-cf0daec4defd')
    def test_aggregate_create_verify_entry_in_list(self):
        # Create an aggregate and ensure it is listed.
        aggregate = self._create_test_aggregate()
        aggregates = self.client.list_aggregates()['aggregates']
        self.assertIn((aggregate['id'], aggregate['availability_zone']),
                      map(lambda x: (x['id'], x['availability_zone']),
                          aggregates))

    @decorators.idempotent_id('36ec92ca-7a73-43bc-b920-7531809e8540')
    def test_aggregate_create_update_metadata_get_details(self):
        # Create an aggregate and ensure its details are returned.
        aggregate = self._create_test_aggregate()
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

    @decorators.idempotent_id('4d2b2004-40fa-40a1-aab2-66f4dab81beb')
    def test_aggregate_create_update_with_az(self):
        # Update an aggregate and ensure properties are updated correctly
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        az_name = data_utils.rand_name(self.az_name_prefix)
        aggregate = self._create_test_aggregate(
            name=aggregate_name, availability_zone=az_name)

        self.assertEqual(az_name, aggregate['availability_zone'])

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

    @decorators.idempotent_id('c8e85064-e79b-4906-9931-c11c24294d02')
    def test_aggregate_add_remove_host(self):
        # Add a host to the given aggregate and remove.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = self._create_test_aggregate(name=aggregate_name)

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

    @decorators.idempotent_id('7f6a1cc5-2446-4cdb-9baa-b6ae0a919b72')
    def test_aggregate_add_host_list(self):
        # Add a host to the given aggregate and list.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = self._create_test_aggregate(name=aggregate_name)

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

    @decorators.idempotent_id('eeef473c-7c52-494d-9f09-2ed7fc8fc036')
    def test_aggregate_add_host_get_details(self):
        # Add a host to the given aggregate and get details.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        aggregate = self._create_test_aggregate(name=aggregate_name)

        self.client.add_host(aggregate['id'], host=self.host)
        self.addCleanup(self.client.remove_host, aggregate['id'],
                        host=self.host)

        body = self.client.show_aggregate(aggregate['id'])['aggregate']
        self.assertEqual(aggregate_name, body['name'])
        self.assertIsNone(body['availability_zone'])
        self.assertIn(self.host, body['hosts'])

    @decorators.idempotent_id('96be03c7-570d-409c-90f8-e4db3c646996')
    def test_aggregate_add_host_create_server_with_az(self):
        # Add a host to the given aggregate and create a server.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        az_name = data_utils.rand_name(self.az_name_prefix)
        aggregate = self._create_test_aggregate(availability_zone=az_name)

        # Find a host that has not been added to other availability zone,
        # for one host can't be added to different availability zones.
        aggregates = self.client.list_aggregates()['aggregates']
        hosts_in_zone = []
        for agg in aggregates:
            if agg['availability_zone']:
                hosts_in_zone.extend(agg['hosts'])
        hosts = [v for v in self.hosts_available if v not in hosts_in_zone]
        if not hosts:
            raise self.skipException("All hosts are already in other "
                                     "availability zones, so can't add "
                                     "host to aggregate. \nAggregates list: "
                                     "%s" % aggregates)
        host = hosts[0]

        self.client.add_host(aggregate['id'], host=host)
        self.addCleanup(self.client.remove_host, aggregate['id'], host=host)
        server = self.create_test_server(availability_zone=az_name,
                                         wait_until='ACTIVE')
        server_host = self.get_host_for_server(server['id'])
        self.assertEqual(host, server_host)


class AggregatesAdminTestV241(AggregatesAdminTestBase):
    min_microversion = '2.41'

    # NOTE(gmann): This test tests the Aggregate APIs response schema
    # for 2.41 microversion. No specific assert or behaviour verification
    # is needed.

    @decorators.idempotent_id('fdf24d9e-8afa-4700-b6aa-9c498351504f')
    def test_create_update_show_aggregate_add_remove_host(self):
        # Update and add a host to the given aggregate and get details.
        self.useFixture(fixtures.LockFixture('availability_zone'))
        # Checking create aggregate API response schema
        aggregate = self._create_test_aggregate()

        new_aggregate_name = data_utils.rand_name(self.aggregate_name_prefix)
        # Checking update aggregate API response schema
        self.client.update_aggregate(aggregate['id'], name=new_aggregate_name)
        # Checking show aggregate API response schema
        self.client.show_aggregate(aggregate['id'])['aggregate']
        # Checking add host to aggregate API response schema
        self.client.add_host(aggregate['id'], host=self.host)
        # Checking rempve host from aggregate API response schema
        self.client.remove_host(aggregate['id'], host=self.host)
