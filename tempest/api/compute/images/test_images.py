# Copyright 2012 OpenStack Foundation
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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class ImagesTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setUpClass(cls):
        super(ImagesTestJSON, cls).setUpClass()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        cls.client = cls.images_client
        cls.servers_client = cls.servers_client

    @test.attr(type='gate')
    def test_delete_saving_image(self):
        snapshot_name = data_utils.rand_name('test-snap-')
        resp, server = self.create_test_server(wait_until='ACTIVE')
        self.addCleanup(self.servers_client.delete_server, server['id'])
        resp, image = self.create_image_from_server(server['id'],
                                                    name=snapshot_name,
                                                    wait_until='SAVING')
        resp, body = self.client.delete_image(image['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='gate')
    def test_verify_image_ext_attrs(self):
        image_name = data_utils.rand_name('test-image')
        metadata = {'auto_disk_config': 'True'}

        resp, server = self.create_test_server(wait_until='ACTIVE')
        self.addCleanup(self.servers_client.delete_server, server['id'])
        resp, _ = self.client.create_image(server['id'],
                                           name=image_name,
                                           meta=metadata)
        image_id = data_utils.parse_image_id(resp['location'])
        self.addCleanup(self.client.delete_image, image_id)
        self.client.wait_for_image_status(image_id, 'ACTIVE')

        resp, image = self.client.get_image(image_id)
        self.assertEqual('AUTO', image['OS-DCF:diskConfig'])
        self.assertIn('OS-EXT-IMG-SIZE:size', image)

        resp, images = self.client.list_images_with_detail()
        image = [i for i in images if i['id'] == image_id][0]
        self.assertEqual('AUTO', image['OS-DCF:diskConfig'])
        self.assertIn('OS-EXT-IMG-SIZE:size', image)


class ImagesTestXML(ImagesTestJSON):
    _interface = 'xml'
