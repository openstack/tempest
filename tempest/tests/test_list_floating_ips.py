from nose.plugins.attrib import attr
from tempest import openstack
import unittest2 as unittest
from tempest import exceptions
from tempest.common.utils.data_utils import rand_name


class FloatingIPDetailsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.floating_ips_client
        cls.floating_ip = []
        cls.floating_ip_id = []
        cls.random_number = 0
        for i in range(3):
            resp, body = cls.client.create_floating_ip()
            cls.floating_ip.append(body)
            cls.floating_ip_id.append(body['id'])

    @classmethod
    def tearDownClass(cls):
        for i in range(3):
            cls.client.delete_floating_ip(cls.floating_ip_id[i])

    @attr(type='positive')
    def test_list_floating_ips(self):
        """Positive test:Should return the list of floating IPs"""
        resp, body = self.client.list_floating_ips()
        self.assertEqual(200, resp.status)
        floating_ips = body
        self.assertNotEqual(0, len(floating_ips),
                            "Expected floating IPs. Got zero.")
        for i in range(3):
            self.assertTrue(self.floating_ip[i] in floating_ips)

    @attr(type='positive')
    def test_get_floating_ip_details(self):
        """Positive test:Should be able to GET the details of floatingIP"""
        #Creating a floating IP for which details are to be checked
        resp, body = self.client.create_floating_ip()
        floating_ip_instance_id = body['instance_id']
        floating_ip_ip = body['ip']
        floating_ip_fixed_ip = body['fixed_ip']
        floating_ip_id = body['id']
        resp, body = \
            self.client.get_floating_ip_details(floating_ip_id)
        self.assertEqual(200, resp.status)
        #Comparing the details of floating IP
        self.assertEqual(floating_ip_instance_id,
                            body['instance_id'])
        self.assertEqual(floating_ip_ip, body['ip'])
        self.assertEqual(floating_ip_fixed_ip,
                            body['fixed_ip'])
        self.assertEqual(floating_ip_id, body['id'])
        #Deleting the floating IP created in this method
        self.client.delete_floating_ip(floating_ip_id)

    @attr(type='negative')
    def test_get_nonexistant_floating_ip_details(self):
        """
        Negative test:Should not be able to GET the details
        of nonexistant floating IP
        """
        floating_ip_id = []
        resp, body = self.client.list_floating_ips()
        for i in range(len(body)):
            floating_ip_id.append(body[i]['id'])
        #Creating a nonexistant floatingIP id
        while True:
            non_exist_id = rand_name('999')
            if non_exist_id not in floating_ip_id:
                break
        try:
            resp, body = \
            self.client.get_floating_ip_details(non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to GET the details from a'
                      'nonexistant floating IP')
