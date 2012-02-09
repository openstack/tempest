from nose.plugins.attrib import attr
from tempest import openstack
import unittest2 as unittest
from tempest import exceptions
from tempest.common.utils.data_utils import rand_name


class FloatingIPsTest(unittest.TestCase):
    server_id = None
    floating_ip_id = None

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.floating_ips_client
        cls.servers_client = cls.os.servers_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref
        #Server creation
        resp, server = cls.servers_client.create_server('floating-server',
                                                        cls.image_ref,
                                                        cls.flavor_ref)
        cls.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        cls.server_id = server['id']
        resp, body = cls.servers_client.get_server(server['id'])
        cls.fixed_ip_addr = body['addresses']['private'][0]['addr']
        #Floating IP creation
        resp, body = cls.client.create_floating_ip()
        cls.floating_ip_id = body['id']
        #Generating a nonexistant floatingIP id
        cls.floating_ip_ids = []
        resp, body = cls.client.list_floating_ips()
        for i in range(len(body)):
            cls.floating_ip_ids.append(body[i]['id'])
        while True:
            cls.non_exist_id = rand_name('999')
            if cls.non_exist_id not in cls.floating_ip_ids:
                break

    @classmethod
    def tearDownClass(cls):
        #Deleting the server which is created in this method
        resp, body = cls.servers_client.delete_server(cls.server_id)
        #Deleting the floating IP which is created in this method
        resp, body = cls.client.delete_floating_ip(cls.floating_ip_id)

    @attr(type='positive')
    def test_allocate_floating_ip(self):
        """
        Positive test:Allocation of a new floating IP to a project
        should be succesfull
        """
        resp, body = self.client.create_floating_ip()
        self.assertEqual(200, resp.status)
        floating_ip_id_allocated = body['id']
        resp, floating_ip_details = \
                self.client.get_floating_ip_details(floating_ip_id_allocated)
        #Checking if the details of allocated IP is in list of floating IP
        resp, body = self.client.list_floating_ips()
        self.assertTrue(floating_ip_details in body)
        #Deleting the floating IP which is created in this method
        self.client.delete_floating_ip(floating_ip_id_allocated)

    @attr(type='positive')
    def test_delete_floating_ip(self):
        """
        Positive test:Deletion of valid floating IP from project
        should be succesfull
        """
        #Creating the floating IP that is to be deleted in this method
        resp, floating_ip_body = self.client.create_floating_ip()
        #Storing the details of floating IP before deleting it
        resp, floating_ip_details = \
                self.client.get_floating_ip_details(floating_ip_body['id'])
        #Deleting the floating IP from the project
        resp, body = self.client.delete_floating_ip(floating_ip_body['id'])
        self.assertEqual(202, resp.status)
        #Listing the floating IPs and checking the existence
        #of deleted floating IP
        resp, body = self.client.list_floating_ips()
        self.assertTrue(floating_ip_details not in body)

    @attr(type='positive')
    def test_associate_floating_ip(self):
        """
        Positive test:Associate the provided floating IP to a specific server
        should be successfull
       l"""
        #Association of floating IP to fixed IP address
        resp, body =\
        self.client.associate_floating_ip_to_server(self.floating_ip_id,
                                                    self.fixed_ip_addr)
        self.assertEqual(202, resp.status)
        #Disassociation of floating IP that was associated in this method
        resp, body = \
            self.client.disassociate_floating_ip_from_server(
                                                           self.floating_ip_id)

    @attr(type='positive')
    def test_dissociate_floating_ip(self):
        """
        Positive test:Dissociate the provided floating IP
        from a specific server should be successfull
        """
        #Association of floating IP to a specific server
        #so as to check dissociation
        resp, body = \
            self.client.associate_floating_ip_to_server(self.floating_ip_id,
                                                        self.fixed_ip_addr)
        #Disassociation of floating IP
        resp, body = \
        self.client.disassociate_floating_ip_from_server(self.floating_ip_id)
        self.assertEqual(202, resp.status)

    @attr(type='negative')
    def test_delete_nonexistant_floating_ip(self):
        """

        Negative test:Deletion of a nonexistant floating IP
        from project should fail
        """
        #Deleting the non existant floating IP
        try:
            resp, body = self.client.delete_floating_ip(self.non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to delete a nonexistant floating IP')

    @attr(type='negative')
    def test_associate_nonexistant_floating_ip(self):
        """
        Negative test:Association of a non existant floating IP
        to specific server should fail
        """
        #Associating non existant floating IP
        try:
            resp, body = \
            self.client.associate_floating_ip_to_server(self.non_exist_id,
                                                        self.fixed_ip_addr)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to associate'
                      ' a nonexistant floating IP')

    @attr(type='negative')
    def test_dissociate_nonexistant_floating_ip(self):
        """
        Negative test:Dissociation of a non existant floating IP should fail
        """
        #Dissociating non existant floating IP
        try:
            resp, body = \
            self.client.disassociate_floating_ip_from_server(self.non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to dissociate'
                      ' a nonexistant floating IP')
