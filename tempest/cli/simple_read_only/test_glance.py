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

from tempest import cli
from tempest import config
from tempest.openstack.common import log as logging

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlyGlanceClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Glance CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def setUpClass(cls):
        if not CONF.service_available.glance:
            msg = ("%s skipped as Glance is not available" % cls.__name__)
            raise cls.skipException(msg)
        super(SimpleReadOnlyGlanceClientTest, cls).setUpClass()

    def test_glance_fake_action(self):
        self.assertRaises(cli.CommandFailed,
                          self.glance,
                          'this-does-not-exist')

    def test_glance_image_list(self):
        out = self.glance('image-list')
        endpoints = self.parser.listing(out)
        self.assertTableStruct(endpoints, [
            'ID', 'Name', 'Disk Format', 'Container Format',
            'Size', 'Status'])

    def test_glance_member_list(self):
        tenant_name = '--tenant-id %s' % CONF.identity.admin_tenant_name
        out = self.glance('member-list',
                          params=tenant_name)
        endpoints = self.parser.listing(out)
        self.assertTableStruct(endpoints,
                               ['Image ID', 'Member ID', 'Can Share'])

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
                               'member-add', 'member-create', 'member-delete',
                               'member-list'))
        self.assertFalse(wanted_commands - commands)

    # Optional arguments:

    def test_glance_version(self):
        self.glance('', flags='--version')

    def test_glance_debug_list(self):
        self.glance('image-list', flags='--debug')

    def test_glance_timeout(self):
        self.glance('image-list', flags='--timeout %d' % CONF.cli.timeout)
