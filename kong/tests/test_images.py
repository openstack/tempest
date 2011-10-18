import json
import os
import re

from kong import openstack
from kong import tests


class ImagesTest(tests.FunctionalTest):

    def setUp(self):
        super(ImagesTest, self).setUp()
        self.os = openstack.Manager(self.nova)

    def _assert_image_links(self, image):
        image_id = str(image['id'])

        mgmt_url = self.os.nova.management_url
        mgmt_url = re.sub(r'1//', r'1/', mgmt_url) # TODO: is this a bug in Nova?
        bmk_url = re.sub(r'v1.1\/', r'', mgmt_url)
        self_link = {'rel': 'self',
                     'href': os.path.join(mgmt_url, 'images', image_id)}
        bookmark_link = {'rel': 'bookmark',
                         'href': os.path.join(bmk_url, 'images', image_id)}

        self.assertIn(bookmark_link, image['links'])
        self.assertIn(self_link, image['links'])

    def _assert_image_entity_basic(self, image):
        actual_keys = set(image.keys())
        expected_keys = set((
            'id',
            'name',
            'links',
        ))
        self.assertEqual(actual_keys, expected_keys)

        self._assert_image_links(image)

    def _assert_image_entity_detailed(self, image):
        keys = image.keys()
        if 'server' in keys:
            keys.remove('server')
        actual_keys = set(keys)
        expected_keys = set((
            'created',
            'id',
            'links',
            'metadata',
            'minDisk',
            'minRam',
            'name',
            'progress',
            'status',
            'updated',
        ))
        self.assertEqual(actual_keys, expected_keys)

        self._assert_image_links(image)

    def test_index(self):
        """List all images"""

        response, body = self.os.nova.request('GET', '/images')

        self.assertEqual(response['status'], '200')
        resp_body = json.loads(body)
        self.assertEqual(resp_body.keys(), ['images'])

        for image in resp_body['images']:
            self._assert_image_entity_basic(image)
    test_index.tags = ['nova', 'glance']

    def test_detail(self):
        """List all images in detail"""

        response, body = self.os.nova.request('GET', '/images/detail')
        self.assertEqual(response['status'], '200')
        resp_body = json.loads(body)
        self.assertEqual(resp_body.keys(), ['images'])

        for image in resp_body['images']:
            self._assert_image_entity_detailed(image)
    test_detail.tags = ['nova', 'glance']
