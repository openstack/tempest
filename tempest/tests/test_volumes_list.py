from nose.plugins.attrib import attr
import unittest2 as unittest
from tempest import openstack
from tempest.common.utils.data_utils import rand_name


class VolumesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.volumes_client
        #Create 3 Volumes
        cls.volume_list = list()
        cls.volume_id_list = list()
        for i in range(3):
            v_name = rand_name('Name-')
            metadata = {'Type': 'work'}
            resp, volume = cls.client.create_volume(size=1,
                                                     display_name=v_name,
                                                     metadata=metadata)
            cls.client.wait_for_volume_status(volume['id'],
                                               'available')
            resp, volume = cls.client.get_volume(volume['id'])
            cls.volume_list.append(volume)
            cls.volume_id_list.append(volume['id'])

    @classmethod
    def tearDownClass(cls):
        #Delete the created Volumes
        for i in range(3):
            resp, _ = cls.client.delete_volume(cls.volume_id_list[i])

    @attr(type='smoke')
    def test_volume_list(self):
        """Should return the list of Volumes"""
        #Fetch all Volumes
        resp, fetched_list = self.client.list_volumes()
        self.assertEqual(200, resp.status)
        #Now check if all the Volumes created in setup are in fetched list
        missing_volumes =\
        [v for v in self.volume_list if v not in fetched_list]
        self.assertFalse(missing_volumes,
                         "Failed to find volume %s in fetched list"
                         % ', '.join(m_vol['displayName']
                                        for m_vol in missing_volumes))

    @attr(type='smoke')
    def test_volume_list_with_details(self):
        """Should return the list of Volumes with details"""
        #Fetch all Volumes
        resp, fetched_list = self.client.list_volumes_with_detail()
        self.assertEqual(200, resp.status)
        #Now check if all the Volumes created in setup are in fetched list
        missing_volumes =\
        [v for v in self.volume_list if v not in fetched_list]
        self.assertFalse(missing_volumes,
                         "Failed to find volume %s in fetched list"
                         % ', '.join(m_vol['displayName']
                                        for m_vol in missing_volumes))
