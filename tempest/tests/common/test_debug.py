# Copyright 2014 NEC Corporation.
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

import mock

from tempest.common import debug
from tempest import config
from tempest.openstack.common.fixture import mockpatch
from tempest import test
from tempest.tests import base
from tempest.tests import fake_config


class TestDebug(base.TestCase):

    def setUp(self):
        super(TestDebug, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)

        common_pre = 'tempest.common.commands'
        self.ip_addr_raw_mock = self.patch(common_pre + '.ip_addr_raw')
        self.ip_route_raw_mock = self.patch(common_pre + '.ip_route_raw')
        self.iptables_raw_mock = self.patch(common_pre + '.iptables_raw')
        self.ip_ns_list_mock = self.patch(common_pre + '.ip_ns_list')
        self.ip_ns_addr_mock = self.patch(common_pre + '.ip_ns_addr')
        self.ip_ns_route_mock = self.patch(common_pre + '.ip_ns_route')
        self.iptables_ns_mock = self.patch(common_pre + '.iptables_ns')
        self.ovs_db_dump_mock = self.patch(common_pre + '.ovs_db_dump')

        self.log_mock = self.patch('tempest.common.debug.LOG')

    def test_log_ip_ns_debug_disabled(self):
        self.useFixture(mockpatch.PatchObject(test.CONF.debug,
                                              'enable', False))
        debug.log_ip_ns()
        self.assertFalse(self.ip_addr_raw_mock.called)
        self.assertFalse(self.log_mock.info.called)

    def test_log_ip_ns_debug_enabled(self):
        self.useFixture(mockpatch.PatchObject(test.CONF.debug,
                                              'enable', True))

        tables = ['filter', 'nat', 'mangle']
        self.ip_ns_list_mock.return_value = [1, 2]

        debug.log_ip_ns()
        self.ip_addr_raw_mock.assert_called_with()
        self.assertTrue(self.log_mock.info.called)
        self.ip_route_raw_mock.assert_called_with()
        self.assertEqual(len(tables), self.iptables_raw_mock.call_count)
        for table in tables:
            self.assertIn(mock.call(table),
                          self.iptables_raw_mock.call_args_list)

        self.ip_ns_list_mock.assert_called_with()
        self.assertEqual(len(self.ip_ns_list_mock.return_value),
                         self.ip_ns_addr_mock.call_count)
        self.assertEqual(len(self.ip_ns_list_mock.return_value),
                         self.ip_ns_route_mock.call_count)
        for ns in self.ip_ns_list_mock.return_value:
            self.assertIn(mock.call(ns),
                          self.ip_ns_addr_mock.call_args_list)
            self.assertIn(mock.call(ns),
                          self.ip_ns_route_mock.call_args_list)

        self.assertEqual(len(tables) * len(self.ip_ns_list_mock.return_value),
                         self.iptables_ns_mock.call_count)
        for ns in self.ip_ns_list_mock.return_value:
            for table in tables:
                self.assertIn(mock.call(ns, table),
                              self.iptables_ns_mock.call_args_list)

    def test_log_ovs_db_debug_disabled(self):
        self.useFixture(mockpatch.PatchObject(test.CONF.debug,
                                              'enable', False))
        self.useFixture(mockpatch.PatchObject(test.CONF.service_available,
                                              'neutron', False))
        debug.log_ovs_db()
        self.assertFalse(self.ovs_db_dump_mock.called)

        self.useFixture(mockpatch.PatchObject(test.CONF.debug,
                                              'enable', True))
        self.useFixture(mockpatch.PatchObject(test.CONF.service_available,
                                              'neutron', False))
        debug.log_ovs_db()
        self.assertFalse(self.ovs_db_dump_mock.called)

        self.useFixture(mockpatch.PatchObject(test.CONF.debug,
                                              'enable', False))
        self.useFixture(mockpatch.PatchObject(test.CONF.service_available,
                                              'neutron', True))
        debug.log_ovs_db()
        self.assertFalse(self.ovs_db_dump_mock.called)

    def test_log_ovs_db_debug_enabled(self):
        self.useFixture(mockpatch.PatchObject(test.CONF.debug,
                                              'enable', True))
        self.useFixture(mockpatch.PatchObject(test.CONF.service_available,
                                              'neutron', True))
        debug.log_ovs_db()
        self.ovs_db_dump_mock.assert_called_with()

    def test_log_net_debug(self):
        self.log_ip_ns_mock = self.patch('tempest.common.debug.log_ip_ns')
        self.log_ovs_db_mock = self.patch('tempest.common.debug.log_ovs_db')

        debug.log_net_debug()
        self.log_ip_ns_mock.assert_called_with()
        self.log_ovs_db_mock.assert_called_with()
