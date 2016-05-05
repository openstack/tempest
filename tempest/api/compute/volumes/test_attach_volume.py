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
from tempest.common import compute
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest import test

CONF = config.CONF


class AttachVolumeTestJSON(base.BaseV2ComputeTest):
    max_microversion = '2.19'

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
        cls.set_validation_resources()

        super(AttachVolumeTestJSON, cls).resource_setup()
        cls.device = CONF.compute.volume_device_name

    def _detach(self, server_id, volume_id):
        if self.attachment:
            self.servers_client.detach_volume(server_id, volume_id)
            waiters.wait_for_volume_status(self.volumes_client,
                                           volume_id, 'available')

    def _delete_volume(self):
        # Delete the created Volumes
        if self.volume:
            self.volumes_client.delete_volume(self.volume['id'])
            self.volumes_client.wait_for_resource_deletion(self.volume['id'])
            self.volume = None

    def _create_and_attach(self, shelve_server=False):
        # Start a server and wait for it to become ready
        self.admin_pass = self.image_ssh_password
        self.server = self.create_test_server(
            validatable=True,
            wait_until='ACTIVE',
            adminPass=self.admin_pass)

        # Record addresses so that we can ssh later
        self.server['addresses'] = self.servers_client.list_addresses(
            self.server['id'])['addresses']

        # Create a volume and wait for it to become ready
        self.volume = self.volumes_client.create_volume(
            size=CONF.volume.volume_size, display_name='test')['volume']
        self.addCleanup(self._delete_volume)
        waiters.wait_for_volume_status(self.volumes_client,
                                       self.volume['id'], 'available')

        if shelve_server:
            # NOTE(andreaf) If we are going to shelve a server, we should
            # check first whether the server is ssh-able. Otherwise we won't
            # be able to distinguish failures introduced by shelve from
            # pre-existing ones. Also it's good to wait for cloud-init to be
            # done and sshd server to be running before shelving to avoid
            # breaking the VM
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(self.server),
                self.image_ssh_user,
                self.admin_pass,
                self.validation_resources['keypair']['private_key'])
            linux_client.validate_authentication()
            # If validation went ok, shelve the server
            compute.shelve_server(self.servers_client, self.server['id'])

        # Attach the volume to the server
        self.attachment = self.servers_client.attach_volume(
            self.server['id'],
            volumeId=self.volume['id'],
            device='/dev/%s' % self.device)['volumeAttachment']
        waiters.wait_for_volume_status(self.volumes_client,
                                       self.volume['id'], 'in-use')

        self.addCleanup(self._detach, self.server['id'], self.volume['id'])

    @test.idempotent_id('52e9045a-e90d-4c0d-9087-79d657faffff')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'SSH required for this test')
    def test_attach_detach_volume(self):
        # Stop and Start a server with an attached volume, ensuring that
        # the volume remains attached.
        self._create_and_attach()

        self.servers_client.stop_server(self.server['id'])
        waiters.wait_for_server_status(self.servers_client, self.server['id'],
                                       'SHUTOFF')

        self.servers_client.start_server(self.server['id'])
        waiters.wait_for_server_status(self.servers_client, self.server['id'],
                                       'ACTIVE')

        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server),
            self.image_ssh_user,
            self.admin_pass,
            self.validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.servers_client)

        partitions = linux_client.get_partitions()
        self.assertIn(self.device, partitions)

        self._detach(self.server['id'], self.volume['id'])
        self.attachment = None
        self.servers_client.stop_server(self.server['id'])
        waiters.wait_for_server_status(self.servers_client, self.server['id'],
                                       'SHUTOFF')

        self.servers_client.start_server(self.server['id'])
        waiters.wait_for_server_status(self.servers_client, self.server['id'],
                                       'ACTIVE')

        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server),
            self.image_ssh_user,
            self.admin_pass,
            self.validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.servers_client)

        partitions = linux_client.get_partitions()
        self.assertNotIn(self.device, partitions)

    @test.idempotent_id('7fa563fe-f0f7-43eb-9e22-a1ece036b513')
    def test_list_get_volume_attachments(self):
        # Create Server, Volume and attach that Volume to Server
        self._create_and_attach()
        # List Volume attachment of the server
        body = self.servers_client.list_volume_attachments(
            self.server['id'])['volumeAttachments']
        self.assertEqual(1, len(body))
        self.assertIn(self.attachment, body)

        # Get Volume attachment of the server
        body = self.servers_client.show_volume_attachment(
            self.server['id'],
            self.attachment['id'])['volumeAttachment']
        self.assertEqual(self.server['id'], body['serverId'])
        self.assertEqual(self.volume['id'], body['volumeId'])
        self.assertEqual(self.attachment['id'], body['id'])


class AttachVolumeShelveTestJSON(AttachVolumeTestJSON):
    """Testing volume with shelved instance.

    This test checks the attaching and detaching volumes from
    a shelved or shelved ofload instance.
    """

    min_microversion = '2.20'
    max_microversion = 'latest'

    def _unshelve_server_and_check_volumes(self, number_of_partition):
        # Unshelve the instance and check that there are expected volumes
        self.servers_client.unshelve_server(self.server['id'])
        waiters.wait_for_server_status(self.servers_client,
                                       self.server['id'],
                                       'ACTIVE')
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server['id']),
            self.image_ssh_user,
            self.admin_pass,
            self.validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.servers_client)

        command = 'grep vd /proc/partitions | wc -l'
        nb_partitions = linux_client.exec_command(command).strip()
        self.assertEqual(number_of_partition, nb_partitions)

    @test.idempotent_id('13a940b6-3474-4c3c-b03f-29b89112bfee')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'SSH required for this test')
    def test_attach_volume_shelved_or_offload_server(self):
        self._create_and_attach(shelve_server=True)

        # Unshelve the instance and check that there are two volumes
        self._unshelve_server_and_check_volumes('2')

        # Get Volume attachment of the server
        volume_attachment = self.servers_client.show_volume_attachment(
            self.server['id'],
            self.attachment['id'])['volumeAttachment']
        self.assertEqual(self.server['id'], volume_attachment['serverId'])
        self.assertEqual(self.attachment['id'], volume_attachment['id'])
        # Check the mountpoint is not None after unshelve server even in
        # case of shelved_offloaded.
        self.assertIsNotNone(volume_attachment['device'])

    @test.idempotent_id('b54e86dd-a070-49c4-9c07-59ae6dae15aa')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'SSH required for this test')
    def test_detach_volume_shelved_or_offload_server(self):
        self._create_and_attach(shelve_server=True)

        # Detach the volume
        self._detach(self.server['id'], self.volume['id'])
        self.attachment = None

        # Unshelve the instance and check that there is only one volume
        self._unshelve_server_and_check_volumes('1')
