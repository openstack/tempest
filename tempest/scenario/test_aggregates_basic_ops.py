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
from tempest.common.utils import data_utils
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest import test


LOG = logging.getLogger(__name__)


class TestAggregatesBasicOps(manager.OfficialClientTest):
    """
    Creates an aggregate within an availability zone
    Adds a host to the aggregate
    Checks aggregate details
    Updates aggregate's name
    Removes host from aggregate
    Deletes aggregate
    """
    @classmethod
    def credentials(cls):
        return cls.admin_credentials()

    def _create_aggregate(self, **kwargs):
        aggregate = self.compute_client.aggregates.create(**kwargs)
        aggregate_name = kwargs['name']
        availability_zone = kwargs['availability_zone']
        self.assertEqual(aggregate.name, aggregate_name)
        self.assertEqual(aggregate.availability_zone, availability_zone)
        self.set_resource(aggregate.id, aggregate)
        LOG.debug("Aggregate %s created." % (aggregate.name))
        return aggregate

    def _delete_aggregate(self, aggregate):
        self.compute_client.aggregates.delete(aggregate.id)
        self.remove_resource(aggregate.id)
        LOG.debug("Aggregate %s deleted. " % (aggregate.name))

    def _get_host_name(self):
        hosts = self.compute_client.hosts.list()
        self.assertTrue(len(hosts) >= 1)
        hostname = hosts[0].host_name
        return hostname

    def _add_host(self, aggregate_name, host):
        aggregate = self.compute_client.aggregates.add_host(aggregate_name,
                                                            host)
        self.assertIn(host, aggregate.hosts)
        LOG.debug("Host %s added to Aggregate %s." % (host, aggregate.name))

    def _remove_host(self, aggregate_name, host):
        aggregate = self.compute_client.aggregates.remove_host(aggregate_name,
                                                               host)
        self.assertNotIn(host, aggregate.hosts)
        LOG.debug("Host %s removed to Aggregate %s." % (host, aggregate.name))

    def _check_aggregate_details(self, aggregate, aggregate_name, azone,
                                 hosts, metadata):
        aggregate = self.compute_client.aggregates.get(aggregate.id)
        self.assertEqual(aggregate_name, aggregate.name)
        self.assertEqual(azone, aggregate.availability_zone)
        self.assertEqual(aggregate.hosts, hosts)
        for meta_key in metadata.keys():
            self.assertIn(meta_key, aggregate.metadata)
            self.assertEqual(metadata[meta_key], aggregate.metadata[meta_key])
        LOG.debug("Aggregate %s details match." % aggregate.name)

    def _set_aggregate_metadata(self, aggregate, meta):
        aggregate = self.compute_client.aggregates.set_metadata(aggregate.id,
                                                                meta)

        for key, value in meta.items():
            self.assertEqual(meta[key], aggregate.metadata[key])
        LOG.debug("Aggregate %s metadata updated successfully." %
                  aggregate.name)

    def _update_aggregate(self, aggregate, aggregate_name,
                          availability_zone):
        values = {}
        if aggregate_name:
            values.update({'name': aggregate_name})
        if availability_zone:
            values.update({'availability_zone': availability_zone})
        if values.keys():
            aggregate = self.compute_client.aggregates.update(aggregate.id,
                                                              values)
            for key, values in values.items():
                self.assertEqual(getattr(aggregate, key), values)
        return aggregate

    @test.services('compute')
    def test_aggregate_basic_ops(self):
        self.useFixture(fixtures.LockFixture('availability_zone'))
        az = 'foo_zone'
        aggregate_name = data_utils.rand_name('aggregate-scenario')
        aggregate = self._create_aggregate(name=aggregate_name,
                                           availability_zone=az)

        metadata = {'meta_key': 'meta_value'}
        self._set_aggregate_metadata(aggregate, metadata)

        host = self._get_host_name()
        self._add_host(aggregate, host)
        self._check_aggregate_details(aggregate, aggregate_name, az, [host],
                                      metadata)

        aggregate_name = data_utils.rand_name('renamed-aggregate-scenario')
        aggregate = self._update_aggregate(aggregate, aggregate_name, None)

        additional_metadata = {'foo': 'bar'}
        self._set_aggregate_metadata(aggregate, additional_metadata)

        metadata.update(additional_metadata)
        self._check_aggregate_details(aggregate, aggregate.name, az, [host],
                                      metadata)

        self._remove_host(aggregate, host)
        self._delete_aggregate(aggregate)
