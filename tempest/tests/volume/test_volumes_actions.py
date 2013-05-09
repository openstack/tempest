# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from tempest.common.utils.data_utils import rand_name
from tempest.tests.volume.base import BaseVolumeTest


class VolumesActionsTest(BaseVolumeTest):

    @classmethod
    def setUpClass(cls):
        super(VolumesActionsTest, cls).setUpClass()
        cls.client = cls.volumes_client
        cls.servers_client = cls.servers_client

        # Create a test shared instance and volume for attach/detach tests
        srv_name = rand_name('Instance-')
        vol_name = rand_name('Volume-')
        resp, cls.server = cls.servers_client.create_server(srv_name,
                                                            cls.image_ref,
                                                            cls.flavor_ref)
        cls.servers_client.wait_for_server_status(cls.server['id'], 'ACTIVE')

        resp, cls.volume = cls.client.create_volume(size=1,
                                                    display_name=vol_name)
        cls.client.wait_for_volume_status(cls.volume['id'], 'available')

    @classmethod
    def tearDownClass(cls):
        # Delete the test instance and volume
        cls.client.delete_volume(cls.volume['id'])
        cls.servers_client.delete_server(cls.server['id'])
        super(VolumesActionsTest, cls).tearDownClass()

    @attr(type='smoke')
    def test_attach_detach_volume_to_instance(self):
        """Volume is attached and detached successfully from an instance"""
        try:
            mountpoint = '/dev/vdc'
            resp, body = self.client.attach_volume(self.volume['id'],
                                                   self.server['id'],
                                                   mountpoint)
            self.assertEqual(202, resp.status)
            self.client.wait_for_volume_status(self.volume['id'], 'in-use')
        except:
            self.fail("Could not attach volume to instance")
        finally:
            # Detach the volume from the instance
            resp, body = self.client.detach_volume(self.volume['id'])
            self.assertEqual(202, resp.status)
            self.client.wait_for_volume_status(self.volume['id'], 'available')

    def test_get_volume_attachment(self):
        """Verify that a volume's attachment information is retrieved"""
        mountpoint = '/dev/vdc'
        resp, body = self.client.attach_volume(self.volume['id'],
                                               self.server['id'],
                                               mountpoint)
        self.client.wait_for_volume_status(self.volume['id'], 'in-use')
        self.assertEqual(202, resp.status)
        try:
            resp, volume = self.client.get_volume(self.volume['id'])
            self.assertEqual(200, resp.status)
            self.assertTrue('attachments' in volume)
            attachment = volume['attachments'][0]
            self.assertEqual(mountpoint, attachment['device'])
            self.assertEqual(self.server['id'], attachment['server_id'])
            self.assertEqual(self.volume['id'], attachment['id'])
            self.assertEqual(self.volume['id'], attachment['volume_id'])
        except:
            self.fail("Could not get attachment details from volume")
        finally:
            self.client.detach_volume(self.volume['id'])
            self.client.wait_for_volume_status(self.volume['id'], 'available')
