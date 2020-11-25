# Copyright 2013 IBM Corp.
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

from tempest.common import tempest_fixtures as fixtures
from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.scenario import manager


class TestAggregatesBasicOps(manager.ScenarioTest):
    """Creates an aggregate within an availability zone

    Adds a host to the aggregate
    Checks aggregate details
    Updates aggregate's name
    Removes host from aggregate
    Deletes aggregate
    """

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(TestAggregatesBasicOps, cls).setup_clients()
        # Use admin client by default
        cls.aggregates_client = cls.os_admin.aggregates_client
        cls.services_client = cls.os_admin.services_client

    def _create_aggregate(self, **kwargs):
        aggregate = (self.aggregates_client.create_aggregate(**kwargs)
                     ['aggregate'])
        self.addCleanup(self.aggregates_client.delete_aggregate,
                        aggregate['id'])
        aggregate_name = kwargs['name']
        availability_zone = kwargs['availability_zone']
        self.assertEqual(aggregate['name'], aggregate_name)
        self.assertEqual(aggregate['availability_zone'], availability_zone)
        return aggregate

    def _get_host_name(self):
        # Find a host that has not been added to other availability zone,
        # for one host can't be added to different availability zones.
        svc_list = self.services_client.list_services(
            binary='nova-compute')['services']
        self.assertNotEmpty(svc_list)
        hosts_available = []
        for host in svc_list:
            if (host['state'] == 'up' and host['status'] == 'enabled'):
                hosts_available.append(host['host'])
        aggregates = self.aggregates_client.list_aggregates()['aggregates']
        hosts_in_zone = []
        for agg in aggregates:
            if agg['availability_zone']:
                hosts_in_zone.extend(agg['hosts'])
        hosts = [v for v in hosts_available if v not in hosts_in_zone]
        if not hosts:
            raise self.skipException("All hosts are already in other "
                                     "availability zones, so can't add "
                                     "host to aggregate. \nAggregates list: "
                                     "%s" % aggregates)
        return hosts[0]

    def _add_host(self, aggregate_id, host):
        aggregate = (self.aggregates_client.add_host(aggregate_id, host=host)
                     ['aggregate'])
        self.addCleanup(self._remove_host, aggregate['id'], host)
        self.assertIn(host, aggregate['hosts'])

    def _remove_host(self, aggregate_id, host):
        aggregate = self.aggregates_client.remove_host(aggregate_id, host=host)
        self.assertNotIn(host, aggregate['aggregate']['hosts'])

    def _check_aggregate_details(self, aggregate, aggregate_name, azone,
                                 hosts, metadata):
        aggregate = (self.aggregates_client.show_aggregate(aggregate['id'])
                     ['aggregate'])
        self.assertEqual(aggregate_name, aggregate['name'])
        self.assertEqual(azone, aggregate['availability_zone'])
        self.assertEqual(hosts, aggregate['hosts'])
        for meta_key in metadata:
            self.assertIn(meta_key, aggregate['metadata'])
            self.assertEqual(metadata[meta_key],
                             aggregate['metadata'][meta_key])

    def _set_aggregate_metadata(self, aggregate, meta):
        aggregate = self.aggregates_client.set_metadata(aggregate['id'],
                                                        metadata=meta)

        for key in meta.keys():
            self.assertEqual(meta[key],
                             aggregate['aggregate']['metadata'][key])

    def _update_aggregate(self, aggregate, aggregate_name,
                          availability_zone):
        aggregate = self.aggregates_client.update_aggregate(
            aggregate['id'], name=aggregate_name,
            availability_zone=availability_zone)['aggregate']
        self.assertEqual(aggregate['name'], aggregate_name)
        self.assertEqual(aggregate['availability_zone'], availability_zone)
        return aggregate

    @decorators.idempotent_id('cb2b4c4f-0c7c-4164-bdde-6285b302a081')
    @decorators.attr(type='slow')
    @utils.services('compute')
    def test_aggregate_basic_ops(self):
        self.useFixture(fixtures.LockFixture('availability_zone'))
        az = 'foo_zone'
        aggregate_name = data_utils.rand_name('aggregate-scenario')
        aggregate = self._create_aggregate(name=aggregate_name,
                                           availability_zone=az)

        metadata = {'meta_key': 'meta_value'}
        self._set_aggregate_metadata(aggregate, metadata)

        host = self._get_host_name()
        self._add_host(aggregate['id'], host)
        self._check_aggregate_details(aggregate, aggregate_name, az, [host],
                                      metadata)

        aggregate_name = data_utils.rand_name('renamed-aggregate-scenario')
        # Updating the name alone. The az must be specified again otherwise
        # the tempest client would send None in the put body
        aggregate = self._update_aggregate(aggregate, aggregate_name, az)

        new_metadata = {'foo': 'bar'}
        self._set_aggregate_metadata(aggregate, new_metadata)

        self._check_aggregate_details(aggregate, aggregate['name'], az,
                                      [host], new_metadata)
