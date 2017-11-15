# Copyright (c) 2015 Deutsche Telekom AG
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

from tempest.lib.services import clients
from tempest.test_discover import plugins
from tempest.tests import base
from tempest.tests import fake_tempest_plugin as fake_plugin
from tempest.tests.lib.services import registry_fixture


class TestPluginDiscovery(base.TestCase):

    def setUp(self):
        super(TestPluginDiscovery, self).setUp()
        # Make sure we leave the registry clean
        self.useFixture(registry_fixture.RegistryFixture())

    def test_load_tests_with_one_plugin(self):
        # we can't mock stevedore since it's a singleton and already executed
        # during test discovery. So basically this test covers the plugin loop
        # and the abstract plugin interface.
        manager = plugins.TempestTestPluginManager()
        fake_obj = fake_plugin.FakeStevedoreObj()
        manager.ext_plugins = [fake_obj]
        result = manager.get_plugin_load_tests_tuple()

        self.assertEqual(fake_plugin.FakePlugin.expected_load_test,
                         result[fake_obj.name])

    def test_load_tests_with_two_plugins(self):
        manager = plugins.TempestTestPluginManager()
        obj1 = fake_plugin.FakeStevedoreObj('fake01')
        obj2 = fake_plugin.FakeStevedoreObj('fake02')
        manager.ext_plugins = [obj1, obj2]
        result = manager.get_plugin_load_tests_tuple()

        self.assertEqual(fake_plugin.FakePlugin.expected_load_test,
                         result['fake01'])
        self.assertEqual(fake_plugin.FakePlugin.expected_load_test,
                         result['fake02'])

    def test__register_service_clients_with_one_plugin(self):
        registry = clients.ClientsRegistry()
        manager = plugins.TempestTestPluginManager()
        fake_obj = fake_plugin.FakeStevedoreObj()
        manager.ext_plugins = [fake_obj]
        manager._register_service_clients()
        expected_result = fake_plugin.FakePlugin.expected_service_clients
        registered_clients = registry.get_service_clients()
        self.assertIn(fake_obj.name, registered_clients)
        self.assertEqual(expected_result, registered_clients[fake_obj.name])

    def test__get_service_clients_with_two_plugins(self):
        registry = clients.ClientsRegistry()
        manager = plugins.TempestTestPluginManager()
        obj1 = fake_plugin.FakeStevedoreObj('fake01')
        obj2 = fake_plugin.FakeStevedoreObj('fake02')
        manager.ext_plugins = [obj1, obj2]
        manager._register_service_clients()
        expected_result = fake_plugin.FakePlugin.expected_service_clients
        registered_clients = registry.get_service_clients()
        self.assertIn('fake01', registered_clients)
        self.assertIn('fake02', registered_clients)
        self.assertEqual(expected_result, registered_clients['fake01'])
        self.assertEqual(expected_result, registered_clients['fake02'])

    def test__register_service_clients_one_plugin_no_service_clients(self):
        registry = clients.ClientsRegistry()
        manager = plugins.TempestTestPluginManager()
        fake_obj = fake_plugin.FakeStevedoreObjNoServiceClients()
        manager.ext_plugins = [fake_obj]
        manager._register_service_clients()
        registered_clients = registry.get_service_clients()
        self.assertNotIn(fake_obj.name, registered_clients)
