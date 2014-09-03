# Copyright 2014 NEC Corporation.  All rights reserved.
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

import subprocess

import mock

from tempest.common import commands
from tempest.tests import base


class TestCommands(base.TestCase):

    def setUp(self):
        super(TestCommands, self).setUp()
        self.subprocess_args = {'stdout': subprocess.PIPE,
                                'stderr': subprocess.STDOUT}

    @mock.patch('subprocess.Popen')
    def test_ip_addr_raw(self, mock):
        expected = ['/usr/bin/sudo', '-n', 'ip', 'a']
        commands.ip_addr_raw()
        mock.assert_called_once_with(expected, **self.subprocess_args)

    @mock.patch('subprocess.Popen')
    def test_ip_route_raw(self, mock):
        expected = ['/usr/bin/sudo', '-n', 'ip', 'r']
        commands.ip_route_raw()
        mock.assert_called_once_with(expected, **self.subprocess_args)

    @mock.patch('subprocess.Popen')
    def test_ip_ns_raw(self, mock):
        expected = ['/usr/bin/sudo', '-n', 'ip', 'netns', 'list']
        commands.ip_ns_raw()
        mock.assert_called_once_with(expected, **self.subprocess_args)

    @mock.patch('subprocess.Popen')
    def test_iptables_raw(self, mock):
        table = 'filter'
        expected = ['/usr/bin/sudo', '-n', 'iptables', '--line-numbers',
                    '-L', '-nv', '-t',
                    '%s' % table]
        commands.iptables_raw(table)
        mock.assert_called_once_with(expected, **self.subprocess_args)

    @mock.patch('subprocess.Popen')
    def test_ip_ns_list(self, mock):
        expected = ['/usr/bin/sudo', '-n', 'ip', 'netns', 'list']
        commands.ip_ns_list()
        mock.assert_called_once_with(expected, **self.subprocess_args)

    @mock.patch('subprocess.Popen')
    def test_ip_ns_addr(self, mock):
        ns_list = commands.ip_ns_list()
        for ns in ns_list:
            expected = ['/usr/bin/sudo', '-n', 'ip', 'netns', 'exec', ns,
                        'ip', 'a']
            commands.ip_ns_addr(ns)
            mock.assert_called_once_with(expected, **self.subprocess_args)

    @mock.patch('subprocess.Popen')
    def test_ip_ns_route(self, mock):
        ns_list = commands.ip_ns_list()
        for ns in ns_list:
            expected = ['/usr/bin/sudo', '-n', 'ip', 'netns', 'exec', ns,
                        'ip', 'r']
            commands.ip_ns_route(ns)
            mock.assert_called_once_with(expected, **self.subprocess_args)

    @mock.patch('subprocess.Popen')
    def test_iptables_ns(self, mock):
        table = 'filter'
        ns_list = commands.ip_ns_list()
        for ns in ns_list:
            expected = ['/usr/bin/sudo', '-n', 'ip', 'netns', 'exec', ns,
                        'iptables', '-v', '-S', '-t', table]
            commands.iptables_ns(ns, table)
            mock.assert_called_once_with(expected, **self.subprocess_args)
