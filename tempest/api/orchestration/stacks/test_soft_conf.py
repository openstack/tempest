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

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.orchestration import base
from tempest import config
from tempest import test

LOG = logging.getLogger(__name__)
CONF = config.CONF


class TestSoftwareConfig(base.BaseOrchestrationTest):

    def setUp(self):
        super(TestSoftwareConfig, self).setUp()
        self.configs = []
        # Add 2 sets of software configuration
        self.configs.append(self._config_create('a'))
        self.configs.append(self._config_create('b'))
        # Create a deployment using config a's id
        self._deployment_create(self.configs[0]['id'])

    def _config_create(self, suffix):
        configuration = {'group': 'script',
                         'inputs': [],
                         'outputs': [],
                         'options': {}}
        configuration['name'] = 'heat_soft_config_%s' % suffix
        configuration['config'] = '#!/bin/bash echo init-%s' % suffix
        api_config = self.client.create_software_config(**configuration)
        configuration['id'] = api_config['software_config']['id']
        self.addCleanup(self._config_delete, configuration['id'])
        self._validate_config(configuration, api_config)
        return configuration

    def _validate_config(self, configuration, api_config):
        # Assert all expected keys are present with matching data
        for k in configuration.keys():
            self.assertEqual(configuration[k],
                             api_config['software_config'][k])

    def _deployment_create(self, config_id):
        self.server_id = data_utils.rand_name('dummy-server')
        self.action = 'ACTION_0'
        self.status = 'STATUS_0'
        self.input_values = {}
        self.output_values = []
        self.status_reason = 'REASON_0'
        self.signal_transport = 'NO_SIGNAL'
        self.deployment = self.client.create_software_deploy(
            self.server_id, config_id, self.action, self.status,
            self.input_values, self.output_values, self.status_reason,
            self.signal_transport)
        self.deployment_id = self.deployment['software_deployment']['id']
        self.addCleanup(self._deployment_delete, self.deployment_id)

    def _deployment_delete(self, deploy_id):
        self.client.delete_software_deploy(deploy_id)
        # Testing that it is really gone
        self.assertRaises(
            lib_exc.NotFound, self.client.show_software_deployment,
            self.deployment_id)

    def _config_delete(self, config_id):
        self.client.delete_software_config(config_id)
        # Testing that it is really gone
        self.assertRaises(
            lib_exc.NotFound, self.client.show_software_config, config_id)

    @test.attr(type='smoke')
    @test.idempotent_id('136162ed-9445-4b9c-b7fc-306af8b5da99')
    def test_get_software_config(self):
        """Testing software config get."""
        for conf in self.configs:
            api_config = self.client.show_software_config(conf['id'])
            self._validate_config(conf, api_config)

    @test.attr(type='smoke')
    @test.idempotent_id('1275c835-c967-4a2c-8d5d-ad533447ed91')
    def test_get_deployment_list(self):
        """Getting a list of all deployments"""
        deploy_list = self.client.list_software_deployments()
        deploy_ids = [deploy['id'] for deploy in
                      deploy_list['software_deployments']]
        self.assertIn(self.deployment_id, deploy_ids)

    @test.attr(type='smoke')
    @test.idempotent_id('fe7cd9f9-54b1-429c-a3b7-7df8451db913')
    def test_get_deployment_metadata(self):
        """Testing deployment metadata get"""
        metadata = self.client.show_software_deployment_metadata(
            self.server_id)
        conf_ids = [conf['id'] for conf in metadata['metadata']]
        self.assertIn(self.configs[0]['id'], conf_ids)

    def _validate_deployment(self, action, status, reason, config_id):
        deployment = self.client.show_software_deployment(self.deployment_id)
        self.assertEqual(action, deployment['software_deployment']['action'])
        self.assertEqual(status, deployment['software_deployment']['status'])
        self.assertEqual(reason,
                         deployment['software_deployment']['status_reason'])
        self.assertEqual(config_id,
                         deployment['software_deployment']['config_id'])

    @test.attr(type='smoke')
    @test.idempotent_id('f29d21f3-ed75-47cf-8cdc-ef1bdeb4c674')
    def test_software_deployment_create_validate(self):
        """Testing software deployment was created as expected."""
        # Asserting that all fields were created
        self.assert_fields_in_dict(
            self.deployment['software_deployment'], 'action', 'config_id',
            'id', 'input_values', 'output_values', 'server_id', 'status',
            'status_reason')
        # Testing get for this deployment and verifying parameters
        self._validate_deployment(self.action, self.status,
                                  self.status_reason, self.configs[0]['id'])

    @test.attr(type='smoke')
    @test.idempotent_id('2ac43ab3-34f2-415d-be2e-eabb4d14ee32')
    def test_software_deployment_update_no_metadata_change(self):
        """Testing software deployment update without metadata change."""
        metadata = self.client.show_software_deployment_metadata(
            self.server_id)
        # Updating values without changing the configuration ID
        new_action = 'ACTION_1'
        new_status = 'STATUS_1'
        new_reason = 'REASON_1'
        self.client.update_software_deploy(
            self.deployment_id, self.server_id, self.configs[0]['id'],
            new_action, new_status, self.input_values, self.output_values,
            new_reason, self.signal_transport)
        # Verifying get and that the deployment was updated as expected
        self._validate_deployment(new_action, new_status,
                                  new_reason, self.configs[0]['id'])

        # Metadata should not be changed at this point
        test_metadata = self.client.show_software_deployment_metadata(
            self.server_id)
        for key in metadata['metadata'][0]:
            self.assertEqual(
                metadata['metadata'][0][key],
                test_metadata['metadata'][0][key])

    @test.attr(type='smoke')
    @test.idempotent_id('92c48944-d79d-4595-a840-8e1a581c1a72')
    def test_software_deployment_update_with_metadata_change(self):
        """Testing software deployment update with metadata change."""
        metadata = self.client.show_software_deployment_metadata(
            self.server_id)
        self.client.update_software_deploy(
            self.deployment_id, self.server_id, self.configs[1]['id'],
            self.action, self.status, self.input_values,
            self.output_values, self.status_reason, self.signal_transport)
        self._validate_deployment(self.action, self.status,
                                  self.status_reason, self.configs[1]['id'])
        # Metadata should now be changed
        new_metadata = self.client.show_software_deployment_metadata(
            self.server_id)
        # Its enough to test the ID in this case
        meta_id = metadata['metadata'][0]['id']
        test_id = new_metadata['metadata'][0]['id']
        self.assertNotEqual(meta_id, test_id)
