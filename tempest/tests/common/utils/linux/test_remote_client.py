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

import time

import fixtures
from oslo_config import cfg

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
        self.ssh_mock = self.useFixture(fixtures.MockPatchObject(self.conn,
                                                                 'ssh_client'))

    def test_write_to_console_regular_str(self):
        self.conn.write_to_console('test')
        self._assert_exec_called_with(
            'sudo sh -c "echo \\"test\\" >/dev/console"')

    def _test_write_to_console_helper(self, message, expected_call):
        self.conn.write_to_console(message)
        self._assert_exec_called_with(expected_call)

    def test_write_to_console_special_chars(self):
        self._test_write_to_console_helper(
            r'\`',
            'sudo sh -c "echo \\"\\\\\\`\\" >/dev/console"')
        self.conn.write_to_console('$')
        self._assert_exec_called_with(
            'sudo sh -c "echo \\"\\\\$\\" >/dev/console"')

    # NOTE(maurosr): The tests below end up closer to an output format
    # assurance than a test since it's basically using comand_exec to format
    # the information using gnu/linux tools.

    def _assert_exec_called_with(self, cmd):
        cmd = "set -eu -o pipefail; PATH=$PATH:/sbin:/usr/sbin; " + cmd
        self.ssh_mock.mock.exec_command.assert_called_with(cmd)

    def test_get_disks(self):
        output_lsblk = """\
NAME       MAJ:MIN    RM          SIZE RO TYPE MOUNTPOINT
sda          8:0       0  128035676160  0 disk
sdb          8:16      0 1000204886016  0 disk
sr0         11:0       1    1073741312  0 rom"""
        result = """\
NAME       MAJ:MIN    RM          SIZE RO TYPE MOUNTPOINT
sda          8:0       0  128035676160  0 disk
sdb          8:16      0 1000204886016  0 disk"""

        self.ssh_mock.mock.exec_command.return_value = output_lsblk
        self.assertEqual(self.conn.get_disks(), result)
        self._assert_exec_called_with('lsblk -lb --nodeps')

    def test_list_disks(self):
        output_lsblk = """\
NAME       MAJ:MIN    RM          SIZE RO TYPE MOUNTPOINT
sda          8:0       0  128035676160  0 disk
sdb          8:16      0 1000204886016  0 disk
sr0         11:0       1    1073741312  0 rom"""
        disk_list = ['sda', 'sdb']
        self.ssh_mock.mock.exec_command.return_value = output_lsblk
        self.assertEqual(self.conn.list_disks(), disk_list)

    def test_get_boot_time(self):
        booted_at = 10000
        uptime_sec = 5000.02
        self.ssh_mock.mock.exec_command.return_value = uptime_sec
        self.useFixture(fixtures.MockPatchObject(
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
            name='tempest.lib.common.utils.linux.remote_client',
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
