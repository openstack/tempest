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


from tempest import config
from tempest import exceptions
from tempest.scenario import manager
from tempest import test

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

    @classmethod
    def setup_clients(cls):
        super(TestServerMultinode, cls).setup_clients()
        # Use admin client by default
        cls.manager = cls.admin_manager
        # this is needed so that we can use the availability_zone:host
        # scheduler hint, which is admin_only by default
        cls.servers_client = cls.admin_manager.servers_client
        super(TestServerMultinode, cls).resource_setup()

    @test.idempotent_id('9cecbe35-b9d4-48da-a37e-7ce70aa43d30')
    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_schedule_to_all_nodes(self):
        host_client = self.manager.hosts_client
        hosts = host_client.list_hosts()['hosts']
        hosts = [x for x in hosts if x['service'] == 'compute']

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
            inst = self.create_server(
                availability_zone='%(zone)s:%(host_name)s' % host,
                wait_until='ACTIVE')
            server = self.servers_client.show_server(inst['id'])['server']
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
