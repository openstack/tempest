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
from tempest.tests.compute import base


class VolumesGetTestBase(object):

    @attr(type='smoke')
    def test_volume_create_get_delete(self):
        """CREATE, GET, DELETE Volume"""
        try:
            v_name = rand_name('Volume-%s-') % self._interface
            metadata = {'Type': 'work'}
            #Create volume
            resp, volume = self.client.create_volume(size=1,
                                                     display_name=v_name,
                                                     metadata=metadata)
            self.assertEqual(200, resp.status)
            self.assertTrue('id' in volume)
            self.assertTrue('displayName' in volume)
            self.assertEqual(volume['displayName'], v_name,
            "The created volume name is not equal to the requested name")
            self.assertTrue(volume['id'] is not None,
            "Field volume id is empty or not found.")
            #Wait for Volume status to become ACTIVE
            self.client.wait_for_volume_status(volume['id'], 'available')
            #GET Volume
            resp, fetched_volume = self.client.get_volume(volume['id'])
            self.assertEqual(200, resp.status)
            #Verfication of details of fetched Volume
            self.assertEqual(v_name,
                             fetched_volume['displayName'],
                             'The fetched Volume is different '
                             'from the created Volume')
            self.assertEqual(volume['id'],
                             fetched_volume['id'],
                             'The fetched Volume is different '
                             'from the created Volume')
            self.assertEqual(metadata,
                             fetched_volume['metadata'],
                             'The fetched Volume is different '
                             'from the created Volume')

        finally:
            #Delete the Volume created in this method
            resp, _ = self.client.delete_volume(volume['id'])
            self.assertEqual(202, resp.status)
            #Checking if the deleted Volume still exists
            self.client.wait_for_resource_deletion(volume['id'])

    @attr(type='positive')
    def test_volume_get_metadata_none(self):
        """CREATE, GET empty metadata dict"""
        try:
            v_name = rand_name('Volume-')
            #Create volume
            resp, volume = self.client.create_volume(size=1,
                                                     display_name=v_name,
                                                     metadata={})
            self.assertEqual(200, resp.status)
            self.assertTrue('id' in volume)
            self.assertTrue('displayName' in volume)
            #Wait for Volume status to become ACTIVE
            self.client.wait_for_volume_status(volume['id'], 'available')
            #GET Volume
            resp, fetched_volume = self.client.get_volume(volume['id'])
            self.assertEqual(200, resp.status)
            self.assertEqual(fetched_volume['metadata'], {})
        finally:
            #Delete the Volume created in this method
            resp, _ = self.client.delete_volume(volume['id'])
            self.assertEqual(202, resp.status)
            #Checking if the deleted Volume still exists
            self.client.wait_for_resource_deletion(volume['id'])


class VolumesGetTestXML(base.BaseComputeTestXML, VolumesGetTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = "xml"
        super(VolumesGetTestXML, cls).setUpClass()
        cls.client = cls.volumes_extensions_client


class VolumesGetTestJSON(base.BaseComputeTestJSON, VolumesGetTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = "json"
        super(VolumesGetTestJSON, cls).setUpClass()
        cls.client = cls.volumes_extensions_client
