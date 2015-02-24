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

from tempest_lib import exceptions
import testtools

from tempest import cli
from tempest import clients
from tempest import config
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class SimpleReadOnlyCinderClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Cinder CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def resource_setup(cls):
        if not CONF.service_available.cinder:
            msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(msg)
        super(SimpleReadOnlyCinderClientTest, cls).resource_setup()
        id_cl = clients.AdminManager().identity_client
        tenant = id_cl.get_tenant_by_name(CONF.identity.admin_tenant_name)
        cls.admin_tenant_id = tenant['id']

    def cinder(self, *args, **kwargs):
        return self.clients.cinder(*args,
                                   endpoint_type=CONF.volume.endpoint_type,
                                   **kwargs)

    @test.idempotent_id('229bc6dc-d804-4668-b753-b590caf63061')
    def test_cinder_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.cinder,
                          'this-does-not-exist')

    @test.idempotent_id('77140216-14db-4fc5-a246-e2a587e9e99b')
    def test_cinder_absolute_limit_list(self):
        roles = self.parser.listing(self.cinder('absolute-limits'))
        self.assertTableStruct(roles, ['Name', 'Value'])

    @test.idempotent_id('2206b9ce-1a36-4a0a-a129-e5afc7cee1dd')
    def test_cinder_backup_list(self):
        backup_list = self.parser.listing(self.cinder('backup-list'))
        self.assertTableStruct(backup_list, ['ID', 'Volume ID', 'Status',
                                             'Name', 'Size', 'Object Count',
                                             'Container'])

    @test.idempotent_id('c7f50346-cd99-4e0b-953f-796ff5f47295')
    def test_cinder_extra_specs_list(self):
        extra_specs_list = self.parser.listing(self.cinder('extra-specs-list'))
        self.assertTableStruct(extra_specs_list, ['ID', 'Name', 'extra_specs'])

    @test.idempotent_id('9de694cb-b40b-442c-a30c-5f9873e144f7')
    def test_cinder_volumes_list(self):
        list = self.parser.listing(self.cinder('list'))
        self.assertTableStruct(list, ['ID', 'Status', 'Name', 'Size',
                                      'Volume Type', 'Bootable',
                                      'Attached to'])
        self.cinder('list', params='--all-tenants 1')
        self.cinder('list', params='--all-tenants 0')
        self.assertRaises(exceptions.CommandFailed,
                          self.cinder,
                          'list',
                          params='--all-tenants bad')

    @test.idempotent_id('56f7c15c-ee82-4f23-bbe8-ce99b66da493')
    def test_cinder_quota_class_show(self):
        """This CLI can accept and string as param."""
        roles = self.parser.listing(self.cinder('quota-class-show',
                                                params='abc'))
        self.assertTableStruct(roles, ['Property', 'Value'])

    @test.idempotent_id('a919a811-b7f0-47a7-b4e5-f3eb674dd200')
    def test_cinder_quota_defaults(self):
        """This CLI can accept and string as param."""
        roles = self.parser.listing(self.cinder('quota-defaults',
                                                params=self.admin_tenant_id))
        self.assertTableStruct(roles, ['Property', 'Value'])

    @test.idempotent_id('18166673-ffa8-4df3-b60c-6375532288bc')
    def test_cinder_quota_show(self):
        """This CLI can accept and string as param."""
        roles = self.parser.listing(self.cinder('quota-show',
                                                params=self.admin_tenant_id))
        self.assertTableStruct(roles, ['Property', 'Value'])

    @test.idempotent_id('b2c66ed9-ca96-4dc4-94cc-8083e664e516')
    def test_cinder_rate_limits(self):
        rate_limits = self.parser.listing(self.cinder('rate-limits'))
        self.assertTableStruct(rate_limits, ['Verb', 'URI', 'Value', 'Remain',
                                             'Unit', 'Next_Available'])

    @test.idempotent_id('7a19955b-807c-481a-a2ee-9d76733eac28')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Volume snapshot not available.')
    def test_cinder_snapshot_list(self):
        snapshot_list = self.parser.listing(self.cinder('snapshot-list'))
        self.assertTableStruct(snapshot_list, ['ID', 'Volume ID', 'Status',
                                               'Name', 'Size'])

    @test.idempotent_id('6e54ecd9-7ba9-490d-8e3b-294b67139e73')
    def test_cinder_type_list(self):
        type_list = self.parser.listing(self.cinder('type-list'))
        self.assertTableStruct(type_list, ['ID', 'Name'])

    @test.idempotent_id('2c363583-24a0-4980-b9cb-b50c0d241e82')
    def test_cinder_list_extensions(self):
        roles = self.parser.listing(self.cinder('list-extensions'))
        self.assertTableStruct(roles, ['Name', 'Summary', 'Alias', 'Updated'])

    @test.idempotent_id('691bd6df-30ad-4be7-927b-a02d62aaa38a')
    def test_cinder_credentials(self):
        credentials = self.parser.listing(self.cinder('credentials'))
        self.assertTableStruct(credentials, ['User Credentials', 'Value'])

    @test.idempotent_id('5c6d71a3-4904-4a3a-aec9-7fd4aa830e95')
    def test_cinder_availability_zone_list(self):
        zone_list = self.parser.listing(self.cinder('availability-zone-list'))
        self.assertTableStruct(zone_list, ['Name', 'Status'])

    @test.idempotent_id('9b0fd5a6-f955-42b9-a42f-6f542a80b9a3')
    def test_cinder_endpoints(self):
        out = self.cinder('endpoints')
        tables = self.parser.tables(out)
        for table in tables:
            headers = table['headers']
            self.assertTrue(2 >= len(headers))
            self.assertEqual('Value', headers[1])

    @test.idempotent_id('301b5ae1-9591-4e9f-999c-d525a9bdf822')
    def test_cinder_service_list(self):
        service_list = self.parser.listing(self.cinder('service-list'))
        self.assertTableStruct(service_list, ['Binary', 'Host', 'Zone',
                                              'Status', 'State', 'Updated_at'])

    @test.idempotent_id('7260ae52-b462-461e-9048-36d0bccf92c6')
    def test_cinder_transfer_list(self):
        transfer_list = self.parser.listing(self.cinder('transfer-list'))
        self.assertTableStruct(transfer_list, ['ID', 'Volume ID', 'Name'])

    @test.idempotent_id('0976dea8-14f3-45a9-8495-3617fc4fbb13')
    def test_cinder_bash_completion(self):
        self.cinder('bash-completion')

    @test.idempotent_id('b7c00361-be80-4512-8735-5f98fc54f2a9')
    def test_cinder_qos_list(self):
        qos_list = self.parser.listing(self.cinder('qos-list'))
        self.assertTableStruct(qos_list, ['ID', 'Name', 'Consumer', 'specs'])

    @test.idempotent_id('2e92dc6e-22b5-4d94-abfc-b543b0c50a89')
    def test_cinder_encryption_type_list(self):
        encrypt_list = self.parser.listing(self.cinder('encryption-type-list'))
        self.assertTableStruct(encrypt_list, ['Volume Type ID', 'Provider',
                                              'Cipher', 'Key Size',
                                              'Control Location'])

    @test.idempotent_id('0ee6cb4c-8de6-4811-a7be-7f4bb75b80cc')
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

    @test.idempotent_id('2fd6f530-183c-4bda-8918-1e59e36c26b9')
    def test_cinder_version(self):
        self.cinder('', flags='--version')

    @test.idempotent_id('306bac51-c443-4426-a6cf-583a953fcd68')
    def test_cinder_debug_list(self):
        self.cinder('list', flags='--debug')

    @test.idempotent_id('6d97fcd2-5dd1-429d-af70-030c949d86cd')
    def test_cinder_retries_list(self):
        self.cinder('list', flags='--retries 3')

    @test.idempotent_id('95a2850c-35b4-4159-bb93-51647a5ad232')
    def test_cinder_region_list(self):
        region = CONF.volume.region
        if not region:
            region = CONF.identity.region
        self.cinder('list', flags='--os-region-name ' + region)
