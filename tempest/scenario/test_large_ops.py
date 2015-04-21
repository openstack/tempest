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

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest import config
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
    def skip_checks(cls):
        super(TestLargeOpsScenario, cls).skip_checks()
        if CONF.scenario.large_ops_number < 1:
            raise cls.skipException("large_ops_number not set to multiple "
                                    "instances")

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(TestLargeOpsScenario, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(TestLargeOpsScenario, cls).resource_setup()
        # list of cleanup calls to be executed in reverse order
        cls._cleanup_resources = []

    @classmethod
    def resource_cleanup(cls):
        while cls._cleanup_resources:
            function, args, kwargs = cls._cleanup_resources.pop(-1)
            try:
                function(*args, **kwargs)
            except lib_exc.NotFound:
                pass
        super(TestLargeOpsScenario, cls).resource_cleanup()

    @classmethod
    def addCleanupClass(cls, function, *arguments, **keywordArguments):
        cls._cleanup_resources.append((function, arguments, keywordArguments))

    def _wait_for_server_status(self, status):
        for server in self.servers:
            # Make sure nova list keeps working throughout the build process
            self.servers_client.list_servers()
            self.servers_client.wait_for_server_status(server['id'], status)

    def nova_boot(self):
        name = data_utils.rand_name('scenario-server')
        flavor_id = CONF.compute.flavor_ref
        # Explicitly create secgroup to avoid cleanup at the end of testcases.
        # Since no traffic is tested, we don't need to actually add rules to
        # secgroup
        secgroup = self.security_groups_client.create_security_group(
            'secgroup-%s' % name, 'secgroup-desc-%s' % name)
        self.addCleanupClass(self.security_groups_client.delete_security_group,
                             secgroup['id'])

        self.servers_client.create_server(
            name,
            self.image,
            flavor_id,
            min_count=CONF.scenario.large_ops_number,
            security_groups=[{'name': secgroup['name']}])
        # needed because of bug 1199788
        params = {'name': name}
        server_list = self.servers_client.list_servers(params)
        self.servers = server_list['servers']
        for server in self.servers:
            # after deleting all servers - wait for all servers to clear
            # before cleanup continues
            self.addCleanupClass(self.servers_client.
                                 wait_for_server_termination,
                                 server['id'])
        for server in self.servers:
            self.addCleanupClass(self.servers_client.delete_server,
                                 server['id'])
        self._wait_for_server_status('ACTIVE')

    def _large_ops_scenario(self):
        self.glance_image_create()
        self.nova_boot()

    @test.idempotent_id('14ba0e78-2ed9-4d17-9659-a48f4756ecb3')
    @test.services('compute', 'image')
    def test_large_ops_scenario_1(self):
        self._large_ops_scenario()

    @test.idempotent_id('b9b79b88-32aa-42db-8f8f-dcc8f4b4ccfe')
    @test.services('compute', 'image')
    def test_large_ops_scenario_2(self):
        self._large_ops_scenario()

    @test.idempotent_id('3aab7e82-2de3-419a-9da1-9f3a070668fb')
    @test.services('compute', 'image')
    def test_large_ops_scenario_3(self):
        self._large_ops_scenario()
