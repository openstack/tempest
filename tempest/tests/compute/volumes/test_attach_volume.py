# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 IBM
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

from nose.plugins.attrib import attr
import unittest2 as unittest

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest.common.utils.linux.remote_client import RemoteClient
import tempest.config
from tempest.tests.compute import base


class AttachVolumeTest(object):

    run_ssh = tempest.config.TempestConfig().compute.run_ssh

    @staticmethod
    def setUpClass(cls):
        cls.device = 'vdb'

    def _detach(self, server_id, volume_id):
        self.servers_client.detach_volume(server_id, volume_id)
        self.volumes_client.wait_for_volume_status(volume_id, 'available')

    def _delete(self, server_id, volume_id):
        self.volumes_client.delete_volume(volume_id)
        self.servers_client.delete_server(server_id)

    def _create_and_attach(self):
        name = rand_name('server')

        # Start a server and wait for it to become ready
        resp, server = self.servers_client.create_server(name,
                                                         self.image_ref,
                                                         self.flavor_ref,
                                                         adminPass='password')
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        # Record addresses so that we can ssh later
        resp, server['addresses'] = \
            self.servers_client.list_addresses(server['id'])

        # Create a volume and wait for it to become ready
        resp, volume = self.volumes_client.create_volume(1,
                                                         display_name='test')
        self.volumes_client.wait_for_volume_status(volume['id'], 'available')

        # Attach the volume to the server
        self.servers_client.attach_volume(server['id'], volume['id'],
                                          device='/dev/%s' % self.device)
        self.volumes_client.wait_for_volume_status(volume['id'], 'in-use')

        return server, volume

    @attr(type='positive')
    @unittest.skipIf(not run_ssh, 'SSH required for this test')
    def test_attach_detach_volume(self):
        # Stop and Start a server with an attached volume, ensuring that
        # the volume remains attached.
        server, volume = self._create_and_attach()

        attached = True

        try:
            self.servers_client.stop(server['id'])
            self.servers_client.wait_for_server_status(server['id'], 'SHUTOFF')

            self.servers_client.start(server['id'])
            self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

            linux_client = RemoteClient(server,
                                        self.ssh_user, server['adminPass'])
            partitions = linux_client.get_partitions()
            self.assertTrue(self.device in partitions)

            self._detach(server['id'], volume['id'])
            attached = False

            self.servers_client.stop(server['id'])
            self.servers_client.wait_for_server_status(server['id'], 'SHUTOFF')

            self.servers_client.start(server['id'])
            self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

            linux_client = RemoteClient(server,
                                        self.ssh_user, server['adminPass'])
            partitions = linux_client.get_partitions()
            self.assertFalse(self.device in partitions)
        finally:
            if attached:
                self._detach(server['id'], volume['id'])
            self._delete(server['id'], volume['id'])


class TestAttachVolumeJSON(base.BaseComputeTestJSON,
                           AttachVolumeTest):
    @classmethod
    def setUpClass(cls):
        super(TestAttachVolumeJSON, cls).setUpClass()
        AttachVolumeTest.setUpClass(cls)


class TestAttachVolumeXML(base.BaseComputeTestXML,
                          AttachVolumeTest):
    @classmethod
    def setUpClass(cls):
        super(TestAttachVolumeXML, cls).setUpClass()
        AttachVolumeTest.setUpClass(cls)
