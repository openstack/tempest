# Copyright 2021 Red Hat, Inc.
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

import io

from oslo_utils import units
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.scenario import manager

CONF = config.CONF


class ImageQuotaTest(manager.ScenarioTest):
    credentials = ['primary', 'system_admin']

    @classmethod
    def resource_setup(cls):
        super(ImageQuotaTest, cls).resource_setup()

        # Figure out and record the glance service id
        services = cls.os_system_admin.identity_services_v3_client.\
            list_services()
        glance_services = [x for x in services['services']
                           if x['name'] == 'glance']
        cls.glance_service_id = glance_services[0]['id']

        # Pre-create all the quota limits and record their IDs so we can
        # update them in-place without needing to know which ones have been
        # created and in which order.
        cls.limit_ids = {}

        try:
            cls.limit_ids['image_size_total'] = cls._create_limit(
                'image_size_total', 10)
            cls.limit_ids['image_stage_total'] = cls._create_limit(
                'image_stage_total', 10)
            cls.limit_ids['image_count_total'] = cls._create_limit(
                'image_count_total', 10)
            cls.limit_ids['image_count_uploading'] = cls._create_limit(
                'image_count_uploading', 10)
        except lib_exc.Forbidden:
            # If we fail to set limits, it means they are not
            # registered, and thus we will skip these tests once we
            # have our os_system_admin client and run
            # check_quotas_enabled().
            pass

    def setUp(self):
        super(ImageQuotaTest, self).setUp()
        self.created_images = []

    def create_image(self, data=None, **kwargs):
        """Wrapper that returns a test image."""

        if 'name' not in kwargs:
            name = data_utils.rand_name(self.__name__ + "-image")
            kwargs['name'] = name

        params = dict(kwargs)
        if data:
            # NOTE: On glance v1 API, the data should be passed on
            # a header. Then here handles the data separately.
            params['data'] = data

        image = self.image_client.create_image(**params)
        # Image objects returned by the v1 client have the image
        # data inside a dict that is keyed against 'image'.
        if 'image' in image:
            image = image['image']
        self.created_images.append(image['id'])
        self.addCleanup(
            self.image_client.wait_for_resource_deletion,
            image['id'])
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.image_client.delete_image, image['id'])
        return image

    def check_quotas_enabled(self):
        # Check to see if we should even be running these tests. Use
        # the presence of a registered limit that we recognize as an
        # indication.  This will be set up by the operator (or
        # devstack) if glance is configured to use/honor the unified
        # limits. If one is set, they must all be set, because glance
        # has a single all-or-nothing flag for whether or not to use
        # keystone limits. If anything, checking only one helps to
        # assert the assumption that, if enabled, they must all be at
        # least registered for proper operation.
        registered_limits = self.os_system_admin.identity_limits_client.\
            get_registered_limits()['registered_limits']
        if 'image_count_total' not in [x['resource_name']
                                       for x in registered_limits]:
            raise self.skipException('Target system is not configured with '
                                     'glance unified limits')

    @classmethod
    def _create_limit(cls, name, value):
        return cls.os_system_admin.identity_limits_client.create_limit(
            CONF.identity.region, cls.glance_service_id,
            cls.image_client.tenant_id, name, value)['limits'][0]['id']

    def _update_limit(self, name, value):
        self.os_system_admin.identity_limits_client.update_limit(
            self.limit_ids[name], value)

    def _cleanup_images(self):
        while self.created_images:
            image_id = self.created_images.pop()
            try:
                self.image_client.delete_image(image_id)
            except lib_exc.NotFound:
                pass

    @decorators.idempotent_id('9b74fe24-183b-41e6-bf42-84c2958a7be8')
    @utils.services('image', 'identity')
    def test_image_count_quota(self):
        self.check_quotas_enabled()

        # Set a quota on the number of images for our tenant to one.
        self._update_limit('image_count_total', 1)

        # Create one image
        image = self.create_image(name='first',
                                  container_format='bare',
                                  disk_format='raw',
                                  visibility='private')

        # Second image would put us over quota, so expect failure.
        self.assertRaises(lib_exc.OverLimit,
                          self.create_image,
                          name='second',
                          container_format='bare',
                          disk_format='raw',
                          visibility='private')

        # Update our limit to two.
        self._update_limit('image_count_total', 2)

        # Now the same create should succeed.
        self.create_image(name='second',
                          container_format='bare',
                          disk_format='raw',
                          visibility='private')

        # Third image would put us over quota, so expect failure.
        self.assertRaises(lib_exc.OverLimit,
                          self.create_image,
                          name='third',
                          container_format='bare',
                          disk_format='raw',
                          visibility='private')

        # Delete the first image to put us under quota.
        self.image_client.delete_image(image['id'])

        # Now the same create should succeed.
        self.create_image(name='third',
                          container_format='bare',
                          disk_format='raw',
                          visibility='private')

        # Delete all the images we created before the next test runs,
        # so that it starts with full quota.
        self._cleanup_images()

    @decorators.idempotent_id('b103788b-5329-4aa9-8b0d-97f8733460db')
    @utils.services('image', 'identity')
    def test_image_count_uploading_quota(self):
        if not CONF.image_feature_enabled.import_image:
            skip_msg = (
                "%s skipped as image import is not available" % __name__)
            raise self.skipException(skip_msg)

        self.check_quotas_enabled()

        # Set a quota on the number of images we can have in uploading state.
        self._update_limit('image_stage_total', 10)
        self._update_limit('image_size_total', 10)
        self._update_limit('image_count_total', 10)
        self._update_limit('image_count_uploading', 1)

        file_content = data_utils.random_bytes(1 * units.Mi)

        # Create and stage an image
        image1 = self.create_image(name='first',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.image_client.stage_image_file(image1['id'],
                                           io.BytesIO(file_content))

        # Check that we can not stage another
        image2 = self.create_image(name='second',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.assertRaises(lib_exc.OverLimit,
                          self.image_client.stage_image_file,
                          image2['id'], io.BytesIO(file_content))

        # ... nor upload directly
        image3 = self.create_image(name='third',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.assertRaises(lib_exc.OverLimit,
                          self.image_client.store_image_file,
                          image3['id'],
                          io.BytesIO(file_content))

        # Update our quota to make room
        self._update_limit('image_count_uploading', 2)

        # Now our upload should work
        self.image_client.store_image_file(image3['id'],
                                           io.BytesIO(file_content))

        # ...and because that is no longer in uploading state, we should be
        # able to stage our second image from above.
        self.image_client.stage_image_file(image2['id'],
                                           io.BytesIO(file_content))

        # Finish our import of image2
        self.image_client.image_import(image2['id'], method='glance-direct')
        waiters.wait_for_image_imported_to_stores(self.image_client,
                                                  image2['id'])

        # Set our quota back to one
        self._update_limit('image_count_uploading', 1)

        # Since image1 is still staged, we should not be able to upload
        # an image.
        image4 = self.create_image(name='fourth',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.assertRaises(lib_exc.OverLimit,
                          self.image_client.store_image_file,
                          image4['id'],
                          io.BytesIO(file_content))

        # Finish our import of image1 to make space in our uploading quota.
        self.image_client.image_import(image1['id'], method='glance-direct')
        waiters.wait_for_image_imported_to_stores(self.image_client,
                                                  image1['id'])

        # Make sure that freed up the one upload quota to complete our upload
        self.image_client.store_image_file(image4['id'],
                                           io.BytesIO(file_content))

        # Delete all the images we created before the next test runs,
        # so that it starts with full quota.
        self._cleanup_images()

    @decorators.idempotent_id('05e8d064-c39a-4801-8c6a-465df375ec5b')
    @utils.services('image', 'identity')
    def test_image_size_quota(self):
        self.check_quotas_enabled()

        # Set a quota on the image size for our tenant to 1MiB, and allow ten
        # images.
        self._update_limit('image_size_total', 1)
        self._update_limit('image_count_total', 10)
        self._update_limit('image_count_uploading', 10)

        file_content = data_utils.random_bytes(1 * units.Mi)

        # Create and upload a 1MiB image.
        image1 = self.create_image(name='first',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.image_client.store_image_file(image1['id'],
                                           io.BytesIO(file_content))

        # Create and upload a second 1MiB image. This succeeds, but
        # after completion, we are over quota. Despite us being at
        # quota above, the initial quota check for the second
        # operation has no idea what the image size will be, and thus
        # uses delta=0. This will succeed because we're not
        # technically over-quota and have not asked for any more (this
        # is oslo.limit behavior). After the second operation,
        # however, we will be over-quota regardless of the delta and
        # subsequent attempts will fail. Because glance goes not
        # require an image size to be declared before upload, this is
        # really the best it can do without an API change.
        image2 = self.create_image(name='second',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.image_client.store_image_file(image2['id'],
                                           io.BytesIO(file_content))

        # Create and attempt to upload a third 1MiB image. This should fail to
        # upload (but not create) because we are over quota.
        image3 = self.create_image(name='third',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.assertRaises(lib_exc.OverLimit,
                          self.image_client.store_image_file,
                          image3['id'], io.BytesIO(file_content))

        # Increase our size quota to 2MiB.
        self._update_limit('image_size_total', 2)

        # Now the upload of the already-created image is allowed, but
        # after completion, we are over quota again.
        self.image_client.store_image_file(image3['id'],
                                           io.BytesIO(file_content))

        # Create and attempt to upload a fourth 1MiB image. This should
        # fail to upload (but not create) because we are over quota.
        image4 = self.create_image(name='fourth',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.assertRaises(lib_exc.OverLimit,
                          self.image_client.store_image_file,
                          image4['id'], io.BytesIO(file_content))

        # Delete our first image to make space in our existing 2MiB quota.
        self.image_client.delete_image(image1['id'])

        # Now the upload of the already-created image is allowed.
        self.image_client.store_image_file(image4['id'],
                                           io.BytesIO(file_content))

        # Delete all the images we created before the next test runs,
        # so that it starts with full quota.
        self._cleanup_images()

    @decorators.idempotent_id('fc76b8d9-aae5-46fb-9285-099e37f311f7')
    @utils.services('image', 'identity')
    def test_image_stage_quota(self):
        if not CONF.image_feature_enabled.import_image:
            skip_msg = (
                "%s skipped as image import is not available" % __name__)
            raise self.skipException(skip_msg)

        self.check_quotas_enabled()

        # Create a staging quota of 1MiB, allow 10MiB of active
        # images, and a total of ten images.
        self._update_limit('image_stage_total', 1)
        self._update_limit('image_size_total', 10)
        self._update_limit('image_count_total', 10)
        self._update_limit('image_count_uploading', 10)

        file_content = data_utils.random_bytes(1 * units.Mi)

        # Create and stage a 1MiB image.
        image1 = self.create_image(name='first',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.image_client.stage_image_file(image1['id'],
                                           io.BytesIO(file_content))

        # Create and stage a second 1MiB image. This succeeds, but
        # after completion, we are over quota.
        image2 = self.create_image(name='second',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.image_client.stage_image_file(image2['id'],
                                           io.BytesIO(file_content))

        # Create and attempt to stage a third 1MiB image. This should fail to
        # stage (but not create) because we are over quota.
        image3 = self.create_image(name='third',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.assertRaises(lib_exc.OverLimit,
                          self.image_client.stage_image_file,
                          image3['id'], io.BytesIO(file_content))

        # Make sure that even though we are over our stage quota, we
        # can still create and upload an image the regular way.
        image_upload = self.create_image(name='uploaded',
                                         container_format='bare',
                                         disk_format='raw',
                                         visibility='private')
        self.image_client.store_image_file(image_upload['id'],
                                           io.BytesIO(file_content))

        # Increase our stage quota to two MiB.
        self._update_limit('image_stage_total', 2)

        # Now the upload of the already-created image is allowed, but
        # after completion, we are over quota again.
        self.image_client.stage_image_file(image3['id'],
                                           io.BytesIO(file_content))

        # Create and attempt to stage a fourth 1MiB image. This should
        # fail to stage (but not create) because we are over quota.
        image4 = self.create_image(name='fourth',
                                   container_format='bare',
                                   disk_format='raw',
                                   visibility='private')
        self.assertRaises(lib_exc.OverLimit,
                          self.image_client.stage_image_file,
                          image4['id'], io.BytesIO(file_content))

        # Finish our import of image1 to make space in our stage quota.
        self.image_client.image_import(image1['id'], method='glance-direct')
        waiters.wait_for_image_imported_to_stores(self.image_client,
                                                  image1['id'])

        # Now the upload of the already-created image is allowed.
        self.image_client.stage_image_file(image4['id'],
                                           io.BytesIO(file_content))

        # Delete all the images we created before the next test runs,
        # so that it starts with full quota.
        self._cleanup_images()
