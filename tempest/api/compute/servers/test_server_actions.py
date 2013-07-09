# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import base64
import time

import testtools

from tempest.api import compute
from tempest.api.compute import base
from tempest.common.utils.data_utils import rand_name
from tempest.common.utils.linux.remote_client import RemoteClient
import tempest.config
from tempest import exceptions
from tempest.test import attr


class ServerActionsTestJSON(base.BaseComputeTest):
    _interface = 'json'
    resize_available = tempest.config.TempestConfig().compute.resize_available
    run_ssh = tempest.config.TempestConfig().compute.run_ssh

    def setUp(self):
        #NOTE(afazekas): Normally we use the same server with all test cases,
        # but if it has an issue, we build a new one
        super(ServerActionsTestJSON, self).setUp()
        # Check if the server is in a clean state after test
        try:
            self.client.wait_for_server_status(self.server_id, 'ACTIVE')
        except Exception:
            # Rebuild server if something happened to it during a test
            self.rebuild_servers()

    @classmethod
    def setUpClass(cls):
        super(ServerActionsTestJSON, cls).setUpClass()
        cls.client = cls.servers_client
        cls.rebuild_servers()

    @testtools.skipUnless(compute.CHANGE_PASSWORD_AVAILABLE,
                          'Change password not available.')
    @attr(type='gate')
    def test_change_server_password(self):
        # The server's password should be set to the provided password
        new_password = 'Newpass1234'
        resp, body = self.client.change_password(self.server_id, new_password)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        if self.run_ssh:
            # Verify that the user can authenticate with the new password
            resp, server = self.client.get_server(self.server_id)
            linux_client = RemoteClient(server, self.ssh_user, new_password)
            self.assertTrue(linux_client.can_authenticate())

    @attr(type='smoke')
    def test_reboot_server_hard(self):
        # The server should be power cycled
        if self.run_ssh:
            # Get the time the server was last rebooted,
            resp, server = self.client.get_server(self.server_id)
            linux_client = RemoteClient(server, self.ssh_user, self.password)
            boot_time = linux_client.get_boot_time()

        resp, body = self.client.reboot(self.server_id, 'HARD')
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        if self.run_ssh:
            # Log in and verify the boot time has changed
            linux_client = RemoteClient(server, self.ssh_user, self.password)
            new_boot_time = linux_client.get_boot_time()
            self.assertGreater(new_boot_time, boot_time)

    @testtools.skip('Until Bug #1014647 is dealt with.')
    @attr(type='smoke')
    def test_reboot_server_soft(self):
        # The server should be signaled to reboot gracefully
        if self.run_ssh:
            # Get the time the server was last rebooted,
            resp, server = self.client.get_server(self.server_id)
            linux_client = RemoteClient(server, self.ssh_user, self.password)
            boot_time = linux_client.get_boot_time()

        resp, body = self.client.reboot(self.server_id, 'SOFT')
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        if self.run_ssh:
            # Log in and verify the boot time has changed
            linux_client = RemoteClient(server, self.ssh_user, self.password)
            new_boot_time = linux_client.get_boot_time()
            self.assertGreater(new_boot_time, boot_time)

    @attr(type='smoke')
    def test_rebuild_server(self):
        # The server should be rebuilt using the provided image and data
        meta = {'rebuild': 'server'}
        new_name = rand_name('server')
        file_contents = 'Test server rebuild.'
        personality = [{'path': '/etc/rebuild.txt',
                       'contents': base64.b64encode(file_contents)}]
        password = 'rebuildPassw0rd'
        resp, rebuilt_server = self.client.rebuild(self.server_id,
                                                   self.image_ref_alt,
                                                   name=new_name, meta=meta,
                                                   personality=personality,
                                                   adminPass=password)

        #Verify the properties in the initial response are correct
        self.assertEqual(self.server_id, rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertTrue(self.image_ref_alt.endswith(rebuilt_image_id))
        self.assertEqual(self.flavor_ref, int(rebuilt_server['flavor']['id']))

        #Verify the server properties after the rebuild completes
        self.client.wait_for_server_status(rebuilt_server['id'], 'ACTIVE')
        resp, server = self.client.get_server(rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertTrue(self.image_ref_alt.endswith(rebuilt_image_id))
        self.assertEqual(new_name, rebuilt_server['name'])

        if self.run_ssh:
            # Verify that the user can authenticate with the provided password
            linux_client = RemoteClient(server, self.ssh_user, password)
            self.assertTrue(linux_client.can_authenticate())

    def _detect_server_image_flavor(self, server_id):
        # Detects the current server image flavor ref.
        resp, server = self.client.get_server(self.server_id)
        current_flavor = server['flavor']['id']
        new_flavor_ref = self.flavor_ref_alt \
            if int(current_flavor) == self.flavor_ref else self.flavor_ref
        return int(current_flavor), int(new_flavor_ref)

    @testtools.skipIf(not resize_available, 'Resize not available.')
    @attr(type='smoke')
    def test_resize_server_confirm(self):
        # The server's RAM and disk space should be modified to that of
        # the provided flavor

        previous_flavor_ref, new_flavor_ref = \
            self._detect_server_image_flavor(self.server_id)

        resp, server = self.client.resize(self.server_id, new_flavor_ref)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        self.client.confirm_resize(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        resp, server = self.client.get_server(self.server_id)
        self.assertEqual(new_flavor_ref, int(server['flavor']['id']))

    @testtools.skipIf(not resize_available, 'Resize not available.')
    @attr(type='gate')
    def test_resize_server_revert(self):
        # The server's RAM and disk space should return to its original
        # values after a resize is reverted

        previous_flavor_ref, new_flavor_ref = \
            self._detect_server_image_flavor(self.server_id)

        resp, server = self.client.resize(self.server_id, new_flavor_ref)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        self.client.revert_resize(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        # Need to poll for the id change until lp#924371 is fixed
        resp, server = self.client.get_server(self.server_id)
        start = int(time.time())

        while int(server['flavor']['id']) != previous_flavor_ref:
            time.sleep(self.build_interval)
            resp, server = self.client.get_server(self.server_id)

            if int(time.time()) - start >= self.build_timeout:
                message = 'Server %s failed to revert resize within the \
                required time (%s s).' % (self.server_id, self.build_timeout)
                raise exceptions.TimeoutException(message)

    @attr(type=['negative', 'gate'])
    def test_reboot_nonexistent_server_soft(self):
        # Negative Test: The server reboot on non existent server should return
        # an error
        self.assertRaises(exceptions.NotFound, self.client.reboot, 999, 'SOFT')

    @attr(type=['negative', 'gate'])
    def test_rebuild_nonexistent_server(self):
        # Negative test: The server rebuild for a non existing server
        # should not be allowed
        meta = {'rebuild': 'server'}
        new_name = rand_name('server')
        file_contents = 'Test server rebuild.'
        personality = [{'path': '/etc/rebuild.txt',
                        'contents': base64.b64encode(file_contents)}]
        self.assertRaises(exceptions.NotFound,
                          self.client.rebuild,
                          999, self.image_ref_alt,
                          name=new_name, meta=meta,
                          personality=personality,
                          adminPass='rebuild')

    @attr(type='gate')
    def test_get_console_output(self):
        # Positive test:Should be able to GET the console output
        # for a given server_id and number of lines
        def get_output():
            resp, output = self.servers_client.get_console_output(
                self.server_id, 10)
            self.assertEqual(200, resp.status)
            self.assertNotEqual(output, None)
            lines = len(output.split('\n'))
            self.assertEqual(lines, 10)
        self.wait_for(get_output)

    @attr(type=['negative', 'gate'])
    def test_get_console_output_invalid_server_id(self):
        # Negative test: Should not be able to get the console output
        # for an invalid server_id
        self.assertRaises(exceptions.NotFound,
                          self.servers_client.get_console_output,
                          '!@#$%^&*()', 10)

    @testtools.skip('Until tempest Bug #1014683 is fixed.')
    @attr(type='gate')
    def test_get_console_output_server_id_in_reboot_status(self):
        # Positive test:Should be able to GET the console output
        # for a given server_id in reboot status
        resp, output = self.servers_client.reboot(self.server_id, 'SOFT')
        self.servers_client.wait_for_server_status(self.server_id,
                                                   'REBOOT')
        resp, output = self.servers_client.get_console_output(self.server_id,
                                                              10)
        self.assertEqual(200, resp.status)
        self.assertNotEqual(output, None)
        lines = len(output.split('\n'))
        self.assertEqual(lines, 10)

    @attr(type='gate')
    def test_pause_unpause_server(self):
        resp, server = self.client.pause_server(self.server_id)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'PAUSED')
        resp, server = self.client.unpause_server(self.server_id)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    @attr(type='gate')
    def test_suspend_resume_server(self):
        resp, server = self.client.suspend_server(self.server_id)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'SUSPENDED')
        resp, server = self.client.resume_server(self.server_id)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    @classmethod
    def rebuild_servers(cls):
        # Destroy any existing server and creates a new one
        cls.clear_servers()
        resp, server = cls.create_server(wait_until='ACTIVE')
        cls.server_id = server['id']
        cls.password = server['adminPass']


class ServerActionsTestXML(ServerActionsTestJSON):
    _interface = 'xml'
