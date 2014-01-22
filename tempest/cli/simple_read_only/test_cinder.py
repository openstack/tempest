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

import logging
import re
import subprocess

import tempest.cli

LOG = logging.getLogger(__name__)


class SimpleReadOnlyCinderClientTest(tempest.cli.ClientTestBase):
    """Basic, read-only tests for Cinder CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    def test_cinder_fake_action(self):
        self.assertRaises(subprocess.CalledProcessError,
                          self.cinder,
                          'this-does-not-exist')

    def test_cinder_absolute_limit_list(self):
        roles = self.parser.listing(self.cinder('absolute-limits'))
        self.assertTableStruct(roles, ['Name', 'Value'])

    def test_cinder_backup_list(self):
        self.cinder('backup-list')

    def test_cinder_extra_specs_list(self):
        self.cinder('extra-specs-list')

    def test_cinder_volumes_list(self):
        self.cinder('list')

    def test_cinder_quota_class_show(self):
        """This CLI can accept and string as param."""
        roles = self.parser.listing(self.cinder('quota-class-show',
                                                params='abc'))
        self.assertTableStruct(roles, ['Property', 'Value'])

    def test_cinder_quota_defaults(self):
        """This CLI can accept and string as param."""
        roles = self.parser.listing(self.cinder('quota-defaults',
                                                params=self.identity.
                                                admin_tenant_name))
        self.assertTableStruct(roles, ['Property', 'Value'])

    def test_cinder_quota_show(self):
        """This CLI can accept and string as param."""
        roles = self.parser.listing(self.cinder('quota-show',
                                                params=self.identity.
                                                admin_tenant_name))
        self.assertTableStruct(roles, ['Property', 'Value'])

    def test_cinder_rate_limits(self):
        self.cinder('rate-limits')

    def test_cinder_snapshot_list(self):
        self.cinder('snapshot-list')

    def test_cinder_type_list(self):
        self.cinder('type-list')

    def test_cinder_list_extensions(self):
        self.cinder('list-extensions')
        roles = self.parser.listing(self.cinder('list-extensions'))
        self.assertTableStruct(roles, ['Name', 'Summary', 'Alias', 'Updated'])

    def test_cinder_credentials(self):
        self.cinder('credentials')

    def test_cinder_availability_zone_list(self):
        self.cinder('availability-zone-list')

    def test_cinder_endpoints(self):
        self.cinder('endpoints')

    def test_cinder_service_list(self):
        self.cinder('service-list')

    def test_cinder_transfer_list(self):
        self.cinder('transfer-list')

    def test_cinder_bash_completion(self):
        self.cinder('bash-completion')

    def test_admin_help(self):
        help_text = self.cinder('help')
        lines = help_text.split('\n')
        self.assertFirstLineStartsWith(lines, 'usage: cinder')

        commands = []
        cmds_start = lines.index('Positional arguments:')
        cmds_end = lines.index('Optional arguments:')
        command_pattern = re.compile('^ {4}([a-z0-9\-\_]+)')
        for line in lines[cmds_start:cmds_end]:
            match = command_pattern.match(line)
            if match:
                commands.append(match.group(1))
        commands = set(commands)
        wanted_commands = set(('absolute-limits', 'list', 'help',
                               'quota-show', 'type-list', 'snapshot-list'))
        self.assertFalse(wanted_commands - commands)

     # Optional arguments:

    def test_cinder_version(self):
        self.cinder('', flags='--version')

    def test_cinder_debug_list(self):
        self.cinder('list', flags='--debug')

    def test_cinder_retries_list(self):
        self.cinder('list', flags='--retries 3')

    def test_cinder_region_list(self):
        region = self.config.volume.region
        if not region:
            region = self.config.identity.region
        self.cinder('list', flags='--os-region-name ' + region)
