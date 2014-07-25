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

import logging as std_logging
import os

from oslo.config import cfg

from tempest.openstack.common import log as logging


def register_opt_group(conf, opt_group, options):
    conf.register_group(opt_group)
    for opt in options:
        conf.register_opt(opt, group=opt_group.name)


identity_group = cfg.OptGroup(name='identity',
                              title="Keystone Configuration Options")

IdentityGroup = [
    cfg.StrOpt('catalog_type',
               default='identity',
               help="Catalog type of the Identity service."),
    cfg.BoolOpt('disable_ssl_certificate_validation',
                default=False,
                help="Set to True if using self-signed SSL certificates."),
    cfg.StrOpt('uri',
               default=None,
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
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the identity service."),
    cfg.StrOpt('username',
               default=None,
               help="Username to use for Nova API requests."),
    cfg.StrOpt('tenant_name',
               default=None,
               help="Tenant name to use for Nova API requests."),
    cfg.StrOpt('admin_role',
               default='admin',
               help="Role required to administrate keystone."),
    cfg.StrOpt('password',
               default=None,
               help="API key to use when authenticating.",
               secret=True),
    cfg.StrOpt('domain_name',
               default=None,
               help="Domain name for authentication (Keystone V3)."
                    "The same domain applies to user and project"),
    cfg.StrOpt('alt_username',
               default=None,
               help="Username of alternate user to use for Nova API "
                    "requests."),
    cfg.StrOpt('alt_tenant_name',
               default=None,
               help="Alternate user's Tenant name to use for Nova API "
                    "requests."),
    cfg.StrOpt('alt_password',
               default=None,
               help="API key to use when authenticating as alternate user.",
               secret=True),
    cfg.StrOpt('alt_domain_name',
               default=None,
               help="Alternate domain name for authentication (Keystone V3)."
                    "The same domain applies to user and project"),
    cfg.StrOpt('admin_username',
               default=None,
               help="Administrative Username to use for "
                    "Keystone API requests."),
    cfg.StrOpt('admin_tenant_name',
               default=None,
               help="Administrative Tenant name to use for Keystone API "
                    "requests."),
    cfg.StrOpt('admin_password',
               default=None,
               help="API key to use when authenticating as admin.",
               secret=True),
    cfg.StrOpt('admin_domain_name',
               default=None,
               help="Admin domain name for authentication (Keystone V3)."
                    "The same domain applies to user and project"),
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
]

compute_group = cfg.OptGroup(name='compute',
                             title='Compute Service Options')

ComputeGroup = [
    cfg.BoolOpt('allow_tenant_isolation',
                default=False,
                help="Allows test cases to create/destroy tenants and "
                     "users. This option enables isolated test cases and "
                     "better parallel execution, but also requires that "
                     "OpenStack Identity API admin credentials are known."),
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
    cfg.StrOpt('default_network_id',
               default="",
               help="Default valid network id to be used in tests for creating an instance."),
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
    cfg.StrOpt('image_alt_ssh_password',
               default="password",
               help="Password used to authenticate to an instance using "
                    "the alternate image."),
    cfg.IntOpt('build_interval',
               default=1,
               help="Time in seconds between build status checks."),
    cfg.IntOpt('build_timeout',
               default=300,
               help="Timeout in seconds to wait for an instance to build."),
    cfg.BoolOpt('run_ssh',
                default=False,
                help="Should the tests ssh to instances?"),
    cfg.StrOpt('ssh_auth_method',
               default='keypair',
               help="Auth method used for authenticate to the instance. "
                    "Valid choices are: keypair, configured, adminpass. "
                    "keypair: start the servers with an ssh keypair. "
                    "configured: use the configured user and password. "
                    "adminpass: use the injected adminPass. "
                    "disabled: avoid using ssh when it is an option."),
    cfg.StrOpt('ssh_connect_method',
               default='fixed',
               help="How to connect to the instance? "
                    "fixed: using the first ip belongs the fixed network "
                    "floating: creating and using a floating ip"),
    cfg.StrOpt('ssh_user',
               default='root',
               help="User name used to authenticate to an instance."),
    cfg.IntOpt('ping_timeout',
               default=120,
               help="Timeout in seconds to wait for ping to "
                    "succeed."),
    cfg.IntOpt('ssh_timeout',
               default=300,
               help="Timeout in seconds to wait for authentication to "
                    "succeed."),
    cfg.IntOpt('ready_wait',
               default=0,
               help="Additional wait time for clean state, when there is "
                    "no OS-EXT-STS extension available"),
    cfg.IntOpt('ssh_channel_timeout',
               default=60,
               help="Timeout in seconds to wait for output from ssh "
                    "channel."),
    cfg.StrOpt('fixed_network_name',
               default='private',
               help="Visible fixed network name "),
    cfg.StrOpt('network_for_ssh',
               default='public',
               help="Network used for SSH connections."),
    cfg.IntOpt('ip_version_for_ssh',
               default=4,
               help="IP version used for SSH connections."),
    cfg.BoolOpt('use_floatingip_for_ssh',
                default=True,
                help="Does SSH use Floating IPs?"),
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
    cfg.StrOpt('catalog_v3_type',
               default='computev3',
               help="Catalog type of the Compute v3 service."),
    cfg.StrOpt('path_to_private_key',
               default=None,
               help="Path to a private key file for SSH access to remote "
                    "hosts"),
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
    cfg.StrOpt('floating_ip_range',
               default='10.0.0.0/29',
               help='Unallocated floating IP range, which will be used to '
                    'test the floating IP bulk feature for CRUD operation.')
]

compute_features_group = cfg.OptGroup(name='compute-feature-enabled',
                                      title="Enabled Compute Service Features")

ComputeFeaturesGroup = [
    cfg.BoolOpt('api_v3',
                default=False,
                help="If false, skip all nova v3 tests."),
    cfg.BoolOpt('disk_config',
                default=True,
                help="If false, skip disk config tests"),
    cfg.ListOpt('api_extensions',
                default=['all'],
                help='A list of enabled compute extensions with a special '
                     'entry all which indicates every extension is enabled. '
                     'Each extension should be specified with alias name'),
    cfg.ListOpt('api_v3_extensions',
                default=['all'],
                help='A list of enabled v3 extensions with a special entry all'
                     ' which indicates every extension is enabled. '
                     'Each extension should be specified with alias name'),
    cfg.BoolOpt('change_password',
                default=False,
                help="Does the test environment support changing the admin "
                     "password?"),
    cfg.BoolOpt('resize',
                default=False,
                help="Does the test environment support resizing?"),
    cfg.BoolOpt('pause',
                default=True,
                help="Does the test environment support pausing?"),
    cfg.BoolOpt('suspend',
                default=True,
                help="Does the test environment support suspend/resume?"),
    cfg.BoolOpt('live_migration',
                default=False,
                help="Does the test environment support live migration "
                     "available?"),
    cfg.BoolOpt('block_migration_for_live_migration',
                default=False,
                help="Does the test environment use block devices for live "
                     "migration"),
    cfg.BoolOpt('block_migrate_cinder_iscsi',
                default=False,
                help="Does the test environment block migration support "
                     "cinder iSCSI volumes"),
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
                     'mode?')
]


compute_admin_group = cfg.OptGroup(name='compute-admin',
                                   title="Compute Admin Options")

ComputeAdminGroup = [
    cfg.StrOpt('username',
               default=None,
               help="Administrative Username to use for Nova API requests."),
    cfg.StrOpt('tenant_name',
               default=None,
               help="Administrative Tenant name to use for Nova API "
                    "requests."),
    cfg.StrOpt('password',
               default=None,
               help="API key to use when authenticating as admin.",
               secret=True),
    cfg.StrOpt('domain_name',
               default=None,
               help="Domain name for authentication as admin (Keystone V3)."
                    "The same domain applies to user and project"),
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
               help='http accessible image')
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
               default="2003::/64",
               help="The cidr block to allocate tenant ipv6 subnets from"),
    cfg.IntOpt('tenant_network_v6_mask_bits',
               default=96,
               help="The mask bits for tenant ipv6 subnets"),
    cfg.BoolOpt('tenant_networks_reachable',
                default=False,
                help="Whether tenant network connectivity should be "
                     "evaluated directly"),
    cfg.StrOpt('public_network_id',
               default="",
               help="Id of the public network that provides external "
                    "connectivity"),
    cfg.StrOpt('public_router_id',
               default="",
               help="Id of the public router that provides external "
                    "connectivity"),
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
                help="List of dns servers whichs hould be used"
                     " for subnet creation")
]

network_feature_group = cfg.OptGroup(name='network-feature-enabled',
                                     title='Enabled network service features')

NetworkFeaturesGroup = [
    cfg.BoolOpt('ipv6',
                default=True,
                help="Allow the execution of IPv6 tests"),
    cfg.ListOpt('api_extensions',
                default=['all'],
                help='A list of enabled network extensions with a special '
                     'entry all which indicates every extension is enabled'),
    cfg.BoolOpt('ipv6_subnet_attributes',
                default=False,
                help="Allow the execution of IPv6 subnet tests that use "
                     "the extended IPv6 attributes ipv6_ra_mode "
                     "and ipv6_address_mode"
                )
]

queuing_group = cfg.OptGroup(name='queuing',
                             title='Queuing Service')

QueuingGroup = [
    cfg.StrOpt('catalog_type',
               default='queuing',
               help='Catalog type of the Queuing service.'),
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

volume_group = cfg.OptGroup(name='volume',
                            title='Block Storage Options')

VolumeGroup = [
    cfg.IntOpt('build_interval',
               default=1,
               help='Time in seconds between volume availability checks.'),
    cfg.IntOpt('build_timeout',
               default=300,
               help='Timeout in seconds to wait for a volume to become'
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
    cfg.StrOpt('backend1_name',
               default='BACKEND_1',
               help="Name of the backend1 (must be declared in cinder.conf)"),
    cfg.StrOpt('backend2_name',
               default='BACKEND_2',
               help="Name of the backend2 (must be declared in cinder.conf)"),
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
    cfg.ListOpt('api_extensions',
                default=['all'],
                help='A list of enabled volume extensions with a special '
                     'entry all which indicates every extension is enabled'),
    cfg.BoolOpt('api_v1',
                default=True,
                help="Is the v1 volume API enabled"),
    cfg.BoolOpt('api_v2',
                default=True,
                help="Is the v2 volume API enabled"),
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
               default=120,
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
]

database_group = cfg.OptGroup(name='database',
                              title='Database Service Options')

DatabaseGroup = [
    cfg.StrOpt('catalog_type',
               default='database',
               help="Catalog type of the Database service."),
    cfg.StrOpt('db_flavor_ref',
               default="1",
               help="Valid primary flavor to use in database tests."),
    cfg.StrOpt('db_current_version',
               default="v1.0",
               help="Current database version to use in database tests."),
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
    cfg.BoolOpt('allow_tenant_isolation',
                default=False,
                help="Allows test cases to create/destroy tenants and "
                     "users. This option enables isolated test cases and "
                     "better parallel execution, but also requires that "
                     "OpenStack Identity API admin credentials are known."),
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
    cfg.StrOpt('image_ref',
               default=None,
               help="Name of heat-cfntools enabled image to use when "
                    "launching test instances."),
    cfg.StrOpt('keypair_name',
               default=None,
               help="Name of existing keypair to launch servers with."),
    cfg.IntOpt('max_template_size',
               default=524288,
               help="Value must match heat configuration of the same name."),
    cfg.IntOpt('max_resources_per_stack',
               default=1000,
               help="Value must match heat configuration of the same name."),
]


telemetry_group = cfg.OptGroup(name='telemetry',
                               title='Telemetry Service Options')

TelemetryGroup = [
    cfg.StrOpt('catalog_type',
               default='metering',
               help="Catalog type of the Telemetry service."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the telemetry service."),
    cfg.BoolOpt('too_slow_to_test',
                default=True,
                help="This variable is used as flag to enable "
                     "notification tests")
]


dashboard_group = cfg.OptGroup(name="dashboard",
                               title="Dashboard options")

DashboardGroup = [
    cfg.StrOpt('dashboard_url',
               default='http://localhost/',
               help="Where the dashboard can be found"),
    cfg.StrOpt('login_url',
               default='http://localhost/auth/login/',
               help="Login page for the dashboard"),
]


data_processing_group = cfg.OptGroup(name="data_processing",
                                     title="Data Processing options")

DataProcessingGroup = [
    cfg.StrOpt('catalog_type',
               default='data_processing',
               help="Catalog type of the data processing service."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the data processing "
                    "service."),
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
               default=None,
               help="AWS Secret Key",
               secret=True),
    cfg.StrOpt('aws_access',
               default=None,
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
               default=None,
               help='Directory containing log files on the compute nodes'),
    cfg.IntOpt('max_instances',
               default=16,
               help='Maximum number of instances to create during test.'),
    cfg.StrOpt('controller',
               default=None,
               help='Controller host.'),
    # new stress options
    cfg.StrOpt('target_controller',
               default=None,
               help='Controller host.'),
    cfg.StrOpt('target_ssh_user',
               default=None,
               help='ssh user.'),
    cfg.StrOpt('target_private_key_path',
               default=None,
               help='Path to private key.'),
    cfg.StrOpt('target_logfiles',
               default=None,
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
                     ' every tenant.')
]


scenario_group = cfg.OptGroup(name='scenario', title='Scenario Test Options')

ScenarioGroup = [
    cfg.StrOpt('img_dir',
               default='/opt/stack/new/devstack/files/images/'
               'cirros-0.3.1-x86_64-uec',
               help='Directory containing image files'),
    cfg.StrOpt('qcow2_img_file',
               default='cirros-0.3.1-x86_64-disk.img',
               help='QCOW2 image file name'),
    cfg.StrOpt('ami_img_file',
               default='cirros-0.3.1-x86_64-blank.img',
               help='AMI image file name'),
    cfg.StrOpt('ari_img_file',
               default='cirros-0.3.1-x86_64-initrd',
               help='ARI image file name'),
    cfg.StrOpt('aki_img_file',
               default='cirros-0.3.1-x86_64-vmlinuz',
               help='AKI image file name'),
    cfg.StrOpt('ssh_user',
               default='cirros',
               help='ssh username for the image file'),
    cfg.IntOpt(
        'large_ops_number',
        default=0,
        help="specifies how many resources to request at once. Used "
        "for large operations testing.")
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
    cfg.BoolOpt('ceilometer',
                default=True,
                help="Whether or not Ceilometer is expected to be available"),
    cfg.BoolOpt('horizon',
                default=True,
                help="Whether or not Horizon is expected to be available"),
    cfg.BoolOpt('sahara',
                default=False,
                help="Whether or not Sahara is expected to be available"),
    cfg.BoolOpt('ironic',
                default=False,
                help="Whether or not Ironic is expected to be available"),
    cfg.BoolOpt('trove',
                default=False,
                help="Whether or not Trove is expected to be available"),
    cfg.BoolOpt('marconi',
                default=False,
                help="Whether or not Marconi is expected to be available"),
]

debug_group = cfg.OptGroup(name="debug",
                           title="Debug System")

DebugGroup = [
    cfg.BoolOpt('enable',
                default=True,
                help="Enable diagnostic commands"),
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
                                          " input scenarios")

InputScenarioGroup = [
    cfg.StrOpt('image_regex',
               default='^cirros-0.3.1-x86_64-uec$',
               help="Matching images become parameters for scenario tests"),
    cfg.StrOpt('flavor_regex',
               default='^m1.nano$',
               help="Matching flavors become parameters for scenario tests"),
    cfg.StrOpt('non_ssh_image_regex',
               default='^.*[Ww]in.*$',
               help="SSH verification in tests is skipped"
                    "for matching images"),
    cfg.StrOpt('ssh_user_regex',
               default="[[\"^.*[Cc]irros.*$\", \"root\"]]",
               help="List of user mapped to regex "
                    "to matching image names."),
]


baremetal_group = cfg.OptGroup(name='baremetal',
                               title='Baremetal provisioning service options')

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
               default=60,
               help="Timeout for unprovisioning an Ironic node.")
]

cli_group = cfg.OptGroup(name='cli', title="cli Configuration Options")

CLIGroup = [
    cfg.BoolOpt('enabled',
                default=True,
                help="enable cli tests"),
    cfg.StrOpt('cli_dir',
               default='/usr/local/bin',
               help="directory where python client binaries are located"),
    cfg.BoolOpt('has_manage',
                default=True,
                help=("Whether the tempest run location has access to the "
                      "*-manage commands. In a pure blackbox environment "
                      "it will not.")),
    cfg.IntOpt('timeout',
               default=15,
               help="Number of seconds to wait on a CLI timeout"),
]

negative_group = cfg.OptGroup(name='negative', title="Negative Test Options")

NegativeGroup = [
    cfg.StrOpt('test_generator',
               default='tempest.common.' +
               'generator.negative_generator.NegativeTestGenerator',
               help="Test generator class for all negative tests"),
]


def register_opts():
    register_opt_group(cfg.CONF, compute_group, ComputeGroup)
    register_opt_group(cfg.CONF, compute_features_group,
                       ComputeFeaturesGroup)
    register_opt_group(cfg.CONF, identity_group, IdentityGroup)
    register_opt_group(cfg.CONF, identity_feature_group,
                       IdentityFeatureGroup)
    register_opt_group(cfg.CONF, image_group, ImageGroup)
    register_opt_group(cfg.CONF, image_feature_group, ImageFeaturesGroup)
    register_opt_group(cfg.CONF, network_group, NetworkGroup)
    register_opt_group(cfg.CONF, network_feature_group,
                       NetworkFeaturesGroup)
    register_opt_group(cfg.CONF, queuing_group, QueuingGroup)
    register_opt_group(cfg.CONF, volume_group, VolumeGroup)
    register_opt_group(cfg.CONF, volume_feature_group,
                       VolumeFeaturesGroup)
    register_opt_group(cfg.CONF, object_storage_group, ObjectStoreGroup)
    register_opt_group(cfg.CONF, object_storage_feature_group,
                       ObjectStoreFeaturesGroup)
    register_opt_group(cfg.CONF, database_group, DatabaseGroup)
    register_opt_group(cfg.CONF, orchestration_group, OrchestrationGroup)
    register_opt_group(cfg.CONF, telemetry_group, TelemetryGroup)
    register_opt_group(cfg.CONF, dashboard_group, DashboardGroup)
    register_opt_group(cfg.CONF, data_processing_group,
                       DataProcessingGroup)
    register_opt_group(cfg.CONF, boto_group, BotoGroup)
    register_opt_group(cfg.CONF, compute_admin_group, ComputeAdminGroup)
    register_opt_group(cfg.CONF, stress_group, StressGroup)
    register_opt_group(cfg.CONF, scenario_group, ScenarioGroup)
    register_opt_group(cfg.CONF, service_available_group,
                       ServiceAvailableGroup)
    register_opt_group(cfg.CONF, debug_group, DebugGroup)
    register_opt_group(cfg.CONF, baremetal_group, BaremetalGroup)
    register_opt_group(cfg.CONF, input_scenario_group, InputScenarioGroup)
    register_opt_group(cfg.CONF, cli_group, CLIGroup)
    register_opt_group(cfg.CONF, negative_group, NegativeGroup)


# this should never be called outside of this class
class TempestConfigPrivate(object):
    """Provides OpenStack configuration information."""

    DEFAULT_CONFIG_DIR = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        "etc")

    DEFAULT_CONFIG_FILE = "tempest.conf"

    def _set_attrs(self):
        self.compute = cfg.CONF.compute
        self.compute_feature_enabled = cfg.CONF['compute-feature-enabled']
        self.identity = cfg.CONF.identity
        self.identity_feature_enabled = cfg.CONF['identity-feature-enabled']
        self.image = cfg.CONF.image
        self.image_feature_enabled = cfg.CONF['image-feature-enabled']
        self.network = cfg.CONF.network
        self.network_feature_enabled = cfg.CONF['network-feature-enabled']
        self.volume = cfg.CONF.volume
        self.volume_feature_enabled = cfg.CONF['volume-feature-enabled']
        self.object_storage = cfg.CONF['object-storage']
        self.object_storage_feature_enabled = cfg.CONF[
            'object-storage-feature-enabled']
        self.database = cfg.CONF.database
        self.orchestration = cfg.CONF.orchestration
        self.queuing = cfg.CONF.queuing
        self.telemetry = cfg.CONF.telemetry
        self.dashboard = cfg.CONF.dashboard
        self.data_processing = cfg.CONF.data_processing
        self.boto = cfg.CONF.boto
        self.compute_admin = cfg.CONF['compute-admin']
        self.stress = cfg.CONF.stress
        self.scenario = cfg.CONF.scenario
        self.service_available = cfg.CONF.service_available
        self.debug = cfg.CONF.debug
        self.baremetal = cfg.CONF.baremetal
        self.input_scenario = cfg.CONF['input-scenario']
        self.cli = cfg.CONF.cli
        self.negative = cfg.CONF.negative
        if not self.compute_admin.username:
            self.compute_admin.username = self.identity.admin_username
            self.compute_admin.password = self.identity.admin_password
            self.compute_admin.tenant_name = self.identity.admin_tenant_name
        cfg.CONF.set_default('domain_name', self.identity.admin_domain_name,
                             group='identity')
        cfg.CONF.set_default('alt_domain_name',
                             self.identity.admin_domain_name,
                             group='identity')
        cfg.CONF.set_default('domain_name', self.identity.admin_domain_name,
                             group='compute-admin')

    def __init__(self, parse_conf=True):
        """Initialize a configuration from a conf directory and conf file."""
        super(TempestConfigPrivate, self).__init__()
        config_files = []
        failsafe_path = "/etc/tempest/" + self.DEFAULT_CONFIG_FILE

        # Environment variables override defaults...
        conf_dir = os.environ.get('TEMPEST_CONFIG_DIR',
                                  self.DEFAULT_CONFIG_DIR)
        conf_file = os.environ.get('TEMPEST_CONFIG', self.DEFAULT_CONFIG_FILE)

        path = os.path.join(conf_dir, conf_file)

        if not os.path.isfile(path):
            path = failsafe_path

        # only parse the config file if we expect one to exist. This is needed
        # to remove an issue with the config file up to date checker.
        if parse_conf:
            config_files.append(path)

        cfg.CONF([], project='tempest', default_config_files=config_files)
        logging.setup('tempest')
        LOG = logging.getLogger('tempest')
        LOG.info("Using tempest config file %s" % path)
        register_opts()
        self._set_attrs()
        if parse_conf:
            cfg.CONF.log_opt_values(LOG, std_logging.DEBUG)


class TempestConfigProxy(object):
    _config = None

    _extra_log_defaults = [
        'keystoneclient.session=INFO',
        'paramiko.transport=INFO',
        'requests.packages.urllib3.connectionpool=WARN'
    ]

    def _fix_log_levels(self):
        """Tweak the oslo log defaults."""
        for opt in logging.log_opts:
            if opt.dest == 'default_log_levels':
                opt.default.extend(self._extra_log_defaults)

    def __getattr__(self, attr):
        if not self._config:
            self._fix_log_levels()
            self._config = TempestConfigPrivate()

        return getattr(self._config, attr)


CONF = TempestConfigProxy()
