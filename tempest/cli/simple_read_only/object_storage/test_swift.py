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

from tempest_lib import exceptions

from tempest import cli
from tempest import config
from tempest import test

CONF = config.CONF


class SimpleReadOnlySwiftClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Swift CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def resource_setup(cls):
        if not CONF.service_available.swift:
            msg = ("%s skipped as Swift is not available" % cls.__name__)
            raise cls.skipException(msg)
        super(SimpleReadOnlySwiftClientTest, cls).resource_setup()

    def swift(self, *args, **kwargs):
        return self.clients.swift(
            *args, endpoint_type=CONF.object_storage.endpoint_type, **kwargs)

    @test.idempotent_id('74360cdc-e7ec-493f-8a87-2b65f4d54aa3')
    def test_swift_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.swift,
                          'this-does-not-exist')

    @test.idempotent_id('809ec373-828e-4279-8df6-9d4db81c7909')
    def test_swift_list(self):
        self.swift('list')

    @test.idempotent_id('325d5fe4-e5ab-4f52-aec4-357533f24fa1')
    def test_swift_stat(self):
        output = self.swift('stat')
        entries = ['Account', 'Containers', 'Objects', 'Bytes', 'Content-Type',
                   'X-Timestamp', 'X-Trans-Id']
        for entry in entries:
            self.assertTrue(entry in output)

    @test.idempotent_id('af1483e1-dafd-4552-a39b-b9d337df808b')
    def test_swift_capabilities(self):
        output = self.swift('capabilities')
        entries = ['account_listing_limit', 'container_listing_limit',
                   'max_file_size', 'Additional middleware']
        for entry in entries:
            self.assertTrue(entry in output)

    @test.idempotent_id('29c83a64-8eb7-418c-a39b-c70cefa5b695')
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

    @test.idempotent_id('2026be82-4e53-4414-a828-f1c894b8cf0f')
    def test_swift_version(self):
        self.swift('', flags='--version')

    @test.idempotent_id('0ae6172e-3df7-42b8-a987-d42609ada6ed')
    def test_swift_debug_list(self):
        self.swift('list', flags='--debug')

    @test.idempotent_id('1bdf5dd0-7df5-446c-a124-2b0703a5d199')
    def test_swift_retries_list(self):
        self.swift('list', flags='--retries 3')

    @test.idempotent_id('64eae749-8fbd-4d85-bc7f-f706d3581c6f')
    def test_swift_region_list(self):
        region = CONF.object_storage.region
        if not region:
            region = CONF.identity.region
        self.swift('list', flags='--os-region-name ' + region)
