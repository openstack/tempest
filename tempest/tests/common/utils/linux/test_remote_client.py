# Copyright 2014 IBM Corp.
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

import fixtures
import time

from oslo_config import cfg
from oslotest import mockpatch

from tempest.common.utils.linux import remote_client
from tempest import config
from tempest.lib import exceptions as lib_exc
from tempest.tests import base
from tempest.tests import fake_config


SERVER = {
    'id': 'server_uuid',
    'name': 'fake_server',
    'status': 'ACTIVE'
}

BROKEN_SERVER = {
    'id': 'broken_server_uuid',
    'name': 'broken_server',
    'status': 'ERROR'
}


class FakeServersClient(object):

    CONSOLE_OUTPUT = "Console output for %s"

    def get_console_output(self, server_id):
        status = 'ERROR'
        for s in SERVER, BROKEN_SERVER:
            if s['id'] == server_id:
                status = s['status']
        if status == 'ERROR':
            raise lib_exc.BadRequest('Server in ERROR state')
        else:
            return dict(output=self.CONSOLE_OUTPUT % server_id)


class TestRemoteClient(base.TestCase):
    def setUp(self):
        super(TestRemoteClient, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)
        cfg.CONF.set_default('ip_version_for_ssh', 4, group='validation')
        cfg.CONF.set_default('network_for_ssh', 'public', group='validation')
        cfg.CONF.set_default('connect_timeout', 1, group='validation')

        self.conn = remote_client.RemoteClient('127.0.0.1', 'user', 'pass')
        self.ssh_mock = self.useFixture(mockpatch.PatchObject(self.conn,
                                                              'ssh_client'))

    def test_hostname_equals_servername_for_expected_names(self):
        self.ssh_mock.mock.exec_command.return_value = 'fake_hostname'
        self.assertTrue(self.conn.hostname_equals_servername('fake_hostname'))

    def test_hostname_equals_servername_for_unexpected_names(self):
        self.ssh_mock.mock.exec_command.return_value = 'fake_hostname'
        self.assertFalse(
            self.conn.hostname_equals_servername('unexpected_hostname'))

    def test_get_ram_size(self):
        free_output = "Mem:         48294      45738       2555          0" \
                      "402      40346"
        self.ssh_mock.mock.exec_command.return_value = free_output
        self.assertEqual(self.conn.get_ram_size_in_mb(), '48294')

    def test_write_to_console_regular_str(self):
        self.conn.write_to_console('test')
        self._assert_exec_called_with(
            'sudo sh -c "echo \\"test\\" >/dev/console"')

    def _test_write_to_console_helper(self, message, expected_call):
        self.conn.write_to_console(message)
        self._assert_exec_called_with(expected_call)

    def test_write_to_console_special_chars(self):
        self._test_write_to_console_helper(
            '\`',
            'sudo sh -c "echo \\"\\\\\\`\\" >/dev/console"')
        self.conn.write_to_console('$')
        self._assert_exec_called_with(
            'sudo sh -c "echo \\"\\\\$\\" >/dev/console"')

    # NOTE(maurosr): The tests below end up closer to an output format
    # assurance than a test since it's basically using comand_exec to format
    # the information using gnu/linux tools.

    def _assert_exec_called_with(self, cmd):
        cmd = "set -eu -o pipefail; PATH=$PATH:/sbin; " + cmd
        self.ssh_mock.mock.exec_command.assert_called_with(cmd)

    def test_get_number_of_vcpus(self):
        self.ssh_mock.mock.exec_command.return_value = '16'
        self.assertEqual(self.conn.get_number_of_vcpus(), 16)
        self._assert_exec_called_with('grep -c ^processor /proc/cpuinfo')

    def test_get_partitions(self):
        proc_partitions = """major minor  #blocks  name

8        0  1048576 vda"""
        self.ssh_mock.mock.exec_command.return_value = proc_partitions
        self.assertEqual(self.conn.get_partitions(), proc_partitions)
        self._assert_exec_called_with('cat /proc/partitions')

    def test_get_boot_time(self):
        booted_at = 10000
        uptime_sec = 5000.02
        self.ssh_mock.mock.exec_command.return_value = uptime_sec
        self.useFixture(mockpatch.PatchObject(
            time, 'time', return_value=booted_at + uptime_sec))
        self.assertEqual(self.conn.get_boot_time(),
                         time.localtime(booted_at))
        self._assert_exec_called_with('cut -f1 -d. /proc/uptime')

    def test_ping_host(self):
        ping_response = """PING localhost (127.0.0.1) 70(98) bytes of data.
78 bytes from localhost (127.0.0.1): icmp_req=1 ttl=64 time=0.048 ms
78 bytes from localhost (127.0.0.1): icmp_req=2 ttl=64 time=0.048 ms

--- localhost ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.048/0.048/0.048/0.000 ms"""
        self.ssh_mock.mock.exec_command.return_value = ping_response
        self.assertEqual(self.conn.ping_host('127.0.0.1', count=2, size=70),
                         ping_response)
        self._assert_exec_called_with('ping -c2 -w2 -s70 127.0.0.1')

    def test_get_mac_address(self):
        macs = """0a:0b:0c:0d:0e:0f
a0:b0:c0:d0:e0:f0"""
        self.ssh_mock.mock.exec_command.return_value = macs

        self.assertEqual(self.conn.get_mac_address(), macs)
        self._assert_exec_called_with(
            "ip addr | awk '/ether/ {print $2}'")

    def test_get_ip_list(self):
        ips = """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 16436 qdisc noqueue
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast qlen 1000
    link/ether fa:16:3e:6e:26:3b brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.4/24 brd 10.0.0.255 scope global eth0
    inet6 fd55:faaf:e1ab:3d9:f816:3eff:fe6e:263b/64 scope global dynamic
       valid_lft 2591936sec preferred_lft 604736sec
    inet6 fe80::f816:3eff:fe6e:263b/64 scope link
       valid_lft forever preferred_lft forever"""
        self.ssh_mock.mock.exec_command.return_value = ips
        self.assertEqual(self.conn.get_ip_list(), ips)
        self._assert_exec_called_with('ip address')

    def test_assign_static_ip(self):
        self.ssh_mock.mock.exec_command.return_value = ''
        ip = '10.0.0.2'
        nic = 'eth0'
        self.assertEqual(self.conn.assign_static_ip(nic, ip), '')
        self._assert_exec_called_with(
            "sudo ip addr add %s/%s dev %s" % (ip, '28', nic))

    def test_set_nic_state(self):
        nic = 'eth0'
        self.conn.set_nic_state(nic)
        self._assert_exec_called_with(
            'sudo ip link set %s up' % nic)
        self.conn.set_nic_state(nic, "down")
        self._assert_exec_called_with(
            'sudo ip link set %s down' % nic)


class TestRemoteClientWithServer(base.TestCase):

    server = SERVER

    def setUp(self):
        super(TestRemoteClientWithServer, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)
        cfg.CONF.set_default('ip_version_for_ssh', 4, group='validation')
        cfg.CONF.set_default('network_for_ssh', 'public',
                             group='validation')
        cfg.CONF.set_default('connect_timeout', 1, group='validation')
        cfg.CONF.set_default('console_output', True,
                             group='compute-feature-enabled')

        self.conn = remote_client.RemoteClient(
            '127.0.0.1', 'user', 'pass',
            server=self.server, servers_client=FakeServersClient())
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.ssh.Client._get_ssh_connection',
            side_effect=lib_exc.SSHTimeout(host='127.0.0.1',
                                           user='user',
                                           password='pass')))
        self.log = self.useFixture(fixtures.FakeLogger(
            name='tempest.common.utils.linux.remote_client',
            level='DEBUG'))

    def test_validate_debug_ssh_console(self):
        self.assertRaises(lib_exc.SSHTimeout,
                          self.conn.validate_authentication)
        msg = 'Caller: %s. Timeout trying to ssh to server %s' % (
            'TestRemoteClientWithServer:test_validate_debug_ssh_console',
            self.server)
        self.assertIn(msg, self.log.output)
        self.assertIn('Console output for', self.log.output)

    def test_exec_command_debug_ssh_console(self):
        self.assertRaises(lib_exc.SSHTimeout,
                          self.conn.exec_command, 'fake command')
        self.assertIn('fake command', self.log.output)
        msg = 'Caller: %s. Timeout trying to ssh to server %s' % (
            'TestRemoteClientWithServer:test_exec_command_debug_ssh_console',
            self.server)
        self.assertIn(msg, self.log.output)
        self.assertIn('Console output for', self.log.output)


class TestRemoteClientWithBrokenServer(TestRemoteClientWithServer):

    server = BROKEN_SERVER

    def test_validate_debug_ssh_console(self):
        self.assertRaises(lib_exc.SSHTimeout,
                          self.conn.validate_authentication)
        msg = 'Caller: %s. Timeout trying to ssh to server %s' % (
            'TestRemoteClientWithBrokenServer:test_validate_debug_ssh_console',
            self.server)
        self.assertIn(msg, self.log.output)
        msg = 'Could not get console_log for server %s' % self.server['id']
        self.assertIn(msg, self.log.output)

    def test_exec_command_debug_ssh_console(self):
        self.assertRaises(lib_exc.SSHTimeout,
                          self.conn.exec_command, 'fake command')
        self.assertIn('fake command', self.log.output)
        caller = ":".join(['TestRemoteClientWithBrokenServer',
                           'test_exec_command_debug_ssh_console'])
        msg = 'Caller: %s. Timeout trying to ssh to server %s' % (
            caller, self.server)
        self.assertIn(msg, self.log.output)
        msg = 'Could not get console_log for server %s' % self.server['id']
        self.assertIn(msg, self.log.output)
