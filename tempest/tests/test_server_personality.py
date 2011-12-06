from nose.plugins.attrib import attr
from tempest import openstack
from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
import base64
import tempest.config
import unittest2 as unittest


class ServerPersonalityTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.servers_client
        cls.config = cls.config = cls.os.config
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref
        cls.user_client = cls.os.limits_client

    def test_personality_files_exceed_limit(self):
        """
        Server creation should fail if greater than the maximum allowed
        number of files are injected into the server.
        """
        name = rand_name('server')
        file_contents = 'This is a test file.'
        personality = []
        resp, max_file_limit = self.user_client.get_personality_file_limit()
        for i in range(0, max_file_limit + 1):
            path = 'etc/test' + str(i) + '.txt'
            personality.append({'path': path,
                                'contents': base64.b64encode(file_contents)})
        try:
            resp, resp_body = self.client.create_server(name, self.image_ref,
                                                   self.flavor_ref,
                                                   personality=personality)
        except exceptions.OverLimit:
            pass
        else:
            self.fail('This request did not fail as expected')

    @attr(type='positive')
    def test_can_create_server_with_max_number_personality_files(self):
        """
        Server should be created successfully if maximum allowed number of
        files is injected into the server during creation.
        """
        name = rand_name('server')
        file_contents = 'This is a test file.'

        resp, max_file_limit = self.user_client.get_personality_file_limit()
        self.assertEqual(200, resp.status)

        personality = []
        for i in range(0, max_file_limit):
            path = 'etc/test' + str(i) + '.txt'
            personality.append({'path': path,
                                'contents': base64.b64encode(file_contents)})

        resp, server = self.client.create_server(name, self.image_ref,
                                               self.flavor_ref,
                                               personality=personality)
        self.assertEqual('202', resp['status'])

        #Teardown
        self.client.delete_server(server['id'])
