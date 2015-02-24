# Copyright 2013 IBM Corp.
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

import testtools

from tempest.api.compute import base
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest import test

CONF = config.CONF


class AttachVolumeTestJSON(base.BaseV2ComputeTest):

    def __init__(self, *args, **kwargs):
        super(AttachVolumeTestJSON, self).__init__(*args, **kwargs)
        self.attachment = None

    @classmethod
    def skip_checks(cls):
        super(AttachVolumeTestJSON, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(AttachVolumeTestJSON, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(AttachVolumeTestJSON, cls).resource_setup()
        cls.device = CONF.compute.volume_device_name

    def _detach(self, server_id, volume_id):
        if self.attachment:
            self.servers_client.detach_volume(server_id, volume_id)
            self.volumes_client.wait_for_volume_status(volume_id, 'available')

    def _delete_volume(self):
        # Delete the created Volumes
        if self.volume:
            self.volumes_client.delete_volume(self.volume['id'])
            self.volumes_client.wait_for_resource_deletion(self.volume['id'])
            self.volume = None

    def _create_and_attach(self):
        # Start a server and wait for it to become ready
        admin_pass = self.image_ssh_password
        self.server = self.create_test_server(wait_until='ACTIVE',
                                              adminPass=admin_pass)

        # Record addresses so that we can ssh later
        self.server['addresses'] = (
            self.servers_client.list_addresses(self.server['id']))

        # Create a volume and wait for it to become ready
        self.volume = self.volumes_client.create_volume(
            CONF.volume.volume_size, display_name='test')
        self.addCleanup(self._delete_volume)
        self.volumes_client.wait_for_volume_status(self.volume['id'],
                                                   'available')

        # Attach the volume to the server
        self.attachment = self.servers_client.attach_volume(
            self.server['id'],
            self.volume['id'],
            device='/dev/%s' % self.device)
        self.volumes_client.wait_for_volume_status(self.volume['id'], 'in-use')

        self.addCleanup(self._detach, self.server['id'], self.volume['id'])

    @test.idempotent_id('52e9045a-e90d-4c0d-9087-79d657faffff')
    @testtools.skipUnless(CONF.compute.run_ssh, 'SSH required for this test')
    @test.attr(type='gate')
    def test_attach_detach_volume(self):
        # Stop and Start a server with an attached volume, ensuring that
        # the volume remains attached.
        self._create_and_attach()

        self.servers_client.stop(self.server['id'])
        self.servers_client.wait_for_server_status(self.server['id'],
                                                   'SHUTOFF')

        self.servers_client.start(self.server['id'])
        self.servers_client.wait_for_server_status(self.server['id'], 'ACTIVE')

        linux_client = remote_client.RemoteClient(self.server,
                                                  self.image_ssh_user,
                                                  self.server['adminPass'])
        partitions = linux_client.get_partitions()
        self.assertIn(self.device, partitions)

        self._detach(self.server['id'], self.volume['id'])
        self.attachment = None
        self.servers_client.stop(self.server['id'])
        self.servers_client.wait_for_server_status(self.server['id'],
                                                   'SHUTOFF')

        self.servers_client.start(self.server['id'])
        self.servers_client.wait_for_server_status(self.server['id'], 'ACTIVE')

        linux_client = remote_client.RemoteClient(self.server,
                                                  self.image_ssh_user,
                                                  self.server['adminPass'])
        partitions = linux_client.get_partitions()
        self.assertNotIn(self.device, partitions)

    @test.attr(type='gate')
    @test.idempotent_id('7fa563fe-f0f7-43eb-9e22-a1ece036b513')
    def test_list_get_volume_attachments(self):
        # Create Server, Volume and attach that Volume to Server
        self._create_and_attach()
        # List Volume attachment of the server
        body = self.servers_client.list_volume_attachments(
            self.server['id'])
        self.assertEqual(1, len(body))
        self.assertIn(self.attachment, body)

        # Get Volume attachment of the server
        body = self.servers_client.get_volume_attachment(
            self.server['id'],
            self.attachment['id'])
        self.assertEqual(self.server['id'], body['serverId'])
        self.assertEqual(self.volume['id'], body['volumeId'])
        self.assertEqual(self.attachment['id'], body['id'])
