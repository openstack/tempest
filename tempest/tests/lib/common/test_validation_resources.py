# Copyright (c) 2017 IBM Corp.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import fixtures
import mock
import testtools

from tempest.lib.common import validation_resources as vr
from tempest.lib import exceptions as lib_exc
from tempest.lib.services import clients
from tempest.tests import base
from tempest.tests.lib import fake_credentials
from tempest.tests.lib.services import registry_fixture

FAKE_SECURITY_GROUP = {'security_group': {'id': 'sg_id'}}
FAKE_KEYPAIR = {'keypair': {'name': 'keypair_name'}}
FAKE_FIP_NOVA_NET = {'floating_ip': {'ip': '1.2.3.4', 'id': '1234'}}
FAKE_FIP_NEUTRON = {'floatingip': {'floating_ip_address': '1.2.3.4',
                                   'id': '1234'}}

SERVICES = 'tempest.lib.services'
SG_CLIENT = (SERVICES + '.%s.security_groups_client.SecurityGroupsClient.%s')
SGR_CLIENT = (SERVICES + '.%s.security_group_rules_client.'
              'SecurityGroupRulesClient.create_security_group_rule')
KP_CLIENT = (SERVICES + '.compute.keypairs_client.KeyPairsClient.%s')
FIP_CLIENT = (SERVICES + '.%s.floating_ips_client.FloatingIPsClient.%s')


class TestValidationResources(base.TestCase):

    def setUp(self):
        super(TestValidationResources, self).setUp()
        self.useFixture(registry_fixture.RegistryFixture())
        self.mock_sg_compute = self.useFixture(fixtures.MockPatch(
            SG_CLIENT % ('compute', 'create_security_group'), autospec=True,
            return_value=FAKE_SECURITY_GROUP))
        self.mock_sg_network = self.useFixture(fixtures.MockPatch(
            SG_CLIENT % ('network', 'create_security_group'), autospec=True,
            return_value=FAKE_SECURITY_GROUP))
        self.mock_sgr_compute = self.useFixture(fixtures.MockPatch(
            SGR_CLIENT % 'compute', autospec=True))
        self.mock_sgr_network = self.useFixture(fixtures.MockPatch(
            SGR_CLIENT % 'network', autospec=True))
        self.mock_kp = self.useFixture(fixtures.MockPatch(
            KP_CLIENT % 'create_keypair', autospec=True,
            return_value=FAKE_KEYPAIR))
        self.mock_fip_compute = self.useFixture(fixtures.MockPatch(
            FIP_CLIENT % ('compute', 'create_floating_ip'), autospec=True,
            return_value=FAKE_FIP_NOVA_NET))
        self.mock_fip_network = self.useFixture(fixtures.MockPatch(
            FIP_CLIENT % ('network', 'create_floatingip'), autospec=True,
            return_value=FAKE_FIP_NEUTRON))
        self.os = clients.ServiceClients(
            fake_credentials.FakeKeystoneV3Credentials(), 'fake_uri')

    def test_create_ssh_security_group_nova_net(self):
        expected_sg_id = FAKE_SECURITY_GROUP['security_group']['id']
        sg = vr.create_ssh_security_group(self.os, add_rule=True,
                                          use_neutron=False)
        self.assertEqual(FAKE_SECURITY_GROUP['security_group'], sg)
        # Neutron clients have not been used
        self.assertEqual(self.mock_sg_network.mock.call_count, 0)
        self.assertEqual(self.mock_sgr_network.mock.call_count, 0)
        # Nova-net clients assertions
        self.assertGreater(self.mock_sg_compute.mock.call_count, 0)
        self.assertGreater(self.mock_sgr_compute.mock.call_count, 0)
        for call in self.mock_sgr_compute.mock.call_args_list[1:]:
            self.assertIn(expected_sg_id, call[1].values())

    def test_create_ssh_security_group_neutron(self):
        expected_sg_id = FAKE_SECURITY_GROUP['security_group']['id']
        expected_ethertype = 'fake_ethertype'
        sg = vr.create_ssh_security_group(self.os, add_rule=True,
                                          use_neutron=True,
                                          ethertype=expected_ethertype)
        self.assertEqual(FAKE_SECURITY_GROUP['security_group'], sg)
        # Nova-net clients have not been used
        self.assertEqual(self.mock_sg_compute.mock.call_count, 0)
        self.assertEqual(self.mock_sgr_compute.mock.call_count, 0)
        # Nova-net clients assertions
        self.assertGreater(self.mock_sg_network.mock.call_count, 0)
        self.assertGreater(self.mock_sgr_network.mock.call_count, 0)
        # Check SG ID and ethertype are passed down to rules
        for call in self.mock_sgr_network.mock.call_args_list[1:]:
            self.assertIn(expected_sg_id, call[1].values())
            self.assertIn(expected_ethertype, call[1].values())

    def test_create_ssh_security_no_rules(self):
        sg = vr.create_ssh_security_group(self.os, add_rule=False)
        self.assertEqual(FAKE_SECURITY_GROUP['security_group'], sg)
        # SG Rules clients have not been used
        self.assertEqual(self.mock_sgr_compute.mock.call_count, 0)
        self.assertEqual(self.mock_sgr_network.mock.call_count, 0)

    @mock.patch.object(vr, 'create_ssh_security_group',
                       return_value=FAKE_SECURITY_GROUP['security_group'])
    def test_create_validation_resources_nova_net(self, mock_create_sg):
        expected_floating_network_id = 'my_fni'
        expected_floating_network_name = 'my_fnn'
        resources = vr.create_validation_resources(
            self.os, keypair=True, floating_ip=True, security_group=True,
            security_group_rules=True, ethertype='IPv6', use_neutron=False,
            floating_network_id=expected_floating_network_id,
            floating_network_name=expected_floating_network_name)
        # Keypair calls
        self.assertGreater(self.mock_kp.mock.call_count, 0)
        # Floating IP calls
        self.assertGreater(self.mock_fip_compute.mock.call_count, 0)
        for call in self.mock_fip_compute.mock.call_args_list[1:]:
            self.assertIn(expected_floating_network_name, call[1].values())
            self.assertNotIn(expected_floating_network_id, call[1].values())
        self.assertEqual(self.mock_fip_network.mock.call_count, 0)
        # SG calls
        mock_create_sg.assert_called_once()
        # Resources
        for resource in ['keypair', 'floating_ip', 'security_group']:
            self.assertIn(resource, resources)
        self.assertEqual(FAKE_KEYPAIR['keypair'], resources['keypair'])
        self.assertEqual(FAKE_SECURITY_GROUP['security_group'],
                         resources['security_group'])
        self.assertEqual(FAKE_FIP_NOVA_NET['floating_ip'],
                         resources['floating_ip'])

    @mock.patch.object(vr, 'create_ssh_security_group',
                       return_value=FAKE_SECURITY_GROUP['security_group'])
    def test_create_validation_resources_neutron(self, mock_create_sg):
        expected_floating_network_id = 'my_fni'
        expected_floating_network_name = 'my_fnn'
        resources = vr.create_validation_resources(
            self.os, keypair=True, floating_ip=True, security_group=True,
            security_group_rules=True, ethertype='IPv6', use_neutron=True,
            floating_network_id=expected_floating_network_id,
            floating_network_name=expected_floating_network_name)
        # Keypair calls
        self.assertGreater(self.mock_kp.mock.call_count, 0)
        # Floating IP calls
        self.assertEqual(self.mock_fip_compute.mock.call_count, 0)
        self.assertGreater(self.mock_fip_network.mock.call_count, 0)
        for call in self.mock_fip_compute.mock.call_args_list[1:]:
            self.assertIn(expected_floating_network_id, call[1].values())
            self.assertNotIn(expected_floating_network_name, call[1].values())
        # SG calls
        mock_create_sg.assert_called_once()
        # Resources
        for resource in ['keypair', 'floating_ip', 'security_group']:
            self.assertIn(resource, resources)
        self.assertEqual(FAKE_KEYPAIR['keypair'], resources['keypair'])
        self.assertEqual(FAKE_SECURITY_GROUP['security_group'],
                         resources['security_group'])
        self.assertIn('ip', resources['floating_ip'])
        self.assertEqual(resources['floating_ip']['ip'],
                         FAKE_FIP_NEUTRON['floatingip']['floating_ip_address'])
        self.assertEqual(resources['floating_ip']['id'],
                         FAKE_FIP_NEUTRON['floatingip']['id'])


class TestClearValidationResourcesFixture(base.TestCase):

    def setUp(self):
        super(TestClearValidationResourcesFixture, self).setUp()
        self.useFixture(registry_fixture.RegistryFixture())
        self.mock_sg_compute = self.useFixture(fixtures.MockPatch(
            SG_CLIENT % ('compute', 'delete_security_group'), autospec=True))
        self.mock_sg_network = self.useFixture(fixtures.MockPatch(
            SG_CLIENT % ('network', 'delete_security_group'), autospec=True))
        self.mock_sg_wait_compute = self.useFixture(fixtures.MockPatch(
            SG_CLIENT % ('compute', 'wait_for_resource_deletion'),
            autospec=True))
        self.mock_sg_wait_network = self.useFixture(fixtures.MockPatch(
            SG_CLIENT % ('network', 'wait_for_resource_deletion'),
            autospec=True))
        self.mock_kp = self.useFixture(fixtures.MockPatch(
            KP_CLIENT % 'delete_keypair', autospec=True))
        self.mock_fip_compute = self.useFixture(fixtures.MockPatch(
            FIP_CLIENT % ('compute', 'delete_floating_ip'), autospec=True))
        self.mock_fip_network = self.useFixture(fixtures.MockPatch(
            FIP_CLIENT % ('network', 'delete_floatingip'), autospec=True))
        self.os = clients.ServiceClients(
            fake_credentials.FakeKeystoneV3Credentials(), 'fake_uri')

    def test_clear_validation_resources_nova_net(self):
        vr.clear_validation_resources(
            self.os,
            floating_ip=FAKE_FIP_NOVA_NET['floating_ip'],
            security_group=FAKE_SECURITY_GROUP['security_group'],
            keypair=FAKE_KEYPAIR['keypair'],
            use_neutron=False)
        self.assertGreater(self.mock_kp.mock.call_count, 0)
        for call in self.mock_kp.mock.call_args_list[1:]:
            self.assertIn(FAKE_KEYPAIR['keypair']['name'], call[1].values())
        self.assertGreater(self.mock_sg_compute.mock.call_count, 0)
        for call in self.mock_sg_compute.mock.call_args_list[1:]:
            self.assertIn(FAKE_SECURITY_GROUP['security_group']['id'],
                          call[1].values())
        self.assertGreater(self.mock_sg_wait_compute.mock.call_count, 0)
        for call in self.mock_sg_wait_compute.mock.call_args_list[1:]:
            self.assertIn(FAKE_SECURITY_GROUP['security_group']['id'],
                          call[1].values())
        self.assertEqual(self.mock_sg_network.mock.call_count, 0)
        self.assertEqual(self.mock_sg_wait_network.mock.call_count, 0)
        self.assertGreater(self.mock_fip_compute.mock.call_count, 0)
        for call in self.mock_fip_compute.mock.call_args_list[1:]:
            self.assertIn(FAKE_FIP_NOVA_NET['floating_ip']['id'],
                          call[1].values())
        self.assertEqual(self.mock_fip_network.mock.call_count, 0)

    def test_clear_validation_resources_neutron(self):
        vr.clear_validation_resources(
            self.os,
            floating_ip=FAKE_FIP_NEUTRON['floatingip'],
            security_group=FAKE_SECURITY_GROUP['security_group'],
            keypair=FAKE_KEYPAIR['keypair'],
            use_neutron=True)
        self.assertGreater(self.mock_kp.mock.call_count, 0)
        for call in self.mock_kp.mock.call_args_list[1:]:
            self.assertIn(FAKE_KEYPAIR['keypair']['name'], call[1].values())
        self.assertGreater(self.mock_sg_network.mock.call_count, 0)
        for call in self.mock_sg_network.mock.call_args_list[1:]:
            self.assertIn(FAKE_SECURITY_GROUP['security_group']['id'],
                          call[1].values())
        self.assertGreater(self.mock_sg_wait_network.mock.call_count, 0)
        for call in self.mock_sg_wait_network.mock.call_args_list[1:]:
            self.assertIn(FAKE_SECURITY_GROUP['security_group']['id'],
                          call[1].values())
        self.assertEqual(self.mock_sg_compute.mock.call_count, 0)
        self.assertEqual(self.mock_sg_wait_compute.mock.call_count, 0)
        self.assertGreater(self.mock_fip_network.mock.call_count, 0)
        for call in self.mock_fip_network.mock.call_args_list[1:]:
            self.assertIn(FAKE_FIP_NEUTRON['floatingip']['id'],
                          call[1].values())
        self.assertEqual(self.mock_fip_compute.mock.call_count, 0)

    def test_clear_validation_resources_exceptions(self):
        # Test that even with exceptions all cleanups are invoked and that only
        # the first exception is reported.
        # NOTE(andreaf) There's not way of knowing which exception is going to
        # be raised first unless we enforce which resource is cleared first,
        # which is not really interesting, but also not harmful. keypair first.
        self.mock_kp.mock.side_effect = Exception('keypair exception')
        self.mock_sg_network.mock.side_effect = Exception('sg exception')
        self.mock_fip_network.mock.side_effect = Exception('fip exception')
        with testtools.ExpectedException(Exception, value_re='keypair'):
            vr.clear_validation_resources(
                self.os,
                floating_ip=FAKE_FIP_NEUTRON['floatingip'],
                security_group=FAKE_SECURITY_GROUP['security_group'],
                keypair=FAKE_KEYPAIR['keypair'],
                use_neutron=True)
        # Clients calls are still made, but not the wait call
        self.assertGreater(self.mock_kp.mock.call_count, 0)
        self.assertGreater(self.mock_sg_network.mock.call_count, 0)
        self.assertGreater(self.mock_fip_network.mock.call_count, 0)

    def test_clear_validation_resources_wait_not_found_wait(self):
        # Test that a not found on wait is not an exception
        self.mock_sg_wait_network.mock.side_effect = lib_exc.NotFound('yay')
        vr.clear_validation_resources(
            self.os,
            floating_ip=FAKE_FIP_NEUTRON['floatingip'],
            security_group=FAKE_SECURITY_GROUP['security_group'],
            keypair=FAKE_KEYPAIR['keypair'],
            use_neutron=True)
        # Clients calls are still made, but not the wait call
        self.assertGreater(self.mock_kp.mock.call_count, 0)
        self.assertGreater(self.mock_sg_network.mock.call_count, 0)
        self.assertGreater(self.mock_sg_wait_network.mock.call_count, 0)
        self.assertGreater(self.mock_fip_network.mock.call_count, 0)

    def test_clear_validation_resources_wait_not_found_delete(self):
        # Test that a not found on delete is not an exception
        self.mock_kp.mock.side_effect = lib_exc.NotFound('yay')
        self.mock_sg_network.mock.side_effect = lib_exc.NotFound('yay')
        self.mock_fip_network.mock.side_effect = lib_exc.NotFound('yay')
        vr.clear_validation_resources(
            self.os,
            floating_ip=FAKE_FIP_NEUTRON['floatingip'],
            security_group=FAKE_SECURITY_GROUP['security_group'],
            keypair=FAKE_KEYPAIR['keypair'],
            use_neutron=True)
        # Clients calls are still made, but not the wait call
        self.assertGreater(self.mock_kp.mock.call_count, 0)
        self.assertGreater(self.mock_sg_network.mock.call_count, 0)
        self.assertEqual(self.mock_sg_wait_network.mock.call_count, 0)
        self.assertGreater(self.mock_fip_network.mock.call_count, 0)


class TestValidationResourcesFixture(base.TestCase):

    @mock.patch.object(vr, 'create_validation_resources', autospec=True)
    def test_use_fixture(self, mock_vr):
        exp_vr = dict(keypair='keypair',
                      floating_ip='floating_ip',
                      security_group='security_group')
        mock_vr.return_value = exp_vr
        exp_clients = 'clients'
        exp_parameters = dict(keypair=True, floating_ip=True,
                              security_group=True, security_group_rules=True,
                              ethertype='v6', use_neutron=True,
                              floating_network_id='fnid',
                              floating_network_name='fnname')
        # First mock cleanup
        self.useFixture(fixtures.MockPatchObject(
            vr, 'clear_validation_resources', autospec=True))
        # And then use vr fixture, so when the fixture is cleaned-up, the mock
        # is still there
        vr_fixture = self.useFixture(vr.ValidationResourcesFixture(
            exp_clients, **exp_parameters))
        # Assert vr have been provisioned
        mock_vr.assert_called_once_with(exp_clients, **exp_parameters)
        # Assert vr have been setup in the fixture
        self.assertEqual(exp_vr, vr_fixture.resources)

    @mock.patch.object(vr, 'clear_validation_resources', autospec=True)
    @mock.patch.object(vr, 'create_validation_resources', autospec=True)
    def test_use_fixture_context(self, mock_vr, mock_clear):
        exp_vr = dict(keypair='keypair',
                      floating_ip='floating_ip',
                      security_group='security_group')
        mock_vr.return_value = exp_vr
        exp_clients = 'clients'
        exp_parameters = dict(keypair=True, floating_ip=True,
                              security_group=True, security_group_rules=True,
                              ethertype='v6', use_neutron=True,
                              floating_network_id='fnid',
                              floating_network_name='fnname')
        with vr.ValidationResourcesFixture(exp_clients,
                                           **exp_parameters) as vr_fixture:
            # Assert vr have been provisioned
            mock_vr.assert_called_once_with(exp_clients, **exp_parameters)
            # Assert vr have been setup in the fixture
            self.assertEqual(exp_vr, vr_fixture.resources)
        # After context manager is closed, clear is invoked
        exp_vr['use_neutron'] = exp_parameters['use_neutron']
        mock_clear.assert_called_once_with(exp_clients, **exp_vr)
