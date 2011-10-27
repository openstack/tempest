import httplib2
import json
import os
import re

from kong import openstack
from kong import tests


class TestImagesThroughCompute(tests.FunctionalTest):

    def setUp(self):
        super(TestImagesThroughCompute, self).setUp()
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


class TestGlanceAPI(tests.FunctionalTest):

    def setUp(self):
        super(TestGlanceAPI, self).setUp()
        self.base_url = "http://%s:%s/%s/images" % (self.glance['host'],
		                                    self.glance['port'],
                                                    self.glance['apiver'])

    def test_upload_ami_style_image(self):
        """Uploads a three-part ami-style image"""
        aki_location = self.config['environment']['aki_location']
        headers = {'x-image-meta-is-public': 'true',
                   'x-image-meta-name': 'test-kernel',
                   'x-image-meta-disk-format': 'aki',
                   'x-image-meta-container-format': 'aki',
                   'Content-Length': '%d' % os.path.getsize(aki_location),
                   'Content-Type': 'application/octet-stream'}
        image_file = open(aki_location, "rb")
        http = httplib2.Http()
        response, content = http.request(self.base_url, 'POST',
                                         headers=headers,body=image_file)
        image_file.close()
        self.assertEqual(201, response.status)
        data = json.loads(content)
        self.assertEqual(data['image']['name'], "test-kernel")
        self.assertEqual(data['image']['checksum'],
                         self._md5sum_file(aki_location))
        kernel_id = data['image']['id']

        ari_location = self.config['environment'].get('ari_location')
        if ari_location:
            headers = {'x-image-meta-is-public': 'true',
                       'x-image-meta-name': 'test-ramdisk',
                       'x-image-meta-disk-format': 'ari',
                       'x-image-meta-container-format': 'ari',
                       'Content-Length': '%d' % os.path.getsize(ari_location),
                       'Content-Type': 'application/octet-stream'}
            image_file = open(ari_location, "rb")
            http = httplib2.Http()
            response, content = http.request(self.base_url, 'POST',
                                             headers=headers, body=image_file)
            image_file.close()
            self.assertEqual(201, response.status)
            data = json.loads(content)
            self.assertEqual(data['image']['name'], "test-ramdisk")
            self.assertEqual(data['image']['checksum'],
                             self._md5sum_file(ari_location))
            ramdisk_id = data['image']['id']
        else:
            ramdisk_id = None

        ami_location = self.config['environment']['ami_location']
        upload_data = ""
        for chunk in self._read_in_chunks(ami_location):
            upload_data += chunk
        headers = {'x-image-meta-is-public': 'true',
                   'x-image-meta-name': 'test-image',
                   'x-image-meta-disk-format': 'ami',
                   'x-image-meta-container-format': 'ami',
                   'x-image-meta-property-kernel_id': kernel_id,
                   'Content-Length': '%d' % os.path.getsize(ami_location),
                   'Content-Type': 'application/octet-stream'}

        if ari_location:
            headers['x-image-meta-property-ramdisk_id'] = ramdisk_id

        http = httplib2.Http()
        response, content = http.request(self.base_url, 'POST',
                                         headers=headers, body=upload_data)
        self.assertEqual(201, response.status)
        data = json.loads(content)
        self.assertEqual(data['image']['name'], "test-image")
        self.assertEqual(data['image']['checksum'], 
                         self._md5sum_file(ami_location))
        machine_id = data['image']['id']

        # now ensure we can modify the image properties
        headers = {'X-Image-Meta-Property-distro': 'Ubuntu',
                   'X-Image-Meta-Property-arch': 'x86_64',
                   'X-Image-Meta-Property-kernel_id': kernel_id}
        if ari_location:
            headers['X-Image-Meta-Property-ramdisk_id'] = ramdisk_id

        http = httplib2.Http()
        url = '%s/%s' % (self.base_url, machine_id)
        response, content = http.request(url, 'PUT', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        properties = data['image']['properties']
        self.assertEqual(properties['arch'], "x86_64")
        self.assertEqual(properties['distro'], "Ubuntu")
        self.assertEqual(properties['kernel_id'], kernel_id)
        if ari_location:
            self.assertEqual(properties['ramdisk_id'], ramdisk_id)

        # list the metadata to ensure the new values stuck
        http = httplib2.Http()
        response, content = http.request(url, 'HEAD')
        self.assertEqual(response.status, 200)
        self.assertEqual(response['x-image-meta-name'], "test-image")
        self.assertEqual(response['x-image-meta-checksum'],
                         self._md5sum_file(ami_location))
        self.assertEqual(response['x-image-meta-container_format'], "ami")
        self.assertEqual(response['x-image-meta-disk_format'], "ami")
        self.assertEqual(response['x-image-meta-property-arch'], "x86_64")
        self.assertEqual(response['x-image-meta-property-distro'], "Ubuntu")
        self.assertEqual(response['x-image-meta-property-kernel_id'],
                         kernel_id)
        if ari_location:
            self.assertEqual(response['x-image-meta-property-ramdisk_id'],
                             ramdisk_id)

        # delete images for which we have non-None ids
        delete_ids = filter(lambda x: x, (kernel_id, ramdisk_id, machine_id))
        for image_id in delete_ids:
            http = httplib2.Http()
            url = '%s/%s' % (self.base_url, image_id)
            response, content = http.request(url, 'DELETE')

    test_upload_ami_style_image.tags = ['glance']
