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

import logging

from tempest.api.orchestration import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class CinderResourcesTest(base.BaseOrchestrationTest):

    @classmethod
    def setUpClass(cls):
        super(CinderResourcesTest, cls).setUpClass()
        if not CONF.service_available.cinder:
            raise cls.skipException('Cinder support is required')

    def _cinder_verify(self, volume_id):
        self.assertIsNotNone(volume_id)
        resp, volume = self.volumes_client.get_volume(volume_id)
        self.assertEqual(200, resp.status)
        self.assertEqual('available', volume.get('status'))
        self.assertEqual(1, volume.get('size'))
        self.assertEqual('a descriptive description',
                         volume.get('display_description'))
        self.assertEqual('volume_name',
                         volume.get('display_name'))

    def _outputs_verify(self, stack_identifier):
        self.assertEqual('available',
                         self.get_stack_output(stack_identifier, 'status'))
        self.assertEqual('1',
                         self.get_stack_output(stack_identifier, 'size'))
        self.assertEqual('a descriptive description',
                         self.get_stack_output(stack_identifier,
                                               'display_description'))
        self.assertEqual('volume_name',
                         self.get_stack_output(stack_identifier,
                                               'display_name'))

    @test.attr(type='gate')
    def test_cinder_volume_create_delete(self):
        """Create and delete a volume via OS::Cinder::Volume."""
        stack_name = data_utils.rand_name('heat')
        template = self.load_template('cinder_basic')
        stack_identifier = self.create_stack(stack_name, template)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        # Verify with cinder that the volume exists, with matching details
        volume_id = self.get_stack_output(stack_identifier, 'volume_id')
        self._cinder_verify(volume_id)

        # Verify the stack outputs are as expected
        self._outputs_verify(stack_identifier)

        # Delete the stack and ensure the volume is gone
        self.client.delete_stack(stack_identifier)
        self.client.wait_for_stack_status(stack_identifier, 'DELETE_COMPLETE')
        self.assertRaises(exceptions.NotFound,
                          self.volumes_client.get_volume,
                          volume_id)

    def _cleanup_volume(self, volume_id):
        """Cleanup the volume direct with cinder."""
        resp = self.volumes_client.delete_volume(volume_id)
        self.assertEqual(202, resp[0].status)
        self.volumes_client.wait_for_resource_deletion(volume_id)

    @test.attr(type='gate')
    def test_cinder_volume_create_delete_retain(self):
        """Ensure the 'Retain' deletion policy is respected."""
        stack_name = data_utils.rand_name('heat')
        template = self.load_template('cinder_basic_delete_retain')
        stack_identifier = self.create_stack(stack_name, template)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        # Verify with cinder that the volume exists, with matching details
        volume_id = self.get_stack_output(stack_identifier, 'volume_id')
        self.addCleanup(self._cleanup_volume, volume_id)
        self._cinder_verify(volume_id)

        # Verify the stack outputs are as expected
        self._outputs_verify(stack_identifier)

        # Delete the stack and ensure the volume is *not* gone
        self.client.delete_stack(stack_identifier)
        self.client.wait_for_stack_status(stack_identifier, 'DELETE_COMPLETE')
        self._cinder_verify(volume_id)

        # Volume cleanup happens via addCleanup calling _cleanup_volume
