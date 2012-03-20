from nose.plugins.attrib import attr
import unittest2 as unittest
from tempest import openstack
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions


class VolumesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.volumes_client

    @attr(type='negative')
    def test_volume_get_nonexistant_volume_id(self):
        """Negative: Should not be able to get details of nonexistant volume"""
        #Creating a nonexistant volume id
        volume_id_list = list()
        resp, body = self.client.list_volumes()
        for i in range(len(body)):
            volume_id_list.append(body[i]['id'])
        while True:
            non_exist_id = rand_name('999')
            if non_exist_id not in volume_id_list:
                break
        #Trying to GET a non existant volume
        try:
            resp, body = self.client.get_volume(non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to GET the details from a '
                      'nonexistant volume')

    @attr(type='negative')
    def test_volume_delete_nonexistant_volume_id(self):
        """Negative: Should not be able to delete nonexistant Volume"""
        #Creating nonexistant volume id
        volume_id_list = list()
        resp, body = self.client.list_volumes()
        for i in range(len(body)):
            volume_id_list.append(body[i]['id'])
        while True:
            non_exist_id = rand_name('999')
            if non_exist_id not in volume_id_list:
                break
        #Trying to DELETE a non existant volume
        try:
            resp, body = self.client.delete_volume(non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to DELETE a nonexistant volume')
