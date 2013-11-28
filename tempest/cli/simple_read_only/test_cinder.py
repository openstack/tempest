# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


class SimpleReadOnlyCinderClientV2Test(tempest.cli.ClientTestBase):
    """Basic, read-only tests for Cinder v2 CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    version_flag = '--os-volume-api-version'
    version_support = 2

    def _get_resp_from_diff_versions(self, version_tuple, cmd, param=None):
        # Get each result from different versions.
        # Note(wingwj): If you want to get each cli response on v1&v2 version,
        #   the value of version_tuple should be (1, 2).
        #   The function will be also available for v3 in future

        resp_set = []
        for i in set(version_tuple):
            if not isinstance(i, int) or \
                    i not in range(1, self.version_support + 1):
                LOG.error("version_num must be a positive integer, "
                          "Cinder supports %s versions now"
                          % self.version_support)
                continue
            else:
                if not param:
                    item = self.cinder(cmd,
                                       flags=self.version_flag + ' ' + str(i))
                else:
                    item = self.cinder(cmd, params=param,
                                       flags=self.version_flag + ' ' + str(i))
                resp_set.append(item)

        return resp_set

    def _check_accordance_between_two_versions(self, input1, input2,
                                               expected=True):
        # Check input1 and input2 is not Empty first
        self.assertNotEqual("", input1)
        self.assertNotEqual("", input2)
        # Compare input1 and input2 based on 'expected' parameter
        if expected:
            self.assertEqual(input1, input2)
        else:
            self.assertNotEqual(input1, input2)

    def test_cinder_volumes_list_in_v2(self):
        cmd = 'list'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        # This CLI representation in v1/v2 is different.
        self._check_accordance_between_two_versions(v1, v2, False)

    def test_cinder_absolute_limit_list_in_v2(self):
        cmd = 'absolute-limits'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_backup_list_in_v2(self):
        cmd = 'backup-list'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_extra_specs_list_in_v2(self):
        cmd = 'extra-specs-list'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_quota_class_show_in_v2(self):
        cmd = 'quota-class-show'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd, 'abc')
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_quota_defaults_in_v2(self):
        cmd = 'quota-defaults'
        v1, v2 = self._get_resp_from_diff_versions(
            (1, 2), cmd, self.identity.admin_tenant_name)
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_quota_show_in_v2(self):
        cmd = 'quota-show'
        v1, v2 = self._get_resp_from_diff_versions(
            (1, 2), cmd, self.identity.admin_tenant_name)
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_rate_limits_in_v2(self):
        cmd = 'rate-limits'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_snapshot_list_in_v2(self):
        cmd = 'snapshot-list'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        # This CLI representation in v1/v2 is different.
        self._check_accordance_between_two_versions(v1, v2, False)

    def test_cinder_type_list_in_v2(self):
        cmd = 'type-list'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_availability_zone_list_in_v2(self):
        cmd = 'availability-zone-list'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_service_list_in_v2(self):
        cmd = 'service-list'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        self.assertNotEqual("", v1)
        self.assertNotEqual("", v2)

        # The 'Updated_at' and 'State' item may be changed
        #   due to the periodical update-task. Need to omit.
        v1 = self.parser.listing(v1)
        v2 = self.parser.listing(v2)
        for i in v1:
            del i['Updated_at']
            del i['State']
        for j in v2:
            del j['Updated_at']
            del j['State']
        self.assertEqual(v1, v2)

    def test_cinder_transfer_list_in_v2(self):
        cmd = 'transfer-list'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        self._check_accordance_between_two_versions(v1, v2, True)

    def test_cinder_bash_completion_in_v2(self):
        cmd = 'bash-completion'
        v1, v2 = self._get_resp_from_diff_versions((1, 2), cmd)
        # This CLI representation in v1/v2 is different.
        self._check_accordance_between_two_versions(v1, v2, False)
