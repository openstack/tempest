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

import testtools

from tempest import cli
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
import tempest.test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlyNovaClientTest(cli.ClientTestBase):

    """
    This is a first pass at a simple read only python-novaclient test. This
    only exercises client commands that are read only.

    This should test commands:
    * as a regular user
    * as a admin user
    * with and without optional parameters
    * initially just check return codes, and later test command outputs

    """

    @classmethod
    def setUpClass(cls):
        if not CONF.service_available.nova:
            msg = ("%s skipped as Nova is not available" % cls.__name__)
            raise cls.skipException(msg)
        super(SimpleReadOnlyNovaClientTest, cls).setUpClass()

    def test_admin_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.nova,
                          'this-does-nova-exist')

    # NOTE(jogo): Commands in order listed in 'nova help'

    # Positional arguments:

    def test_admin_absolute_limites(self):
        self.nova('absolute-limits')
        self.nova('absolute-limits', params='--reserved')

    def test_admin_aggregate_list(self):
        self.nova('aggregate-list')

    def test_admin_availability_zone_list(self):
        self.assertIn("internal", self.nova('availability-zone-list'))

    def test_admin_cloudpipe_list(self):
        self.nova('cloudpipe-list')

    def test_admin_credentials(self):
        self.nova('credentials')

    @testtools.skipIf(CONF.service_available.neutron,
                      "Neutron does not provide this feature")
    def test_admin_dns_domains(self):
        self.nova('dns-domains')

    @tempest.test.skip_because(bug="1157349")
    def test_admin_dns_list(self):
        self.nova('dns-list')

    def test_admin_endpoints(self):
        self.nova('endpoints')

    def test_admin_flavor_acces_list(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.nova,
                          'flavor-access-list')
        # Failed to get access list for public flavor type
        self.assertRaises(exceptions.CommandFailed,
                          self.nova,
                          'flavor-access-list',
                          params='--flavor m1.tiny')

    def test_admin_flavor_list(self):
        self.assertIn("Memory_MB", self.nova('flavor-list'))

    def test_admin_floating_ip_bulk_list(self):
        self.nova('floating-ip-bulk-list')

    def test_admin_floating_ip_list(self):
        self.nova('floating-ip-list')

    def test_admin_floating_ip_pool_list(self):
        self.nova('floating-ip-pool-list')

    def test_admin_host_list(self):
        self.nova('host-list')

    def test_admin_hypervisor_list(self):
        self.nova('hypervisor-list')

    def test_admin_image_list(self):
        self.nova('image-list')

    @tempest.test.skip_because(bug="1157349")
    def test_admin_interface_list(self):
        self.nova('interface-list')

    def test_admin_keypair_list(self):
        self.nova('keypair-list')

    def test_admin_list(self):
        self.nova('list')
        self.nova('list', params='--all-tenants 1')
        self.nova('list', params='--all-tenants 0')
        self.assertRaises(exceptions.CommandFailed,
                          self.nova,
                          'list',
                          params='--all-tenants bad')

    def test_admin_network_list(self):
        self.nova('network-list')

    def test_admin_rate_limits(self):
        self.nova('rate-limits')

    def test_admin_secgroup_list(self):
        self.nova('secgroup-list')

    @tempest.test.skip_because(bug="1157349")
    def test_admin_secgroup_list_rules(self):
        self.nova('secgroup-list-rules')

    @tempest.cli.min_client_version(client='nova', version='2.18')
    def test_admin_server_group_list(self):
        self.nova('server-group-list')

    def test_admin_servce_list(self):
        self.nova('service-list')

    def test_admin_usage(self):
        self.nova('usage')

    def test_admin_usage_list(self):
        self.nova('usage-list')

    @testtools.skipIf(not CONF.service_available.cinder,
                      "Skipped as Cinder is not available")
    def test_admin_volume_list(self):
        self.nova('volume-list')

    @testtools.skipIf(not CONF.service_available.cinder,
                      "Skipped as Cinder is not available")
    def test_admin_volume_snapshot_list(self):
        self.nova('volume-snapshot-list')

    @testtools.skipIf(not CONF.service_available.cinder,
                      "Skipped as Cinder is not available")
    def test_admin_volume_type_list(self):
        self.nova('volume-type-list')

    def test_admin_help(self):
        self.nova('help')

    def test_admin_list_extensions(self):
        self.nova('list-extensions')

    def test_admin_net_list(self):
        self.nova('net-list')

    def test_agent_list(self):
        self.nova('agent-list')
        self.nova('agent-list', flags='--debug')

    def test_migration_list(self):
        self.nova('migration-list')
        self.nova('migration-list', flags='--debug')

    # Optional arguments:

    def test_admin_version(self):
        self.nova('', flags='--version')

    def test_admin_debug_list(self):
        self.nova('list', flags='--debug')

    def test_admin_timeout(self):
        self.nova('list', flags='--timeout %d' % CONF.cli.timeout)

    def test_admin_timing(self):
        self.nova('list', flags='--timing')
