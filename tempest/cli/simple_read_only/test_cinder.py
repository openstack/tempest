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
import testtools

import tempest.cli
from tempest import config

CONF = config.CONF
LOG = logging.getLogger(__name__)


class SimpleReadOnlyCinderClientTest(tempest.cli.ClientTestBase):
    """Basic, read-only tests for Cinder CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def setUpClass(cls):
        if not CONF.service_available.cinder:
            msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(msg)
        super(SimpleReadOnlyCinderClientTest, cls).setUpClass()

    def test_cinder_fake_action(self):
        self.assertRaises(subprocess.CalledProcessError,
                          self.cinder,
                          'this-does-not-exist')

    def test_cinder_absolute_limit_list(self):
        roles = self.parser.listing(self.cinder('absolute-limits'))
        self.assertTableStruct(roles, ['Name', 'Value'])

    def test_cinder_backup_list(self):
        backup_list = self.parser.listing(self.cinder('backup-list'))
        self.assertTableStruct(backup_list, ['ID', 'Volume ID', 'Status',
                                             'Name', 'Size', 'Object Count',
                                             'Container'])

    def test_cinder_extra_specs_list(self):
        extra_specs_list = self.parser.listing(self.cinder('extra-specs-list'))
        self.assertTableStruct(extra_specs_list, ['ID', 'Name', 'extra_specs'])

    def test_cinder_volumes_list(self):
        list = self.parser.listing(self.cinder('list'))
        self.assertTableStruct(list, ['ID', 'Status', 'Name', 'Size',
                                      'Volume Type', 'Bootable',
                                      'Attached to'])
        self.cinder('list', params='--all-tenants 1')
        self.cinder('list', params='--all-tenants 0')
        self.assertRaises(subprocess.CalledProcessError,
                          self.cinder,
                          'list',
                          params='--all-tenants bad')

    def test_cinder_quota_class_show(self):
        """This CLI can accept and string as param."""
        roles = self.parser.listing(self.cinder('quota-class-show',
                                                params='abc'))
        self.assertTableStruct(roles, ['Property', 'Value'])

    def test_cinder_quota_defaults(self):
        """This CLI can accept and string as param."""
        roles = self.parser.listing(self.cinder('quota-defaults',
                                                params=CONF.identity.
                                                admin_tenant_name))
        self.assertTableStruct(roles, ['Property', 'Value'])

    def test_cinder_quota_show(self):
        """This CLI can accept and string as param."""
        roles = self.parser.listing(self.cinder('quota-show',
                                                params=CONF.identity.
                                                admin_tenant_name))
        self.assertTableStruct(roles, ['Property', 'Value'])

    def test_cinder_rate_limits(self):
        rate_limits = self.parser.listing(self.cinder('rate-limits'))
        self.assertTableStruct(rate_limits, ['Verb', 'URI', 'Value', 'Remain',
                                             'Unit', 'Next_Available'])

    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Volume snapshot not available.')
    def test_cinder_snapshot_list(self):
        snapshot_list = self.parser.listing(self.cinder('snapshot-list'))
        self.assertTableStruct(snapshot_list, ['ID', 'Volume ID', 'Status',
                                               'Name', 'Size'])

    def test_cinder_type_list(self):
        type_list = self.parser.listing(self.cinder('type-list'))
        self.assertTableStruct(type_list, ['ID', 'Name'])

    def test_cinder_list_extensions(self):
        roles = self.parser.listing(self.cinder('list-extensions'))
        self.assertTableStruct(roles, ['Name', 'Summary', 'Alias', 'Updated'])

    def test_cinder_credentials(self):
        credentials = self.parser.listing(self.cinder('credentials'))
        self.assertTableStruct(credentials, ['User Credentials', 'Value'])

    def test_cinder_availability_zone_list(self):
        zone_list = self.parser.listing(self.cinder('availability-zone-list'))
        self.assertTableStruct(zone_list, ['Name', 'Status'])

    def test_cinder_endpoints(self):
        endpoints = self.parser.listing(self.cinder('endpoints'))
        self.assertTableStruct(endpoints, ['nova', 'Value'])

    def test_cinder_service_list(self):
        service_list = self.parser.listing(self.cinder('service-list'))
        self.assertTableStruct(service_list, ['Binary', 'Host', 'Zone',
                                              'Status', 'State', 'Updated_at',
                                              'Disabled Reason'])

    def test_cinder_transfer_list(self):
        transfer_list = self.parser.listing(self.cinder('transfer-list'))
        self.assertTableStruct(transfer_list, ['ID', 'Volume ID', 'Name'])

    def test_cinder_bash_completion(self):
        self.cinder('bash-completion')

    def test_cinder_qos_list(self):
        qos_list = self.parser.listing(self.cinder('qos-list'))
        self.assertTableStruct(qos_list, ['ID', 'Name', 'Consumer', 'specs'])

    def test_cinder_encryption_type_list(self):
        encrypt_list = self.parser.listing(self.cinder('encryption-type-list'))
        self.assertTableStruct(encrypt_list, ['Volume Type ID', 'Provider',
                                              'Cipher', 'Key Size',
                                              'Control Location'])

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
        region = CONF.volume.region
        if not region:
            region = CONF.identity.region
        self.cinder('list', flags='--os-region-name ' + region)
