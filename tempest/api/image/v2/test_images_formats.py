# Copyright 2024 Red Hat, Inc.
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

import os

import testscenarios
import yaml

from tempest.api.image import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


def load_tests(loader, suite, pattern):
    """Generate scenarios from the image manifest."""
    if CONF.image.images_manifest_file is None:
        return suite
    ImagesFormatTest.scenarios = []
    with open(CONF.image.images_manifest_file) as f:
        ImagesFormatTest._manifest = yaml.load(f, Loader=yaml.SafeLoader)
        for imgdef in ImagesFormatTest._manifest['images']:
            ImagesFormatTest.scenarios.append((imgdef['name'],
                                               {'imgdef': imgdef}))
    result = loader.suiteClass()
    result.addTests(testscenarios.generate_scenarios(suite))
    return result


class ImagesFormatTest(base.BaseV2ImageTest):
    def setUp(self):
        super().setUp()
        if CONF.image.images_manifest_file is None:
            self.skipTest('Image format testing is not configured')
        self._image_base = os.path.dirname(os.path.abspath(
            CONF.image.images_manifest_file))

        self.images = []

    def tearDown(self):
        for img in self.images:
            try:
                self.client.delete_image(img['id'])
            except lib_exc.NotFound:
                pass
        return super().tearDown()

    def _test_image(self, image_def, override_format=None):
        image_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=image_def['name'])
        image = self.client.create_image(
            name=image_name,
            container_format='bare',
            disk_format=override_format or image_def['format'])
        self.images.append(image)
        image_fn = os.path.join(self._image_base, image_def['filename'])
        with open(image_fn, 'rb') as f:
            self.client.store_image_file(image['id'], f)

    @decorators.idempotent_id('a245fcbe-63ce-4dc1-a1d0-c16d76d9e6df')
    def test_accept_usable_formats(self):
        if self.imgdef['usable']:
            if self.imgdef['format'] in CONF.image.disk_formats:
                # These are expected to work
                self._test_image(self.imgdef)
            else:
                # If this is not configured to be supported, we should get
                # a BadRequest from glance
                self.assertRaises(lib_exc.BadRequest,
                                  self._test_image, self.imgdef)
        else:
            self.skipTest(
                'Glance does not currently reject unusable images on upload')
