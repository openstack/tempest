# Copyright 2012 OpenStack Foundation
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

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class DeleteServersV3Test(base.BaseV3ComputeTest):
    # NOTE: Server creations of each test class should be under 10
    # for preventing "Quota exceeded for instances".
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(DeleteServersV3Test, cls).setUpClass()
        cls.client = cls.servers_client

    @test.attr(type='gate')
    def test_delete_server_while_in_building_state(self):
        # Delete a server while it's VM state is Building
        resp, server = self.create_test_server(wait_until='BUILD')
        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='gate')
    def test_delete_active_server(self):
        # Delete a server while it's VM state is Active
        resp, server = self.create_test_server(wait_until='ACTIVE')
        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='gate')
    def test_delete_server_while_in_shutoff_state(self):
        # Delete a server while it's VM state is Shutoff
        resp, server = self.create_test_server(wait_until='ACTIVE')
        resp, body = self.client.stop(server['id'])
        self.client.wait_for_server_status(server['id'], 'SHUTOFF')
        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='gate')
    def test_delete_server_while_in_pause_state(self):
        # Delete a server while it's VM state is Pause
        resp, server = self.create_test_server(wait_until='ACTIVE')
        resp, body = self.client.pause_server(server['id'])
        self.client.wait_for_server_status(server['id'], 'PAUSED')
        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='gate')
    def test_delete_server_while_in_shelved_state(self):
        # Delete a server while it's VM state is Shelved
        resp, server = self.create_test_server(wait_until='ACTIVE')
        resp, body = self.client.shelve_server(server['id'])
        self.assertEqual(202, resp.status)

        offload_time = CONF.compute.shelved_offload_time
        if offload_time >= 0:
            self.client.wait_for_server_status(server['id'],
                                               'SHELVED_OFFLOADED',
                                               extra_timeout=offload_time)
        else:
            self.client.wait_for_server_status(server['id'],
                                               'SHELVED')

        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])
