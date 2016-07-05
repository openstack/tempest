# Copyright 2016 NEC Corporation
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

from tempest.common import image
from tempest.lib.common import rest_client
from tempest.tests import base


class TestImage(base.TestCase):

    def test_get_image_meta_from_headers(self):
        resp = {
            'x-image-meta-id': 'ea30c926-0629-4400-bb6e-f8a8da6a4e56',
            'x-image-meta-owner': '8f421f9470e645b1b10f5d2db7804924',
            'x-image-meta-status': 'queued',
            'x-image-meta-name': 'New Http Image'
        }
        respbody = rest_client.ResponseBody(resp)
        observed = image.get_image_meta_from_headers(respbody)

        expected = {
            'properties': {},
            'id': 'ea30c926-0629-4400-bb6e-f8a8da6a4e56',
            'owner': '8f421f9470e645b1b10f5d2db7804924',
            'status': 'queued',
            'name': 'New Http Image'
        }
        self.assertEqual(expected, observed)

    def test_image_meta_to_headers(self):
        observed = image.image_meta_to_headers(
            name='test',
            container_format='wrong',
            disk_format='vhd',
            copy_from='http://localhost/images/10',
            properties={'foo': 'bar'},
            api={'abc': 'def'},
            purge_props=True)

        expected = {
            'x-image-meta-name': 'test',
            'x-image-meta-container_format': 'wrong',
            'x-image-meta-disk_format': 'vhd',
            'x-glance-api-copy-from': 'http://localhost/images/10',
            'x-image-meta-property-foo': 'bar',
            'x-glance-api-property-abc': 'def',
            'x-glance-registry-purge-props': True
        }
        self.assertEqual(expected, observed)
