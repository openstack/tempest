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

from tempest_lib.common.utils import data_utils

from tempest.api.orchestration import base
from tempest import test


LOG = logging.getLogger(__name__)


class NovaKeyPairResourcesYAMLTest(base.BaseOrchestrationTest):
    _tpl_type = 'yaml'
    _resource = 'resources'
    _type = 'type'

    @classmethod
    def resource_setup(cls):
        super(NovaKeyPairResourcesYAMLTest, cls).resource_setup()
        cls.stack_name = data_utils.rand_name('heat')
        template = cls.read_template('nova_keypair', ext=cls._tpl_type)

        # create the stack, avoid any duplicated key.
        cls.stack_identifier = cls.create_stack(
            cls.stack_name,
            template,
            parameters={
                'KeyPairName1': cls.stack_name + '_1',
                'KeyPairName2': cls.stack_name + '_2'
            })

        cls.stack_id = cls.stack_identifier.split('/')[1]
        cls.client.wait_for_stack_status(cls.stack_id, 'CREATE_COMPLETE')
        resources = cls.client.list_resources(cls.stack_identifier)
        cls.test_resources = {}
        for resource in resources:
            cls.test_resources[resource['logical_resource_id']] = resource

    @test.attr(type='gate')
    @test.idempotent_id('b476eac2-a302-4815-961f-18c410a2a537')
    def test_created_resources(self):
        """Verifies created keypair resource."""

        nova_keypair_template = self.load_template('nova_keypair',
                                                   ext=self._tpl_type)
        resources = [('KeyPairSavePrivate',
                      nova_keypair_template[self._resource][
                          'KeyPairSavePrivate'][self._type]),
                     ('KeyPairDontSavePrivate',
                      nova_keypair_template[self._resource][
                          'KeyPairDontSavePrivate'][self._type])]

        for resource_name, resource_type in resources:
            resource = self.test_resources.get(resource_name, None)
            self.assertIsInstance(resource, dict)
            self.assertEqual(resource_name, resource['logical_resource_id'])
            self.assertEqual(resource_type, resource['resource_type'])
            self.assertEqual('CREATE_COMPLETE', resource['resource_status'])

    @test.attr(type='gate')
    @test.idempotent_id('8d77dec7-91fd-45a6-943d-5abd45e338a4')
    def test_stack_keypairs_output(self):
        stack = self.client.show_stack(self.stack_name)
        self.assertIsInstance(stack, dict)

        output_map = {}
        for outputs in stack['outputs']:
            output_map[outputs['output_key']] = outputs['output_value']
        # Test that first key generated public and private keys
        self.assertTrue('KeyPair_PublicKey' in output_map)
        self.assertTrue("Generated" in output_map['KeyPair_PublicKey'])
        self.assertTrue('KeyPair_PrivateKey' in output_map)
        self.assertTrue('-----BEGIN' in output_map['KeyPair_PrivateKey'])
        # Test that second key generated public key, and private key is not
        # in the output due to save_private_key = false
        self.assertTrue('KeyPairDontSavePrivate_PublicKey' in output_map)
        self.assertTrue('Generated' in
                        output_map['KeyPairDontSavePrivate_PublicKey'])
        self.assertTrue(u'KeyPairDontSavePrivate_PrivateKey' in output_map)
        private_key = output_map['KeyPairDontSavePrivate_PrivateKey']
        self.assertTrue(len(private_key) == 0)


class NovaKeyPairResourcesAWSTest(NovaKeyPairResourcesYAMLTest):
    _tpl_type = 'json'
    _resource = 'Resources'
    _type = 'Type'
