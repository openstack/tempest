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
import logging
import urlparse

from tempest_lib.common.utils import data_utils
from tempest_lib import decorators
from tempest_lib import exceptions as lib_exc
import testtools

from tempest.api.compute import base
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class ServerActionsTestJSON(base.BaseV2ComputeTest):
    run_ssh = CONF.compute.run_ssh

    def setUp(self):
        # NOTE(afazekas): Normally we use the same server with all test cases,
        # but if it has an issue, we build a new one
        super(ServerActionsTestJSON, self).setUp()
        # Check if the server is in a clean state after test
        try:
            self.client.wait_for_server_status(self.server_id, 'ACTIVE')
        except Exception:
            # Rebuild server if something happened to it during a test
            self.__class__.server_id = self.rebuild_server(self.server_id)

    def tearDown(self):
        server = self.client.get_server(self.server_id)
        self.assertEqual(self.image_ref, server['image']['id'])
        self.server_check_teardown()
        super(ServerActionsTestJSON, self).tearDown()

    @classmethod
    def setup_clients(cls):
        super(ServerActionsTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        cls.prepare_instance_network()
        super(ServerActionsTestJSON, cls).resource_setup()
        cls.server_id = cls.rebuild_server(None)

    @test.idempotent_id('6158df09-4b82-4ab3-af6d-29cf36af858d')
    @testtools.skipUnless(CONF.compute_feature_enabled.change_password,
                          'Change password not available.')
    @test.attr(type='gate')
    def test_change_server_password(self):
        # The server's password should be set to the provided password
        new_password = 'Newpass1234'
        self.client.change_password(self.server_id, new_password)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        if self.run_ssh:
            # Verify that the user can authenticate with the new password
            server = self.client.get_server(self.server_id)
            linux_client = remote_client.RemoteClient(server, self.ssh_user,
                                                      new_password)
            linux_client.validate_authentication()

    def _test_reboot_server(self, reboot_type):
        if self.run_ssh:
            # Get the time the server was last rebooted,
            server = self.client.get_server(self.server_id)
            linux_client = remote_client.RemoteClient(server, self.ssh_user,
                                                      self.password)
            boot_time = linux_client.get_boot_time()

        self.client.reboot(self.server_id, reboot_type)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        if self.run_ssh:
            # Log in and verify the boot time has changed
            linux_client = remote_client.RemoteClient(server, self.ssh_user,
                                                      self.password)
            new_boot_time = linux_client.get_boot_time()
            self.assertTrue(new_boot_time > boot_time,
                            '%s > %s' % (new_boot_time, boot_time))

    @test.attr(type='smoke')
    @test.idempotent_id('2cb1baf6-ac8d-4429-bf0d-ba8a0ba53e32')
    def test_reboot_server_hard(self):
        # The server should be power cycled
        self._test_reboot_server('HARD')

    @decorators.skip_because(bug="1014647")
    @test.attr(type='smoke')
    @test.idempotent_id('4640e3ef-a5df-482e-95a1-ceeeb0faa84d')
    def test_reboot_server_soft(self):
        # The server should be signaled to reboot gracefully
        self._test_reboot_server('SOFT')

    @test.attr(type='smoke')
    @test.idempotent_id('aaa6cdf3-55a7-461a-add9-1c8596b9a07c')
    def test_rebuild_server(self):
        # The server should be rebuilt using the provided image and data
        meta = {'rebuild': 'server'}
        new_name = data_utils.rand_name('server')
        file_contents = 'Test server rebuild.'
        personality = [{'path': 'rebuild.txt',
                       'contents': base64.b64encode(file_contents)}]
        password = 'rebuildPassw0rd'
        rebuilt_server = self.client.rebuild(self.server_id,
                                             self.image_ref_alt,
                                             name=new_name,
                                             metadata=meta,
                                             personality=personality,
                                             adminPass=password)

        # Verify the properties in the initial response are correct
        self.assertEqual(self.server_id, rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertTrue(self.image_ref_alt.endswith(rebuilt_image_id))
        self.assertEqual(self.flavor_ref, rebuilt_server['flavor']['id'])

        # Verify the server properties after the rebuild completes
        self.client.wait_for_server_status(rebuilt_server['id'], 'ACTIVE')
        server = self.client.get_server(rebuilt_server['id'])
        rebuilt_image_id = server['image']['id']
        self.assertTrue(self.image_ref_alt.endswith(rebuilt_image_id))
        self.assertEqual(new_name, server['name'])

        if self.run_ssh:
            # Verify that the user can authenticate with the provided password
            linux_client = remote_client.RemoteClient(server, self.ssh_user,
                                                      password)
            linux_client.validate_authentication()
        if self.image_ref_alt != self.image_ref:
            self.client.rebuild(self.server_id, self.image_ref)

    @test.attr(type='gate')
    @test.idempotent_id('30449a88-5aff-4f9b-9866-6ee9b17f906d')
    def test_rebuild_server_in_stop_state(self):
        # The server in stop state  should be rebuilt using the provided
        # image and remain in SHUTOFF state
        server = self.client.get_server(self.server_id)
        old_image = server['image']['id']
        new_image = self.image_ref_alt \
            if old_image == self.image_ref else self.image_ref
        self.client.stop(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'SHUTOFF')
        rebuilt_server = self.client.rebuild(self.server_id, new_image)

        # Verify the properties in the initial response are correct
        self.assertEqual(self.server_id, rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertEqual(new_image, rebuilt_image_id)
        self.assertEqual(self.flavor_ref, rebuilt_server['flavor']['id'])

        # Verify the server properties after the rebuild completes
        self.client.wait_for_server_status(rebuilt_server['id'], 'SHUTOFF')
        server = self.client.get_server(rebuilt_server['id'])
        rebuilt_image_id = server['image']['id']
        self.assertEqual(new_image, rebuilt_image_id)

        # Restore to the original image (The tearDown will test it again)
        if self.image_ref_alt != self.image_ref:
            self.client.rebuild(self.server_id, old_image)
            self.client.wait_for_server_status(self.server_id, 'SHUTOFF')
        self.client.start(self.server_id)

    def _detect_server_image_flavor(self, server_id):
        # Detects the current server image flavor ref.
        server = self.client.get_server(server_id)
        current_flavor = server['flavor']['id']
        new_flavor_ref = self.flavor_ref_alt \
            if current_flavor == self.flavor_ref else self.flavor_ref
        return current_flavor, new_flavor_ref

    def _test_resize_server_confirm(self, stop=False):
        # The server's RAM and disk space should be modified to that of
        # the provided flavor

        previous_flavor_ref, new_flavor_ref = \
            self._detect_server_image_flavor(self.server_id)

        if stop:
            self.servers_client.stop(self.server_id)
            self.servers_client.wait_for_server_status(self.server_id,
                                                       'SHUTOFF')

        self.client.resize(self.server_id, new_flavor_ref)
        self.client.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        self.client.confirm_resize(self.server_id)
        expected_status = 'SHUTOFF' if stop else 'ACTIVE'
        self.client.wait_for_server_status(self.server_id, expected_status)

        server = self.client.get_server(self.server_id)
        self.assertEqual(new_flavor_ref, server['flavor']['id'])

        if stop:
            # NOTE(mriedem): tearDown requires the server to be started.
            self.client.start(self.server_id)

    @test.idempotent_id('1499262a-9328-4eda-9068-db1ac57498d2')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @test.attr(type='smoke')
    def test_resize_server_confirm(self):
        self._test_resize_server_confirm(stop=False)

    @test.idempotent_id('138b131d-66df-48c9-a171-64f45eb92962')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @test.attr(type='smoke')
    def test_resize_server_confirm_from_stopped(self):
        self._test_resize_server_confirm(stop=True)

    @test.idempotent_id('c03aab19-adb1-44f5-917d-c419577e9e68')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @test.attr(type='gate')
    def test_resize_server_revert(self):
        # The server's RAM and disk space should return to its original
        # values after a resize is reverted

        previous_flavor_ref, new_flavor_ref = \
            self._detect_server_image_flavor(self.server_id)

        self.client.resize(self.server_id, new_flavor_ref)
        self.client.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        self.client.revert_resize(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        server = self.client.get_server(self.server_id)
        self.assertEqual(previous_flavor_ref, server['flavor']['id'])

    @test.idempotent_id('b963d4f1-94b3-4c40-9e97-7b583f46e470')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting not available, backup not possible.')
    @test.attr(type='gate')
    @test.services('image')
    def test_create_backup(self):
        # Positive test:create backup successfully and rotate backups correctly
        # create the first and the second backup
        backup1 = data_utils.rand_name('backup-1')
        resp = self.servers_client.create_backup(self.server_id,
                                                 'daily',
                                                 2,
                                                 backup1).response
        oldest_backup_exist = True

        # the oldest one should be deleted automatically in this test
        def _clean_oldest_backup(oldest_backup):
            if oldest_backup_exist:
                try:
                    self.os.image_client.delete_image(oldest_backup)
                except lib_exc.NotFound:
                    pass
                else:
                    LOG.warning("Deletion of oldest backup %s should not have "
                                "been successful as it should have been "
                                "deleted during rotation." % oldest_backup)

        image1_id = data_utils.parse_image_id(resp['location'])
        self.addCleanup(_clean_oldest_backup, image1_id)
        self.os.image_client.wait_for_image_status(image1_id, 'active')

        backup2 = data_utils.rand_name('backup-2')
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')
        resp = self.servers_client.create_backup(self.server_id,
                                                 'daily',
                                                 2,
                                                 backup2).response
        image2_id = data_utils.parse_image_id(resp['location'])
        self.addCleanup(self.os.image_client.delete_image, image2_id)
        self.os.image_client.wait_for_image_status(image2_id, 'active')

        # verify they have been created
        properties = {
            'image_type': 'backup',
            'backup_type': "daily",
            'instance_uuid': self.server_id,
        }
        image_list = self.os.image_client.image_list_detail(
            properties,
            status='active',
            sort_key='created_at',
            sort_dir='asc')
        self.assertEqual(2, len(image_list))
        self.assertEqual((backup1, backup2),
                         (image_list[0]['name'], image_list[1]['name']))

        # create the third one, due to the rotation is 2,
        # the first one will be deleted
        backup3 = data_utils.rand_name('backup-3')
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')
        resp = self.servers_client.create_backup(self.server_id,
                                                 'daily',
                                                 2,
                                                 backup3).response
        image3_id = data_utils.parse_image_id(resp['location'])
        self.addCleanup(self.os.image_client.delete_image, image3_id)
        # the first back up should be deleted
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')
        self.os.image_client.wait_for_resource_deletion(image1_id)
        oldest_backup_exist = False
        image_list = self.os.image_client.image_list_detail(
            properties,
            status='active',
            sort_key='created_at',
            sort_dir='asc')
        self.assertEqual(2, len(image_list),
                         'Unexpected number of images for '
                         'v2:test_create_backup; was the oldest backup not '
                         'yet deleted? Image list: %s' %
                         [image['name'] for image in image_list])
        self.assertEqual((backup2, backup3),
                         (image_list[0]['name'], image_list[1]['name']))

    def _get_output(self):
        output = self.servers_client.get_console_output(
            self.server_id, 10).data
        self.assertTrue(output, "Console output was empty.")
        lines = len(output.split('\n'))
        self.assertEqual(lines, 10)

    @test.idempotent_id('4b8867e6-fffa-4d54-b1d1-6fdda57be2f3')
    @testtools.skipUnless(CONF.compute_feature_enabled.console_output,
                          'Console output not supported.')
    @test.attr(type='gate')
    def test_get_console_output(self):
        # Positive test:Should be able to GET the console output
        # for a given server_id and number of lines

        # This reboot is necessary for outputting some console log after
        # creating a instance backup. If a instance backup, the console
        # log file is truncated and we cannot get any console log through
        # "console-log" API.
        # The detail is https://bugs.launchpad.net/nova/+bug/1251920
        self.servers_client.reboot(self.server_id, 'HARD')
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')

        self.wait_for(self._get_output)

    @test.idempotent_id('89104062-69d8-4b19-a71b-f47b7af093d7')
    @testtools.skipUnless(CONF.compute_feature_enabled.console_output,
                          'Console output not supported.')
    @test.attr(type='gate')
    def test_get_console_output_with_unlimited_size(self):
        server = self.create_test_server(wait_until='ACTIVE')

        def _check_full_length_console_log():
            output = self.servers_client.get_console_output(server['id'],
                                                            None).data
            self.assertTrue(output, "Console output was empty.")
            lines = len(output.split('\n'))

            # NOTE: This test tries to get full length console log, and the
            # length should be bigger than the one of test_get_console_output.
            self.assertTrue(lines > 10, "Cannot get enough console log length."
                                        " (lines: %s)" % lines)

        self.wait_for(_check_full_length_console_log)

    @test.idempotent_id('5b65d4e7-4ecd-437c-83c0-d6b79d927568')
    @testtools.skipUnless(CONF.compute_feature_enabled.console_output,
                          'Console output not supported.')
    @test.attr(type='gate')
    def test_get_console_output_server_id_in_shutoff_status(self):
        # Positive test:Should be able to GET the console output
        # for a given server_id in SHUTOFF status

        # NOTE: SHUTOFF is irregular status. To avoid test instability,
        #       one server is created only for this test without using
        #       the server that was created in setupClass.
        server = self.create_test_server(wait_until='ACTIVE')
        temp_server_id = server['id']

        self.servers_client.stop(temp_server_id)
        self.servers_client.wait_for_server_status(temp_server_id, 'SHUTOFF')

        self.wait_for(self._get_output)

    @test.idempotent_id('bd61a9fd-062f-4670-972b-2d6c3e3b9e73')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @test.attr(type='gate')
    def test_pause_unpause_server(self):
        self.client.pause_server(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'PAUSED')
        self.client.unpause_server(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    @test.idempotent_id('0d8ee21e-b749-462d-83da-b85b41c86c7f')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @test.attr(type='gate')
    def test_suspend_resume_server(self):
        self.client.suspend_server(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'SUSPENDED')
        self.client.resume_server(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    @test.idempotent_id('77eba8e0-036e-4635-944b-f7a8f3b78dc9')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @test.attr(type='gate')
    def test_shelve_unshelve_server(self):
        self.client.shelve_server(self.server_id)

        offload_time = CONF.compute.shelved_offload_time
        if offload_time >= 0:
            self.client.wait_for_server_status(self.server_id,
                                               'SHELVED_OFFLOADED',
                                               extra_timeout=offload_time)
        else:
            self.client.wait_for_server_status(self.server_id,
                                               'SHELVED')

            self.client.shelve_offload_server(self.server_id)
            self.client.wait_for_server_status(self.server_id,
                                               'SHELVED_OFFLOADED')

        server = self.client.get_server(self.server_id)
        image_name = server['name'] + '-shelved'
        params = {'name': image_name}
        images = self.images_client.list_images(params)
        self.assertEqual(1, len(images))
        self.assertEqual(image_name, images[0]['name'])

        self.client.unshelve_server(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    @test.attr(type='gate')
    @test.idempotent_id('af8eafd4-38a7-4a4b-bdbc-75145a580560')
    def test_stop_start_server(self):
        self.servers_client.stop(self.server_id)
        self.servers_client.wait_for_server_status(self.server_id, 'SHUTOFF')
        self.servers_client.start(self.server_id)
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')

    @test.attr(type='gate')
    @test.idempotent_id('80a8094c-211e-440a-ab88-9e59d556c7ee')
    def test_lock_unlock_server(self):
        # Lock the server,try server stop(exceptions throw),unlock it and retry
        self.servers_client.lock_server(self.server_id)
        server = self.servers_client.get_server(self.server_id)
        self.assertEqual(server['status'], 'ACTIVE')
        # Locked server is not allowed to be stopped by non-admin user
        self.assertRaises(lib_exc.Conflict,
                          self.servers_client.stop, self.server_id)
        self.servers_client.unlock_server(self.server_id)
        self.servers_client.stop(self.server_id)
        self.servers_client.wait_for_server_status(self.server_id, 'SHUTOFF')
        self.servers_client.start(self.server_id)
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')

    def _validate_url(self, url):
        valid_scheme = ['http', 'https']
        parsed_url = urlparse.urlparse(url)
        self.assertNotEqual('None', parsed_url.port)
        self.assertNotEqual('None', parsed_url.hostname)
        self.assertIn(parsed_url.scheme, valid_scheme)

    @test.idempotent_id('c6bc11bf-592e-4015-9319-1c98dc64daf5')
    @testtools.skipUnless(CONF.compute_feature_enabled.vnc_console,
                          'VNC Console feature is disabled.')
    @test.attr(type='gate')
    def test_get_vnc_console(self):
        # Get the VNC console of type 'novnc' and 'xvpvnc'
        console_types = ['novnc', 'xvpvnc']
        for console_type in console_types:
            body = self.servers_client.get_vnc_console(self.server_id,
                                                       console_type)
            self.assertEqual(console_type, body['type'])
            self.assertNotEqual('', body['url'])
            self._validate_url(body['url'])
