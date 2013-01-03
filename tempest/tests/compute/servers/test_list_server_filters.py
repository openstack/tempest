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
import nose.plugins.skip
import unittest2 as unittest

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.tests.compute import base
from tempest.tests import utils


class ListServerFiltersTest(object):

    @staticmethod
    def setUpClass(cls):
        cls.client = cls.servers_client

        # Check to see if the alternate image ref actually exists...
        images_client = cls.images_client
        resp, images = images_client.list_images()

        if cls.image_ref != cls.image_ref_alt and \
            any([image for image in images
                 if image['id'] == cls.image_ref_alt]):
            cls.multiple_images = True
        else:
            cls.image_ref_alt = cls.image_ref

        # Do some sanity checks here. If one of the images does
        # not exist, fail early since the tests won't work...
        try:
            cls.images_client.get_image(cls.image_ref)
        except exceptions.NotFound:
            raise RuntimeError("Image %s (image_ref) was not found!" %
                               cls.image_ref)

        try:
            cls.images_client.get_image(cls.image_ref_alt)
        except exceptions.NotFound:
            raise RuntimeError("Image %s (image_ref_alt) was not found!" %
                               cls.image_ref_alt)

        cls.s1_name = rand_name('server')
        resp, cls.s1 = cls.client.create_server(cls.s1_name, cls.image_ref,
                                                cls.flavor_ref)
        cls.s2_name = rand_name('server')
        resp, cls.s2 = cls.client.create_server(cls.s2_name, cls.image_ref_alt,
                                                cls.flavor_ref)
        cls.s3_name = rand_name('server')
        resp, cls.s3 = cls.client.create_server(cls.s3_name, cls.image_ref,
                                                cls.flavor_ref_alt)

        cls.client.wait_for_server_status(cls.s1['id'], 'ACTIVE')
        resp, cls.s1 = cls.client.get_server(cls.s1['id'])
        cls.client.wait_for_server_status(cls.s2['id'], 'ACTIVE')
        resp, cls.s2 = cls.client.get_server(cls.s2['id'])
        cls.client.wait_for_server_status(cls.s3['id'], 'ACTIVE')
        resp, cls.s3 = cls.client.get_server(cls.s3['id'])

        # The list server call returns minimal results, so we need
        # a less detailed version of each server also
        cls.s1_min = cls._convert_to_min_details(cls.s1)
        cls.s2_min = cls._convert_to_min_details(cls.s2)
        cls.s3_min = cls._convert_to_min_details(cls.s3)

    @staticmethod
    def tearDownClass(cls):
        cls.client.delete_server(cls.s1['id'])
        cls.client.delete_server(cls.s2['id'])
        cls.client.delete_server(cls.s3['id'])

    def _server_id_in_results(self, server_id, results):
        ids = [row['id'] for row in results]
        return server_id in ids

    @utils.skip_unless_attr('multiple_images', 'Only one image found')
    @attr(type='positive')
    def test_list_servers_filter_by_image(self):
        # Filter the list of servers by image
        params = {'image': self.image_ref}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertTrue(self._server_id_in_results(self.s1['id'], servers))
        self.assertFalse(self._server_id_in_results(self.s2['id'], servers))
        self.assertTrue(self._server_id_in_results(self.s3['id'], servers))

    @attr(type='positive')
    def test_list_servers_filter_by_flavor(self):
        # Filter the list of servers by flavor
        params = {'flavor': self.flavor_ref_alt}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertFalse(self._server_id_in_results(self.s1['id'], servers))
        self.assertFalse(self._server_id_in_results(self.s2['id'], servers))
        self.assertTrue(self._server_id_in_results(self.s3['id'], servers))

    @attr(type='positive')
    def test_list_servers_filter_by_server_name(self):
        # Filter the list of servers by server name
        params = {'name': self.s1_name}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertTrue(self._server_id_in_results(self.s1['id'], servers))
        self.assertFalse(self._server_id_in_results(self.s2['id'], servers))
        self.assertFalse(self._server_id_in_results(self.s3['id'], servers))

    @attr(type='positive')
    def test_list_servers_filter_by_server_status(self):
        # Filter the list of servers by server status
        params = {'status': 'active'}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertTrue(self._server_id_in_results(self.s1['id'], servers))
        self.assertTrue(self._server_id_in_results(self.s2['id'], servers))
        self.assertTrue(self._server_id_in_results(self.s3['id'], servers))

    @attr(type='positive')
    def test_list_servers_limit_results(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 1}
        resp, servers = self.client.list_servers_with_detail(params)
        self.assertEqual(1, len(servers['servers']))

    @utils.skip_unless_attr('multiple_images', 'Only one image found')
    @attr(type='positive')
    def test_list_servers_detailed_filter_by_image(self):
        # Filter the detailed list of servers by image
        params = {'image': self.image_ref}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertTrue(self._server_id_in_results(self.s1['id'], servers))
        self.assertFalse(self._server_id_in_results(self.s2['id'], servers))
        self.assertTrue(self._server_id_in_results(self.s3['id'], servers))

    @attr(type='positive')
    def test_list_servers_detailed_filter_by_flavor(self):
        # Filter the detailed list of servers by flavor
        params = {'flavor': self.flavor_ref_alt}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertFalse(self._server_id_in_results(self.s1['id'], servers))
        self.assertFalse(self._server_id_in_results(self.s2['id'], servers))
        self.assertTrue(self._server_id_in_results(self.s3['id'], servers))

    @attr(type='positive')
    def test_list_servers_detailed_filter_by_server_name(self):
        # Filter the detailed list of servers by server name
        params = {'name': self.s1_name}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertTrue(self._server_id_in_results(self.s1['id'], servers))
        self.assertFalse(self._server_id_in_results(self.s2['id'], servers))
        self.assertFalse(self._server_id_in_results(self.s3['id'], servers))

    @attr(type='positive')
    def test_list_servers_detailed_filter_by_server_status(self):
        # Filter the detailed list of servers by server status
        params = {'status': 'active'}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertTrue(self._server_id_in_results(self.s1['id'], servers))
        self.assertTrue(self._server_id_in_results(self.s2['id'], servers))
        self.assertTrue(self._server_id_in_results(self.s3['id'], servers))

    @attr(type='positive')
    def test_list_servers_detailed_limit_results(self):
        # Verify only the expected number of detailed results are returned
        params = {'limit': 1}
        resp, servers = self.client.list_servers_with_detail(params)
        self.assertEqual(1, len(servers['servers']))

    @classmethod
    def _convert_to_min_details(self, server):
        min_detail = {}
        min_detail['name'] = server['name']
        min_detail['links'] = server['links']
        min_detail['id'] = server['id']
        return min_detail


class ListServerFiltersTestJSON(base.BaseComputeTestJSON,
                                ListServerFiltersTest):
    @classmethod
    def setUpClass(cls):
        raise nose.SkipTest("Until Bug 1039753 is fixed")
        super(ListServerFiltersTestJSON, cls).setUpClass()
        ListServerFiltersTest.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        super(ListServerFiltersTestJSON, cls).tearDownClass()
        ListServerFiltersTest.tearDownClass(cls)


class ListServerFiltersTestXML(base.BaseComputeTestXML,
                               ListServerFiltersTest):
    @classmethod
    def setUpClass(cls):
        raise nose.SkipTest("Until Bug 1039753 is fixed")
        super(ListServerFiltersTestXML, cls).setUpClass()
        ListServerFiltersTest.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        super(ListServerFiltersTestXML, cls).tearDownClass()
        ListServerFiltersTest.tearDownClass(cls)
