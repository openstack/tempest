# Copyright 2012 OpenStack Foundation
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

from tempest.common import utils
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions
from tempest.scenario import manager

CONF = config.CONF


class TestServerMultinode(manager.ScenarioTest):
    """This is a set of tests specific to multinode testing."""
    credentials = ['primary', 'admin']

    @classmethod
    def skip_checks(cls):
        super(TestServerMultinode, cls).skip_checks()

        if CONF.compute.min_compute_nodes < 2:
            raise cls.skipException(
                "Less than 2 compute nodes, skipping multinode tests.")

    @decorators.idempotent_id('9cecbe35-b9d4-48da-a37e-7ce70aa43d30')
    @decorators.attr(type='smoke')
    @utils.services('compute', 'network')
    def test_schedule_to_all_nodes(self):
        available_zone = \
            self.os_admin.availability_zone_client.list_availability_zones(
                detail=True)['availabilityZoneInfo']
        hosts = []
        for zone in available_zone:
            if zone['zoneState']['available']:
                for host in zone['hosts']:
                    if 'nova-compute' in zone['hosts'][host] and \
                        zone['hosts'][host]['nova-compute']['available']:
                        hosts.append({'zone': zone['zoneName'],
                                      'host_name': host})

        # ensure we have at least as many compute hosts as we expect
        if len(hosts) < CONF.compute.min_compute_nodes:
            raise exceptions.InvalidConfiguration(
                "Host list %s is shorter than min_compute_nodes. "
                "Did a compute worker not boot correctly?" % hosts)

        # create 1 compute for each node, up to the min_compute_nodes
        # threshold (so that things don't get crazy if you have 1000
        # compute nodes but set min to 3).
        servers = []

        for host in hosts[:CONF.compute.min_compute_nodes]:
            # by getting to active state here, this means this has
            # landed on the host in question.
            # in order to use the availability_zone:host scheduler hint,
            # admin client is need here.
            inst = self.create_server(
                clients=self.os_admin,
                availability_zone='%(zone)s:%(host_name)s' % host)
            server = self.os_admin.servers_client.show_server(
                inst['id'])['server']
            # ensure server is located on the requested host
            self.assertEqual(host['host_name'], server['OS-EXT-SRV-ATTR:host'])
            servers.append(server)

        # make sure we really have the number of servers we think we should
        self.assertEqual(
            len(servers), CONF.compute.min_compute_nodes,
            "Incorrect number of servers built %s" % servers)

        # ensure that every server ended up on a different host
        host_ids = [x['hostId'] for x in servers]
        self.assertEqual(
            len(set(host_ids)), len(servers),
            "Incorrect number of distinct host_ids scheduled to %s" % servers)
