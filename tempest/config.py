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

import functools
import logging as std_logging
import os
import tempfile

from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_log import log as logging
import testtools

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
    cfg.BoolOpt('allow_tenant_isolation',
                default=True,
                help="Allows test cases to create/destroy tenants and "
                     "users. This option requires that OpenStack Identity "
                     "API admin credentials are known. If false, isolated "
                     "test cases and parallel execution, can still be "
                     "achieved configuring a list of test accounts",
                deprecated_opts=[cfg.DeprecatedOpt('allow_tenant_isolation',
                                                   group='compute'),
                                 cfg.DeprecatedOpt('allow_tenant_isolation',
                                                   group='orchestration')]),
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
                                                   group='compute'),
                                 cfg.DeprecatedOpt('allow_tenant_isolation',
                                                   group='orchestration')]),
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
               default='v2',
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
                    "(Keystone) API v3"),
    cfg.StrOpt('admin_role',
               default='admin',
               help="Role required to administrate keystone."),
    cfg.StrOpt('default_domain_id',
               default='default',
               help="ID of the default domain"),
    cfg.StrOpt('admin_username',
               help="Administrative Username to use for "
                    "Keystone API requests."),
    cfg.StrOpt('admin_password',
               help="API key to use when authenticating as admin.",
               secret=True),
    cfg.StrOpt('admin_tenant_name',
               help="Administrative Tenant name to use for Keystone API "
                    "requests."),
    cfg.BoolOpt('admin_domain_scope',
                default=False,
                help="Whether keystone identity v3 policy required "
                     "a domain scoped token to use admin APIs")
]

service_clients_group = cfg.OptGroup(name='service-clients',
                                     title="Service Clients Options")

ServiceClientsGroup = [
    cfg.IntOpt('http_timeout',
               default=60,
               help='Timeout in seconds to wait for the http request to '
                    'return'),
]

identity_feature_group = cfg.OptGroup(name='identity-feature-enabled',
                                      title='Enabled Identity Features')

IdentityFeatureGroup = [
    cfg.BoolOpt('trust',
                default=True,
                help='Does the identity service have delegation and '
                     'impersonation enabled'),
    cfg.BoolOpt('api_v2',
                default=True,
                help='Is the v2 identity API enabled'),
    cfg.BoolOpt('api_v3',
                default=True,
                help='Is the v3 identity API enabled'),
    cfg.ListOpt('api_extensions',
                default=['all'],
                help="A list of enabled identity extensions with a special "
                     "entry all which indicates every extension is enabled. "
                     "Empty list indicates all extensions are disabled. "
                     "To get the list of extensions run: 'keystone discover'"),
    # TODO(rodrigods): Remove the reseller flag when Kilo and Liberty is end
    # of life.
    cfg.BoolOpt('reseller',
                default=False,
                help='Does the environment support reseller?')
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
    cfg.StrOpt('ssh_shell_prologue',
               default="set -eu -o pipefail; PATH=$$PATH:/sbin;",
               help="Shell fragments to use before executing a command "
                    "when sshing to a guest."),
    cfg.StrOpt('ssh_auth_method',
               default='keypair',
               help="Auth method used for authenticate to the instance. "
                    "Valid choices are: keypair, configured, adminpass "
                    "and disabled. "
                    "Keypair: start the servers with a ssh keypair. "
                    "Configured: use the configured user and password. "
                    "Adminpass: use the injected adminPass. "
                    "Disabled: avoid using ssh when it is an option."),
    cfg.StrOpt('ssh_connect_method',
               default='floating',
               help="How to connect to the instance? "
                    "fixed: using the first ip belongs the fixed network "
                    "floating: creating and using a floating ip."),
    cfg.StrOpt('ssh_user',
               default='root',
               help="User name used to authenticate to an instance."),
    cfg.StrOpt('image_ssh_user',
               default="root",
               help="User name used to authenticate to an instance."),
    cfg.StrOpt('image_ssh_password',
               default="password",
               help="Password used to authenticate to an instance."),
    cfg.StrOpt('image_alt_ssh_user',
               default="root",
               help="User name used to authenticate to an instance using "
                    "the alternate image."),
    cfg.IntOpt('ping_timeout',
               default=120,
               help="Timeout in seconds to wait for ping to "
                    "succeed."),
    cfg.IntOpt('ping_size',
               default=56,
               help="The packet size for ping packets originating "
                    "from remote linux hosts"),
    cfg.IntOpt('ping_count',
               default=1,
               help="The number of ping packets originating from remote "
                    "linux hosts"),
    cfg.StrOpt('network_for_ssh',
               default='public',
               help="Network used for SSH connections. Ignored if "
                    "use_floatingip_for_ssh=true or run_validation=false."),
    cfg.IntOpt('ready_wait',
               default=0,
               help="Additional wait time for clean state, when there is "
                    "no OS-EXT-STS extension available"),
    cfg.StrOpt('fixed_network_name',
               help="Name of the fixed network that is visible to all test "
                    "projects. If multiple networks are available for a "
                    "project, this is the network which will be used for "
                    "creating servers if tempest does not create a network or "
                    "s network is not specified elsewhere. It may be used for "
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
                    "an instance"),
    cfg.IntOpt('shelved_offload_time',
               default=0,
               help='Time in seconds before a shelved instance is eligible '
                    'for removing from a host.  -1 never offload, 0 offload '
                    'when shelved. This time should be the same as the time '
                    'of nova.conf, and some tests will run for as long as the '
                    'time.'),
    cfg.IntOpt('min_compute_nodes',
               default=1,
               help=('The minimum number of compute nodes expected. This will '
                     'be utilized by some multinode specific tests to ensure '
                     'that requests match the expected size of the cluster '
                     'you are testing with.')),
    cfg.StrOpt('min_microversion',
               default=None,
               help="Lower version of the test target microversion range. "
                    "The format is 'X.Y', where 'X' and 'Y' are int values. "
                    "Tempest selects tests based on the range between "
                    "min_microversion and max_microversion. "
                    "If both values are not specified, Tempest avoids tests "
                    "which require a microversion. Valid values are string "
                    "with format 'X.Y' or string 'latest'",
                    deprecated_group='compute-feature-enabled'),
    cfg.StrOpt('max_microversion',
               default=None,
               help="Upper version of the test target microversion range. "
                    "The format is 'X.Y', where 'X' and 'Y' are int values. "
                    "Tempest selects tests based on the range between "
                    "min_microversion and max_microversion. "
                    "If both values are not specified, Tempest avoids tests "
                    "which require a microversion. Valid values are string "
                    "with format 'X.Y' or string 'latest'",
                    deprecated_group='compute-feature-enabled'),
    cfg.StrOpt('region2_image_ref',
               help="Valid primary image reference to be used in tests "
                    "in Region 2 for multi regions."
                    "This is a required option for multi regions."),
    cfg.StrOpt('region2_image_ref_alt',
               help="Valid secondary image reference to be used in tests "
                    "in Region 2 for multi regions."
                    "This is a required option for mutli regions.  But if "
                    "only one image is available duplicate the value of "
                    "region2_image_ref above")
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
                     'Empty list indicates all extensions are disabled'),
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
                help="Does the test environment support resizing?"),
    cfg.BoolOpt('pause',
                default=True,
                help="Does the test environment support pausing?"),
    cfg.BoolOpt('shelve',
                default=True,
                help="Does the test environment support shelving/unshelving?"),
    cfg.BoolOpt('suspend',
                default=True,
                help="Does the test environment support suspend/resume?"),
    cfg.BoolOpt('live_migration',
                default=True,
                help="Does the test environment support live migration "
                     "available?"),
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
                help="Does the test environment block migration support "
                "cinder iSCSI volumes. Note, libvirt doesn't support this, "
                "see https://bugs.launchpad.net/nova/+bug/1398999"),
    cfg.BoolOpt('live_migrate_paused_instances',
                default=False,
                help="Does the test system allow live-migration of paused "
                "instances? Note, this is more than just the ANDing of "
                "paused and live_migrate, but all 3 should be set to True "
                "to run those tests"),
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
    cfg.BoolOpt('rescue',
                default=True,
                help='Does the test environment support instance rescue '
                     'mode?'),
    cfg.BoolOpt('enable_instance_password',
                default=True,
                help='Enables returning of the instance password by the '
                     'relevant server API calls such as create, rebuild '
                     'or rescue.'),
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
                deprecated_for_removal=True),
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
                     "entry 'all' indicates all filters are enabled. Empty "
                     "list indicates all filters are disabled. The full "
                     "available list of filters is in nova.conf: "
                     "DEFAULT.scheduler_available_filters"),
    cfg.BoolOpt('preserve_ports',
                default=False,
                help='Does Nova preserve preexisting ports from Neutron '
                     'when deleting an instance? This should be set to True '
                     'if testing Kilo+ Nova.'),

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
                         'vdi', 'iso'],
                help="A list of image's disk formats "
                     "users can specify.")
]

image_feature_group = cfg.OptGroup(name='image-feature-enabled',
                                   title='Enabled image service features')

ImageFeaturesGroup = [
    cfg.BoolOpt('api_v2',
                default=True,
                help="Is the v2 image API enabled"),
    cfg.BoolOpt('api_v1',
                default=True,
                help="Is the v1 image API enabled"),
    cfg.BoolOpt('deactivate_image',
                default=False,
                help="Is the deactivate-image feature enabled."
                     " The feature has been integrated since Kilo."),
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
    cfg.StrOpt('tenant_network_cidr',
               default="10.100.0.0/16",
               help="The cidr block to allocate tenant ipv4 subnets from"),
    cfg.IntOpt('tenant_network_mask_bits',
               default=28,
               help="The mask bits for tenant ipv4 subnets"),
    cfg.StrOpt('tenant_network_v6_cidr',
               default="2003::/48",
               help="The cidr block to allocate tenant ipv6 subnets from"),
    cfg.IntOpt('tenant_network_v6_mask_bits',
               default=64,
               help="The mask bits for tenant ipv6 subnets"),
    cfg.BoolOpt('tenant_networks_reachable',
                default=False,
                help="Whether tenant networks can be reached directly from "
                     "the test client. This must be set to True when the "
                     "'fixed' ssh_connect_method is selected."),
    cfg.StrOpt('project_network_cidr',
               deprecated_name='tenant_network_cidr',
               default="10.100.0.0/16",
               help="The cidr block to allocate project ipv4 subnets from"),
    cfg.IntOpt('project_network_mask_bits',
               deprecated_name='tenant_network_mask_bits',
               default=28,
               help="The mask bits for project ipv4 subnets"),
    cfg.StrOpt('project_network_v6_cidr',
               deprecated_name='tenant_network_v6_cidr',
               default="2003::/48",
               help="The cidr block to allocate project ipv6 subnets from"),
    cfg.IntOpt('project_network_v6_mask_bits',
               deprecated_name='tenant_network_v6_mask_bits',
               default=64,
               help="The mask bits for project ipv6 subnets"),
    cfg.BoolOpt('project_networks_reachable',
                deprecated_name='tenant_networks_reachable',
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
    cfg.StrOpt('leaf1',
               help='The name of leaf switch 1'),
    cfg.StrOpt('leaf2',
               help='The name of leaf switch 2'),
    cfg.StrOpt('controller',
               help='Name of the controller'),
    cfg.StrOpt('controller_ip',
               help='IP of the controller'),
    cfg.StrOpt('controller_user',
               default='localadmin',
               help='User login name for the controller'),
    cfg.StrOpt('controller_pw',
               default='ubuntu',
               help='User login password for the controller'),
    cfg.StrOpt('controller_rc_file',
               default='~/devstack/openrc',
               help='File to source for Openstack env variables'),
    cfg.StrOpt('compute1',
               help='Name of compute server 1'),
    cfg.StrOpt('compute2',
               help='Name of compute server 2'),
    cfg.StrOpt('bridge_type',
               choices=['ovs', 'linux'],
               help='Identifies the type of bridge used'),
    cfg.StrOpt('region1_id',
               default=None,
               help='Region 1 ID used in building ASR config elements'),
    cfg.StrOpt('region2_id',
               default=None,
               help='Region 2 ID used in building ASR config elements'),
    cfg.IntOpt('network_interface_mtu',
               default=1500,
               help="MTU for network interface."),
    cfg.ListOpt('default_network',
                default=["1.0.0.0/16", "2.0.0.0/16"],
                help="List of ip pools"
                     " for subnetpools creation"),
    cfg.StrOpt('region2_public_network_id',
               default="",
               help="Id of the public network that provides external "
                    "connectivity in Region 2 in multi regions."),
    cfg.StrOpt('region2_controller',
               help='Name of the controller in Region 2'),
    cfg.StrOpt('region2_controller_ip',
               help='IP of the controller in Region 2'),
    cfg.StrOpt('region2_controller_user',
               default='localadmin',
               help='User login name for the controller in Region 2'),
    cfg.StrOpt('region2_controller_pw',
               default='ubuntu',
               help='User login password for the controller in Region 2'),
    cfg.StrOpt('region2_controller_rc_file',
               default='~/devstack/openrc',
               help='File to source for Openstack env variables in Region 2'),
    cfg.StrOpt('reboot_controller_ip',
               help='IP of the controller to be rebooted'),
    cfg.StrOpt('reboot_controller_user',
               default='localadmin',
               help='User login name for the controller to be rebooted'),
    cfg.StrOpt('reboot_controller_pw',
               default='ubuntu',
               help='User login password for the controller to be rebooted')
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
    cfg.BoolOpt('advertise_mtu',
                default=False,
                help="Allow the execution of MTU tests that use the extended "
                     "Advertise MTU feature API."),
    cfg.BoolOpt('vlan_transparent',
                default=False,
                help="Allow the execution of VLAN Transparency tests that use "
                     "the extended VLAN Transparent API."),
]

messaging_group = cfg.OptGroup(name='messaging',
                               title='Messaging Service')

MessagingGroup = [
    cfg.StrOpt('catalog_type',
               default='messaging',
               help='Catalog type of the Messaging service.'),
    cfg.IntOpt('max_queues_per_page',
               default=20,
               help='The maximum number of queue records per page when '
                    'listing queues'),
    cfg.IntOpt('max_queue_metadata',
               default=65536,
               help='The maximum metadata size for a queue'),
    cfg.IntOpt('max_messages_per_page',
               default=20,
               help='The maximum number of queue message per page when '
                    'listing (or) posting messages'),
    cfg.IntOpt('max_message_size',
               default=262144,
               help='The maximum size of a message body'),
    cfg.IntOpt('max_messages_per_claim',
               default=20,
               help='The maximum number of messages per claim'),
    cfg.IntOpt('max_message_ttl',
               default=1209600,
               help='The maximum ttl for a message'),
    cfg.IntOpt('max_claim_ttl',
               default=43200,
               help='The maximum ttl for a claim'),
    cfg.IntOpt('max_claim_grace',
               default=43200,
               help='The maximum grace period for a claim'),
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
                    '-floating: creates and uses a floating IP',
               deprecated_opts=[cfg.DeprecatedOpt('use_floatingip_for_ssh',
                                                  group='compute')]),
    cfg.StrOpt('auth_method',
               default='keypair',
               choices=['keypair', 'password'],
               help='Default authentication method to the instance. '
                    'Only ssh via keypair is supported for now. '
                    'Additional methods will be handled in a separate spec.',
               deprecated_opts=[cfg.DeprecatedOpt('ssh_auth_method',
                                                  group='compute')]),
    cfg.IntOpt('ip_version_for_ssh',
               default=4,
               help='Default IP version for ssh connections.'),
    cfg.IntOpt('ping_timeout',
               default=120,
               help='Timeout in seconds to wait for ping to succeed.',
               deprecated_opts=[cfg.DeprecatedOpt('ping_timeout',
                                                  group='compute')]),
    cfg.IntOpt('connect_timeout',
               default=60,
               help='Timeout in seconds to wait for the TCP connection to be '
                    'successful.'),
    cfg.IntOpt('ssh_timeout',
               default=300,
               help='Timeout in seconds to wait for the ssh banner.'),
    cfg.StrOpt('image_ssh_user',
               default="root",
               help="User name used to authenticate to an instance.",
               deprecated_opts=[cfg.DeprecatedOpt('image_ssh_user',
                                                  group='compute'),
                                cfg.DeprecatedOpt('ssh_user',
                                                  group='compute'),
                                cfg.DeprecatedOpt('ssh_user',
                                                  group='scenario')]),
    cfg.StrOpt('image_ssh_password',
               default="password",
               help="Password used to authenticate to an instance.",
               deprecated_opts=[cfg.DeprecatedOpt('image_ssh_password',
                                                  group='compute')]),
    cfg.StrOpt('ssh_shell_prologue',
               default="set -eu -o pipefail; PATH=$$PATH:/sbin;",
               help="Shell fragments to use before executing a command "
                    "when sshing to a guest.",
               deprecated_opts=[cfg.DeprecatedOpt('ssh_shell_prologue',
                                                  group='compute')]),
    cfg.IntOpt('ping_size',
               default=56,
               help="The packet size for ping packets originating "
                    "from remote linux hosts",
               deprecated_opts=[cfg.DeprecatedOpt('ping_size',
                                                  group='compute')]),
    cfg.IntOpt('ping_count',
               default=1,
               help="The number of ping packets originating from remote "
                    "linux hosts",
               deprecated_opts=[cfg.DeprecatedOpt('ping_count',
                                                  group='compute')]),
    cfg.StrOpt('floating_ip_range',
               default='10.0.0.0/29',
               help='Unallocated floating IP range, which will be used to '
                    'test the floating IP bulk feature for CRUD operation. '
                    'This block must not overlap an existing floating IP '
                    'pool.',
               deprecated_opts=[cfg.DeprecatedOpt('floating_ip_range',
                                                  group='compute')]),
    cfg.StrOpt('network_for_ssh',
               default='public',
               help="Network used for SSH connections. Ignored if "
                    "connect_method=floating.",
               deprecated_opts=[cfg.DeprecatedOpt('network_for_ssh',
                                                  group='compute')]),
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
    cfg.ListOpt('api_extensions',
                default=['all'],
                help='A list of enabled volume extensions with a special '
                     'entry all which indicates every extension is enabled. '
                     'Empty list indicates all extensions are disabled'),
    cfg.BoolOpt('api_v1',
                default=True,
                help="Is the v1 volume API enabled"),
    cfg.BoolOpt('api_v2',
                default=True,
                help="Is the v2 volume API enabled"),
    cfg.BoolOpt('api_v3',
                default=False,
                help="Is the v3 volume API enabled"),
    cfg.BoolOpt('bootable',
                default=True,
                help='Update bootable status of a volume '
                     'Not implemented on icehouse ',
                deprecated_for_removal=True),
    # TODO(ynesenenko): Remove volume_services once liberty-eol happens.
    cfg.BoolOpt('volume_services',
                default=False,
                help='Extract correct host info from host@backend')
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

orchestration_group = cfg.OptGroup(name='orchestration',
                                   title='Orchestration Service Options')

OrchestrationGroup = [
    cfg.StrOpt('catalog_type',
               default='orchestration',
               help="Catalog type of the Orchestration service."),
    cfg.StrOpt('region',
               default='',
               help="The orchestration region name to use. If empty, the "
                    "value of identity.region is used instead. If no such "
                    "region is found in the service catalog, the first found "
                    "one is used."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the orchestration service."),
    cfg.StrOpt('stack_owner_role', default='heat_stack_owner',
               help='Role required for users to be able to manage stacks'),
    cfg.IntOpt('build_interval',
               default=1,
               help="Time in seconds between build status checks."),
    cfg.IntOpt('build_timeout',
               default=1200,
               help="Timeout in seconds to wait for a stack to build."),
    cfg.StrOpt('instance_type',
               default='m1.micro',
               help="Instance type for tests. Needs to be big enough for a "
                    "full OS plus the test workload"),
    cfg.StrOpt('keypair_name',
               help="Name of existing keypair to launch servers with."),
    cfg.IntOpt('max_template_size',
               default=524288,
               help="Value must match heat configuration of the same name."),
    cfg.IntOpt('max_resources_per_stack',
               default=1000,
               help="Value must match heat configuration of the same name."),
]

data_processing_group = cfg.OptGroup(name="data-processing",
                                     title="Data Processing options")

DataProcessingGroup = [
    cfg.StrOpt('catalog_type',
               default='data-processing',
               deprecated_group="data_processing",
               help="Catalog type of the data processing service."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               deprecated_group="data_processing",
               help="The endpoint type to use for the data processing "
                    "service."),
]


data_processing_feature_group = cfg.OptGroup(
    name="data-processing-feature-enabled",
    title="Enabled Data Processing features")

DataProcessingFeaturesGroup = [
    cfg.ListOpt('plugins',
                default=["vanilla", "cdh"],
                deprecated_group="data_processing-feature-enabled",
                help="List of enabled data processing plugins")
]

boto_group = cfg.OptGroup(name='boto',
                          title='EC2/S3 options')
BotoGroup = [
    cfg.StrOpt('ec2_url',
               default="http://localhost:8773/services/Cloud",
               help="EC2 URL"),
    cfg.StrOpt('s3_url',
               default="http://localhost:8080",
               help="S3 URL"),
    cfg.StrOpt('aws_secret',
               help="AWS Secret Key",
               secret=True),
    cfg.StrOpt('aws_access',
               help="AWS Access Key"),
    cfg.StrOpt('aws_zone',
               default="nova",
               help="AWS Zone for EC2 tests"),
    cfg.StrOpt('s3_materials_path',
               default="/opt/stack/devstack/files/images/"
                       "s3-materials/cirros-0.3.0",
               help="S3 Materials Path"),
    cfg.StrOpt('ari_manifest',
               default="cirros-0.3.0-x86_64-initrd.manifest.xml",
               help="ARI Ramdisk Image manifest"),
    cfg.StrOpt('ami_manifest',
               default="cirros-0.3.0-x86_64-blank.img.manifest.xml",
               help="AMI Machine Image manifest"),
    cfg.StrOpt('aki_manifest',
               default="cirros-0.3.0-x86_64-vmlinuz.manifest.xml",
               help="AKI Kernel Image manifest"),
    cfg.StrOpt('instance_type',
               default="m1.tiny",
               help="Instance type"),
    cfg.IntOpt('http_socket_timeout',
               default=3,
               help="boto Http socket timeout"),
    cfg.IntOpt('num_retries',
               default=1,
               help="boto num_retries on error"),
    cfg.IntOpt('build_timeout',
               default=60,
               help="Status Change Timeout"),
    cfg.IntOpt('build_interval',
               default=1,
               help="Status Change Test Interval"),
]

stress_group = cfg.OptGroup(name='stress', title='Stress Test Options')

StressGroup = [
    cfg.StrOpt('nova_logdir',
               help='Directory containing log files on the compute nodes'),
    cfg.IntOpt('max_instances',
               default=16,
               help='Maximum number of instances to create during test.'),
    cfg.StrOpt('controller',
               help='Controller host.'),
    # new stress options
    cfg.StrOpt('target_controller',
               help='Controller host.'),
    cfg.StrOpt('target_ssh_user',
               help='ssh user.'),
    cfg.StrOpt('target_private_key_path',
               help='Path to private key.'),
    cfg.StrOpt('target_logfiles',
               help='regexp for list of log files.'),
    cfg.IntOpt('log_check_interval',
               default=60,
               help='time (in seconds) between log file error checks.'),
    cfg.IntOpt('default_thread_number_per_action',
               default=4,
               help='The number of threads created while stress test.'),
    cfg.BoolOpt('leave_dirty_stack',
                default=False,
                help='Prevent the cleaning (tearDownClass()) between'
                     ' each stress test run if an exception occurs'
                     ' during this run.'),
    cfg.BoolOpt('full_clean_stack',
                default=False,
                help='Allows a full cleaning process after a stress test.'
                     ' Caution : this cleanup will remove every objects of'
                     ' every project.')
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
    cfg.StrOpt('ssh_user',
               default='cirros',
               help='ssh username for the image file'),
    # TODO(yfried): add support for dhcpcd
    cfg.StrOpt('dhcp_client',
               default='udhcpc',
               choices=["udhcpc", "dhclient", ""],
               help='DHCP client used by images to renew DCHP lease. '
                    'If left empty, update operation will be skipped. '
                    'Supported clients: "udhcpc", "dhclient"'),
    cfg.ListOpt('test_packet_sizes',
                default=['56', '1456'],
                help='A list of ICMP packet sizes used during testing'),
    cfg.IntOpt('test_packet_count',
               default=1,
               help='The number of packets to send for each packet size'),
    cfg.IntOpt('max_instances_per_tenant',
               default=9,
               help='The maximum number of instances for one tenant'),
    cfg.IntOpt('number_vm_flap_interations',
               default=2,
               help='The number of times VMs are deleted/added during test'),
    cfg.BoolOpt('network_node_segments_deleted',
                default=True,
                help='Indicates if VLAN/VxLANs associated with the network '
                     'node are deleted when VMs are deleted'),
    cfg.BoolOpt('advanced_vm_capabilities',
                default=False,
                help='Indicates if the VM has advanced testing features.'),
    cfg.StrOpt('test_bed_id',
               help='A file containing details for a test bed'),
    cfg.BoolOpt('use_host_aggregates',
                default=False,
                help='Indicates if the test will use host aggregates when '
                     'creating servers.'),
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
    cfg.BoolOpt('heat',
                default=False,
                help="Whether or not Heat is expected to be available"),
    cfg.BoolOpt('sahara',
                default=False,
                help="Whether or not Sahara is expected to be available"),
    cfg.BoolOpt('ironic',
                default=False,
                help="Whether or not Ironic is expected to be available"),
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

input_scenario_group = cfg.OptGroup(name="input-scenario",
                                    title="Filters and values for"
                                          " input scenarios[DEPRECATED]")


InputScenarioGroup = [
    cfg.StrOpt('image_regex',
               default='^cirros-0.3.1-x86_64-uec$',
               help="Matching images become parameters for scenario tests",
               deprecated_for_removal=True),
    cfg.StrOpt('flavor_regex',
               default='^m1.nano$',
               help="Matching flavors become parameters for scenario tests",
               deprecated_for_removal=True),
    cfg.StrOpt('non_ssh_image_regex',
               default='^.*[Ww]in.*$',
               help="SSH verification in tests is skipped"
                    "for matching images",
               deprecated_for_removal=True),
    cfg.StrOpt('ssh_user_regex',
               default="[[\"^.*[Cc]irros.*$\", \"cirros\"]]",
               help="List of user mapped to regex "
                    "to matching image names.",
               deprecated_for_removal=True),
]


baremetal_group = cfg.OptGroup(name='baremetal',
                               title='Baremetal provisioning service options',
                               help='When enabling baremetal tests, Nova '
                                    'must be configured to use the Ironic '
                                    'driver. The following parameters for the '
                                    '[compute] section must be disabled: '
                                    'console_output, interface_attach, '
                                    'live_migration, pause, rescue, resize '
                                    'shelve, snapshot, and suspend')


# NOTE(deva): Ironic tests have been ported to tempest.lib. New config options
#             should be added to ironic/ironic_tempest_plugin/config.py.
#             However, these options need to remain here for testing stable
#             branches until Liberty release reaches EOL.
BaremetalGroup = [
    cfg.StrOpt('catalog_type',
               default='baremetal',
               help="Catalog type of the baremetal provisioning service"),
    cfg.BoolOpt('driver_enabled',
                default=False,
                help="Whether the Ironic nova-compute driver is enabled"),
    cfg.StrOpt('driver',
               default='fake',
               help="Driver name which Ironic uses"),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the baremetal provisioning "
                    "service"),
    cfg.IntOpt('active_timeout',
               default=300,
               help="Timeout for Ironic node to completely provision"),
    cfg.IntOpt('association_timeout',
               default=30,
               help="Timeout for association of Nova instance and Ironic "
                    "node"),
    cfg.IntOpt('power_timeout',
               default=60,
               help="Timeout for Ironic power transitions."),
    cfg.IntOpt('unprovision_timeout',
               default=300,
               help="Timeout for unprovisioning an Ironic node. "
                    "Takes longer since Kilo as Ironic performs an extra "
                    "step in Node cleaning."),
    cfg.StrOpt('node_ssh_user',
               default="root",
               help="User name used to authenticate to bare metal node."),
    cfg.StrOpt('node_ssh_password',
               default="cisco123",
               help="Password used to authenticate to bare metal node."),
    cfg.StrOpt('node_ssh_console_ip',
               default="10.30.118.6",
               help="IP of the compute bare metal node .")
]

negative_group = cfg.OptGroup(name='negative', title="Negative Test Options")

NegativeGroup = [
    cfg.StrOpt('test_generator',
               default='tempest.common.' +
               'generator.negative_generator.NegativeTestGenerator',
               help="Test generator class for all negative tests"),
]

cisco_group = cfg.OptGroup(name='cisco', title="Cisco specific Options")

CiscoGroup = [
    cfg.StrOpt('user_name',
               default="admin",
               help="User name for Cisco gear"),
    cfg.StrOpt('user_pw',
               default="cisco123",
               help="Password for Cisco gear"),
    cfg.StrOpt('asr1',
               help="The name of the first ASR in the testbed"),
    cfg.StrOpt('asr1_ip',
               help="The IP Address of the first ASR in the testbed"),
    cfg.StrOpt('asr1_ts_ip',
               help="IP address of the Terminal Server for the first ASR"),
    cfg.StrOpt('asr1_ts_port',
               help="The Terminal Server port number for the first ASR"),
    cfg.StrOpt('asr1_ts_pw',
               help="The Terminal Server password for the first ASR"),
    cfg.StrOpt('asr2',
               help="The name of the second ASR in the testbed"),
    cfg.StrOpt('asr2_ip',
               help="The IP Address of the second ASR in the testbed"),
    cfg.StrOpt('asr2_ts_ip',
               help="IP address of the Terminal Server for the second ASR"),
    cfg.StrOpt('asr2_ts_port',
               help="The Terminal Server port number for the second ASR"),
    cfg.StrOpt('asr2_ts_pw',
               help="The Terminal Server password for the second ASR"),
    cfg.StrOpt('asr1_internal_intf',
               default='TenGigabitEthernet0/1/0',
               help="The internal interface for the first ASR"),
    cfg.StrOpt('asr1_external_intf',
               default='TenGigabitEthernet0/1/0',
               help="The external interface for the first ASR"),
    cfg.StrOpt('asr2_internal_intf',
               default='TenGigabitEthernet0/1/0',
               help="The internal interface for the second ASR"),
    cfg.StrOpt('asr2_external_intf',
               default='TenGigabitEthernet0/1/0',
               help="The external interface for the second ASR"),
    cfg.StrOpt('leaf1',
               help="The name of the leaf1 switch in the testbed"),
    cfg.StrOpt('leaf1_ip',
               help="The IP Address of the leaf1 switch in the testbed"),
    cfg.StrOpt('leaf2',
               help="The name of the leaf2 switch in the testbed"),
    cfg.StrOpt('leaf2_ip',
               help="The IP Address of the leaf2 switch in the testbed"),
]


DefaultGroup = [
    cfg.StrOpt('resources_prefix',
               default='tempest',
               help="Prefix to be added when generating the name for "
                    "test resources. It can be used to discover all "
                    "resources associated with a specific test run when "
                    "running tempest on a real-life cloud"),
]

ucsm_group = cfg.OptGroup(name='ucsm',
                          title="Options for UCSM tests")

UcsmGroup = [
    cfg.StrOpt('ucsm_ip',
               help="UCSM ip"),
    cfg.StrOpt('ucsm_username',
               help="UCSM username"),
    cfg.StrOpt('ucsm_password',
               help="UCSM password"),
    cfg.DictOpt('controller_host_dict',
                help="Controller host VS Service profile dictionary. Ex.: controller:org-root/ls-tmpl, ..."),
    cfg.DictOpt('compute_host_dict',
                help="Compute host VS Service profile "),
    cfg.ListOpt('eth_names',
                default=['eth0', 'eth1'],
                help="Hosts eth names"),
    cfg.IntOpt('virtual_functions_amount',
               help="Amount of virtual functions"),
    cfg.ListOpt('ucsm_list',
                help="List of ucsm IPs. Used in testing multi-ucsm installation"),
    cfg.ListOpt('physnets',
                help="List of physnets. Used in testing vNIC templates"),
    cfg.BoolOpt('test_connectivity', default=True, help='Run connectivity tests'),
    cfg.StrOpt('provider_network_id', help="Provider network"),
    cfg.ListOpt('network_node_list',
                help="hostname of a network node"),
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
    (messaging_group, MessagingGroup),
    (validation_group, ValidationGroup),
    (volume_group, VolumeGroup),
    (volume_feature_group, VolumeFeaturesGroup),
    (object_storage_group, ObjectStoreGroup),
    (object_storage_feature_group, ObjectStoreFeaturesGroup),
    (orchestration_group, OrchestrationGroup),
    (data_processing_group, DataProcessingGroup),
    (data_processing_feature_group, DataProcessingFeaturesGroup),
    (boto_group, BotoGroup),
    (stress_group, StressGroup),
    (scenario_group, ScenarioGroup),
    (service_available_group, ServiceAvailableGroup),
    (debug_group, DebugGroup),
    (baremetal_group, BaremetalGroup),
    (input_scenario_group, InputScenarioGroup),
    (negative_group, NegativeGroup),
    (cisco_group, CiscoGroup),
    (ucsm_group, UcsmGroup),
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
        self.orchestration = _CONF.orchestration
        self.data_processing = _CONF['data-processing']
        self.data_processing_feature_enabled = _CONF[
            'data-processing-feature-enabled']
        self.stress = _CONF.stress
        self.scenario = _CONF.scenario
        self.service_available = _CONF.service_available
        self.debug = _CONF.debug
        self.baremetal = _CONF.baremetal
        self.input_scenario = _CONF['input-scenario']
        self.negative = _CONF.negative
        logging.tempest_set_log_file('tempest.log')

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
        LOG.info("Using tempest config file %s" % path)
        register_opts()
        self._set_attrs()
        if parse_conf:
            _CONF.log_opt_values(LOG, std_logging.DEBUG)


class TempestConfigProxy(object):
    _config = None
    _path = None

    _extra_log_defaults = [
        ('paramiko.transport', std_logging.INFO),
        ('requests.packages.urllib3.connectionpool', std_logging.WARN),
    ]

    def _fix_log_levels(self):
        """Tweak the oslo log defaults."""
        for name, level in self._extra_log_defaults:
            std_logging.getLogger(name).setLevel(level)

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

        return getattr(self._config, attr)

    def set_config_path(self, path):
        self._path = path


CONF = TempestConfigProxy()


def skip_unless_config(*args):
    """Decorator to raise a skip if a config opt doesn't exist or is False

    :param str group: The first arg, the option group to check
    :param str name: The second arg, the option name to check
    :param str msg: Optional third arg, the skip msg to use if a skip is raised
    :raises testtools.TestCaseskipException: If the specified config option
        doesn't exist or it exists and evaluates to False
    """
    def decorator(f):
        group = args[0]
        name = args[1]

        @functools.wraps(f)
        def wrapper(self, *func_args, **func_kwargs):
            if not hasattr(CONF, group):
                msg = "Config group %s doesn't exist" % group
                raise testtools.TestCase.skipException(msg)

            conf_group = getattr(CONF, group)
            if not hasattr(conf_group, name):
                msg = "Config option %s.%s doesn't exist" % (group,
                                                             name)
                raise testtools.TestCase.skipException(msg)

            value = getattr(conf_group, name)
            if not value:
                if len(args) == 3:
                    msg = args[2]
                else:
                    msg = "Config option %s.%s is false" % (group,
                                                            name)
                raise testtools.TestCase.skipException(msg)
            return f(self, *func_args, **func_kwargs)
        return wrapper
    return decorator


def skip_if_config(*args):
    """Raise a skipException if a config exists and is True

    :param str group: The first arg, the option group to check
    :param str name: The second arg, the option name to check
    :param str msg: Optional third arg, the skip msg to use if a skip is raised
    :raises testtools.TestCase.skipException: If the specified config option
        exists and evaluates to True
    """
    def decorator(f):
        group = args[0]
        name = args[1]

        @functools.wraps(f)
        def wrapper(self, *func_args, **func_kwargs):
            if hasattr(CONF, group):
                conf_group = getattr(CONF, group)
                if hasattr(conf_group, name):
                    value = getattr(conf_group, name)
                    if value:
                        if len(args) == 3:
                            msg = args[2]
                        else:
                            msg = "Config option %s.%s is false" % (group,
                                                                    name)
                        raise testtools.TestCase.skipException(msg)
            return f(self, *func_args, **func_kwargs)
        return wrapper
    return decorator


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
        'http_timeout': CONF.service_clients.http_timeout
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
            name=service_client.replace('.', '_'),
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
