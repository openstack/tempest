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

from tempest_lib import exceptions

from tempest import cli
from tempest import config
from tempest.openstack.common import log as logging
from tempest import test

CONF = config.CONF


LOG = logging.getLogger(__name__)


class SimpleReadOnlyKeystoneClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Keystone CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    def keystone(self, *args, **kwargs):
        return self.clients.keystone(*args, **kwargs)

    @test.idempotent_id('19c3ae95-3c19-4bba-8ba3-48ad19939b71')
    def test_admin_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.keystone,
                          'this-does-not-exist')

    @test.idempotent_id('a1100917-c7c5-4887-a4da-f7d7f13194f5')
    def test_admin_catalog_list(self):
        out = self.keystone('catalog')
        catalog = self.parser.details_multiple(out, with_label=True)
        for svc in catalog:
            if svc.get('__label'):
                self.assertTrue(svc['__label'].startswith('Service:'),
                                msg=('Invalid beginning of service block: '
                                     '%s' % svc['__label']))
            # check that region and publicURL exists. One might also
            # check for adminURL and internalURL. id seems to be optional
            # and is missing in the catalog backend
            self.assertIn('publicURL', svc.keys())
            self.assertIn('region', svc.keys())

    @test.idempotent_id('35c73506-eab6-4abc-956e-42da90aba8ec')
    def test_admin_endpoint_list(self):
        out = self.keystone('endpoint-list')
        endpoints = self.parser.listing(out)
        self.assertTableStruct(endpoints, [
            'id', 'region', 'publicurl', 'internalurl',
            'adminurl', 'service_id'])

    @test.idempotent_id('f17cb155-bd16-4f32-9956-1b073752fc07')
    def test_admin_endpoint_service_match(self):
        endpoints = self.parser.listing(self.keystone('endpoint-list'))
        services = self.parser.listing(self.keystone('service-list'))
        svc_by_id = {}
        for svc in services:
            svc_by_id[svc['id']] = svc
        for endpoint in endpoints:
            self.assertIn(endpoint['service_id'], svc_by_id)

    @test.idempotent_id('be7176f2-9c34-4d84-bb7d-b4bc85d06a33')
    def test_admin_role_list(self):
        roles = self.parser.listing(self.keystone('role-list'))
        self.assertTableStruct(roles, ['id', 'name'])

    @test.idempotent_id('96a4de8d-aa9e-4ca5-89f0-985809eccd66')
    def test_admin_service_list(self):
        services = self.parser.listing(self.keystone('service-list'))
        self.assertTableStruct(services, ['id', 'name', 'type', 'description'])

    @test.idempotent_id('edb45480-0f7b-49eb-8f95-7562cbba96da')
    def test_admin_tenant_list(self):
        tenants = self.parser.listing(self.keystone('tenant-list'))
        self.assertTableStruct(tenants, ['id', 'name', 'enabled'])

    @test.idempotent_id('25a2753d-6bd1-40c0-addc-32864b00cb2d')
    def test_admin_user_list(self):
        users = self.parser.listing(self.keystone('user-list'))
        self.assertTableStruct(users, [
            'id', 'name', 'enabled', 'email'])

    @test.idempotent_id('f92bf8d4-b27b-47c9-8450-e27c57758de9')
    def test_admin_user_role_list(self):
        user_roles = self.parser.listing(self.keystone('user-role-list'))
        self.assertTableStruct(user_roles, [
            'id', 'name', 'user_id', 'tenant_id'])

    @test.idempotent_id('14a2687b-3ce1-404c-9f78-a0e28e2f8f7b')
    def test_admin_discover(self):
        discovered = self.keystone('discover')
        self.assertIn('Keystone found at http', discovered)
        self.assertIn('supports version', discovered)

    @test.idempotent_id('9a567c8c-3787-4e5f-9c30-bed55f2b75c0')
    def test_admin_help(self):
        help_text = self.keystone('help')
        lines = help_text.split('\n')
        self.assertFirstLineStartsWith(lines, 'usage: keystone')

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

    @test.idempotent_id('a7b9e1fe-db31-4846-82c5-52a7aa9863c3')
    def test_admin_bashcompletion(self):
        self.keystone('bash-completion')

    @test.idempotent_id('5328c681-df8b-4874-a65c-8fa278f0af8f')
    def test_admin_ec2_credentials_list(self):
        creds = self.keystone('ec2-credentials-list')
        creds = self.parser.listing(creds)
        self.assertTableStruct(creds, ['tenant', 'access', 'secret'])

    # Optional arguments:

    @test.idempotent_id('af95e809-ce95-4505-8627-170d803b1d13')
    def test_admin_version(self):
        self.keystone('', flags='--version')

    @test.idempotent_id('9e26521f-7bfa-4d8e-9d61-fd364f0c20c0')
    def test_admin_debug_list(self):
        self.keystone('catalog', flags='--debug')

    @test.idempotent_id('097b3a52-725f-4df7-84b6-277a2b6f6e38')
    def test_admin_timeout(self):
        self.keystone('catalog', flags='--timeout %d' % CONF.cli.timeout)
