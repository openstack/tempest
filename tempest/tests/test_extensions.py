from nose.plugins.attrib import attr
from tempest import openstack
import tempest.config
from base_compute_test import BaseComputeTest


class ExtentionsTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        cls.client = cls.extensions_client

    @attr(type='smoke')
    def test_list_extensions(self):
        """List of all extensions"""
        resp, extensions = self.client.list_extensions()
        self.assertTrue("extensions" in extensions)
        self.assertEqual(200, resp.status)
