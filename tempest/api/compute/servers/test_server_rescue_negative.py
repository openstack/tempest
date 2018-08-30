# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright 2014 NEC Corporation.  All rights reserved.
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
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class ServerRescueNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(ServerRescueNegativeTestJSON, cls).skip_checks()
        if not CONF.compute_feature_enabled.rescue:
            msg = "Server rescue not available."
            raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources(network=True, subnet=True, router=True)
        super(ServerRescueNegativeTestJSON, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(ServerRescueNegativeTestJSON, cls).resource_setup()
        cls.password = data_utils.rand_password()
        rescue_password = data_utils.rand_password()
        # Server for negative tests
        server = cls.create_test_server(adminPass=cls.password,
                                        wait_until='BUILD')
        resc_server = cls.create_test_server(adminPass=rescue_password,
                                             wait_until='ACTIVE')
        cls.server_id = server['id']
        cls.rescue_id = resc_server['id']

        cls.servers_client.rescue_server(
            cls.rescue_id, adminPass=rescue_password)
        waiters.wait_for_server_status(cls.servers_client,
                                       cls.rescue_id, 'RESCUE')
        waiters.wait_for_server_status(cls.servers_client,
                                       cls.server_id, 'ACTIVE')

    def _unrescue(self, server_id):
        self.servers_client.unrescue_server(server_id)
        waiters.wait_for_server_status(self.servers_client,
                                       server_id, 'ACTIVE')

    def _unpause(self, server_id):
        self.servers_client.unpause_server(server_id)
        waiters.wait_for_server_status(self.servers_client,
                                       server_id, 'ACTIVE')

    @decorators.idempotent_id('cc3a883f-43c0-4fb6-a9bb-5579d64984ed')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @decorators.attr(type=['negative'])
    def test_rescue_paused_instance(self):
        # Rescue a paused server
        self.servers_client.pause_server(self.server_id)
        self.addCleanup(self._unpause, self.server_id)
        waiters.wait_for_server_status(self.servers_client,
                                       self.server_id, 'PAUSED')
        self.assertRaises(lib_exc.Conflict,
                          self.servers_client.rescue_server,
                          self.server_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('db22b618-f157-4566-a317-1b6d467a8094')
    def test_rescued_vm_reboot(self):
        self.assertRaises(lib_exc.Conflict, self.servers_client.reboot_server,
                          self.rescue_id, type='HARD')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('6dfc0a55-3a77-4564-a144-1587b7971dde')
    def test_rescue_non_existent_server(self):
        # Rescue a non-existing server
        non_existent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.servers_client.rescue_server,
                          non_existent_server)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('70cdb8a1-89f8-437d-9448-8844fd82bf46')
    def test_rescued_vm_rebuild(self):
        self.assertRaises(lib_exc.Conflict,
                          self.servers_client.rebuild_server,
                          self.rescue_id,
                          self.image_ref_alt)

    @decorators.idempotent_id('d0ccac79-0091-4cf4-a1ce-26162d0cc55f')
    @utils.services('volume')
    @decorators.attr(type=['negative'])
    def test_rescued_vm_attach_volume(self):
        volume = self.create_volume()

        # Rescue the server
        self.servers_client.rescue_server(self.server_id,
                                          adminPass=self.password)
        waiters.wait_for_server_status(self.servers_client,
                                       self.server_id, 'RESCUE')
        self.addCleanup(self._unrescue, self.server_id)

        # Attach the volume to the server
        self.assertRaises(lib_exc.Conflict,
                          self.servers_client.attach_volume,
                          self.server_id,
                          volumeId=volume['id'])

    @decorators.idempotent_id('f56e465b-fe10-48bf-b75d-646cda3a8bc9')
    @utils.services('volume')
    @decorators.attr(type=['negative'])
    def test_rescued_vm_detach_volume(self):
        volume = self.create_volume()

        # Attach the volume to the server
        server = self.servers_client.show_server(self.server_id)['server']
        self.attach_volume(server, volume)

        # Rescue the server
        self.servers_client.rescue_server(self.server_id,
                                          adminPass=self.password)
        waiters.wait_for_server_status(self.servers_client,
                                       self.server_id, 'RESCUE')
        # addCleanup is a LIFO queue
        self.addCleanup(self._unrescue, self.server_id)

        # Detach the volume from the server expecting failure
        self.assertRaises(lib_exc.Conflict,
                          self.servers_client.detach_volume,
                          self.server_id,
                          volume['id'])
