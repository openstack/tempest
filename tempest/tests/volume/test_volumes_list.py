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

import nose
from nose.plugins.attrib import attr

from tempest.common.utils.data_utils import rand_name
from tempest.tests.volume import base


class VolumesListTestBase(object):

    """
    This test creates a number of 1G volumes. To run successfully,
    ensure that the backing file for the volume group that Nova uses
    has space for at least 3 1G volumes!
    If you are running a Devstack environment, ensure that the
    VOLUME_BACKING_FILE_SIZE is atleast 4G in your localrc
    """

    @attr(type='smoke')
    def test_volume_list(self):
        # Get a list of Volumes
        # Fetch all volumes
        resp, fetched_list = self.client.list_volumes()
        self.assertEqual(200, resp.status)
        # Now check if all the volumes created in setup are in fetched list
        missing_vols = [v for v in self.volume_list if v not in fetched_list]
        self.assertFalse(missing_vols,
                         "Failed to find volume %s in fetched list" %
                         ', '.join(m_vol['display_name']
                                   for m_vol in missing_vols))

    @attr(type='smoke')
    def test_volume_list_with_details(self):
        # Get a list of Volumes with details
        # Fetch all Volumes
        resp, fetched_list = self.client.list_volumes_with_detail()
        self.assertEqual(200, resp.status)
        # Verify that all the volumes are returned
        missing_vols = [v for v in self.volume_list if v not in fetched_list]
        self.assertFalse(missing_vols,
                         "Failed to find volume %s in fetched list" %
                         ', '.join(m_vol['display_name']
                                   for m_vol in missing_vols))


class VolumeListTestXML(base.BaseVolumeTestXML, VolumesListTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = 'xml'
        super(VolumeListTestXML, cls).setUpClass()
        cls.client = cls.volumes_client

        # Create 3 test volumes
        cls.volume_list = []
        cls.volume_id_list = []
        for i in range(3):
            v_name = rand_name('volume')
            metadata = {'Type': 'work'}
            try:
                resp, volume = cls.client.create_volume(size=1,
                                                        display_name=v_name,
                                                        metadata=metadata)
                cls.client.wait_for_volume_status(volume['id'], 'available')
                resp, volume = cls.client.get_volume(volume['id'])
                cls.volume_list.append(volume)
                cls.volume_id_list.append(volume['id'])
            except Exception:
                if cls.volume_list:
                    # We could not create all the volumes, though we were able
                    # to create *some* of the volumes. This is typically
                    # because the backing file size of the volume group is
                    # too small. So, here, we clean up whatever we did manage
                    # to create and raise a SkipTest
                    for volume in cls.volume_id_list:
                        cls.client.delete_volume(volume)
                    msg = ("Failed to create ALL necessary volumes to run "
                           "test. This typically means that the backing file "
                           "size of the nova-volumes group is too small to "
                           "create the 3 volumes needed by this test case")
                    raise nose.SkipTest(msg)
                raise

    @classmethod
    def tearDownClass(cls):
        # Delete the created volumes
        for volume in cls.volume_id_list:
            resp, _ = cls.client.delete_volume(volume)
            cls.client.wait_for_resource_deletion(volume)
        super(VolumeListTestXML, cls).tearDownClass()


class VolumeListTestJSON(base.BaseVolumeTestJSON, VolumesListTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = 'json'
        super(VolumeListTestJSON, cls).setUpClass()
        cls.client = cls.volumes_client

        # Create 3 test volumes
        cls.volume_list = []
        cls.volume_id_list = []
        for i in range(3):
            v_name = rand_name('volume')
            metadata = {'Type': 'work'}
            try:
                resp, volume = cls.client.create_volume(size=1,
                                                        display_name=v_name,
                                                        metadata=metadata)
                cls.client.wait_for_volume_status(volume['id'], 'available')
                resp, volume = cls.client.get_volume(volume['id'])
                cls.volume_list.append(volume)
                cls.volume_id_list.append(volume['id'])
            except Exception:
                if cls.volume_list:
                    # We could not create all the volumes, though we were able
                    # to create *some* of the volumes. This is typically
                    # because the backing file size of the volume group is
                    # too small. So, here, we clean up whatever we did manage
                    # to create and raise a SkipTest
                    for volume in cls.volume_id_list:
                        cls.client.delete_volume(volume)
                    msg = ("Failed to create ALL necessary volumes to run "
                           "test. This typically means that the backing file "
                           "size of the nova-volumes group is too small to "
                           "create the 3 volumes needed by this test case")
                    raise nose.SkipTest(msg)
                raise

    @classmethod
    def tearDownClass(cls):
        # Delete the created volumes
        for volume in cls.volume_id_list:
            resp, _ = cls.client.delete_volume(volume)
            cls.client.wait_for_resource_deletion(volume)
        super(VolumeListTestJSON, cls).tearDownClass()
