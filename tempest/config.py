# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import sys


from oslo.config import cfg

from tempest.common.utils.misc import singleton
from tempest.openstack.common import log as logging


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
    cfg.StrOpt('region',
               default='RegionOne',
               help="The identity region name to use. Also used as the other "
                    "services' region name unless they are set explicitly. "
                    "If no such region is found in the service catalog, the "
                    "first found one is used."),
    cfg.StrOpt('username',
               default='demo',
               help="Username to use for Nova API requests."),
    cfg.StrOpt('tenant_name',
               default='demo',
               help="Tenant name to use for Nova API requests."),
    cfg.StrOpt('admin_role',
               default='admin',
               help="Role required to administrate keystone."),
    cfg.StrOpt('password',
               default='pass',
               help="API key to use when authenticating.",
               secret=True),
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
    cfg.StrOpt('admin_username',
               default='admin',
               help="Administrative Username to use for"
                    "Keystone API requests."),
    cfg.StrOpt('admin_tenant_name',
               default='admin',
               help="Administrative Tenant name to use for Keystone API "
                    "requests."),
    cfg.StrOpt('admin_password',
               default='pass',
               help="API key to use when authenticating as admin.",
               secret=True),
]


def register_identity_opts(conf):
    conf.register_group(identity_group)
    for opt in IdentityGroup:
        conf.register_opt(opt, group='identity')


compute_group = cfg.OptGroup(name='compute',
                             title='Compute Service Options')

ComputeGroup = [
    cfg.BoolOpt('allow_tenant_isolation',
                default=False,
                help="Allows test cases to create/destroy tenants and "
                     "users. This option enables isolated test cases and "
                     "better parallel execution, but also requires that "
                     "OpenStack Identity API admin credentials are known."),
    cfg.BoolOpt('allow_tenant_reuse',
                default=True,
                help="If allow_tenant_isolation is True and a tenant that "
                     "would be created for a given test already exists (such "
                     "as from a previously-failed run), re-use that tenant "
                     "instead of failing because of the conflict. Note that "
                     "this would result in the tenant being deleted at the "
                     "end of a subsequent successful run."),
    cfg.StrOpt('image_ref',
               default="{$IMAGE_ID}",
               help="Valid secondary image reference to be used in tests."),
    cfg.StrOpt('image_ref_alt',
               default="{$IMAGE_ID_ALT}",
               help="Valid secondary image reference to be used in tests."),
    cfg.IntOpt('flavor_ref',
               default=1,
               help="Valid primary flavor to use in tests."),
    cfg.IntOpt('flavor_ref_alt',
               default=2,
               help='Valid secondary flavor to be used in tests.'),
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
    cfg.BoolOpt('resize_available',
                default=False,
                help="Does the test environment support resizing?"),
    cfg.BoolOpt('live_migration_available',
                default=False,
                help="Does the test environment support live migration "
                     "available?"),
    cfg.BoolOpt('use_block_migration_for_live_migration',
                default=False,
                help="Does the test environment use block devices for live "
                     "migration"),
    cfg.BoolOpt('block_migrate_supports_cinder_iscsi',
                default=False,
                help="Does the test environment block migration support "
                     "cinder iSCSI volumes"),
    cfg.BoolOpt('change_password_available',
                default=False,
                help="Does the test environment support changing the admin "
                     "password?"),
    cfg.BoolOpt('create_image_enabled',
                default=False,
                help="Does the test environment support snapshots?"),
    cfg.IntOpt('build_interval',
               default=10,
               help="Time in seconds between build status checks."),
    cfg.IntOpt('build_timeout',
               default=300,
               help="Timeout in seconds to wait for an instance to build."),
    cfg.BoolOpt('run_ssh',
                default=False,
                help="Does the test environment support snapshots?"),
    cfg.StrOpt('ssh_user',
               default='root',
               help="User name used to authenticate to an instance."),
    cfg.IntOpt('ping_timeout',
               default=60,
               help="Timeout in seconds to wait for ping to "
                    "succeed."),
    cfg.IntOpt('ssh_timeout',
               default=300,
               help="Timeout in seconds to wait for authentication to "
                    "succeed."),
    cfg.IntOpt('ready_wait',
               default=0,
               help="Additinal wait time for clean state, when there is"
                    " no OS-EXT-STS extension availiable"),
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
                help="Dose the SSH uses Floating IP?"),
    cfg.StrOpt('catalog_type',
               default='compute',
               help="Catalog type of the Compute service."),
    cfg.StrOpt('region',
               default='',
               help="The compute region name to use. If empty, the value "
                    "of identity.region is used instead. If no such region "
                    "is found in the service catalog, the first found one is "
                    "used."),
    cfg.StrOpt('path_to_private_key',
               default=None,
               help="Path to a private key file for SSH access to remote "
                    "hosts"),
    cfg.BoolOpt('disk_config_enabled',
                default=True,
                help="If false, skip disk config tests"),
    cfg.BoolOpt('flavor_extra_enabled',
                default=True,
                help="If false, skip flavor extra data test"),
    cfg.StrOpt('volume_device_name',
               default='vdb',
               help="Expected device name when a volume is attached to "
                    "an instance")
]


def register_compute_opts(conf):
    conf.register_group(compute_group)
    for opt in ComputeGroup:
        conf.register_opt(opt, group='compute')

compute_admin_group = cfg.OptGroup(name='compute-admin',
                                   title="Compute Admin Options")

ComputeAdminGroup = [
    cfg.StrOpt('username',
               default='admin',
               help="Administrative Username to use for Nova API requests."),
    cfg.StrOpt('tenant_name',
               default='admin',
               help="Administrative Tenant name to use for Nova API "
                    "requests."),
    cfg.StrOpt('password',
               default='pass',
               help="API key to use when authenticating as admin.",
               secret=True),
]


def register_compute_admin_opts(conf):
    conf.register_group(compute_admin_group)
    for opt in ComputeAdminGroup:
        conf.register_opt(opt, group='compute-admin')

image_group = cfg.OptGroup(name='image',
                           title="Image Service Options")

ImageGroup = [
    cfg.StrOpt('api_version',
               default='1',
               help="Version of the API"),
    cfg.StrOpt('catalog_type',
               default='image',
               help='Catalog type of the Image service.'),
    cfg.StrOpt('region',
               default='',
               help="The image region name to use. If empty, the value "
                    "of identity.region is used instead. If no such region "
                    "is found in the service catalog, the first found one is "
                    "used."),
    cfg.StrOpt('http_image',
               default='http://download.cirros-cloud.net/0.3.1/'
               'cirros-0.3.1-x86_64-uec.tar.gz',
               help='http accessable image')
]


def register_image_opts(conf):
    conf.register_group(image_group)
    for opt in ImageGroup:
        conf.register_opt(opt, group='image')


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
    cfg.StrOpt('tenant_network_cidr',
               default="10.100.0.0/16",
               help="The cidr block to allocate tenant networks from"),
    cfg.IntOpt('tenant_network_mask_bits',
               default=28,
               help="The mask bits for tenant networks"),
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
]


def register_network_opts(conf):
    conf.register_group(network_group)
    for opt in NetworkGroup:
        conf.register_opt(opt, group='network')

volume_group = cfg.OptGroup(name='volume',
                            title='Block Storage Options')

VolumeGroup = [
    cfg.IntOpt('build_interval',
               default=10,
               help='Time in seconds between volume availability checks.'),
    cfg.IntOpt('build_timeout',
               default=300,
               help='Timeout in seconds to wait for a volume to become'
                    'available.'),
    cfg.StrOpt('catalog_type',
               default='Volume',
               help="Catalog type of the Volume Service"),
    cfg.StrOpt('region',
               default='',
               help="The volume region name to use. If empty, the value "
                    "of identity.region is used instead. If no such region "
                    "is found in the service catalog, the first found one is "
                    "used."),
    cfg.BoolOpt('multi_backend_enabled',
                default=False,
                help="Runs Cinder multi-backend test (requires 2 backends)"),
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
]


def register_volume_opts(conf):
    conf.register_group(volume_group)
    for opt in VolumeGroup:
        conf.register_opt(opt, group='volume')


object_storage_group = cfg.OptGroup(name='object-storage',
                                    title='Object Storage Service Options')

ObjectStoreConfig = [
    cfg.StrOpt('catalog_type',
               default='object-store',
               help="Catalog type of the Object-Storage service."),
    cfg.StrOpt('region',
               default='',
               help="The object-storage region name to use. If empty, the "
                    "value of identity.region is used instead. If no such "
                    "region is found in the service catalog, the first found "
                    "one is used."),
    cfg.StrOpt('container_sync_timeout',
               default=120,
               help="Number of seconds to time on waiting for a container"
                    "to container synchronization complete."),
    cfg.StrOpt('container_sync_interval',
               default=5,
               help="Number of seconds to wait while looping to check the"
                    "status of a container to container synchronization"),
    cfg.BoolOpt('accounts_quotas_available',
                default=True,
                help="Set to True if the Account Quota middleware is enabled"),
    cfg.BoolOpt('container_quotas_available',
                default=True,
                help="Set to True if the container quota middleware "
                     "is enabled"),
    cfg.StrOpt('operator_role',
               default='Member',
               help="Role to add to users created for swift tests to "
                    "enable creating containers"),
]


def register_object_storage_opts(conf):
    conf.register_group(object_storage_group)
    for opt in ObjectStoreConfig:
        conf.register_opt(opt, group='object-storage')


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
               default=300,
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
]


def register_orchestration_opts(conf):
    conf.register_group(orchestration_group)
    for opt in OrchestrationGroup:
        conf.register_opt(opt, group='orchestration')


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


def register_dashboard_opts(conf):
    conf.register_group(scenario_group)
    for opt in DashboardGroup:
        conf.register_opt(opt, group='dashboard')


boto_group = cfg.OptGroup(name='boto',
                          title='EC2/S3 options')
BotoConfig = [
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


def register_boto_opts(conf):
    conf.register_group(boto_group)
    for opt in BotoConfig:
        conf.register_opt(opt, group='boto')

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
    cfg.StrOpt('log_check_interval',
               default=60,
               help='time (in seconds) between log file error checks.'),
    cfg.StrOpt('default_thread_number_per_action',
               default=4,
               help='The number of threads created while stress test.')
]


def register_stress_opts(conf):
    conf.register_group(stress_group)
    for opt in StressGroup:
        conf.register_opt(opt, group='stress')


scenario_group = cfg.OptGroup(name='scenario', title='Scenario Test Options')

ScenarioGroup = [
    cfg.StrOpt('img_dir',
               default='/opt/stack/new/devstack/files/images/'
               'cirros-0.3.1-x86_64-uec',
               help='Directory containing image files'),
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


def register_scenario_opts(conf):
    conf.register_group(scenario_group)
    for opt in ScenarioGroup:
        conf.register_opt(opt, group='scenario')


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
    cfg.BoolOpt('horizon',
                default=True,
                help="Whether or not Horizon is expected to be available"),
]


def register_service_available_opts(conf):
    conf.register_group(scenario_group)
    for opt in ServiceAvailableGroup:
        conf.register_opt(opt, group='service_available')

debug_group = cfg.OptGroup(name="debug",
                           title="Debug System")

DebugGroup = [
    cfg.BoolOpt('enable',
                default=True,
                help="Enable diagnostic commands"),
]


def register_debug_opts(conf):
    conf.register_group(debug_group)
    for opt in DebugGroup:
        conf.register_opt(opt, group='debug')


@singleton
class TempestConfig:
    """Provides OpenStack configuration information."""

    DEFAULT_CONFIG_DIR = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        "etc")

    DEFAULT_CONFIG_FILE = "tempest.conf"

    def __init__(self):
        """Initialize a configuration from a conf directory and conf file."""
        config_files = []
        failsafe_path = "/etc/tempest/" + self.DEFAULT_CONFIG_FILE

        # Environment variables override defaults...
        conf_dir = os.environ.get('TEMPEST_CONFIG_DIR',
                                  self.DEFAULT_CONFIG_DIR)
        conf_file = os.environ.get('TEMPEST_CONFIG', self.DEFAULT_CONFIG_FILE)

        path = os.path.join(conf_dir, conf_file)

        if not (os.path.isfile(path) or
                'TEMPEST_CONFIG_DIR' in os.environ or
                'TEMPEST_CONFIG' in os.environ):
            path = failsafe_path

        if not os.path.exists(path):
            msg = "Config file %s not found" % path
            print(RuntimeError(msg), file=sys.stderr)
        else:
            config_files.append(path)

        cfg.CONF([], project='tempest', default_config_files=config_files)
        logging.setup('tempest')
        LOG = logging.getLogger('tempest')
        LOG.info("Using tempest config file %s" % path)

        register_compute_opts(cfg.CONF)
        register_identity_opts(cfg.CONF)
        register_image_opts(cfg.CONF)
        register_network_opts(cfg.CONF)
        register_volume_opts(cfg.CONF)
        register_object_storage_opts(cfg.CONF)
        register_orchestration_opts(cfg.CONF)
        register_dashboard_opts(cfg.CONF)
        register_boto_opts(cfg.CONF)
        register_compute_admin_opts(cfg.CONF)
        register_stress_opts(cfg.CONF)
        register_scenario_opts(cfg.CONF)
        register_service_available_opts(cfg.CONF)
        self.compute = cfg.CONF.compute
        self.identity = cfg.CONF.identity
        self.images = cfg.CONF.image
        self.network = cfg.CONF.network
        self.volume = cfg.CONF.volume
        self.object_storage = cfg.CONF['object-storage']
        self.orchestration = cfg.CONF.orchestration
        self.dashboard = cfg.CONF.dashboard
        self.boto = cfg.CONF.boto
        self.compute_admin = cfg.CONF['compute-admin']
        self.stress = cfg.CONF.stress
        self.scenario = cfg.CONF.scenario
        self.service_available = cfg.CONF.service_available
        if not self.compute_admin.username:
            self.compute_admin.username = self.identity.admin_username
            self.compute_admin.password = self.identity.admin_password
            self.compute_admin.tenant_name = self.identity.admin_tenant_name
