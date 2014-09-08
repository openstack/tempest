# Copyright 2013 NEC Corporation
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

from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest import test

CONF = config.CONF


LOG = logging.getLogger(__name__)


class TestLargeOpsScenario(manager.ScenarioTest):

    """
    Test large operations.

    This test below:
    * Spin up multiple instances in one nova call, and repeat three times
    * as a regular user
    * TODO: same thing for cinder

    """

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(TestLargeOpsScenario, cls).setUpClass()

    def _wait_for_server_status(self, status):
        for server in self.servers:
            self.servers_client.wait_for_server_status(server['id'], status)

    def nova_boot(self):
        name = data_utils.rand_name('scenario-server-')
        flavor_id = CONF.compute.flavor_ref
        secgroup = self._create_security_group()
        self.servers_client.create_server(
            name,
            self.image,
            flavor_id,
            min_count=CONF.scenario.large_ops_number,
            security_groups=[secgroup])
        # needed because of bug 1199788
        params = {'name': name}
        _, server_list = self.servers_client.list_servers(params)
        self.servers = server_list['servers']
        for server in self.servers:
            # after deleting all servers - wait for all servers to clear
            # before cleanup continues
            self.addCleanup(self.servers_client.wait_for_server_termination,
                            server['id'])
        for server in self.servers:
            self.addCleanup_with_wait(
                waiter_callable=(self.servers_client.
                                 wait_for_server_termination),
                thing_id=server['id'], thing_id_param='server_id',
                cleanup_callable=self.delete_wrapper,
                cleanup_args=[self.servers_client.delete_server, server['id']])
        self._wait_for_server_status('ACTIVE')

    def _large_ops_scenario(self):
        if CONF.scenario.large_ops_number < 1:
            return
        self.glance_image_create()
        self.nova_boot()

    @test.services('compute', 'image')
    def test_large_ops_scenario_1(self):
        self._large_ops_scenario()

    @test.services('compute', 'image')
    def test_large_ops_scenario_2(self):
        self._large_ops_scenario()

    @test.services('compute', 'image')
    def test_large_ops_scenario_3(self):
        self._large_ops_scenario()
