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
from tempest.test import services

CONF = config.CONF


LOG = logging.getLogger(__name__)


class TestLargeOpsScenario(manager.NetworkScenarioTest):

    """
    Test large operations.

    This test below:
    * Spin up multiple instances in one nova call
    * as a regular user
    * TODO: same thing for cinder

    """

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(TestLargeOpsScenario, cls).setUpClass()

    def _wait_for_server_status(self, status):
        for server in self.servers:
            self.status_timeout(
                self.compute_client.servers, server.id, status)

    def nova_boot(self):
        name = data_utils.rand_name('scenario-server-')
        client = self.compute_client
        flavor_id = CONF.compute.flavor_ref
        secgroup = self._create_security_group_nova()
        self.servers = client.servers.create(
            name=name, image=self.image,
            flavor=flavor_id,
            min_count=CONF.scenario.large_ops_number,
            security_groups=[secgroup.name])
        # needed because of bug 1199788
        self.servers = [x for x in client.servers.list() if name in x.name]
        for server in self.servers:
            self.set_resource(server.name, server)
        self._wait_for_server_status('ACTIVE')

    @services('compute', 'image')
    def test_large_ops_scenario(self):
        if CONF.scenario.large_ops_number < 1:
            return
        self.glance_image_create()
        self.nova_boot()
