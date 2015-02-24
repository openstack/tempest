# Copyright 2013 OpenStack Foundation
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

from oslo_log import log as logging
from tempest_lib import exceptions

from tempest import cli
from tempest import config
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlyGlanceClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Glance CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def resource_setup(cls):
        if not CONF.service_available.glance:
            msg = ("%s skipped as Glance is not available" % cls.__name__)
            raise cls.skipException(msg)
        super(SimpleReadOnlyGlanceClientTest, cls).resource_setup()

    def glance(self, *args, **kwargs):
        return self.clients.glance(*args,
                                   endpoint_type=CONF.image.endpoint_type,
                                   **kwargs)

    @test.idempotent_id('c6bd9bf9-717f-4458-8d74-05b682ea7adf')
    def test_glance_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.glance,
                          'this-does-not-exist')

    @test.idempotent_id('72bcdaf3-11cd-48cb-bb8e-62b329acc1ef')
    def test_glance_image_list(self):
        out = self.glance('image-list')
        endpoints = self.parser.listing(out)
        self.assertTableStruct(endpoints, [
            'ID', 'Name', 'Disk Format', 'Container Format',
            'Size', 'Status'])

    @test.idempotent_id('965d294c-8772-4899-ba33-26ee23406135')
    def test_glance_member_list(self):
        tenant_name = '--tenant-id %s' % CONF.identity.admin_tenant_name
        out = self.glance('member-list',
                          params=tenant_name)
        endpoints = self.parser.listing(out)
        self.assertTableStruct(endpoints,
                               ['Image ID', 'Member ID', 'Can Share'])

    @test.idempotent_id('43b80ee5-4297-47f3-ab4c-6f81b9c6edb3')
    def test_glance_help(self):
        help_text = self.glance('help')
        lines = help_text.split('\n')
        self.assertFirstLineStartsWith(lines, 'usage: glance')

        commands = []
        cmds_start = lines.index('Positional arguments:')
        cmds_end = lines.index('Optional arguments:')
        command_pattern = re.compile('^ {4}([a-z0-9\-\_]+)')
        for line in lines[cmds_start:cmds_end]:
            match = command_pattern.match(line)
            if match:
                commands.append(match.group(1))
        commands = set(commands)
        wanted_commands = set(('image-create', 'image-delete', 'help',
                               'image-download', 'image-show', 'image-update',
                               'member-create', 'member-delete',
                               'member-list', 'image-list'))
        self.assertFalse(wanted_commands - commands)

    # Optional arguments:

    @test.idempotent_id('3b2359ea-3719-4b47-81e5-44a042572b11')
    def test_glance_version(self):
        self.glance('', flags='--version')

    @test.idempotent_id('1a52d3bd-3edf-4d67-b3da-999a5d9e0c5e')
    def test_glance_debug_list(self):
        self.glance('image-list', flags='--debug')

    @test.idempotent_id('6f42b076-f9a7-4e2b-a729-579f53e7814e')
    def test_glance_timeout(self):
        self.glance('image-list', flags='--timeout %d' % CONF.cli.timeout)
