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


from tempest.common.utils.data_utils import rand_name
from tempest.tests.compute import base


class VolumesTestBase(object):

    """
    This test creates a number of 1G volumes. To run successfully,
    ensure that the backing file for the volume group that Nova uses
    has space for at least 3 1G volumes!
    If you are running a Devstack environment, ensure that the
    VOLUME_BACKING_FILE_SIZE is atleast 4G in your localrc
    """

    def test_volume_list(self):
        # Should return the list of Volumes
        # Fetch all Volumes
        resp, fetched_list = self.client.list_volumes()
        self.assertEqual(200, resp.status)
        # Now check if all the Volumes created in setup are in fetched list
        missing_volumes = [
            v for v in self.volume_list if v not in fetched_list
        ]

        self.assertFalse(missing_volumes,
                         "Failed to find volume %s in fetched list" %
                         ', '.join(m_vol['displayName']
                                   for m_vol in missing_volumes))

    def test_volume_list_with_details(self):
        # Should return the list of Volumes with details
        #Fetch all Volumes
        resp, fetched_list = self.client.list_volumes_with_detail()
        self.assertEqual(200, resp.status)
        #Now check if all the Volumes created in setup are in fetched list
        missing_volumes = [
            v for v in self.volume_list if v not in fetched_list
        ]

        self.assertFalse(missing_volumes,
                         "Failed to find volume %s in fetched list" %
                         ', '.join(m_vol['displayName']
                                   for m_vol in missing_volumes))


class VolumesTestXML(base.BaseComputeTestXML, VolumesTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = 'xml'
        super(VolumesTestXML, cls).setUpClass()
        cls.client = cls.volumes_extensions_client
        # Create 3 Volumes
        cls.volume_list = list()
        cls.volume_id_list = list()
        for i in range(3):
            v_name = rand_name('volume')
            metadata = {'Type': 'work'}
            v_name += cls._interface
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
                    for volume in cls.volume_list:
                        cls.client.delete_volume(volume)
                    msg = ("Failed to create ALL necessary volumes to run "
                           "test. This typically means that the backing file "
                           "size of the nova-volumes group is too small to "
                           "create the 3 volumes needed by this test case")
                    raise cls.skipException(msg)
                raise

    @classmethod
    def tearDownClass(cls):
        # Delete the created Volumes
        for volume in cls.volume_list:
            resp, _ = cls.client.delete_volume(volume['id'])
            cls.client.wait_for_resource_deletion(volume['id'])
        super(VolumesTestXML, cls).tearDownClass()


class VolumesTestJSON(base.BaseComputeTestJSON, VolumesTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = 'json'
        super(VolumesTestJSON, cls).setUpClass()
        cls.client = cls.volumes_extensions_client
        # Create 3 Volumes
        cls.volume_list = []
        cls.volume_id_list = []
        for i in range(3):
            v_name = rand_name('volume-%s')
            metadata = {'Type': 'work'}
            v_name += cls._interface
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
                    for volume in cls.volume_list:
                        cls.client.delete_volume(volume)
                    msg = ("Failed to create ALL necessary volumes to run "
                           "test. This typically means that the backing file "
                           "size of the nova-volumes group is too small to "
                           "create the 3 volumes needed by this test case")
                    raise cls.skipException(msg)
                raise

    @classmethod
    def tearDownClass(cls):
        # Delete the created Volumes
        for volume in cls.volume_list:
            resp, _ = cls.client.delete_volume(volume['id'])
            cls.client.wait_for_resource_deletion(volume['id'])
        super(VolumesTestJSON, cls).tearDownClass()
