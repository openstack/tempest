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
from tempest.common.utils.linux.remote_client import RemoteClient
from tempest import config
from tempest.test import attr

CONF = config.CONF


class AttachVolumeV3TestJSON(base.BaseV3ComputeTest):
    _interface = 'json'
    run_ssh = CONF.compute.run_ssh

    def __init__(self, *args, **kwargs):
        super(AttachVolumeV3TestJSON, self).__init__(*args, **kwargs)
        self.server = None
        self.volume = None
        self.attached = False

    @classmethod
    def setUpClass(cls):
        super(AttachVolumeV3TestJSON, cls).setUpClass()
        cls.device = cls.config.compute.volume_device_name
        if not cls.config.service_available.cinder:
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
        resp, server = self.create_test_server(wait_until='ACTIVE',
                                               admin_password=admin_pass)
        self.server = server

        # Record addresses so that we can ssh later
        resp, server['addresses'] = \
            self.servers_client.list_addresses(server['id'])

        # Create a volume and wait for it to become ready
        resp, volume = self.volumes_client.create_volume(1,
                                                         display_name='test')
        self.volume = volume
        self.addCleanup(self._delete_volume)
        self.volumes_client.wait_for_volume_status(volume['id'], 'available')

        # Attach the volume to the server
        self.servers_client.attach_volume(server['id'], volume['id'],
                                          device='/dev/%s' % self.device)
        self.volumes_client.wait_for_volume_status(volume['id'], 'in-use')

        self.attached = True
        self.addCleanup(self._detach, server['id'], volume['id'])

    @testtools.skipIf(not run_ssh, 'SSH required for this test')
    @attr(type='gate')
    def test_attach_detach_volume(self):
        # Stop and Start a server with an attached volume, ensuring that
        # the volume remains attached.
        self._create_and_attach()
        server = self.server
        volume = self.volume

        self.servers_client.stop(server['id'])
        self.servers_client.wait_for_server_status(server['id'], 'SHUTOFF')

        self.servers_client.start(server['id'])
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        linux_client = RemoteClient(server,
                                    self.image_ssh_user,
                                    server['admin_password'])
        partitions = linux_client.get_partitions()
        self.assertIn(self.device, partitions)

        self._detach(server['id'], volume['id'])
        self.attached = False

        self.servers_client.stop(server['id'])
        self.servers_client.wait_for_server_status(server['id'], 'SHUTOFF')

        self.servers_client.start(server['id'])
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        linux_client = RemoteClient(server,
                                    self.image_ssh_user,
                                    server['admin_password'])
        partitions = linux_client.get_partitions()
        self.assertNotIn(self.device, partitions)
