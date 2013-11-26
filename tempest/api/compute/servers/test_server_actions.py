# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import base64
import time

import testtools

from tempest.api import compute
from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest.common.utils.linux.remote_client import RemoteClient
import tempest.config
from tempest import exceptions
from tempest.test import attr
from tempest.test import skip_because


class ServerActionsTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'
    resize_available = tempest.config.TempestConfig().\
        compute_feature_enabled.resize
    run_ssh = tempest.config.TempestConfig().compute.run_ssh

    def setUp(self):
        # NOTE(afazekas): Normally we use the same server with all test cases,
        # but if it has an issue, we build a new one
        super(ServerActionsTestJSON, self).setUp()
        # Check if the server is in a clean state after test
        try:
            self.client.wait_for_server_status(self.server_id, 'ACTIVE')
        except Exception:
            # Rebuild server if something happened to it during a test
            self.rebuild_server()

    @classmethod
    def setUpClass(cls):
        super(ServerActionsTestJSON, cls).setUpClass()
        cls.client = cls.servers_client
        cls.rebuild_server()

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

    @skip_because(bug="1014647")
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
        new_name = data_utils.rand_name('server')
        file_contents = 'Test server rebuild.'
        personality = [{'path': 'rebuild.txt',
                       'contents': base64.b64encode(file_contents)}]
        password = 'rebuildPassw0rd'
        resp, rebuilt_server = self.client.rebuild(self.server_id,
                                                   self.image_ref_alt,
                                                   name=new_name,
                                                   metadata=meta,
                                                   personality=personality,
                                                   adminPass=password)

        # Verify the properties in the initial response are correct
        self.assertEqual(self.server_id, rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertTrue(self.image_ref_alt.endswith(rebuilt_image_id))
        self.assertEqual(self.flavor_ref, int(rebuilt_server['flavor']['id']))

        # Verify the server properties after the rebuild completes
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

    @attr(type='gate')
    def test_create_backup(self):
        # Positive test:create backup successfully and rotate backups correctly
        # create the first and the second backup
        backup1 = data_utils.rand_name('backup')
        resp, _ = self.servers_client.create_backup(self.server_id,
                                                    'daily',
                                                    2,
                                                    backup1)
        oldest_backup_exist = True

        # the oldest one should be deleted automatically in this test
        def _clean_oldest_backup(oldest_backup):
            if oldest_backup_exist:
                self.os.image_client.delete_image(oldest_backup)

        image1_id = data_utils.parse_image_id(resp['location'])
        self.addCleanup(_clean_oldest_backup, image1_id)
        self.assertEqual(202, resp.status)

        backup2 = data_utils.rand_name('backup')
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')
        resp, _ = self.servers_client.create_backup(self.server_id,
                                                    'daily',
                                                    2,
                                                    backup2)
        image2_id = data_utils.parse_image_id(resp['location'])
        self.addCleanup(self.os.image_client.delete_image, image2_id)
        self.assertEqual(202, resp.status)

        # verify they have been created
        properties = {
            'image_type': 'backup',
            'backup_type': "daily",
            'instance_uuid': self.server_id,
        }
        resp, image_list = self.os.image_client.image_list_detail(
            properties,
            sort_key='created_at',
            sort_dir='asc')
        self.assertEqual(200, resp.status)
        self.assertEqual(2, len(image_list))
        self.assertEqual((backup1, backup2),
                         (image_list[0]['name'], image_list[1]['name']))

        # create the third one, due to the rotation is 2,
        # the first one will be deleted
        backup3 = data_utils.rand_name('backup')
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')
        resp, _ = self.servers_client.create_backup(self.server_id,
                                                    'daily',
                                                    2,
                                                    backup3)
        image3_id = data_utils.parse_image_id(resp['location'])
        self.addCleanup(self.os.image_client.delete_image, image3_id)
        self.assertEqual(202, resp.status)
        # the first back up should be deleted
        self.os.image_client.wait_for_resource_deletion(image1_id)
        oldest_backup_exist = False
        resp, image_list = self.os.image_client.image_list_detail(
            properties,
            sort_key='created_at',
            sort_dir='asc')
        self.assertEqual(200, resp.status)
        self.assertEqual(2, len(image_list))
        self.assertEqual((backup2, backup3),
                         (image_list[0]['name'], image_list[1]['name']))

    @attr(type='gate')
    def test_get_console_output(self):
        # Positive test:Should be able to GET the console output
        # for a given server_id and number of lines

        # This reboot is necessary for outputting some console log after
        # creating a instance backup. If a instance backup, the console
        # log file is truncated and we cannot get any console log through
        # "console-log" API.
        # The detail is https://bugs.launchpad.net/nova/+bug/1251920
        resp, body = self.servers_client.reboot(self.server_id, 'HARD')
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')

        def get_output():
            resp, output = self.servers_client.get_console_output(
                self.server_id, 10)
            self.assertEqual(200, resp.status)
            self.assertTrue(output, "Console output was empty.")
            lines = len(output.split('\n'))
            self.assertEqual(lines, 10)
        self.wait_for(get_output)

    @skip_because(bug="1014683")
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
        self.assertIsNotNone(output)
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

    @attr(type='gate')
    def test_shelve_unshelve_server(self):
        resp, server = self.client.shelve_server(self.server_id)
        self.assertEqual(202, resp.status)

        offload_time = self.config.compute.shelved_offload_time
        if offload_time >= 0:
            self.client.wait_for_server_status(self.server_id,
                                               'SHELVED_OFFLOADED',
                                               extra_timeout=offload_time)
        else:
            self.client.wait_for_server_status(self.server_id,
                                               'SHELVED')

        resp, server = self.client.get_server(self.server_id)
        image_name = server['name'] + '-shelved'
        params = {'name': image_name}
        resp, images = self.images_client.list_images(params)
        self.assertEqual(1, len(images))
        self.assertEqual(image_name, images[0]['name'])

        resp, server = self.client.unshelve_server(self.server_id)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    @attr(type='gate')
    def test_stop_start_server(self):
        resp, server = self.servers_client.stop(self.server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'SHUTOFF')
        resp, server = self.servers_client.start(self.server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')

    @attr(type='gate')
    def test_lock_unlock_server(self):
        # Lock the server,try server stop(exceptions throw),unlock it and retry
        resp, server = self.servers_client.lock_server(self.server_id)
        self.assertEqual(202, resp.status)
        resp, server = self.servers_client.get_server(self.server_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(server['status'], 'ACTIVE')
        # Locked server is not allowed to be stopped by non-admin user
        self.assertRaises(exceptions.Conflict,
                          self.servers_client.stop, self.server_id)
        resp, server = self.servers_client.unlock_server(self.server_id)
        self.assertEqual(202, resp.status)
        resp, server = self.servers_client.stop(self.server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'SHUTOFF')
        resp, server = self.servers_client.start(self.server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')


class ServerActionsTestXML(ServerActionsTestJSON):
    _interface = 'xml'
