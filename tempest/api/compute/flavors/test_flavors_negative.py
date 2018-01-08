# Copyright 2017 Red Hat, Inc.
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

import random

import six

from tempest.api.compute import base
from tempest.common import image as common_image
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class FlavorsV2NegativeTest(base.BaseV2ComputeTest):

    @decorators.attr(type=['negative'])
    @utils.services('image')
    @decorators.idempotent_id('90f0d93a-91c1-450c-91e6-07d18172cefe')
    def test_boot_with_low_ram(self):
        """Try boot a vm with lower than min ram

        Create an image with min_ram value
        Try to create server with flavor of insufficient ram size from
        that image
        """
        flavor = self.flavors_client.show_flavor(
            CONF.compute.flavor_ref)['flavor']
        min_img_ram = flavor['ram'] + 1
        size = random.randint(1024, 4096)
        image_file = six.BytesIO(data_utils.random_bytes(size))
        params = {
            'name': data_utils.rand_name('image'),
            'container_format': CONF.image.container_formats[0],
            'disk_format': CONF.image.disk_formats[0],
            'min_ram': min_img_ram
        }

        if CONF.image_feature_enabled.api_v1:
            params.update({'is_public': False})
            params = {'headers': common_image.image_meta_to_headers(**params)}
        else:
            params.update({'visibility': 'private'})

        image = self.images_client.create_image(**params)
        image = image['image'] if 'image' in image else image
        self.addCleanup(self.images_client.delete_image, image['id'])

        if CONF.image_feature_enabled.api_v1:
            self.images_client.update_image(image['id'], data=image_file)
        else:
            self.images_client.store_image_file(image['id'], data=image_file)

        self.assertEqual(min_img_ram, image['min_ram'])

        # Try to create server with flavor of insufficient ram size
        self.assertRaisesRegex(lib_exc.BadRequest,
                               "Flavor's memory is too small for "
                               "requested image",
                               self.create_test_server,
                               image_id=image['id'],
                               flavor=flavor['id'])
