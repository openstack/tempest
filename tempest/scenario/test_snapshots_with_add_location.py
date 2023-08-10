# Copyright 2026 OpenStack Foundation
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

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF


class TestImageHashVerification(manager.ScenarioTest):
    """Test location, hash and checksum for images created via Nova and
    Cinder when do_secure_hash is enabled.

    These scenario tests verify end-to-end integration when Nova creates
    an instance snapshot or Cinder uploads a volume to Glance:

    * The image has at least one valid location entry.
    * When do_secure_hash is True, checksum, os_hash_algo and
      os_hash_value are populated after the location_import task.

    These tests run only when do_secure_hash=True. The
    do_secure_hash=False add-location contract is not exercised here
    because Nova and Cinder may use the traditional upload path
    (file-based Nova snapshot, non-optimized Cinder volume upload)
    instead of POST /v2/images/{id}/locations. Upload computes
    checksum independently of do_secure_hash, so asserting that hash
    fields remain None is not reliable in scenario tests.

    False-path coverage is provided by Glance functional tests and
    Tempest API tests (LocationImportTest and
    MultistoreLocationImportTest.test_add_location_with_do_secure_hash_false).
    """

    @classmethod
    def skip_checks(cls):
        super(TestImageHashVerification, cls).skip_checks()
        if not CONF.compute_feature_enabled.snapshot:
            raise cls.skipException("Snapshotting is not available.")
        if not CONF.image_feature_enabled.do_secure_hash:
            raise cls.skipException(
                '%s skipped: do_secure_hash=False is covered by Glance '
                'functional and Tempest API tests, not Nova/Cinder '
                'scenario tests (upload path may set checksum)' %
                cls.__name__)

    @classmethod
    def resource_setup(cls):
        super(TestImageHashVerification, cls).resource_setup()
        if not cls.os_primary.image_versions_client.has_version('2.17'):
            raise cls.skipException(
                '%s skipped as Glance does not support v2.17' % cls.__name__)

    def _verify_image_location_and_hash(self, image_id, image_description):
        """Verify location is added and hash values are populated.

        When Nova or Cinder use the new add location API, the image
        should have a location entry populated. With do_secure_hash
        enabled in glance, hash computation happens asynchronously
        and hash values should be populated after the task completes.
        """
        # Wait for all image tasks to reach 'success' status.
        # When glance receives an image via the add location API,
        # it spawns a background task for hash computation.
        waiters.wait_for_image_tasks_status(
            self.image_client, image_id, 'success')

        # Re-fetch image after tasks are complete
        image = self.image_client.show_image(image_id)
        self.assertEqual('active', image['status'],
                         '%s is not in active status' % image_description)

        # Verify location has been added via the new add location API.
        # The image should have at least one location entry after
        # Nova/Cinder added the location.
        if 'locations' in image:
            self.assertGreaterEqual(
                len(image['locations']), 1,
                'Expected at least one location for %s'
                % image_description)
            for loc in image['locations']:
                self.assertIn('url', loc,
                              'Location entry missing url for '
                              '%s' % image_description)
                self.assertTrue(
                    len(loc['url']) > 0,
                    'Location url should not be empty for '
                    '%s' % image_description)

        # Verify size is populated (location must have been valid)
        self.assertIsNotNone(
            image['size'],
            'Image size should not be None for %s' % image_description)

        # do_secure_hash=True is required; class is skipped otherwise.
        self.assertIsNotNone(
            image['checksum'],
            'checksum should not be None for %s when '
            'do_secure_hash is enabled' % image_description)
        self.assertIsNotNone(
            image['os_hash_algo'],
            'os_hash_algo should not be None for %s when '
            'do_secure_hash is enabled' % image_description)
        self.assertIsNotNone(
            image['os_hash_value'],
            'os_hash_value should not be None for %s when '
            'do_secure_hash is enabled' % image_description)

        return image

    @decorators.idempotent_id('a1b2c3d4-e5f6-7890-abcd-ef1234567890')
    @utils.services('compute', 'image')
    def test_instance_snapshot_image_hash_verification(self):
        """Test location and hash for instance snapshot image.

        This test verifies that when Nova creates a snapshot of an
        instance using the new add location API, the resulting image
        in Glance has:

        - A valid location entry added via the new add location API
        - Proper checksum, os_hash_algo and os_hash_value when
          do_secure_hash is enabled

        Steps:

        1. Create an instance from the configured image
        2. Create a snapshot of the instance
        3. Wait for the background image task to complete
        4. Verify the snapshot image has a valid location
        5. Verify hash values are populated
        """
        server = self.create_server(wait_until='ACTIVE')

        snapshot_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name='instance-snapshot-hash-test')
        snapshot_image = self.create_server_snapshot(
            server=server, name=snapshot_name)

        self._verify_image_location_and_hash(
            snapshot_image['id'], 'instance snapshot image')

    @decorators.idempotent_id('b2c3d4e5-f6a7-8901-bcde-f12345678901')
    @utils.services('compute', 'volume', 'image')
    def test_volume_upload_image_hash_verification(self):
        """Test location and hash for volume uploaded to image.

        This test verifies that when Cinder uploads a volume as an
        image to Glance using the new add location API, the resulting
        image has:

        - A valid location entry added via the new add location API
        - Proper checksum, os_hash_algo and os_hash_value when
          do_secure_hash is enabled

        Steps:

        1. Create a volume
        2. Upload the volume to Glance as an image
        3. Wait for the background image task to complete
        4. Verify the resulting image has a valid location
        5. Verify hash values are populated
        """
        if not CONF.service_available.cinder:
            raise self.skipException("Cinder is not available")

        volume = self.create_volume()

        image_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name='volume-upload-hash-test')
        body = self.volumes_client.upload_volume(
            volume['id'],
            image_name=image_name,
            disk_format=CONF.volume.disk_format[0]
        )['os-volume_upload_image']
        image_id = body['image_id']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.image_client.delete_image, image_id)

        # Wait for the image to become active
        waiters.wait_for_image_status(
            self.image_client, image_id, 'active')
        # Wait for the volume to become available again
        waiters.wait_for_volume_resource_status(
            self.volumes_client, volume['id'], 'available')

        image = self._verify_image_location_and_hash(
            image_id, 'volume uploaded image')
        self.assertEqual(image_name, image['name'])
