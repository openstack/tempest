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
from tempest.common import utils
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class BaseAttachVolumeTest(base.BaseV2ComputeTest):
    """Base class for the attach volume tests in this module."""

    @classmethod
    def skip_checks(cls):
        super(BaseAttachVolumeTest, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(BaseAttachVolumeTest, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(BaseAttachVolumeTest, cls).resource_setup()
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


class AttachVolumeTestJSON(BaseAttachVolumeTest):

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


class AttachVolumeShelveTestJSON(BaseAttachVolumeTest):
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
                                        device=('/dev/%s' % self.device))

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
        self.attach_volume(server, volume, device=('/dev/%s' % self.device))
        self.servers_client.detach_volume(server['id'], volume['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')

        # Unshelve the instance and check that we have the expected number of
        # volume(s)
        self._unshelve_server_and_check_volumes(
            server, validation_resources, num_vol)


class AttachVolumeMultiAttachTest(BaseAttachVolumeTest):
    min_microversion = '2.60'
    max_microversion = 'latest'

    @classmethod
    def skip_checks(cls):
        super(AttachVolumeMultiAttachTest, cls).skip_checks()
        if not CONF.compute_feature_enabled.volume_multiattach:
            raise cls.skipException('Volume multi-attach is not available.')

    def _attach_volume_to_servers(self, volume, servers):
        """Attaches the given volume to the list of servers.

        :param volume: The multiattach volume to use.
        :param servers: list of server instances on which the volume will be
                        attached
        :returns: dict of server ID to volumeAttachment dict entries
        """
        attachments = {}
        for server in servers:
            # map the server id to the volume attachment
            attachments[server['id']] = self.attach_volume(server, volume)
            # NOTE(mriedem): In the case of multi-attach, after the first
            # attach the volume will be in-use. On the second attach, nova will
            # 'reserve' the volume which puts it back into 'attaching' status
            # and then the volume shouldn't go back to in-use until the compute
            # actually attaches the server to the volume.
        return attachments

    def _detach_multiattach_volume(self, volume_id, server_id):
        """Detaches a multiattach volume from the given server.

        Depending on the number of attachments the volume has, this method
        will wait for the volume to go to back to 'in-use' status if there are
        more attachments or 'available' state if there are no more attachments.
        """
        # Count the number of attachments before starting the detach.
        volume = self.volumes_client.show_volume(volume_id)['volume']
        attachments = volume['attachments']
        wait_status = 'in-use' if len(attachments) > 1 else 'available'
        # Now detach the volume from the given server.
        self.servers_client.detach_volume(server_id, volume_id)
        # Now wait for the volume status to change.
        waiters.wait_for_volume_resource_status(
            self.volumes_client, volume_id, wait_status)

    def _create_multiattach_volume(self, bootable=False):
        kwargs = {}
        if bootable:
            kwargs['image_ref'] = CONF.compute.image_ref
        return self.create_volume(multiattach=True, **kwargs)

    def _create_and_multiattach(self):
        """Creates two server instances and a volume and attaches to both.

        :returns: A three-item tuple of the list of created servers,
                  the created volume, and dict of server ID to volumeAttachment
                  dict entries
        """
        servers = []
        for x in range(2):
            name = 'multiattach-server-%i' % x
            servers.append(self.create_test_server(name=name))

        # Now wait for the servers to be ACTIVE.
        for server in servers:
            waiters.wait_for_server_status(self.servers_client, server['id'],
                                           'ACTIVE')

        volume = self._create_multiattach_volume()

        # Attach the volume to the servers
        attachments = self._attach_volume_to_servers(volume, servers)
        return servers, volume, attachments

    @decorators.idempotent_id('8d5853f7-56e7-4988-9b0c-48cea3c7049a')
    def test_list_get_volume_attachments_multiattach(self):
        # Attach a single volume to two servers.
        servers, volume, attachments = self._create_and_multiattach()

        # List attachments from the volume and make sure the server uuids
        # are in that list.
        vol_attachments = self.volumes_client.show_volume(
            volume['id'])['volume']['attachments']
        attached_server_ids = [attachment['server_id']
                               for attachment in vol_attachments]
        self.assertEqual(2, len(attached_server_ids))

        # List Volume attachment of the servers
        for server in servers:
            self.assertIn(server['id'], attached_server_ids)
            vol_attachments = self.servers_client.list_volume_attachments(
                server['id'])['volumeAttachments']
            self.assertEqual(1, len(vol_attachments))
            attachment = attachments[server['id']]
            self.assertDictEqual(attachment, vol_attachments[0])
            # Detach the volume from this server.
            self._detach_multiattach_volume(volume['id'], server['id'])

    def _boot_from_multiattach_volume(self):
        """Boots a server from a multiattach volume.

        The volume will not be deleted when the server is deleted.

        :returns: 2-item tuple of (server, volume)
        """
        volume = self._create_multiattach_volume(bootable=True)
        # Now create a server from the bootable volume.
        bdm = [{
            'uuid': volume['id'],
            'source_type': 'volume',
            'destination_type': 'volume',
            'boot_index': 0,
            'delete_on_termination': False}]
        server = self.create_test_server(
            image_id='', block_device_mapping_v2=bdm, wait_until='ACTIVE')
        # Assert the volume is attached to the server.
        attachments = self.servers_client.list_volume_attachments(
            server['id'])['volumeAttachments']
        self.assertEqual(1, len(attachments))
        self.assertEqual(volume['id'], attachments[0]['volumeId'])
        return server, volume

    @decorators.idempotent_id('65e33aa2-185b-44c8-b22e-e524973ed625')
    def test_boot_from_multiattach_volume(self):
        """Simple test to boot an instance from a multiattach volume."""
        self._boot_from_multiattach_volume()

    @utils.services('image')
    @decorators.idempotent_id('885ac48a-2d7a-40c5-ae8b-1993882d724c')
    def test_snapshot_volume_backed_multiattach(self):
        """Boots a server from a multiattach volume and snapshots the server.

        Creating the snapshot of the server will also create a snapshot of
        the volume.
        """
        server, volume = self._boot_from_multiattach_volume()
        # Create a snapshot of the server (and volume implicitly).
        self.create_image_from_server(
            server['id'], name='multiattach-snapshot',
            wait_until='active', wait_for_server=True)
        # TODO(mriedem): Make sure the volume snapshot exists. This requires
        # adding the volume snapshots client to BaseV2ComputeTest.
        # Delete the server, wait for it to be gone, and make sure the volume
        # still exists.
        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])
        # Delete the volume and cascade the delete of the volume snapshot.
        self.volumes_client.delete_volume(volume['id'], cascade=True)
        # Now we have to wait for the volume to be gone otherwise the normal
        # teardown will fail since it will race with our call and the snapshot
        # might still exist.
        self.volumes_client.wait_for_resource_deletion(volume['id'])

    @decorators.idempotent_id('f01c7169-a124-4fc7-ae60-5e380e247c9c')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_resize_server_with_multiattached_volume(self):
        # Attach a single volume to multiple servers, then resize the servers
        servers, volume, _ = self._create_and_multiattach()

        for server in servers:
            self.resize_server(server['id'], self.flavor_ref_alt)

        for server in servers:
            self._detach_multiattach_volume(volume['id'], server['id'])

    # TODO(mriedem): Might be interesting to create a bootable multiattach
    # volume with delete_on_termination=True, create server1 from the
    # volume, then attach it to server2, and then delete server1 in which
    # case the volume won't be deleted because it's still attached to
    # server2 and make sure the volume is still attached to server2.
