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


class SimpleReadOnlyKeystoneClientTest(tempest.cli.ClientTestBase):
    """Basic, read-only tests for Keystone CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    def test_admin_fake_action(self):
        self.assertRaises(subprocess.CalledProcessError,
                          self.keystone,
                          'this-does-not-exist')

    def test_admin_catalog_list(self):
        out = self.keystone('catalog')
        catalog = self.parser.details_multiple(out, with_label=True)
        for svc in catalog:
            self.assertTrue(svc['__label'].startswith('Service:'))

    def test_admin_endpoint_list(self):
        out = self.keystone('endpoint-list')
        endpoints = self.parser.listing(out)
        self.assertTableStruct(endpoints, [
            'id', 'region', 'publicurl', 'internalurl',
            'adminurl', 'service_id'])

    def test_admin_endpoint_service_match(self):
        endpoints = self.parser.listing(self.keystone('endpoint-list'))
        services = self.parser.listing(self.keystone('service-list'))
        svc_by_id = {}
        for svc in services:
            svc_by_id[svc['id']] = svc
        for endpoint in endpoints:
            self.assertIn(endpoint['service_id'], svc_by_id)

    def test_admin_role_list(self):
        roles = self.parser.listing(self.keystone('role-list'))
        self.assertTableStruct(roles, ['id', 'name'])

    def test_admin_service_list(self):
        services = self.parser.listing(self.keystone('service-list'))
        self.assertTableStruct(services, ['id', 'name', 'type', 'description'])

    def test_admin_tenant_list(self):
        tenants = self.parser.listing(self.keystone('tenant-list'))
        self.assertTableStruct(tenants, ['id', 'name', 'enabled'])

    def test_admin_user_list(self):
        users = self.parser.listing(self.keystone('user-list'))
        self.assertTableStruct(users, [
            'id', 'name', 'enabled', 'email'])

    def test_admin_user_role_list(self):
        user_roles = self.parser.listing(self.keystone('user-role-list'))
        self.assertTableStruct(user_roles, [
            'id', 'name', 'user_id', 'tenant_id'])

    def test_admin_discover(self):
        discovered = self.keystone('discover')
        self.assertIn('Keystone found at http', discovered)
        self.assertIn('supports version', discovered)

    def test_admin_help(self):
        help_text = self.keystone('help')
        lines = help_text.split('\n')
        self.assertTrue(lines[0].startswith('usage: keystone'))

        commands = []
        cmds_start = lines.index('Positional arguments:')
        cmds_end = lines.index('Optional arguments:')
        command_pattern = re.compile('^ {4}([a-z0-9\-\_]+)')
        for line in lines[cmds_start:cmds_end]:
            match = command_pattern.match(line)
            if match:
                commands.append(match.group(1))
        commands = set(commands)
        wanted_commands = set(('catalog', 'endpoint-list', 'help',
                               'token-get', 'discover', 'bootstrap'))
        self.assertFalse(wanted_commands - commands)

    def test_admin_bashcompletion(self):
        self.keystone('bash-completion')
