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
        self.server = None
        self.volume = None
        self.attached = False

    @classmethod
    def setUpClass(cls):
        cls.prepare_instance_network()
        super(AttachVolumeTestJSON, cls).setUpClass()
        cls.device = CONF.compute.volume_device_name
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    def _detach(self, server_id, volume_id):
        if self.attached:
            self.servers_client.detach_volume(server_id, volume_id)
            self.volumes_client.wait_for_volume_status(volume_id, 'available')

    def _delete_volume(self):
        if self.volume:
            self.volumes_client.delete_volume(self.volume['id'])
            self.volume = None

    def _create_and_attach(self):
        # Start a server and wait for it to become ready
        admin_pass = self.image_ssh_password
        _, self.server = self.create_test_server(wait_until='ACTIVE',
                                                 adminPass=admin_pass)

        # Record addresses so that we can ssh later
        _, self.server['addresses'] = \
            self.servers_client.list_addresses(self.server['id'])

        # Create a volume and wait for it to become ready
        _, self.volume = self.volumes_client.create_volume(
            1, display_name='test')
        self.addCleanup(self._delete_volume)
        self.volumes_client.wait_for_volume_status(self.volume['id'],
                                                   'available')

        # Attach the volume to the server
        self.servers_client.attach_volume(self.server['id'],
                                          self.volume['id'],
                                          device='/dev/%s' % self.device)
        self.volumes_client.wait_for_volume_status(self.volume['id'], 'in-use')

        self.attached = True
        self.addCleanup(self._detach, self.server['id'], self.volume['id'])

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
        self.attached = False

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
    def test_list_get_volume_attachment(self):
        # Stop and Start a server with an attached volume, ensuring that
        # the volume remains attached.
        self._create_and_attach()

        self.servers_client.stop(self.server['id'])
        self.servers_client.wait_for_server_status(self.server['id'],
                                                   'SHUTOFF')

        self.servers_client.start(self.server['id'])
        self.servers_client.wait_for_server_status(self.server['id'], 'ACTIVE')

        device_path = '/dev/%s' % self.device

        resp, attachments = self.servers_client.list_volume_attachment(self.server['id'])

        self.assertIn(self.server['id'], map(lambda x: x['serverId'], attachments))
        self.assertIn(self.volume['id'], map(lambda x: x['volumeId'], attachments))
        self.assertIn(device_path, map(lambda x: x['device'], attachments))

        resp, attachment = self.servers_client.get_volume_attachment(self.server['id'],
                                                                     self.volume['id'])

        self.assertEqual(self.server['id'], attachment['serverId'])
        self.assertEqual(self.volume['id'], attachment['volumeId'])
        self.assertEqual(device_path, attachment['device'])


class AttachVolumeTestXML(AttachVolumeTestJSON):
    _interface = 'xml'
