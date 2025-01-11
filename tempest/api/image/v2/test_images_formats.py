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

from tempest.api.compute import base as compute_base
from tempest.api.image import base
from tempest.common import waiters
from tempest import config
from tempest import exceptions
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


class ImagesFormatTest(base.BaseV2ImageTest,
                       compute_base.BaseV2ComputeTest):
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

    @classmethod
    def resource_setup(cls):
        super().resource_setup()
        cls.available_import_methods = cls.client.info_import()[
            'import-methods']['value']

    def _test_image(self, image_def, override_format=None, asimport=False):
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
            if asimport:
                self.client.stage_image_file(image['id'], f)
                self.client.image_import(image['id'], method='glance-direct')
            else:
                self.client.store_image_file(image['id'], f)
        return image

    @decorators.idempotent_id('a245fcbe-63ce-4dc1-a1d0-c16d76d9e6df')
    def test_accept_usable_formats(self):
        if self.imgdef['usable']:
            try:
                self._test_image(self.imgdef)
            except lib_exc.BadRequest:
                format = self.imgdef['format']
                if format == 'gpt' and format not in CONF.image.disk_formats:
                    # If we don't have gpt defined, we don't expect this to
                    # work because glance has not been updated for GPT
                    # FIXME(danms): Remove this once glance support for GPT is
                    # landed on master
                    self.skipTest('GPT not configured and glance is too '
                                  'old to support it')
                raise
        else:
            self.skipTest(
                'Glance does not currently reject unusable images on upload')

    @decorators.idempotent_id('7c7c2f16-2e97-4dce-8cb4-bc10be031c85')
    def test_accept_reject_formats_import(self):
        """Make sure glance rejects invalid images during conversion."""
        if 'glance-direct' not in self.available_import_methods:
            self.skipTest('Import via glance-direct is not available')
        if not CONF.image_feature_enabled.image_conversion:
            self.skipTest('Import image_conversion not enabled')

        # VMDK with footer was not supported by earlier service versions,
        # so we need to tolerate it passing and failing (skip for the latter).
        # See this for more info:
        # https://bugs.launchpad.net/glance/+bug/2073262
        is_broken = 'footer' in self.imgdef['name']

        if (self.imgdef['format'] in CONF.image.disk_formats and
                self.imgdef['usable']):
            # Usable images should end up in active state
            image = self._test_image(self.imgdef, asimport=True)
            try:
                waiters.wait_for_image_status(self.client, image['id'],
                                              'active')
            except lib_exc.TimeoutException:
                if is_broken:
                    self.skipTest(
                        'Older glance did not support vmdk-with-footer')
                else:
                    raise
        else:
            # FIXME(danms): Make this better, but gpt will fail before
            # the import even starts until glance has it in its API
            # schema as a valid value. Other formats expected to fail
            # do so during import and return to queued state.
            try:
                image = self._test_image(self.imgdef, asimport=True)
                waiters.wait_for_image_status(self.client, image['id'],
                                              ['queued', 'active'])
                self.client.delete_image(image['id'])
            except lib_exc.BadRequest:
                format = self.imgdef['format']
                if format == 'gpt' and format not in CONF.image.disk_formats:
                    # If we don't have gpt defined, we don't expect this to
                    # work because glance has not been updated for GPT
                    # FIXME(danms): Remove this once glance support for GPT is
                    # landed on master
                    self.skipTest('GPT not configured and glance is too '
                                  'old to support it')
                elif format in CONF.image.disk_formats:
                    # This is in our config so it's supposed to work, fail
                    raise

        if self.imgdef['format'] == 'iso':
            # NOTE(danms): Glance has a special case to not convert ISO images
            # because they are special and must remain as ISOs in order to be
            # properly used for CD-based rescue and boot.
            self.assertEqual('iso', image['disk_format'])

    def _create_server_with_image_def(self, image_def, **overrides):
        image_def = dict(image_def, **overrides)
        image = self._test_image(image_def)
        server = self.create_test_server(name='server-%s' % image['name'],
                                         image_id=image['id'],
                                         wait_until='ACTIVE')
        return server

    @decorators.idempotent_id('f77394bc-81f4-4d54-9f5b-e48f3d6b5376')
    def test_compute_rejects_invalid(self):
        """Make sure compute rejects invalid/insecure images."""
        if self.imgdef['format'] not in CONF.image.disk_formats:
            # if this format is not allowed by glance, we can not create
            # a properly-formatted image for it, so skip it.
            self.skipTest(
                'Format %s not allowed by config' % self.imgdef['format'])
        if CONF.image_feature_enabled.image_format_enforcement:
            # If glance rejects bad images during upload, we cannot get them
            # registered so that we can test nova.
            self.skipTest(
                'Unable to test compute image formats if glance does not '
                'allow them to be uploaded')

        # VMDK with footer was not supported by earlier service versions,
        # so we need to tolerate it passing and failing (skip for the latter).
        # See this for more info:
        # https://bugs.launchpad.net/glance/+bug/2073262
        is_broken = 'footer' in self.imgdef['name']

        if self.imgdef['usable']:
            try:
                server = self._create_server_with_image_def(self.imgdef)
            except exceptions.BuildErrorException:
                if is_broken:
                    self.skip('Tolerating failed build with known-broken '
                              'image format')
                else:
                    raise
            self.delete_server(server['id'])
        else:
            self.assertRaises(exceptions.BuildErrorException,
                              self._create_server_with_image_def,
                              self.imgdef)

    @decorators.idempotent_id('ffe21610-e801-4992-9b81-e2d646e2e2e9')
    def test_compute_rejects_format_mismatch(self):
        """Make sure compute rejects any image with a format mismatch."""
        if CONF.image_feature_enabled.image_format_enforcement:
            # If glance rejects bad images during upload, we cannot get them
            # registered so that we can test nova.
            self.skipTest(
                'Unable to test compute image formats if glance does not '
                'allow them to be uploaded')
        # Lying about the disk_format should always fail
        override_fmt = (
            self.imgdef['format'] in ('raw', 'gpt') and 'qcow2' or 'raw')
        self.assertRaises(exceptions.BuildErrorException,
                          self._create_server_with_image_def,
                          self.imgdef,
                          format=override_fmt)
