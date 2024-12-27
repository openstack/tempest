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

from urllib import parse as urlparse

from oslo_log import log as logging
import testtools

from tempest.api.compute import base
from tempest.common import compute
from tempest.common import utils
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF

LOG = logging.getLogger(__name__)


class ServerActionsBase(base.BaseV2ComputeTest):
    """Test server actions"""

    def setUp(self):
        # NOTE(afazekas): Normally we use the same server with all test cases,
        # but if it has an issue, we build a new one
        super().setUp()
        # Check if the server is in a clean state after test
        try:
            self.validation_resources = self.get_class_validation_resources(
                self.os_primary)
            waiters.wait_for_server_status(self.client,
                                           self.server_id, 'ACTIVE')
        except lib_exc.NotFound:
            # The server was deleted by previous test, create a new one
            # Use class level validation resources to avoid them being
            # deleted once a test is over
            self.validation_resources = self.get_class_validation_resources(
                self.os_primary)
            server = self.create_test_server(
                validatable=True,
                validation_resources=self.validation_resources,
                wait_until='SSHABLE')
            self.__class__.server_id = server['id']
        except Exception:
            # Rebuild server if something happened to it during a test
            self.__class__.server_id = self.recreate_server(
                self.server_id, validatable=True, wait_until='SSHABLE')

    def tearDown(self):
        super(ServerActionsBase, self).tearDown()
        # NOTE(zhufl): Because server_check_teardown will raise Exception
        # which will prevent other cleanup steps from being executed, so
        # server_check_teardown should be called after super's tearDown.
        self.server_check_teardown()

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServerActionsBase, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServerActionsBase, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServerActionsBase, cls).resource_setup()
        cls.server_id = cls.recreate_server(None, validatable=True,
                                            wait_until='SSHABLE')

    def _test_reboot_server(self, reboot_type):
        if CONF.validation.run_validation:
            # Get the time the server was last rebooted,
            server = self.client.show_server(self.server_id)['server']
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server, self.validation_resources),
                self.ssh_user,
                self.password,
                self.validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.client)
            boot_time = linux_client.get_boot_time()

            # NOTE: This sync is for avoiding the loss of pub key data
            # in a server
            linux_client.exec_command("sync")

        self.reboot_server(self.server_id, type=reboot_type)

        if CONF.validation.run_validation:
            # Log in and verify the boot time has changed
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server, self.validation_resources),
                self.ssh_user,
                self.password,
                self.validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.client)
            new_boot_time = linux_client.get_boot_time()
            self.assertGreater(new_boot_time, boot_time,
                               '%s > %s' % (new_boot_time, boot_time))

    def _test_rebuild_server(self, server_id, **kwargs):
        # Get the IPs the server has before rebuilding it
        original_addresses = (self.client.show_server(server_id)['server']
                              ['addresses'])
        # The server should be rebuilt using the provided image and data
        meta = {'rebuild': 'server'}
        new_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=self.__class__.__name__ + '-server')
        password = 'rebuildPassw0rd'
        rebuilt_server = self.client.rebuild_server(
            server_id,
            self.image_ref_alt,
            name=new_name,
            metadata=meta,
            adminPass=password)['server']

        # Verify the properties in the initial response are correct
        self.assertEqual(server_id, rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertTrue(self.image_ref_alt.endswith(rebuilt_image_id))
        self.assert_flavor_equal(self.flavor_ref, rebuilt_server['flavor'])

        # Verify the server properties after the rebuild completes
        waiters.wait_for_server_status(self.client,
                                       rebuilt_server['id'], 'ACTIVE')
        server = self.client.show_server(rebuilt_server['id'])['server']
        rebuilt_image_id = server['image']['id']
        self.assertTrue(self.image_ref_alt.endswith(rebuilt_image_id))
        self.assertEqual(new_name, server['name'])
        self.assertEqual(original_addresses, server['addresses'])

        if CONF.validation.run_validation:
            # Authentication is attempted in the following order of priority:
            # 1.The key passed in, if one was passed in.
            # 2.Any key we can find through an SSH agent (if allowed).
            # 3.Any "id_rsa", "id_dsa" or "id_ecdsa" key discoverable in
            #   ~/.ssh/ (if allowed).
            # 4.Plain username/password auth, if a password was given.

            if 'validation_resources' in kwargs:
                validation_resources = kwargs['validation_resources']
            else:
                validation_resources = self.validation_resources

            linux_client = remote_client.RemoteClient(
                self.get_server_ip(rebuilt_server, validation_resources),
                self.ssh_alt_user,
                password,
                validation_resources['keypair']['private_key'],
                server=rebuilt_server,
                servers_client=self.client)
            linux_client.validate_authentication()

    def _test_resize_server_confirm(self, server_id, stop=False):
        # The server's RAM and disk space should be modified to that of
        # the provided flavor

        if stop:
            self.client.stop_server(server_id)
            waiters.wait_for_server_status(self.client, server_id,
                                           'SHUTOFF')

        self.client.resize_server(server_id, self.flavor_ref_alt)
        # NOTE(jlk): Explicitly delete the server to get a new one for later
        # tests. Avoids resize down race issues.
        self.addCleanup(self.delete_server, server_id)
        waiters.wait_for_server_status(self.client, server_id,
                                       'VERIFY_RESIZE')

        self.client.confirm_resize_server(server_id)
        expected_status = 'SHUTOFF' if stop else 'ACTIVE'
        waiters.wait_for_server_status(self.client, server_id,
                                       expected_status)

        server = self.client.show_server(server_id)['server']
        self.assert_flavor_equal(self.flavor_ref_alt, server['flavor'])

        if stop:
            # NOTE(mriedem): tearDown requires the server to be started.
            self.client.start_server(server_id)

    def _get_output(self, server_id):
        output = self.client.get_console_output(
            server_id, length=3)['output']
        self.assertTrue(output, "Console output was empty.")
        lines = len(output.split('\n'))
        self.assertEqual(lines, 3)

    def _validate_url(self, url):
        valid_scheme = ['http', 'https']
        parsed_url = urlparse.urlparse(url)
        self.assertNotEqual('None', parsed_url.port)
        self.assertNotEqual('None', parsed_url.hostname)
        self.assertIn(parsed_url.scheme, valid_scheme)


class ServerActionsTestJSON(ServerActionsBase):
    @decorators.idempotent_id('6158df09-4b82-4ab3-af6d-29cf36af858d')
    @testtools.skipUnless(CONF.compute_feature_enabled.change_password,
                          'Change password not available.')
    def test_change_server_password(self):
        """Test changing server's password

        The server's password should be set to the provided password and
        the user can authenticate with the new password.
        """
        # Since this test messes with the password and makes the
        # server unreachable, it should create its own server
        newserver = self.create_test_server(
            validatable=True,
            validation_resources=self.validation_resources,
            wait_until='ACTIVE')
        self.addCleanup(self.delete_server, newserver['id'])
        # The server's password should be set to the provided password
        new_password = 'Newpass1234'
        self.client.change_password(newserver['id'], adminPass=new_password)
        waiters.wait_for_server_status(self.client, newserver['id'], 'ACTIVE')

        if CONF.validation.run_validation:
            # Verify that the user can authenticate with the new password
            server = self.client.show_server(newserver['id'])['server']
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server, self.validation_resources),
                self.ssh_user,
                new_password,
                server=server,
                servers_client=self.client)
            linux_client.validate_authentication()

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('2cb1baf6-ac8d-4429-bf0d-ba8a0ba53e32')
    def test_reboot_server_hard(self):
        """Test hard rebooting server

        The server should be power cycled.
        """
        self._test_reboot_server('HARD')

    @decorators.idempotent_id('aaa6cdf3-55a7-461a-add9-1c8596b9a07c')
    def test_rebuild_server(self):
        """Test rebuilding server

        The server should be rebuilt using the provided image and data.
        """
        tenant_network = self.get_tenant_network()
        validation_resources = self.get_test_validation_resources(
            self.os_primary)
        _, servers = compute.create_test_server(
            self.os_primary,
            wait_until='SSHABLE',
            validatable=True,
            validation_resources=validation_resources,
            tenant_network=tenant_network)
        server = servers[0]
        # _test_rebuild_server test compares ip address attached to the
        # server before and after the rebuild, in order to avoid
        # a situation when a newly created server doesn't have a floating
        # ip attached at the beginning of the test_rebuild_server let's
        # make sure right here the floating ip is attached
        waiters.wait_for_server_floating_ip(
            self.client,
            server,
            validation_resources['floating_ip'])

        self.addCleanup(waiters.wait_for_server_termination,
                        self.client, server['id'])
        self.addCleanup(self.client.delete_server, server['id'])

        self._test_rebuild_server(
            server_id=server['id'],
            validation_resources=validation_resources)

    @decorators.idempotent_id('1499262a-9328-4eda-9068-db1ac57498d2')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_resize_server_confirm(self):
        """Test resizing server and then confirming"""
        self._test_resize_server_confirm(self.server_id, stop=False)

    @decorators.idempotent_id('c03aab19-adb1-44f5-917d-c419577e9e68')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_resize_server_revert(self):
        """Test resizing server and then reverting

        The server's RAM and disk space should return to its original
        values after a resize is reverted.
        """

        self.client.resize_server(self.server_id, self.flavor_ref_alt)
        # NOTE(zhufl): Explicitly delete the server to get a new one for later
        # tests. Avoids resize down race issues.
        self.addCleanup(self.delete_server, self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id,
                                       'VERIFY_RESIZE')

        self.client.revert_resize_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')

        server = self.client.show_server(self.server_id)['server']
        self.assert_flavor_equal(self.flavor_ref, server['flavor'])

    @decorators.idempotent_id('4b8867e6-fffa-4d54-b1d1-6fdda57be2f3')
    @testtools.skipUnless(CONF.compute_feature_enabled.console_output,
                          'Console output not supported.')
    def test_get_console_output(self):
        """Test getting console output for a server

        Should be able to GET the console output for a given server_id and
        number of lines.
        """

        # This reboot is necessary for outputting some console log after
        # creating an instance backup. If an instance backup, the console
        # log file is truncated and we cannot get any console log through
        # "console-log" API.
        # The detail is https://bugs.launchpad.net/nova/+bug/1251920
        self.reboot_server(self.server_id, type='HARD')
        self.wait_for(self._get_output, self.server_id)

    @decorators.idempotent_id('bd61a9fd-062f-4670-972b-2d6c3e3b9e73')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    def test_pause_unpause_server(self):
        """Test pausing and unpausing server"""
        self.client.pause_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'PAUSED')
        self.client.unpause_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')

    @decorators.idempotent_id('0d8ee21e-b749-462d-83da-b85b41c86c7f')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    def test_suspend_resume_server(self):
        """Test suspending and resuming server"""
        self.client.suspend_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id,
                                       'SUSPENDED')
        self.client.resume_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')

    @decorators.idempotent_id('af8eafd4-38a7-4a4b-bdbc-75145a580560')
    def test_stop_start_server(self):
        """Test stopping and starting server"""
        self.client.stop_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'SHUTOFF')
        self.client.start_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')

    @decorators.idempotent_id('80a8094c-211e-440a-ab88-9e59d556c7ee')
    def test_lock_unlock_server(self):
        """Test locking and unlocking server

        Lock the server, and trying to stop it will fail because locked
        server is not allowed to be stopped by non-admin user.
        Then unlock the server, now the server can be stopped and started.
        """
        # Lock the server,try server stop(exceptions throw),unlock it and retry
        self.client.lock_server(self.server_id)
        self.addCleanup(self.client.unlock_server, self.server_id)
        server = self.client.show_server(self.server_id)['server']
        self.assertEqual(server['status'], 'ACTIVE')
        # Locked server is not allowed to be stopped by non-admin user
        self.assertRaises(lib_exc.Conflict,
                          self.client.stop_server, self.server_id)
        self.client.unlock_server(self.server_id)
        self.client.stop_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'SHUTOFF')
        self.client.start_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')


class ServerActionsTestOtherA(ServerActionsBase):
    @decorators.idempotent_id('1d1c9104-1b0a-11e7-a3d4-fa163e65f5ce')
    def test_remove_server_all_security_groups(self):
        """Test removing all security groups from server"""
        server = self.create_test_server(wait_until='ACTIVE')

        # Remove all Security group
        self.client.remove_security_group(
            server['id'], name=server['security_groups'][0]['name'])

        # Verify all Security group
        server = self.client.show_server(server['id'])['server']
        self.assertNotIn('security_groups', server)

    @decorators.idempotent_id('30449a88-5aff-4f9b-9866-6ee9b17f906d')
    def test_rebuild_server_in_stop_state(self):
        """Test rebuilding server in stop state

        The server in stop state should be rebuilt using the provided
        image and remain in SHUTOFF state.
        """
        tenant_network = self.get_tenant_network()
        _, servers = compute.create_test_server(
            self.os_primary,
            wait_until='ACTIVE',
            tenant_network=tenant_network)
        server = servers[0]

        self.addCleanup(waiters.wait_for_server_termination,
                        self.client, server['id'])
        self.addCleanup(self.client.delete_server, server['id'])
        server = self.client.show_server(server['id'])['server']
        old_image = server['image']['id']
        new_image = (self.image_ref_alt
                     if old_image == self.image_ref else self.image_ref)
        self.client.stop_server(server['id'])
        waiters.wait_for_server_status(self.client, server['id'], 'SHUTOFF')
        rebuilt_server = (self.client.rebuild_server(server['id'], new_image)
                          ['server'])

        # Verify the properties in the initial response are correct
        self.assertEqual(server['id'], rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertEqual(new_image, rebuilt_image_id)
        self.assert_flavor_equal(self.flavor_ref, rebuilt_server['flavor'])

        # Verify the server properties after the rebuild completes
        waiters.wait_for_server_status(self.client,
                                       rebuilt_server['id'], 'SHUTOFF')
        server = self.client.show_server(rebuilt_server['id'])['server']
        rebuilt_image_id = server['image']['id']
        self.assertEqual(new_image, rebuilt_image_id)

    # NOTE(mriedem): Marked as slow because while rebuild and volume-backed is
    # common, we don't actually change the image (you can't with volume-backed
    # rebuild) so this isn't testing much outside normal rebuild
    # (and it's slow).
    @decorators.attr(type='slow')
    @decorators.idempotent_id('b68bd8d6-855d-4212-b59b-2e704044dace')
    @utils.services('volume')
    def test_rebuild_server_with_volume_attached(self):
        """Test rebuilding server with volume attached

        The volume should be attached to the instance after rebuild.
        """
        # create a new volume and attach it to the server
        volume = self.create_volume(wait_for_available=False)
        network = self.get_tenant_network()
        validation_resources = self.get_test_validation_resources(
            self.os_primary)
        _, servers = compute.create_test_server(
            self.os_primary, tenant_network=network,
            validatable=True,
            validation_resources=validation_resources,
            wait_until='SSHABLE')
        server = servers[0]
        self.addCleanup(waiters.wait_for_server_termination,
                        self.client, server['id'])
        self.addCleanup(self.client.delete_server, server['id'])

        server = self.client.show_server(server['id'])['server']
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        self.attach_volume(server, volume)

        # run general rebuild test
        self._test_rebuild_server(
            server_id=server['id'],
            validation_resources=validation_resources)

        # make sure the volume is attached to the instance after rebuild
        vol_after_rebuild = self.volumes_client.show_volume(volume['id'])
        vol_after_rebuild = vol_after_rebuild['volume']
        self.assertEqual('in-use', vol_after_rebuild['status'])
        self.assertEqual(server['id'],
                         vol_after_rebuild['attachments'][0]['server_id'])

    @decorators.idempotent_id('e6c28180-7454-4b59-b188-0257af08a63b')
    @decorators.related_bug('1728603')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @utils.services('volume')
    def test_resize_volume_backed_server_confirm(self):
        """Test resizing a volume backed server and then confirming"""
        # We have to create a new server that is volume-backed since the one
        # from setUp is not volume-backed.
        kwargs = {'volume_backed': True,
                  'wait_until': 'ACTIVE'}
        if CONF.validation.run_validation:
            kwargs.update({'validatable': True,
                           'validation_resources': self.validation_resources})
        server = self.create_test_server(**kwargs)

        # NOTE(mgoddard): Get detailed server to ensure addresses are present
        # in fixed IP case.
        server = self.servers_client.show_server(server['id'])['server']

        self._test_resize_server_confirm(server['id'])

        if CONF.compute_feature_enabled.console_output:
            # Now do something interactive with the guest like get its console
            # output; we don't actually care about the output,
            # just that it doesn't raise an error.
            self.client.get_console_output(server['id'])
        if CONF.validation.run_validation:
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server, self.validation_resources),
                self.ssh_user,
                password=None,
                pkey=self.validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.client)
            linux_client.validate_authentication()


class ServerActionsTestOtherB(ServerActionsBase):
    @decorators.idempotent_id('138b131d-66df-48c9-a171-64f45eb92962')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_resize_server_confirm_from_stopped(self):
        """Test resizing a stopped server and then confirming"""
        self._test_resize_server_confirm(self.server_id, stop=True)

    @decorators.idempotent_id('fbbf075f-a812-4022-bc5c-ccb8047eef12')
    @decorators.related_bug('1737599')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @utils.services('volume')
    def test_resize_server_revert_with_volume_attached(self):
        """Test resizing a volume attached server and then reverting

        Tests attaching a volume to a server instance and then resizing
        the instance. Once the instance is resized, revert the resize which
        should move the instance and volume attachment back to the original
        compute host.
        """

        # Create a blank volume and attach it to the server created in setUp.
        volume = self.create_volume()
        server = self.client.show_server(self.server_id)['server']
        self.attach_volume(server, volume)
        # Now resize the server with the blank volume attached.
        self.client.resize_server(self.server_id, self.flavor_ref_alt)
        # Explicitly delete the server to get a new one for later
        # tests. Avoids resize down race issues.
        self.addCleanup(self.delete_server, self.server_id)
        waiters.wait_for_server_status(
            self.client, self.server_id, 'VERIFY_RESIZE')
        # Now revert the resize which should move the instance and it's volume
        # attachment back to the original source compute host.
        self.client.revert_resize_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')
        # Make sure everything still looks OK.
        server = self.client.show_server(self.server_id)['server']
        self.assert_flavor_equal(self.flavor_ref, server['flavor'])
        attached_volumes = server['os-extended-volumes:volumes_attached']
        self.assertEqual(1, len(attached_volumes))
        self.assertEqual(volume['id'], attached_volumes[0]['id'])

    @decorators.idempotent_id('b963d4f1-94b3-4c40-9e97-7b583f46e470')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting not available, backup not possible.')
    @utils.services('image')
    def test_create_backup(self):
        """Test creating server backup

        1. create server backup1 with rotation=2, there are 1 backup.
        2. create server backup2 with rotation=2, there are 2 backups.
        3. create server backup3, due to the rotation is 2, the first one
           (backup1) will be deleted, so now there are still 2 backups.
        """

        # create the first and the second backup

        if CONF.image_feature_enabled.api_v2:
            glance_client = self.os_primary.image_client_v2
        else:
            raise lib_exc.InvalidConfiguration(
                'api_v2 must be True in [image-feature-enabled].')

        backup1 = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='backup-1')
        resp = self.client.create_backup(self.server_id,
                                         backup_type='daily',
                                         rotation=2,
                                         name=backup1)
        oldest_backup_exist = True

        # the oldest one should be deleted automatically in this test
        def _clean_oldest_backup(oldest_backup):
            if oldest_backup_exist:
                try:
                    glance_client.delete_image(oldest_backup)
                except lib_exc.NotFound:
                    pass
                else:
                    LOG.warning("Deletion of oldest backup %s should not have "
                                "been successful as it should have been "
                                "deleted during rotation.", oldest_backup)

        if api_version_utils.compare_version_header_to_response(
                "OpenStack-API-Version", "compute 2.45", resp.response, "lt"):
            image1_id = resp['image_id']
        else:
            image1_id = data_utils.parse_image_id(resp.response['location'])
        self.addCleanup(_clean_oldest_backup, image1_id)
        waiters.wait_for_image_status(glance_client,
                                      image1_id, 'active')
        # This is required due to ceph issue:
        # https://bugs.launchpad.net/glance/+bug/2045769.
        # New location APIs are async so we need to wait for the location
        # import task to complete.
        # This should work with old location API since we don't fail if there
        # are no tasks for the image
        waiters.wait_for_image_tasks_status(self.images_client,
                                            image1_id, 'success')

        backup2 = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='backup-2')
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')
        resp = self.client.create_backup(self.server_id,
                                         backup_type='daily',
                                         rotation=2,
                                         name=backup2)
        if api_version_utils.compare_version_header_to_response(
                "OpenStack-API-Version", "compute 2.45", resp.response, "lt"):
            image2_id = resp['image_id']
        else:
            image2_id = data_utils.parse_image_id(resp.response['location'])
        self.addCleanup(glance_client.delete_image, image2_id)
        waiters.wait_for_image_status(glance_client,
                                      image2_id, 'active')
        waiters.wait_for_image_tasks_status(self.images_client,
                                            image2_id, 'success')

        # verify they have been created
        properties = {
            'image_type': 'backup',
            'backup_type': "daily",
            'instance_uuid': self.server_id,
        }
        params = {
            'status': 'active',
            'sort_key': 'created_at',
            'sort_dir': 'asc'
        }
        # Additional properties are flattened in glance v2.
        params.update(properties)
        image_list = glance_client.list_images(params)['images']

        self.assertEqual(2, len(image_list))
        self.assertEqual((backup1, backup2),
                         (image_list[0]['name'], image_list[1]['name']))

        # create the third one, due to the rotation is 2,
        # the first one will be deleted
        backup3 = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='backup-3')
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')
        resp = self.client.create_backup(self.server_id,
                                         backup_type='daily',
                                         rotation=2,
                                         name=backup3)
        if api_version_utils.compare_version_header_to_response(
                "OpenStack-API-Version", "compute 2.45", resp.response, "lt"):
            image3_id = resp['image_id']
        else:
            image3_id = data_utils.parse_image_id(resp.response['location'])
        waiters.wait_for_image_tasks_status(self.images_client,
                                            image3_id, 'success')
        self.addCleanup(glance_client.delete_image, image3_id)
        # the first back up should be deleted
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')
        glance_client.wait_for_resource_deletion(image1_id)
        oldest_backup_exist = False
        image_list = glance_client.list_images(params)['images']
        self.assertEqual(2, len(image_list),
                         'Unexpected number of images for '
                         'v2:test_create_backup; was the oldest backup not '
                         'yet deleted? Image list: %s' %
                         [image['name'] for image in image_list])
        self.assertEqual((backup2, backup3),
                         (image_list[0]['name'], image_list[1]['name']))

    @decorators.idempotent_id('89104062-69d8-4b19-a71b-f47b7af093d7')
    @testtools.skipUnless(CONF.compute_feature_enabled.console_output,
                          'Console output not supported.')
    def test_get_console_output_with_unlimited_size(self):
        """Test getting server's console output with unlimited size

        The console output lines length should be bigger than the one
        of test_get_console_output.
        """
        server = self.create_test_server(wait_until='ACTIVE')

        def _check_full_length_console_log():
            output = self.client.get_console_output(server['id'])['output']
            self.assertTrue(output, "Console output was empty.")
            lines = len(output.split('\n'))

            # NOTE: This test tries to get full length console log, and the
            # length should be bigger than the one of test_get_console_output.
            self.assertGreater(lines, 3, "Cannot get enough console log "
                                         "length. (lines: %s)" % lines)

        self.wait_for(_check_full_length_console_log)

    @decorators.skip_because(bug='2028851')
    @decorators.idempotent_id('5b65d4e7-4ecd-437c-83c0-d6b79d927568')
    @testtools.skipUnless(CONF.compute_feature_enabled.console_output,
                          'Console output not supported.')
    def test_get_console_output_server_id_in_shutoff_status(self):
        """Test getting console output for a server in SHUTOFF status

        Should be able to GET the console output for a given server_id
        in SHUTOFF status.
        """

        # NOTE: SHUTOFF is irregular status. To avoid test instability,
        #       one server is created only for this test without using
        #       the server that was created in setUpClass.
        server = self.create_test_server(wait_until='ACTIVE')
        temp_server_id = server['id']

        self.client.stop_server(temp_server_id)
        waiters.wait_for_server_status(self.client, temp_server_id, 'SHUTOFF')
        self.wait_for(self._get_output, temp_server_id)

    @decorators.idempotent_id('77eba8e0-036e-4635-944b-f7a8f3b78dc9')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @utils.services('image')
    def test_shelve_unshelve_server(self):
        """Test shelving and unshelving server"""
        if CONF.image_feature_enabled.api_v2:
            glance_client = self.os_primary.image_client_v2
        else:
            raise lib_exc.InvalidConfiguration(
                'api_v2 must be True in [image-feature-enabled].')
        compute.shelve_server(self.client, self.server_id,
                              force_shelve_offload=True)

        server = self.client.show_server(self.server_id)['server']
        image_name = server['name'] + '-shelved'
        params = {'name': image_name}
        images = glance_client.list_images(params)['images']
        self.assertEqual(1, len(images))
        self.assertEqual(image_name, images[0]['name'])

        body = self.client.unshelve_server(self.server_id)
        waiters.wait_for_server_status(
            self.client,
            self.server_id,
            "ACTIVE",
            request_id=body.response["x-openstack-request-id"],
        )
        glance_client.wait_for_resource_deletion(images[0]['id'])

    @decorators.idempotent_id('8cf9f450-a871-42cf-9bef-77eba189c0b0')
    @decorators.related_bug('1745529')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    def test_shelve_paused_server(self):
        """Test shelving a paused server"""
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.pause_server(server['id'])
        waiters.wait_for_server_status(self.client, server['id'], 'PAUSED')
        # Check if Shelve operation is successful on paused server.
        compute.shelve_server(self.client, server['id'],
                              force_shelve_offload=True)

    @decorators.idempotent_id('c6bc11bf-592e-4015-9319-1c98dc64daf5')
    @testtools.skipUnless(CONF.compute_feature_enabled.vnc_console,
                          'VNC Console feature is disabled.')
    def test_get_vnc_console(self):
        """Test getting vnc console from a server

        The returned vnc console url should be in valid format.
        """
        if self.is_requested_microversion_compatible('2.5'):
            body = self.client.get_vnc_console(
                self.server_id, type='novnc')['console']
        else:
            body = self.client.get_remote_console(
                self.server_id, console_type='novnc',
                protocol='vnc')['remote_console']
        self.assertEqual('novnc', body['type'])
        self.assertNotEqual('', body['url'])
        self._validate_url(body['url'])


class ServersAaction247Test(base.BaseV2ComputeTest):
    """Test compute server with microversion greater than 2.47

    # NOTE(gmann): This test tests the Server create backup APIs
    # response schema for 2.47 microversion. No specific assert
    # or behaviour verification is needed.
    """

    min_microversion = '2.47'

    @classmethod
    def skip_checks(cls):
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        super(ServersAaction247Test, cls).skip_checks()

    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting not available, backup not possible.')
    @decorators.idempotent_id('252a4bdd-6366-4dae-9994-8c30aa660f23')
    def test_create_backup(self):
        server = self.create_test_server(wait_until='ACTIVE')

        backup1 = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='backup-1')
        # Just check create_back to verify the schema with 2.47
        self.servers_client.create_backup(server['id'],
                                          backup_type='daily',
                                          rotation=2,
                                          name=backup1)


class ServerActionsV293TestJSON(base.BaseV2ComputeTest):

    min_microversion = '2.93'
    volume_min_microversion = '3.68'

    @classmethod
    def skip_checks(cls):
        if not CONF.service_available.cinder:
            raise cls.skipException("Cinder is not available")
        return super().skip_checks()

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServerActionsV293TestJSON, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(ServerActionsV293TestJSON, cls).resource_setup()
        cls.server_id = cls.recreate_server(None, volume_backed=True,
                                            validatable=True)

    @decorators.idempotent_id('6652dab9-ea24-4c93-ab5a-93d79c3041cf')
    def test_rebuild_volume_backed_server(self):
        """Test rebuilding a volume backed server"""
        self.validation_resources = self.get_class_validation_resources(
            self.os_primary)
        server = self.servers_client.show_server(self.server_id)['server']
        volume_id = server['os-extended-volumes:volumes_attached'][0]['id']
        volume_before_rebuild = self.volumes_client.show_volume(volume_id)
        image_before_rebuild = (
            volume_before_rebuild['volume']
            ['volume_image_metadata']['image_id'])
        # Verify that image inside volume is our initial image before rebuild
        self.assertEqual(self.image_ref, image_before_rebuild)

        # Authentication is attempted in the following order of priority:
        # 1.The key passed in, if one was passed in.
        # 2.Any key we can find through an SSH agent (if allowed).
        # 3.Any "id_rsa", "id_dsa" or "id_ecdsa" key discoverable in
        #   ~/.ssh/ (if allowed).
        # 4.Plain username/password auth, if a password was given.
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(server, self.validation_resources),
            self.ssh_user,
            password=None,
            pkey=self.validation_resources['keypair']['private_key'],
            server=server,
            servers_client=self.servers_client)
        output = linux_client.exec_command('touch test_file')
        # No output means success
        self.assertEqual('', output.strip())

        # The server should be rebuilt using the provided image and data
        meta = {'rebuild': 'server'}
        new_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=self.__class__.__name__ + '-server')
        password = 'rebuildPassw0rd'
        rebuilt_server = self.servers_client.rebuild_server(
            server['id'],
            self.image_ref_alt,
            name=new_name,
            metadata=meta,
            adminPass=password)['server']

        # Verify the properties in the initial response are correct
        self.assertEqual(server['id'], rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']
        # Since it is a volume backed server, image id will remain empty
        self.assertEqual('', rebuilt_image_id)
        self.assert_flavor_equal(self.flavor_ref, rebuilt_server['flavor'])

        # Verify the server properties after the rebuild completes
        waiters.wait_for_server_status(self.servers_client,
                                       rebuilt_server['id'], 'ACTIVE')
        server = self.servers_client.show_server(
            rebuilt_server['id'])['server']
        volume_id = server['os-extended-volumes:volumes_attached'][0]['id']
        volume_after_rebuild = self.volumes_client.show_volume(volume_id)
        image_after_rebuild = (
            volume_after_rebuild['volume']
            ['volume_image_metadata']['image_id'])

        self.assertEqual(new_name, server['name'])
        # Verify that volume ID remains same before and after rebuild
        self.assertEqual(volume_before_rebuild['volume']['id'],
                         volume_after_rebuild['volume']['id'])
        # Verify that image inside volume is our final image after rebuild
        self.assertEqual(self.image_ref_alt, image_after_rebuild)

        # Authentication is attempted in the following order of priority:
        # 1.The key passed in, if one was passed in.
        # 2.Any key we can find through an SSH agent (if allowed).
        # 3.Any "id_rsa", "id_dsa" or "id_ecdsa" key discoverable in
        #   ~/.ssh/ (if allowed).
        # 4.Plain username/password auth, if a password was given.
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(rebuilt_server, self.validation_resources),
            self.ssh_alt_user,
            password,
            self.validation_resources['keypair']['private_key'],
            server=rebuilt_server,
            servers_client=self.servers_client)
        linux_client.validate_authentication()
        e = self.assertRaises(lib_exc.SSHExecCommandFailed,
                              linux_client.exec_command,
                              'cat test_file')
        # If we rebuilt the boot volume, then we should not find
        # the file we touched.
        self.assertIn('No such file or directory', str(e))
