# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 IBM Corp.
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
import tempest.config
from tempest.test import attr


class AttachVolumeTestJSON(base.BaseComputeTest):
    _interface = 'json'
    run_ssh = tempest.config.TempestConfig().compute.run_ssh

    def __init__(self, *args, **kwargs):
        super(AttachVolumeTestJSON, self).__init__(*args, **kwargs)
        self.server = None
        self.volume = None
        self.attached = False

    @classmethod
    def setUpClass(cls):
        super(AttachVolumeTestJSON, cls).setUpClass()
        cls.device = 'vdb'
        if not cls.config.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    def _detach(self, server_id, volume_id):
        self.servers_client.detach_volume(server_id, volume_id)
        self.volumes_client.wait_for_volume_status(volume_id, 'available')

    def _delete(self, volume):
        if self.volume:
            self.volumes_client.delete_volume(self.volume['id'])
            self.volume = None

    def _create_and_attach(self):
        # Start a server and wait for it to become ready
        resp, server = self.create_server(wait_until='ACTIVE',
                                          adminPass='password')

        # Record addresses so that we can ssh later
        resp, server['addresses'] = \
            self.servers_client.list_addresses(server['id'])

        # Create a volume and wait for it to become ready
        resp, volume = self.volumes_client.create_volume(1,
                                                         display_name='test')
        self.volume = volume
        self.volumes_client.wait_for_volume_status(volume['id'], 'available')

        # Attach the volume to the server
        self.servers_client.attach_volume(server['id'], volume['id'],
                                          device='/dev/%s' % self.device)
        self.volumes_client.wait_for_volume_status(volume['id'], 'in-use')

        self.attached = True

    @testtools.skipIf(not run_ssh, 'SSH required for this test')
    @attr(type='gate')
    def test_attach_detach_volume(self):
        # Stop and Start a server with an attached volume, ensuring that
        # the volume remains attached.
        try:
            self._create_and_attach()
            server = self.server
            volume = self.volume

            self.servers_client.stop(server['id'])
            self.servers_client.wait_for_server_status(server['id'], 'SHUTOFF')

            self.servers_client.start(server['id'])
            self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

            linux_client = RemoteClient(server,
                                        self.ssh_user, server['adminPass'])
            partitions = linux_client.get_partitions()
            self.assertTrue(self.device in partitions)

            self._detach(server['id'], volume['id'])
            self.attached = False

            self.servers_client.stop(server['id'])
            self.servers_client.wait_for_server_status(server['id'], 'SHUTOFF')

            self.servers_client.start(server['id'])
            self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

            linux_client = RemoteClient(server,
                                        self.ssh_user, server['adminPass'])
            partitions = linux_client.get_partitions()
            self.assertFalse(self.device in partitions)
        except Exception:
            self.fail("The test_attach_detach_volume is faild!")
        finally:
            if self.attached:
                self._detach(server['id'], volume['id'])
            # NOTE(maurosr): here we do the cleanup for volume, servers are
            # dealt on BaseComputeTest.tearDownClass
            self._delete(self.volume)


class AttachVolumeTestXML(AttachVolumeTestJSON):
    _interface = 'xml'
