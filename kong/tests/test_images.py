import json
import os

from kong import openstack
from kong import tests


class ImagesTest(tests.FunctionalTest):

    def setUp(self):
        super(ImagesTest, self).setUp()
        self.os = openstack.Manager(self.nova)

    def _assert_image_links(self, image):
        image_id = str(image['id'])

        mgmt_url = self.os.nova.management_url
        bmk_url = re.sub(r'v1.1\/', r'', mgmt_url)

        self_link = os.path.join(mgmt_url, 'images', image_id)
        bookmark_link = os.path.join(bmk_url, 'images', image_id)

        expected_links = [
            {
                'rel': 'self',
                'href': self_link,
            },
            {
                'rel': 'bookmark',
                'href': bookmark_link,
            },
        ]

        self.assertEqual(image['links'], expected_links)

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
            'id',
            'name',
            'progress',
            'created',
            'updated',
            'status',
            'metadata',
            'links',
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

    def test_detail(self):
        """List all images in detail"""

        response, body = self.os.nova.request('GET', '/images/detail')

        self.assertEqual(response['status'], '200')
        resp_body = json.loads(body)
        self.assertEqual(resp_body.keys(), ['images'])

        for image in resp_body['images']:
            self._assert_image_entity_detailed(image)
