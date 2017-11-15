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

from tempest.api.compute import base
from tempest.common import compute
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class AttachVolumeTestJSON(base.BaseV2ComputeTest):
    max_microversion = '2.19'

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

    def _create_server(self):
        # Start a server and wait for it to become ready
        validation_resources = self.get_test_validation_resources(
            self.os_primary)
        server = self.create_test_server(
            validatable=True,
            validation_resources=validation_resources,
            wait_until='ACTIVE',
            adminPass=self.image_ssh_password)
        self.addCleanup(self.delete_server, server['id'])
        # Record addresses so that we can ssh later
        server['addresses'] = self.servers_client.list_addresses(
            server['id'])['addresses']
        return server, validation_resources

    @decorators.idempotent_id('52e9045a-e90d-4c0d-9087-79d657faffff')
    def test_attach_detach_volume(self):
        # Stop and Start a server with an attached volume, ensuring that
        # the volume remains attached.
        server, validation_resources = self._create_server()

        # NOTE(andreaf) Create one remote client used throughout the test.
        if CONF.validation.run_validation:
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server, validation_resources),
                self.image_ssh_user,
                self.image_ssh_password,
                validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.servers_client)
            # NOTE(andreaf) We need to ensure the ssh key has been
            # injected in the guest before we power cycle
            linux_client.validate_authentication()

        volume = self.create_volume()
        attachment = self.attach_volume(server, volume,
                                        device=('/dev/%s' % self.device))

        self.servers_client.stop_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'SHUTOFF')

        self.servers_client.start_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')

        if CONF.validation.run_validation:
            disks = linux_client.get_disks()
            device_name_to_match = '\n' + self.device + ' '
            self.assertIn(device_name_to_match, disks)

        self.servers_client.detach_volume(server['id'], attachment['volumeId'])
        waiters.wait_for_volume_resource_status(
            self.volumes_client, attachment['volumeId'], 'available')

        self.servers_client.stop_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'SHUTOFF')

        self.servers_client.start_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')

        if CONF.validation.run_validation:
            disks = linux_client.get_disks()
            self.assertNotIn(device_name_to_match, disks)

    @decorators.idempotent_id('7fa563fe-f0f7-43eb-9e22-a1ece036b513')
    def test_list_get_volume_attachments(self):
        # List volume attachment of the server
        server, _ = self._create_server()
        volume_1st = self.create_volume()
        attachment_1st = self.attach_volume(server, volume_1st,
                                            device=('/dev/%s' % self.device))
        body = self.servers_client.list_volume_attachments(
            server['id'])['volumeAttachments']
        self.assertEqual(1, len(body))
        self.assertIn(attachment_1st, body)

        # Get volume attachment of the server
        body = self.servers_client.show_volume_attachment(
            server['id'],
            attachment_1st['id'])['volumeAttachment']
        self.assertEqual(server['id'], body['serverId'])
        self.assertEqual(volume_1st['id'], body['volumeId'])
        self.assertEqual(attachment_1st['id'], body['id'])

        # attach one more volume to server
        volume_2nd = self.create_volume()
        attachment_2nd = self.attach_volume(server, volume_2nd)
        body = self.servers_client.list_volume_attachments(
            server['id'])['volumeAttachments']
        self.assertEqual(2, len(body))

        for attachment in [attachment_1st, attachment_2nd]:
            body = self.servers_client.show_volume_attachment(
                server['id'], attachment['id'])['volumeAttachment']
            self.assertEqual(server['id'], body['serverId'])
            self.assertEqual(attachment['volumeId'], body['volumeId'])
            self.assertEqual(attachment['id'], body['id'])
            self.servers_client.detach_volume(server['id'],
                                              attachment['volumeId'])
            waiters.wait_for_volume_resource_status(
                self.volumes_client, attachment['volumeId'], 'available')


class AttachVolumeShelveTestJSON(AttachVolumeTestJSON):
    """Testing volume with shelved instance.

    This test checks the attaching and detaching volumes from
    a shelved or shelved offload instance.
    """

    min_microversion = '2.20'
    max_microversion = 'latest'

    @classmethod
    def skip_checks(cls):
        super(AttachVolumeShelveTestJSON, cls).skip_checks()
        if not CONF.compute_feature_enabled.shelve:
            raise cls.skipException('Shelve is not available.')

    def _count_volumes(self, server, validation_resources):
        # Count number of volumes on an instance
        volumes = 0
        if CONF.validation.run_validation:
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server, validation_resources),
                self.image_ssh_user,
                self.image_ssh_password,
                validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.servers_client)

            command = 'grep -c -E [vs]d.$ /proc/partitions'
            volumes = int(linux_client.exec_command(command).strip())
        return volumes

    def _shelve_server(self, server, validation_resources):
        # NOTE(andreaf) If we are going to shelve a server, we should
        # check first whether the server is ssh-able. Otherwise we
        # won't be able to distinguish failures introduced by shelve
        # from pre-existing ones. Also it's good to wait for cloud-init
        # to be done and sshd server to be running before shelving to
        # avoid breaking the VM
        if CONF.validation.run_validation:
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server, validation_resources),
                self.image_ssh_user,
                self.image_ssh_password,
                validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.servers_client)
            linux_client.validate_authentication()

        # If validation went ok, or it was skipped, shelve the server
        compute.shelve_server(self.servers_client, server['id'])

    def _unshelve_server_and_check_volumes(self, server,
                                           validation_resources,
                                           number_of_volumes):
        # Unshelve the instance and check that there are expected volumes
        self.servers_client.unshelve_server(server['id'])
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'],
                                       'ACTIVE')
        if CONF.validation.run_validation:
            counted_volumes = self._count_volumes(
                server, validation_resources)
            self.assertEqual(number_of_volumes, counted_volumes)

    @decorators.idempotent_id('13a940b6-3474-4c3c-b03f-29b89112bfee')
    def test_attach_volume_shelved_or_offload_server(self):
        # Create server, count number of volumes on it, shelve
        # server and attach pre-created volume to shelved server
        server, validation_resources = self._create_server()
        volume = self.create_volume()
        num_vol = self._count_volumes(server, validation_resources)
        self._shelve_server(server, validation_resources)
        attachment = self.attach_volume(server, volume,
                                        device=('/dev/%s' % self.device),
                                        check_reserved=True)

        # Unshelve the instance and check that attached volume exists
        self._unshelve_server_and_check_volumes(
            server, validation_resources, num_vol + 1)

        # Get volume attachment of the server
        volume_attachment = self.servers_client.show_volume_attachment(
            server['id'],
            attachment['id'])['volumeAttachment']
        self.assertEqual(server['id'], volume_attachment['serverId'])
        self.assertEqual(attachment['id'], volume_attachment['id'])
        # Check the mountpoint is not None after unshelve server even in
        # case of shelved_offloaded.
        self.assertIsNotNone(volume_attachment['device'])

    @decorators.idempotent_id('b54e86dd-a070-49c4-9c07-59ae6dae15aa')
    def test_detach_volume_shelved_or_offload_server(self):
        # Count number of volumes on instance, shelve
        # server and attach pre-created volume to shelved server
        server, validation_resources = self._create_server()
        volume = self.create_volume()
        num_vol = self._count_volumes(server, validation_resources)
        self._shelve_server(server, validation_resources)

        # Attach and then detach the volume
        self.attach_volume(server, volume, device=('/dev/%s' % self.device),
                           check_reserved=True)
        self.servers_client.detach_volume(server['id'], volume['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')

        # Unshelve the instance and check that we have the expected number of
        # volume(s)
        self._unshelve_server_and_check_volumes(
            server, validation_resources, num_vol)
