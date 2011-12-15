from nose.plugins.attrib import attr
from tempest import openstack
import tempest.config
import unittest2 as unittest


class ExtentionsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.extensions_client
        cls.config = cls.os.config

    @attr(type='smoke')
    def test_list_extensions(self):
        """List of all extensions"""
        resp, extensions = self.client.list_extensions()
        self.assertTrue("extensions" in extensions)
        self.assertEqual(200, resp.status)
