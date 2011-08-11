# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack, LLC
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
"""Validate a working Glance deployment"""

import httplib2
import json
import os
from pprint import pprint

import tests


class TestGlanceAPI(tests.FunctionalTest):
    def test_001_connect_to_glance_api(self):
        """
        Verifies ability to connect to glance api,
        expects glance to return an empty set
        """
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'])
        else:
            path = "http://%s:%s/images" % (self.glance['host'],
                                        self.glance['port'])
        http = httplib2.Http()
        response, content = http.request(path, 'GET')
        self.assertEqual(200, response.status)
        data = json.loads(content)
        self.assertTrue('images' in data)
    test_001_connect_to_glance_api.tags = ['glance']

    def test_002_upload_kernel_to_glance(self):
        """
        Uploads a test kernal to glance api
        """
        kernel = "sample_vm/vmlinuz-2.6.32-23-server"
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'])
        else:
            path = "http://%s:%s/images" % (self.glance['host'],
                                        self.glance['port'])
        headers = {'x-image-meta-is-public': 'true',
                   'x-image-meta-name': 'test-kernel',
                   'x-image-meta-disk-format': 'aki',
                   'x-image-meta-container-format': 'aki',
                   'Content-Length': '%d' % os.path.getsize(kernel),
                   'Content-Type': 'application/octet-stream'}
        image_file = open(kernel, "rb")
        http = httplib2.Http()
        response, content = http.request(path, 'POST',
                                         headers=headers,
                                         body=image_file)
        image_file.close()
        self.assertEqual(201, response.status)
        data = json.loads(content)
        self.glance['kernel_id'] = data['image']['id']
        self.assertEqual(data['image']['name'], "test-kernel")
        self.assertEqual(data['image']['checksum'], self._md5sum_file(kernel))
    test_002_upload_kernel_to_glance.tags = ['glance', 'nova']

    def test_003_upload_initrd_to_glance(self):
        """
        Uploads a test initrd to glance api
        """
        initrd = "sample_vm/initrd.img-2.6.32-23-server"
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'])
        else:
            path = "http://%s:%s/images" % (self.glance['host'],
                                        self.glance['port'])
        headers = {'x-image-meta-is-public': 'true',
                   'x-image-meta-name': 'test-ramdisk',
                   'x-image-meta-disk-format': 'ari',
                   'x-image-meta-container-format': 'ari',
                   'Content-Length': '%d' % os.path.getsize(initrd),
                   'Content-Type': 'application/octet-stream'}
        image_file = open(initrd, "rb")
        http = httplib2.Http()
        response, content = http.request(path,
                                         'POST',
                                         headers=headers,
                                         body=image_file)
        image_file.close()
        self.assertEqual(201, response.status)
        data = json.loads(content)
        self.glance['ramdisk_id'] = data['image']['id']
        self.assertEqual(data['image']['name'], "test-ramdisk")
        self.assertEqual(data['image']['checksum'], self._md5sum_file(initrd))
    test_003_upload_initrd_to_glance.tags = ['glance', 'nova']

    def test_004_upload_image_to_glance(self):
        """
        Uploads a test image to glance api, and
        links it to the initrd and kernel uploaded
        earlier
        """
        image = "sample_vm/ubuntu-lucid.img"
        upload_data = ""
        for chunk in self._read_in_chunks(image):
            upload_data += chunk
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images" % (self.glance['host'],
                          self.glance['port'], self.glance['apiver'])
        else:
            path = "http://%s:%s/images" % (self.glance['host'],
                                        self.glance['port'])
        headers = {'x-image-meta-is-public': 'true',
                   'x-image-meta-name': 'test-image',
                   'x-image-meta-disk-format': 'ami',
                   'x-image-meta-container-format': 'ami',
                   'x-image-meta-property-Kernel_id': '%s' % \
                       self.glance['kernel_id'],
                   'x-image-meta-property-Ramdisk_id': '%s' % \
                       self.glance['ramdisk_id'],
                   'Content-Length': '%d' % os.path.getsize(image),
                   'Content-Type': 'application/octet-stream'}
        http = httplib2.Http()
        response, content = http.request(path, 'POST',
                                         headers=headers,
                                         body=upload_data)
        self.assertEqual(201, response.status)
        data = json.loads(content)
        self.glance['image_id'] = data['image']['id']
        self.assertEqual(data['image']['name'], "test-image")
        self.assertEqual(data['image']['checksum'], self._md5sum_file(image))
    test_004_upload_image_to_glance.tags = ['glance', 'nova']

    def test_005_set_image_meta_property(self):
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images/%s" % (self.glance['host'],
                           self.glance['port'], self.glance['apiver'],
                           self.glance['image_id'])
        else:
            path = "http://%s:%s/images/%s" % (self.glance['host'],
                           self.glance['port'], self.glance['image_id'])
        headers = {'X-Image-Meta-Property-Distro': 'Ubuntu',
                   'X-Image-Meta-Property-Arch': 'x86_64',
                   'X-Image-Meta-Property-Kernel_id': '%s' % \
                       self.glance['kernel_id'],
                   'X-Image-Meta-Property-Ramdisk_id': '%s' % \
                       self.glance['ramdisk_id']}
        http = httplib2.Http()
        response, content = http.request(path, 'PUT', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(data['image']['properties']['arch'], "x86_64")
        self.assertEqual(data['image']['properties']['distro'], "Ubuntu")
        self.assertEqual(data['image']['properties']['kernel_id'],
                         str(self.glance['kernel_id']))
        self.assertEqual(data['image']['properties']['ramdisk_id'],
                         str(self.glance['ramdisk_id']))
    test_005_set_image_meta_property.tags = ['glance']

    def test_006_list_image_metadata(self):
        image = "sample_vm/ubuntu-lucid.img"
        if 'apiver' in self.glance:
            path = "http://%s:%s/%s/images/%s" % (self.glance['host'],
                           self.glance['port'], self.glance['apiver'],
                           self.glance['image_id'])
        else:
            path = "http://%s:%s/images/%s" % (self.glance['host'],
                           self.glance['port'], self.glance['image_id'])
        http = httplib2.Http()
        response, content = http.request(path, 'HEAD')
        self.assertEqual(response.status, 200)
        self.assertEqual(response['x-image-meta-name'], "test-image")
        self.assertEqual(response['x-image-meta-checksum'],
                         self._md5sum_file(image))
        self.assertEqual(response['x-image-meta-container_format'], "ami")
        self.assertEqual(response['x-image-meta-disk_format'], "ami")
        self.assertEqual(response['x-image-meta-property-arch'], "x86_64")
        self.assertEqual(response['x-image-meta-property-distro'], "Ubuntu")
        self.assertEqual(response['x-image-meta-property-kernel_id'],
                         str(self.glance['kernel_id']))
        self.assertEqual(response['x-image-meta-property-ramdisk_id'],
                         str(self.glance['ramdisk_id']))
    test_006_list_image_metadata.tags = ['glance']
