# Copyright 2012 OpenStack Foundation
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

from __future__ import print_function

import os
import tempfile

from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_log import log as logging

from tempest.lib import exceptions
from tempest.lib.services import clients
from tempest.test_discover import plugins


# TODO(marun) Replace use of oslo_config's global ConfigOpts
# (cfg.CONF) instance with a local instance (cfg.ConfigOpts()) once
# the cli tests move to the clients.  The cli tests rely on oslo
# incubator modules that use the global cfg.CONF.
_CONF = cfg.CONF


def register_opt_group(conf, opt_group, options):
    if opt_group:
        conf.register_group(opt_group)
    for opt in options:
        conf.register_opt(opt, group=getattr(opt_group, 'name', None))


auth_group = cfg.OptGroup(name='auth',
                          title="Options for authentication and credentials")


AuthGroup = [
    cfg.StrOpt('test_accounts_file',
               help="Path to the yaml file that contains the list of "
                    "credentials to use for running tests. If used when "
                    "running in parallel you have to make sure sufficient "
                    "credentials are provided in the accounts file. For "
                    "example if no tests with roles are being run it requires "
                    "at least `2 * CONC` distinct accounts configured in "
                    " the `test_accounts_file`, with CONC == the "
                    "number of concurrent test processes."),
    cfg.BoolOpt('use_dynamic_credentials',
                default=True,
                help="Allows test cases to create/destroy projects and "
                     "users. This option requires that OpenStack Identity "
                     "API admin credentials are known. If false, isolated "
                     "test cases and parallel execution, can still be "
                     "achieved configuring a list of test accounts",
                deprecated_opts=[cfg.DeprecatedOpt('allow_tenant_isolation',
                                                   group='auth'),
                                 cfg.DeprecatedOpt('allow_tenant_isolation',
                                                   group='compute')]),
    cfg.ListOpt('tempest_roles',
                help="Roles to assign to all users created by tempest",
                default=[]),
    cfg.StrOpt('default_credentials_domain_name',
               default='Default',
               help="Default domain used when getting v3 credentials. "
                    "This is the name keystone uses for v2 compatibility.",
               deprecated_opts=[cfg.DeprecatedOpt(
                                'tenant_isolation_domain_name',
                                group='auth')]),
    cfg.BoolOpt('create_isolated_networks',
                default=True,
                help="If use_dynamic_credentials is set to True and Neutron "
                     "is enabled Tempest will try to create a usable network, "
                     "subnet, and router when needed for each project it "
                     "creates. However in some neutron configurations, like "
                     "with VLAN provider networks, this doesn't work. So if "
                     "set to False the isolated networks will not be created"),
    cfg.StrOpt('admin_username',
               help="Username for an administrative user. This is needed for "
                    "authenticating requests made by project isolation to "
                    "create users and projects",
               deprecated_group='identity'),
    cfg.StrOpt('admin_project_name',
               help="Project name to use for an administrative user. This is "
                    "needed for authenticating requests made by project "
                    "isolation to create users and projects",
               deprecated_opts=[cfg.DeprecatedOpt('admin_tenant_name',
                                                  group='auth'),
                                cfg.DeprecatedOpt('admin_tenant_name',
                                                  group='identity')]),
    cfg.StrOpt('admin_password',
               help="Password to use for an administrative user. This is "
                    "needed for authenticating requests made by project "
                    "isolation to create users and projects",
               secret=True,
               deprecated_group='identity'),
    cfg.StrOpt('admin_domain_name',
               help="Admin domain name for authentication (Keystone V3)."
                    "The same domain applies to user and project",
               deprecated_group='identity'),
]

identity_group = cfg.OptGroup(name='identity',
                              title="Keystone Configuration Options")

IdentityGroup = [
    cfg.StrOpt('catalog_type',
               default='identity',
               help="Catalog type of the Identity service."),
    cfg.BoolOpt('disable_ssl_certificate_validation',
                default=False,
                help="Set to True if using self-signed SSL certificates."),
    cfg.StrOpt('ca_certificates_file',
               default=None,
               help='Specify a CA bundle file to use in verifying a '
                    'TLS (https) server certificate.'),
    cfg.StrOpt('uri',
               help="Full URI of the OpenStack Identity API (Keystone), v2"),
    cfg.StrOpt('uri_v3',
               help='Full URI of the OpenStack Identity API (Keystone), v3'),
    cfg.StrOpt('auth_version',
               default='v3',
               help="Identity API version to be used for authentication "
                    "for API tests."),
    cfg.StrOpt('region',
               default='RegionOne',
               help="The identity region name to use. Also used as the other "
                    "services' region name unless they are set explicitly. "
                    "If no such region is found in the service catalog, the "
                    "first found one is used."),
    cfg.StrOpt('v2_admin_endpoint_type',
               default='adminURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The admin endpoint type to use for OpenStack Identity "
                    "(Keystone) API v2"),
    cfg.StrOpt('v2_public_endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The public endpoint type to use for OpenStack Identity "
                    "(Keystone) API v2",
               deprecated_opts=[cfg.DeprecatedOpt('endpoint_type',
                                                  group='identity')]),
    cfg.StrOpt('v3_endpoint_type',
               default='adminURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for OpenStack Identity "
                    "(Keystone) API v3. The default value adminURL is "
                    "deprecated and will be modified to publicURL in "
                    "the next release."),
    cfg.StrOpt('admin_role',
               default='admin',
               help="Role required to administrate keystone."),
    cfg.StrOpt('default_domain_id',
               default='default',
               help="ID of the default domain"),
    cfg.BoolOpt('admin_domain_scope',
                default=False,
                help="Whether keystone identity v3 policy required "
                     "a domain scoped token to use admin APIs"),
    # Security Compliance (PCI-DSS)
    cfg.IntOpt('user_lockout_failure_attempts',
               default=2,
               help="The number of unsuccessful login attempts the user is "
                    "allowed before having the account locked."),
    cfg.IntOpt('user_lockout_duration',
               default=5,
               help="The number of seconds a user account will remain "
                    "locked."),
    cfg.IntOpt('user_unique_last_password_count',
               default=2,
               help="The number of passwords for a user that must be unique "
                    "before an old password can be reused."),
]

service_clients_group = cfg.OptGroup(name='service-clients',
                                     title="Service Clients Options")

ServiceClientsGroup = [
    cfg.IntOpt('http_timeout',
               default=60,
               help='Timeout in seconds to wait for the http request to '
                    'return'),
    cfg.StrOpt('proxy_url',
               help='Specify an http proxy to use.')
]

identity_feature_group = cfg.OptGroup(name='identity-feature-enabled',
                                      title='Enabled Identity Features')

IdentityFeatureGroup = [
    cfg.BoolOpt('trust',
                default=True,
                help='Does the identity service have delegation and '
                     'impersonation enabled'),
    cfg.BoolOpt('api_v2',
                default=False,
                help='Is the v2 identity API enabled',
                deprecated_for_removal=True,
                deprecated_reason='The identity v2.0 API was removed in the '
                                  'Queens release. Tests that exercise the '
                                  'v2.0 API will be removed from tempest in '
                                  'the v22.0.0 release. They are kept only to '
                                  'test stable branches.'),
    cfg.BoolOpt('api_v2_admin',
                default=True,
                help="Is the v2 identity admin API available? This setting "
                     "only applies if api_v2 is set to True."),
    cfg.BoolOpt('api_v3',
                default=True,
                help='Is the v3 identity API enabled'),
    cfg.ListOpt('api_extensions',
                default=['all'],
                help="A list of enabled identity extensions with a special "
                     "entry all which indicates every extension is enabled. "
                     "Empty list indicates all extensions are disabled. "
                     "To get the list of extensions run: "
                     "'openstack extension list --identity'"),
    cfg.BoolOpt('domain_specific_drivers',
                default=False,
                help='Are domain specific drivers enabled? '
                     'This configuration value should be same as '
                     '[identity]->domain_specific_drivers_enabled '
                     'in keystone.conf.'),
    cfg.BoolOpt('security_compliance',
                default=False,
                help='Does the environment have the security compliance '
                     'settings enabled?')
]

compute_group = cfg.OptGroup(name='compute',
                             title='Compute Service Options')

ComputeGroup = [
    cfg.StrOpt('image_ref',
               help="Valid primary image reference to be used in tests. "
                    "This is a required option"),
    cfg.StrOpt('image_ref_alt',
               help="Valid secondary image reference to be used in tests. "
                    "This is a required option, but if only one image is "
                    "available duplicate the value of image_ref above"),
    cfg.StrOpt('flavor_ref',
               default="1",
               help="Valid primary flavor to use in tests."),
    cfg.StrOpt('flavor_ref_alt',
               default="2",
               help='Valid secondary flavor to be used in tests.'),
    cfg.IntOpt('build_interval',
               default=1,
               help="Time in seconds between build status checks."),
    cfg.IntOpt('build_timeout',
               default=300,
               help="Timeout in seconds to wait for an instance to build. "
                    "Other services that do not define build_timeout will "
                    "inherit this value."),
    cfg.IntOpt('ready_wait',
               default=0,
               help="Additional wait time for clean state, when there is "
                    "no OS-EXT-STS extension available"),
    cfg.StrOpt('fixed_network_name',
               help="Name of the fixed network that is visible to all test "
                    "projects. If multiple networks are available for a "
                    "project, this is the network which will be used for "
                    "creating servers if tempest does not create a network or "
                    "a network is not specified elsewhere. It may be used for "
                    "ssh validation only if floating IPs are disabled."),
    cfg.StrOpt('catalog_type',
               default='compute',
               help="Catalog type of the Compute service."),
    cfg.StrOpt('region',
               default='',
               help="The compute region name to use. If empty, the value "
                    "of identity.region is used instead. If no such region "
                    "is found in the service catalog, the first found one is "
                    "used."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the compute service."),
    cfg.StrOpt('volume_device_name',
               default='vdb',
               help="Expected device name when a volume is attached to "
                    "an instance. Not all hypervisors guarantee that they "
                    "will respect the user defined device name, tests may "
                    "fail if inappropriate device name is set."),
    cfg.IntOpt('shelved_offload_time',
               default=0,
               help='Time in seconds before a shelved instance is eligible '
                    'for removing from a host.  -1 never offload, 0 offload '
                    'when shelved. This configuration value should be same as '
                    '[nova.DEFAULT]->shelved_offload_time in nova.conf, and '
                    'some tests will run for as long as the time.'),
    cfg.IntOpt('min_compute_nodes',
               default=1,
               help=('The minimum number of compute nodes expected. This will '
                     'be utilized by some multinode specific tests to ensure '
                     'that requests match the expected size of the cluster '
                     'you are testing with.')),
    cfg.StrOpt('hypervisor_type',
               default=None,
               help="Hypervisor type of the test target on heterogeneous "
                    "compute environment. The value can be 'QEMU', 'xen' or "
                    "something."),
    cfg.StrOpt('min_microversion',
               default=None,
               help="Lower version of the test target microversion range. "
                    "The format is 'X.Y', where 'X' and 'Y' are int values. "
                    "Tempest selects tests based on the range between "
                    "min_microversion and max_microversion. "
                    "If both values are not specified, Tempest avoids tests "
                    "which require a microversion. Valid values are string "
                    "with format 'X.Y' or string 'latest'"),
    cfg.StrOpt('max_microversion',
               default=None,
               help="Upper version of the test target microversion range. "
                    "The format is 'X.Y', where 'X' and 'Y' are int values. "
                    "Tempest selects tests based on the range between "
                    "min_microversion and max_microversion. "
                    "If both values are not specified, Tempest avoids tests "
                    "which require a microversion. Valid values are string "
                    "with format 'X.Y' or string 'latest'"),
]

compute_features_group = cfg.OptGroup(name='compute-feature-enabled',
                                      title="Enabled Compute Service Features")

ComputeFeaturesGroup = [
    cfg.BoolOpt('disk_config',
                default=True,
                help="If false, skip disk config tests"),
    cfg.ListOpt('api_extensions',
                default=['all'],
                help='A list of enabled compute extensions with a special '
                     'entry all which indicates every extension is enabled. '
                     'Each extension should be specified with alias name. '
                     'Empty list indicates all extensions are disabled',
                     deprecated_for_removal=True,
                     deprecated_reason='The Nova extensions API and mechanism '
                                       'is deprecated. This option will be '
                                       'removed when all releases supported '
                                       'by tempest no longer contain the Nova '
                                       'extensions API and mechanism.'),
    cfg.BoolOpt('change_password',
                default=False,
                help="Does the test environment support changing the admin "
                     "password?"),
    cfg.BoolOpt('console_output',
                default=True,
                help="Does the test environment support obtaining instance "
                     "serial console output?"),
    cfg.BoolOpt('resize',
                default=False,
                help="Does the test environment support resizing? When you "
                     "enable this feature, 'flavor_ref_alt' should be set and "
                     "it should refer to a larger flavor than 'flavor_ref' "
                     "one."),
    cfg.BoolOpt('pause',
                default=True,
                help="Does the test environment support pausing?"),
    cfg.BoolOpt('shelve',
                default=True,
                help="Does the test environment support shelving/unshelving?"),
    cfg.BoolOpt('suspend',
                default=True,
                help="Does the test environment support suspend/resume?"),
    cfg.BoolOpt('cold_migration',
                default=True,
                help="Does the test environment support cold migration?"),
    cfg.BoolOpt('live_migration',
                default=True,
                help="Does the test environment support live migration?"),
    cfg.BoolOpt('live_migrate_back_and_forth',
                default=False,
                help="Does the test environment support live migrating "
                     "VM back and forth between different versions of "
                     "nova-compute?"),
    cfg.BoolOpt('metadata_service',
                default=True,
                help="Does the test environment support metadata service? "
                     "Ignored unless validation.run_validation=true."),
    cfg.BoolOpt('block_migration_for_live_migration',
                default=False,
                help="Does the test environment use block devices for live "
                     "migration"),
    cfg.BoolOpt('block_migrate_cinder_iscsi',
                default=False,
                help="Does the test environment support block migration with "
                "Cinder iSCSI volumes. Note: libvirt >= 1.2.17 is required "
                "to support this if using the libvirt compute driver."),
    cfg.BoolOpt('vnc_console',
                default=False,
                help='Enable VNC console. This configuration value should '
                     'be same as [nova.vnc]->vnc_enabled in nova.conf'),
    cfg.BoolOpt('spice_console',
                default=False,
                help='Enable Spice console. This configuration value should '
                     'be same as [nova.spice]->enabled in nova.conf'),
    cfg.BoolOpt('rdp_console',
                default=False,
                help='Enable RDP console. This configuration value should '
                     'be same as [nova.rdp]->enabled in nova.conf'),
    cfg.BoolOpt('serial_console',
                default=False,
                help='Enable serial console. This configuration value '
                     'should be the same as [nova.serial_console]->enabled '
                     'in nova.conf'),
    cfg.BoolOpt('rescue',
                default=True,
                help='Does the test environment support instance rescue '
                     'mode?'),
    cfg.BoolOpt('enable_instance_password',
                default=True,
                help='Enables returning of the instance password by the '
                     'relevant server API calls such as create, rebuild '
                     'or rescue. This configuration value should be same as '
                     'nova.conf: DEFAULT.enable_instance_password'),
    cfg.BoolOpt('interface_attach',
                default=True,
                help='Does the test environment support dynamic network '
                     'interface attachment?'),
    cfg.BoolOpt('snapshot',
                default=True,
                help='Does the test environment support creating snapshot '
                     'images of running instances?'),
    cfg.BoolOpt('nova_cert',
                default=False,
                help='Does the test environment have the nova cert running?',
                deprecated_for_removal=True,
                deprecated_reason="On Nova side, the nova-cert service is "
                                  "deprecated and the service will be removed "
                                  "as early as Ocata."),
    cfg.BoolOpt('personality',
                default=False,
                help='Does the test environment support server personality'),
    cfg.BoolOpt('attach_encrypted_volume',
                default=True,
                help='Does the test environment support attaching an '
                     'encrypted volume to a running server instance? This may '
                     'depend on the combination of compute_driver in nova and '
                     'the volume_driver(s) in cinder.'),
    cfg.BoolOpt('config_drive',
                default=True,
                help='Enable special configuration drive with metadata.'),
    cfg.ListOpt('scheduler_available_filters',
                default=['all'],
                help="A list of enabled filters that nova will accept as hints"
                     " to the scheduler when creating a server. A special "
                     "entry 'all' indicates all filters that are included "
                     "with nova are enabled. Empty list indicates all filters "
                     "are disabled. The full list of available filters is in "
                     "nova.conf: DEFAULT.scheduler_available_filters. If the "
                     "default value is overridden in nova.conf by the test "
                     "environment (which means that a different set of "
                     "filters is enabled than what is included in Nova by "
                     "default) then, this option must be configured to "
                     "contain the same filters that Nova uses in the test "
                     "environment."),
    cfg.BoolOpt('swap_volume',
                default=False,
                help='Does the test environment support in-place swapping of '
                     'volumes attached to a server instance?'),
    cfg.BoolOpt('volume_backed_live_migration',
                default=False,
                help='Does the test environment support volume-backed live '
                     'migration?'),
    cfg.BoolOpt('volume_multiattach',
                default=False,
                help='Does the test environment support attaching a volume to '
                     'more than one instance? This depends on hypervisor and '
                     'volume backend/type and compute API version 2.60.'),
]


image_group = cfg.OptGroup(name='image',
                           title="Image Service Options")

ImageGroup = [
    cfg.StrOpt('catalog_type',
               default='image',
               help='Catalog type of the Image service.'),
    cfg.StrOpt('region',
               default='',
               help="The image region name to use. If empty, the value "
                    "of identity.region is used instead. If no such region "
                    "is found in the service catalog, the first found one is "
                    "used."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the image service."),
    cfg.StrOpt('http_image',
               default='http://download.cirros-cloud.net/0.3.1/'
               'cirros-0.3.1-x86_64-uec.tar.gz',
               help='http accessible image'),
    cfg.IntOpt('build_timeout',
               default=300,
               help="Timeout in seconds to wait for an image to "
                    "become available."),
    cfg.IntOpt('build_interval',
               default=1,
               help="Time in seconds between image operation status "
                    "checks."),
    cfg.ListOpt('container_formats',
                default=['ami', 'ari', 'aki', 'bare', 'ovf', 'ova'],
                help="A list of image's container formats "
                     "users can specify."),
    cfg.ListOpt('disk_formats',
                default=['ami', 'ari', 'aki', 'vhd', 'vmdk', 'raw', 'qcow2',
                         'vdi', 'iso', 'vhdx'],
                help="A list of image's disk formats "
                     "users can specify.")
]

image_feature_group = cfg.OptGroup(name='image-feature-enabled',
                                   title='Enabled image service features')

ImageFeaturesGroup = [
    cfg.BoolOpt('api_v2',
                default=True,
                help="Is the v2 image API enabled",
                deprecated_for_removal=True,
                deprecated_reason='Glance v1 APIs are deprecated and v2 APIs '
                                  'are current one. In future, Tempest will '
                                  'test v2 APIs only so this config option '
                                  'will be removed.'),
    cfg.BoolOpt('api_v1',
                default=True,
                help="Is the v1 image API enabled",
                deprecated_for_removal=True,
                deprecated_reason='Glance v1 APIs are deprecated and v2 APIs '
                                  'are current one. In future, Tempest will '
                                  'test v2 APIs only so this config option '
                                  'will be removed.'),
]

network_group = cfg.OptGroup(name='network',
                             title='Network Service Options')

NetworkGroup = [
    cfg.StrOpt('catalog_type',
               default='network',
               help='Catalog type of the Neutron service.'),
    cfg.StrOpt('region',
               default='',
               help="The network region name to use. If empty, the value "
                    "of identity.region is used instead. If no such region "
                    "is found in the service catalog, the first found one is "
                    "used."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the network service."),
    cfg.StrOpt('project_network_cidr',
               default="10.100.0.0/16",
               help="The cidr block to allocate project ipv4 subnets from"),
    cfg.IntOpt('project_network_mask_bits',
               default=28,
               help="The mask bits for project ipv4 subnets"),
    cfg.StrOpt('project_network_v6_cidr',
               default="2003::/48",
               help="The cidr block to allocate project ipv6 subnets from"),
    cfg.IntOpt('project_network_v6_mask_bits',
               default=64,
               help="The mask bits for project ipv6 subnets"),
    cfg.BoolOpt('project_networks_reachable',
                default=False,
                help="Whether project networks can be reached directly from "
                     "the test client. This must be set to True when the "
                     "'fixed' connect_method is selected."),
    cfg.StrOpt('public_network_id',
               default="",
               help="Id of the public network that provides external "
                    "connectivity"),
    cfg.StrOpt('floating_network_name',
               help="Default floating network name. Used to allocate floating "
                    "IPs when neutron is enabled."),
    cfg.StrOpt('public_router_id',
               default="",
               help="Id of the public router that provides external "
                    "connectivity. This should only be used when Neutron's "
                    "'allow_overlapping_ips' is set to 'False' in "
                    "neutron.conf. usually not needed past 'Grizzly' release"),
    cfg.IntOpt('build_timeout',
               default=300,
               help="Timeout in seconds to wait for network operation to "
                    "complete."),
    cfg.IntOpt('build_interval',
               default=1,
               help="Time in seconds between network operation status "
                    "checks."),
    cfg.ListOpt('dns_servers',
                default=["8.8.8.8", "8.8.4.4"],
                help="List of dns servers which should be used"
                     " for subnet creation"),
    cfg.StrOpt('port_vnic_type',
               choices=[None, 'normal', 'direct', 'macvtap'],
               help="vnic_type to use when Launching instances"
                    " with pre-configured ports."
                    " Supported ports are:"
                    " ['normal','direct','macvtap']"),
    cfg.ListOpt('default_network',
                default=["1.0.0.0/16", "2.0.0.0/16"],
                help="List of ip pools"
                     " for subnetpools creation"),
    cfg.BoolOpt('shared_physical_network',
                default=False,
                help="The environment does not support network separation "
                     "between tenants."),
]

network_feature_group = cfg.OptGroup(name='network-feature-enabled',
                                     title='Enabled network service features')

NetworkFeaturesGroup = [
    cfg.BoolOpt('ipv6',
                default=True,
                help="Allow the execution of IPv6 tests"),
    cfg.ListOpt('api_extensions',
                default=['all'],
                help="A list of enabled network extensions with a special "
                     "entry all which indicates every extension is enabled. "
                     "Empty list indicates all extensions are disabled. "
                     "To get the list of extensions run: 'neutron ext-list'"),
    cfg.BoolOpt('ipv6_subnet_attributes',
                default=False,
                help="Allow the execution of IPv6 subnet tests that use "
                     "the extended IPv6 attributes ipv6_ra_mode "
                     "and ipv6_address_mode"
                ),
    cfg.BoolOpt('port_admin_state_change',
                default=True,
                help="Does the test environment support changing"
                     " port admin state"),
    cfg.BoolOpt('port_security',
                default=False,
                help="Does the test environment support port security?"),
    cfg.BoolOpt('floating_ips',
                default=True,
                help='Does the test environment support floating_ips')
]

validation_group = cfg.OptGroup(name='validation',
                                title='SSH Validation options')

ValidationGroup = [
    cfg.BoolOpt('run_validation',
                default=False,
                help='Enable ssh on created servers and creation of additional'
                     ' validation resources to enable remote access'),
    cfg.BoolOpt('security_group',
                default=True,
                help='Enable/disable security groups.'),
    cfg.BoolOpt('security_group_rules',
                default=True,
                help='Enable/disable security group rules.'),
    cfg.StrOpt('connect_method',
               default='floating',
               choices=['fixed', 'floating'],
               help='Default IP type used for validation: '
                    '-fixed: uses the first IP belonging to the fixed network '
                    '-floating: creates and uses a floating IP'),
    cfg.StrOpt('auth_method',
               default='keypair',
               choices=['keypair'],
               help='Default authentication method to the instance. '
                    'Only ssh via keypair is supported for now. '
                    'Additional methods will be handled in a separate spec.'),
    cfg.IntOpt('ip_version_for_ssh',
               default=4,
               help='Default IP version for ssh connections.'),
    cfg.IntOpt('ping_timeout',
               default=120,
               help='Timeout in seconds to wait for ping to succeed.'),
    cfg.IntOpt('connect_timeout',
               default=60,
               help='Timeout in seconds to wait for the TCP connection to be '
                    'successful.'),
    cfg.IntOpt('ssh_timeout',
               default=300,
               help='Timeout in seconds to wait for the ssh banner.'),
    cfg.StrOpt('image_ssh_user',
               default="root",
               help="User name used to authenticate to an instance."),
    cfg.StrOpt('image_ssh_password',
               default="password",
               help="Password used to authenticate to an instance."),
    cfg.StrOpt('ssh_shell_prologue',
               default="set -eu -o pipefail; PATH=$$PATH:/sbin;",
               help="Shell fragments to use before executing a command "
                    "when sshing to a guest."),
    cfg.IntOpt('ping_size',
               default=56,
               help="The packet size for ping packets originating "
                    "from remote linux hosts"),
    cfg.IntOpt('ping_count',
               default=1,
               help="The number of ping packets originating from remote "
                    "linux hosts"),
    cfg.StrOpt('floating_ip_range',
               default='10.0.0.0/29',
               help='Unallocated floating IP range, which will be used to '
                    'test the floating IP bulk feature for CRUD operation. '
                    'This block must not overlap an existing floating IP '
                    'pool.'),
    cfg.StrOpt('network_for_ssh',
               default='public',
               help="Network used for SSH connections. Ignored if "
                    "connect_method=floating."),
]

volume_group = cfg.OptGroup(name='volume',
                            title='Block Storage Options')

VolumeGroup = [
    cfg.IntOpt('build_interval',
               default=1,
               help='Time in seconds between volume availability checks.'),
    cfg.IntOpt('build_timeout',
               default=300,
               help='Timeout in seconds to wait for a volume to become '
                    'available.'),
    cfg.StrOpt('catalog_type',
               default='volume',
               help="Catalog type of the Volume Service"),
    cfg.StrOpt('region',
               default='',
               help="The volume region name to use. If empty, the value "
                    "of identity.region is used instead. If no such region "
                    "is found in the service catalog, the first found one is "
                    "used."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the volume service."),
    cfg.ListOpt('backend_names',
                default=['BACKEND_1', 'BACKEND_2'],
                help='A list of backend names separated by comma. '
                     'The backend name must be declared in cinder.conf'),
    cfg.StrOpt('storage_protocol',
               default='iSCSI',
               help='Backend protocol to target when creating volume types'),
    cfg.StrOpt('vendor_name',
               default='Open Source',
               help='Backend vendor to target when creating volume types'),
    cfg.StrOpt('disk_format',
               default='raw',
               help='Disk format to use when copying a volume to image'),
    cfg.IntOpt('volume_size',
               default=1,
               help='Default size in GB for volumes created by volumes tests'),
    cfg.ListOpt('manage_volume_ref',
                default=['source-name', 'volume-%s'],
                help="A reference to existing volume for volume manage. "
                     "It contains two elements, the first is ref type "
                     "(like 'source-name', 'source-id', etc), the second is "
                     "volume name template used in storage backend"),
    cfg.ListOpt('manage_snapshot_ref',
                default=['source-name', '_snapshot-%s'],
                help="A reference to existing snapshot for snapshot manage. "
                     "It contains two elements, the first is ref type "
                     "(like 'source-name', 'source-id', etc), the second is "
                     "snapshot name template used in storage backend"),
    cfg.StrOpt('min_microversion',
               default=None,
               help="Lower version of the test target microversion range. "
                    "The format is 'X.Y', where 'X' and 'Y' are int values. "
                    "Tempest selects tests based on the range between "
                    "min_microversion and max_microversion. "
                    "If both values are not specified, Tempest avoids tests "
                    "which require a microversion. Valid values are string "
                    "with format 'X.Y' or string 'latest'",),
    cfg.StrOpt('max_microversion',
               default=None,
               help="Upper version of the test target microversion range. "
                    "The format is 'X.Y', where 'X' and 'Y' are int values. "
                    "Tempest selects tests based on the range between "
                    "min_microversion and max_microversion. "
                    "If both values are not specified, Tempest avoids tests "
                    "which require a microversion. Valid values are string "
                    "with format 'X.Y' or string 'latest'",),
]

volume_feature_group = cfg.OptGroup(name='volume-feature-enabled',
                                    title='Enabled Cinder Features')

VolumeFeaturesGroup = [
    cfg.BoolOpt('multi_backend',
                default=False,
                help="Runs Cinder multi-backend test (requires 2 backends)"),
    cfg.BoolOpt('backup',
                default=True,
                help='Runs Cinder volumes backup test'),
    cfg.BoolOpt('snapshot',
                default=True,
                help='Runs Cinder volume snapshot test'),
    cfg.BoolOpt('clone',
                default=True,
                help='Runs Cinder volume clone test'),
    cfg.BoolOpt('manage_snapshot',
                default=False,
                help='Runs Cinder manage snapshot tests'),
    cfg.BoolOpt('manage_volume',
                default=False,
                help='Runs Cinder manage volume tests'),
    cfg.ListOpt('api_extensions',
                default=['all'],
                help='A list of enabled volume extensions with a special '
                     'entry all which indicates every extension is enabled. '
                     'Empty list indicates all extensions are disabled'),
    cfg.BoolOpt('api_v1',
                default=False,
                help="Is the v1 volume API enabled",
                deprecated_for_removal=True,
                deprecated_reason="The v1 volume API has been deprecated "
                                  "since Juno release, and the API will be "
                                  "removed."),
    cfg.BoolOpt('api_v2',
                default=True,
                help="Is the v2 volume API enabled"),
    cfg.BoolOpt('api_v3',
                default=True,
                help="Is the v3 volume API enabled"),
    cfg.BoolOpt('extend_attached_volume',
                default=False,
                help='Does the cloud support extending the size of a volume '
                     'which is currently attached to a server instance? This '
                     'depends on the 3.42 volume API microversion and the '
                     '2.51 compute API microversion. Also, not all volume or '
                     'compute backends support this operation.')
]


object_storage_group = cfg.OptGroup(name='object-storage',
                                    title='Object Storage Service Options')

ObjectStoreGroup = [
    cfg.StrOpt('catalog_type',
               default='object-store',
               help="Catalog type of the Object-Storage service."),
    cfg.StrOpt('region',
               default='',
               help="The object-storage region name to use. If empty, the "
                    "value of identity.region is used instead. If no such "
                    "region is found in the service catalog, the first found "
                    "one is used."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the object-store service."),
    cfg.IntOpt('container_sync_timeout',
               default=600,
               help="Number of seconds to time on waiting for a container "
                    "to container synchronization complete."),
    cfg.IntOpt('container_sync_interval',
               default=5,
               help="Number of seconds to wait while looping to check the "
                    "status of a container to container synchronization"),
    cfg.StrOpt('operator_role',
               default='Member',
               help="Role to add to users created for swift tests to "
                    "enable creating containers"),
    cfg.StrOpt('reseller_admin_role',
               default='ResellerAdmin',
               help="User role that has reseller admin"),
    cfg.StrOpt('realm_name',
               default='realm1',
               help="Name of sync realm. A sync realm is a set of clusters "
                    "that have agreed to allow container syncing with each "
                    "other. Set the same realm name as Swift's "
                    "container-sync-realms.conf"),
    cfg.StrOpt('cluster_name',
               default='name1',
               help="One name of cluster which is set in the realm whose name "
                    "is set in 'realm_name' item in this file. Set the "
                    "same cluster name as Swift's container-sync-realms.conf"),
]

object_storage_feature_group = cfg.OptGroup(
    name='object-storage-feature-enabled',
    title='Enabled object-storage features')

ObjectStoreFeaturesGroup = [
    cfg.ListOpt('discoverable_apis',
                default=['all'],
                help="A list of the enabled optional discoverable apis. "
                     "A single entry, all, indicates that all of these "
                     "features are expected to be enabled"),
    cfg.BoolOpt('container_sync',
                default=True,
                help="Execute (old style) container-sync tests"),
    cfg.BoolOpt('object_versioning',
                default=True,
                help="Execute object-versioning tests"),
    cfg.BoolOpt('discoverability',
                default=True,
                help="Execute discoverability tests"),
]


scenario_group = cfg.OptGroup(name='scenario', title='Scenario Test Options')

ScenarioGroup = [
    cfg.StrOpt('img_dir',
               default='/opt/stack/new/devstack/files/images/'
               'cirros-0.3.1-x86_64-uec',
               help='Directory containing image files',
               deprecated_for_removal=True),
    cfg.StrOpt('img_file', deprecated_name='qcow2_img_file',
               default='cirros-0.3.1-x86_64-disk.img',
               help='Image file name'),
    cfg.StrOpt('img_disk_format',
               default='qcow2',
               help='Image disk format'),
    cfg.StrOpt('img_container_format',
               default='bare',
               help='Image container format'),
    cfg.DictOpt('img_properties', help='Glance image properties. '
                'Use for custom images which require them'),
    cfg.StrOpt('ami_img_file',
               default='cirros-0.3.1-x86_64-blank.img',
               help='AMI image file name',
               deprecated_for_removal=True),
    cfg.StrOpt('ari_img_file',
               default='cirros-0.3.1-x86_64-initrd',
               help='ARI image file name',
               deprecated_for_removal=True),
    cfg.StrOpt('aki_img_file',
               default='cirros-0.3.1-x86_64-vmlinuz',
               help='AKI image file name',
               deprecated_for_removal=True),
    # TODO(yfried): add support for dhcpcd
    cfg.StrOpt('dhcp_client',
               default='udhcpc',
               choices=["udhcpc", "dhclient", ""],
               help='DHCP client used by images to renew DCHP lease. '
                    'If left empty, update operation will be skipped. '
                    'Supported clients: "udhcpc", "dhclient"')
]


service_available_group = cfg.OptGroup(name="service_available",
                                       title="Available OpenStack Services")

ServiceAvailableGroup = [
    cfg.BoolOpt('cinder',
                default=True,
                help="Whether or not cinder is expected to be available"),
    cfg.BoolOpt('neutron',
                default=False,
                help="Whether or not neutron is expected to be available"),
    cfg.BoolOpt('glance',
                default=True,
                help="Whether or not glance is expected to be available"),
    cfg.BoolOpt('swift',
                default=True,
                help="Whether or not swift is expected to be available"),
    cfg.BoolOpt('nova',
                default=True,
                help="Whether or not nova is expected to be available"),
]

debug_group = cfg.OptGroup(name="debug",
                           title="Debug System")

DebugGroup = [
    cfg.StrOpt('trace_requests',
               default='',
               help="""A regex to determine which requests should be traced.

This is a regex to match the caller for rest client requests to be able to
selectively trace calls out of specific classes and methods. It largely
exists for test development, and is not expected to be used in a real deploy
of tempest. This will be matched against the discovered ClassName:method
in the test environment.

Expected values for this field are:

 * ClassName:test_method_name - traces one test_method
 * ClassName:setUp(Class) - traces specific setup functions
 * ClassName:tearDown(Class) - traces specific teardown functions
 * ClassName:_run_cleanups - traces the cleanup functions

If nothing is specified, this feature is not enabled. To trace everything
specify .* as the regex.
""")
]

DefaultGroup = [
    cfg.BoolOpt('pause_teardown',
                default=False,
                help="""Whether to pause a test in global teardown.

The best use case is investigating used resources of one test.
A test can be run as follows:
 $ ostestr --pdb TEST_ID
or
 $ python -m testtools.run TEST_ID"""),
]

_opts = [
    (auth_group, AuthGroup),
    (compute_group, ComputeGroup),
    (compute_features_group, ComputeFeaturesGroup),
    (identity_group, IdentityGroup),
    (service_clients_group, ServiceClientsGroup),
    (identity_feature_group, IdentityFeatureGroup),
    (image_group, ImageGroup),
    (image_feature_group, ImageFeaturesGroup),
    (network_group, NetworkGroup),
    (network_feature_group, NetworkFeaturesGroup),
    (validation_group, ValidationGroup),
    (volume_group, VolumeGroup),
    (volume_feature_group, VolumeFeaturesGroup),
    (object_storage_group, ObjectStoreGroup),
    (object_storage_feature_group, ObjectStoreFeaturesGroup),
    (scenario_group, ScenarioGroup),
    (service_available_group, ServiceAvailableGroup),
    (debug_group, DebugGroup),
    (None, DefaultGroup)
]


def register_opts():
    ext_plugins = plugins.TempestTestPluginManager()
    # Register in-tree tempest config options
    for g, o in _opts:
        register_opt_group(_CONF, g, o)
    # Call external plugin config option registration
    ext_plugins.register_plugin_opts(_CONF)


def list_opts():
    """Return a list of oslo.config options available.

    The purpose of this is to allow tools like the Oslo sample config file
    generator to discover the options exposed to users.
    """
    ext_plugins = plugins.TempestTestPluginManager()
    # Make a shallow copy of the options list that can be
    # extended by plugins. Send back the group object
    # to allow group help text to be generated.
    opt_list = [(g, o) for g, o in _opts]
    opt_list.extend(ext_plugins.get_plugin_options_list())
    return opt_list


# this should never be called outside of this class
class TempestConfigPrivate(object):
    """Provides OpenStack configuration information."""

    DEFAULT_CONFIG_DIR = os.path.join(os.getcwd(), "etc")

    DEFAULT_CONFIG_FILE = "tempest.conf"

    def __getattr__(self, attr):
        # Handles config options from the default group
        return getattr(_CONF, attr)

    def _set_attrs(self):
        # This methods ensures that config options in Tempest as well as
        # in Tempest plugins can be accessed via:
        #     CONF.<normalised_group_name>.<key_name>
        # where:
        #     normalised_group_name = group_name.replace('-', '_')
        # Attributes are set at __init__ time *only* for known option groups
        self.auth = _CONF.auth
        self.compute = _CONF.compute
        self.compute_feature_enabled = _CONF['compute-feature-enabled']
        self.identity = _CONF.identity
        self.service_clients = _CONF['service-clients']
        self.identity_feature_enabled = _CONF['identity-feature-enabled']
        self.image = _CONF.image
        self.image_feature_enabled = _CONF['image-feature-enabled']
        self.network = _CONF.network
        self.network_feature_enabled = _CONF['network-feature-enabled']
        self.validation = _CONF.validation
        self.volume = _CONF.volume
        self.volume_feature_enabled = _CONF['volume-feature-enabled']
        self.object_storage = _CONF['object-storage']
        self.object_storage_feature_enabled = _CONF[
            'object-storage-feature-enabled']
        self.scenario = _CONF.scenario
        self.service_available = _CONF.service_available
        self.debug = _CONF.debug
        logging.tempest_set_log_file('tempest.log')
        # Setting attributes for plugins
        # NOTE(andreaf) Plugins have no access to the TempestConfigPrivate
        # instance at discovery time, so they have no way of setting these
        # aliases themselves.
        ext_plugins = plugins.TempestTestPluginManager()
        for group, _ in ext_plugins.get_plugin_options_list():
            if isinstance(group, cfg.OptGroup):
                # If we have an OptGroup
                group_name = group.name
                group_dest = group.dest
            else:
                # If we have a group name as a string
                group_name = group
                group_dest = group.replace('-', '_')
            # NOTE(andreaf) We can set the attribute safely here since in
            # case of name conflict we would not have reached this point.
            setattr(self, group_dest, _CONF[group_name])

    def __init__(self, parse_conf=True, config_path=None):
        """Initialize a configuration from a conf directory and conf file."""
        super(TempestConfigPrivate, self).__init__()
        config_files = []
        failsafe_path = "/etc/tempest/" + self.DEFAULT_CONFIG_FILE

        if config_path:
            path = config_path
        else:
            # Environment variables override defaults...
            conf_dir = os.environ.get('TEMPEST_CONFIG_DIR',
                                      self.DEFAULT_CONFIG_DIR)
            conf_file = os.environ.get('TEMPEST_CONFIG',
                                       self.DEFAULT_CONFIG_FILE)

            path = os.path.join(conf_dir, conf_file)

        if not os.path.isfile(path):
            path = failsafe_path

        # only parse the config file if we expect one to exist. This is needed
        # to remove an issue with the config file up to date checker.
        if parse_conf:
            config_files.append(path)
        logging.register_options(_CONF)
        if os.path.isfile(path):
            _CONF([], project='tempest', default_config_files=config_files)
        else:
            _CONF([], project='tempest')

        logging_cfg_path = "%s/logging.conf" % os.path.dirname(path)
        if ((not hasattr(_CONF, 'log_config_append') or
            _CONF.log_config_append is None) and
            os.path.isfile(logging_cfg_path)):
            # if logging conf is in place we need to set log_config_append
            _CONF.log_config_append = logging_cfg_path

        logging.setup(_CONF, 'tempest')
        LOG = logging.getLogger('tempest')
        LOG.info("Using tempest config file %s", path)
        register_opts()
        self._set_attrs()
        if parse_conf:
            _CONF.log_opt_values(LOG, logging.DEBUG)


class TempestConfigProxy(object):
    _config = None
    _path = None

    _extra_log_defaults = [
        ('paramiko.transport', logging.INFO),
        ('requests.packages.urllib3.connectionpool', logging.WARN),
    ]

    def _fix_log_levels(self):
        """Tweak the oslo log defaults."""
        for name, level in self._extra_log_defaults:
            logging.getLogger(name).logger.setLevel(level)

    def __getattr__(self, attr):
        if not self._config:
            self._fix_log_levels()
            lock_dir = os.path.join(tempfile.gettempdir(), 'tempest-lock')
            lockutils.set_defaults(lock_dir)
            self._config = TempestConfigPrivate(config_path=self._path)

            # Pushing tempest internal service client configuration to the
            # service clients register. Doing this in the config module ensures
            # that the configuration is available by the time we register the
            # service clients.
            # NOTE(andreaf) This has to be done at the time the first
            # attribute is accessed, to ensure all plugins have been already
            # loaded, options registered, and _config is set.
            _register_tempest_service_clients()

            # Registering service clients and pushing their configuration to
            # the service clients register. Doing this in the config module
            # ensures that the configuration is available by the time we
            # discover tests from plugins.
            plugins.TempestTestPluginManager()._register_service_clients()

        return getattr(self._config, attr)

    def set_config_path(self, path):
        self._path = path


CONF = TempestConfigProxy()


def service_client_config(service_client_name=None):
    """Return a dict with the parameters to init service clients

    Extracts from CONF the settings specific to the service_client_name and
    api_version, and formats them as dict ready to be passed to the service
    clients __init__:

        * `region` (default to identity)
        * `catalog_type`
        * `endpoint_type`
        * `build_timeout` (object-storage and identity default to compute)
        * `build_interval` (object-storage and identity default to compute)

    The following common settings are always returned, even if
    `service_client_name` is None:

        * `disable_ssl_certificate_validation`
        * `ca_certs`
        * `trace_requests`
        * `http_timeout`
        * `proxy_url`

    The dict returned by this does not fit a few service clients:

        * The endpoint type is not returned for identity client, since it takes
          three different values for v2 admin, v2 public and v3
        * The `ServersClient` from compute accepts an optional
          `enable_instance_password` parameter, which is not returned.
        * The `VolumesClient` for both v1 and v2 volume accept an optional
          `default_volume_size` parameter, which is not returned.
        * The `TokenClient` and `V3TokenClient` have a very different
          interface, only auth_url is needed for them.

    :param service_client_name: str Name of the service. Supported values are
        'compute', 'identity', 'image', 'network', 'object-storage', 'volume'
    :return: dictionary of __init__ parameters for the service clients
    :rtype: dict
    """
    _parameters = {
        'disable_ssl_certificate_validation':
            CONF.identity.disable_ssl_certificate_validation,
        'ca_certs': CONF.identity.ca_certificates_file,
        'trace_requests': CONF.debug.trace_requests,
        'http_timeout': CONF.service_clients.http_timeout,
        'proxy_url': CONF.service_clients.proxy_url,
    }

    if service_client_name is None:
        return _parameters

    # Get the group of options first, by normalising the service_group_name
    # Services with a '-' in the name have an '_' in the option group name
    config_group = service_client_name.replace('-', '_')
    # NOTE(andreaf) Check if the config group exists. This allows for this
    # helper to be used for settings from registered plugins as well
    try:
        options = getattr(CONF, config_group)
    except cfg.NoSuchOptError:
        # Option group not defined
        raise exceptions.UnknownServiceClient(services=service_client_name)
    # Set endpoint_type
    # Identity uses different settings depending on API version, so do not
    # return the endpoint at all.
    if service_client_name != 'identity':
        _parameters['endpoint_type'] = getattr(options, 'endpoint_type')
    # Set build_*
    # Object storage and identity groups do not have conf settings for
    # build_* parameters, and we default to compute in any case
    for setting in ['build_timeout', 'build_interval']:
        if not hasattr(options, setting) or not getattr(options, setting):
            _parameters[setting] = getattr(CONF.compute, setting)
        else:
            _parameters[setting] = getattr(options, setting)
    # Set region
    # If a service client does not define region or region is not set
    # default to the identity region
    if not hasattr(options, 'region') or not getattr(options, 'region'):
        _parameters['region'] = CONF.identity.region
    else:
        _parameters['region'] = getattr(options, 'region')
    # Set service
    _parameters['service'] = getattr(options, 'catalog_type')
    return _parameters


def _register_tempest_service_clients():
    # Register tempest own service clients using the same mechanism used
    # for external plugins.
    # The configuration data is pushed to the registry so that automatic
    # configuration of tempest own service clients is possible both for
    # tempest as well as for the plugins.
    service_clients = clients.tempest_modules()
    registry = clients.ClientsRegistry()
    all_clients = []
    for service_client in service_clients:
        module = service_clients[service_client]
        configs = service_client.split('.')[0]
        service_client_data = dict(
            name=service_client.replace('.', '_').replace('-', '_'),
            service_version=service_client,
            module_path=module.__name__,
            client_names=module.__all__,
            **service_client_config(configs)
        )
        all_clients.append(service_client_data)
    # NOTE(andreaf) Internal service clients do not actually belong
    # to a plugin, so using '__tempest__' to indicate a virtual plugin
    # which holds internal service clients.
    registry.register_service_client('__tempest__', all_clients)
