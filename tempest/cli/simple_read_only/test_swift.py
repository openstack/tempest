# Copyright 2014 OpenStack Foundation
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

import re

from tempest import cli
from tempest import config
from tempest import exceptions

CONF = config.CONF


class SimpleReadOnlySwiftClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Swift CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def setUpClass(cls):
        if not CONF.service_available.swift:
            msg = ("%s skipped as Swift is not available" % cls.__name__)
            raise cls.skipException(msg)
        super(SimpleReadOnlySwiftClientTest, cls).setUpClass()

    def test_swift_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.swift,
                          'this-does-not-exist')

    def test_swift_list(self):
        self.swift('list')

    def test_swift_stat(self):
        output = self.swift('stat')
        entries = ['Account', 'Containers', 'Objects', 'Bytes', 'Content-Type',
                   'X-Timestamp', 'X-Trans-Id']
        for entry in entries:
            self.assertTrue(entry in output)

    def test_swift_capabilities(self):
        output = self.swift('capabilities')
        entries = ['account_listing_limit', 'container_listing_limit',
                   'max_file_size', 'Additional middleware']
        for entry in entries:
            self.assertTrue(entry in output)

    def test_swift_help(self):
        help_text = self.swift('', flags='--help')
        lines = help_text.split('\n')
        self.assertFirstLineStartsWith(lines, 'Usage: swift')

        commands = []
        cmds_start = lines.index('Positional arguments:')
        cmds_end = lines.index('Examples:')
        command_pattern = re.compile('^ {4}([a-z0-9\-\_]+)')
        for line in lines[cmds_start:cmds_end]:
            match = command_pattern.match(line)
            if match:
                commands.append(match.group(1))
        commands = set(commands)
        wanted_commands = set(('stat', 'list', 'delete',
                               'download', 'post', 'upload'))
        self.assertFalse(wanted_commands - commands)

    # Optional arguments:

    def test_swift_version(self):
        self.swift('', flags='--version')

    def test_swift_debug_list(self):
        self.swift('list', flags='--debug')

    def test_swift_retries_list(self):
        self.swift('list', flags='--retries 3')

    def test_swift_region_list(self):
        region = CONF.object_storage.region
        if not region:
            region = CONF.identity.region
        self.swift('list', flags='--os-region-name ' + region)
