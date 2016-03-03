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

from tempest.api.orchestration import base
from tempest.common.utils import data_utils
from tempest import config
from tempest.lib import exceptions as lib_exc
from tempest import test


CONF = config.CONF


class CinderResourcesTest(base.BaseOrchestrationTest):

    @classmethod
    def skip_checks(cls):
        super(CinderResourcesTest, cls).skip_checks()
        if not CONF.service_available.cinder:
            raise cls.skipException('Cinder support is required')

    def _cinder_verify(self, volume_id, template):
        self.assertIsNotNone(volume_id)
        volume = self.volumes_client.show_volume(volume_id)['volume']
        self.assertEqual('available', volume.get('status'))
        self.assertEqual(CONF.volume.volume_size, volume.get('size'))

        # Some volume properties have been renamed with Cinder v2
        if CONF.volume_feature_enabled.api_v2:
            description_field = 'description'
            name_field = 'name'
        else:
            description_field = 'display_description'
            name_field = 'display_name'

        self.assertEqual(template['resources']['volume']['properties'][
            'description'], volume.get(description_field))
        self.assertEqual(template['resources']['volume']['properties'][
            'name'], volume.get(name_field))

    def _outputs_verify(self, stack_identifier, template):
        self.assertEqual('available',
                         self.get_stack_output(stack_identifier, 'status'))
        self.assertEqual(str(CONF.volume.volume_size),
                         self.get_stack_output(stack_identifier, 'size'))
        self.assertEqual(template['resources']['volume']['properties'][
            'description'], self.get_stack_output(stack_identifier,
                                                  'display_description'))
        self.assertEqual(template['resources']['volume']['properties'][
            'name'], self.get_stack_output(stack_identifier, 'display_name'))

    @test.idempotent_id('c3243329-7bdd-4730-b402-4d19d50c41d8')
    @test.services('volume')
    def test_cinder_volume_create_delete(self):
        """Create and delete a volume via OS::Cinder::Volume."""
        stack_name = data_utils.rand_name('heat')
        template = self.read_template('cinder_basic')
        stack_identifier = self.create_stack(
            stack_name,
            template,
            parameters={
                'volume_size': CONF.volume.volume_size
            })
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        # Verify with cinder that the volume exists, with matching details
        volume_id = self.get_stack_output(stack_identifier, 'volume_id')
        cinder_basic_template = self.load_template('cinder_basic')
        self._cinder_verify(volume_id, cinder_basic_template)

        # Verify the stack outputs are as expected
        self._outputs_verify(stack_identifier, cinder_basic_template)

        # Delete the stack and ensure the volume is gone
        self.client.delete_stack(stack_identifier)
        self.client.wait_for_stack_status(stack_identifier, 'DELETE_COMPLETE')
        self.assertRaises(lib_exc.NotFound,
                          self.volumes_client.show_volume,
                          volume_id)

    def _cleanup_volume(self, volume_id):
        """Cleanup the volume direct with cinder."""
        self.volumes_client.delete_volume(volume_id)
        self.volumes_client.wait_for_resource_deletion(volume_id)

    @test.idempotent_id('ea8b3a46-b932-4c18-907a-fe23f00b33f8')
    @test.services('volume')
    def test_cinder_volume_create_delete_retain(self):
        """Ensure the 'Retain' deletion policy is respected."""
        stack_name = data_utils.rand_name('heat')
        template = self.read_template('cinder_basic_delete_retain')
        stack_identifier = self.create_stack(
            stack_name,
            template,
            parameters={
                'volume_size': CONF.volume.volume_size
            })
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        # Verify with cinder that the volume exists, with matching details
        volume_id = self.get_stack_output(stack_identifier, 'volume_id')
        self.addCleanup(self._cleanup_volume, volume_id)
        retain_template = self.load_template('cinder_basic_delete_retain')
        self._cinder_verify(volume_id, retain_template)

        # Verify the stack outputs are as expected
        self._outputs_verify(stack_identifier, retain_template)

        # Delete the stack and ensure the volume is *not* gone
        self.client.delete_stack(stack_identifier)
        self.client.wait_for_stack_status(stack_identifier, 'DELETE_COMPLETE')
        self._cinder_verify(volume_id, retain_template)

        # Volume cleanup happens via addCleanup calling _cleanup_volume
