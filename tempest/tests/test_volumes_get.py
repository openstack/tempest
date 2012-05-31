from nose.plugins.attrib import attr
import unittest2 as unittest
from unittest.case import SkipTest
from tempest import openstack
from tempest.common.utils.data_utils import rand_name


class VolumesGetTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.volumes_client

    @attr(type='smoke')
    def test_volume_create_get_delete(self):
        """CREATE, GET, DELETE Volume"""
        try:
            v_name = rand_name('Volume-')
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
            resp, fetched_list = self.client.list_volumes()
            self.assertTrue(fetched_volume not in fetched_list,
                            'The Volume is not Deleted')

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
