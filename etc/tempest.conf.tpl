[identity]
# This section contains configuration options that a variety of Tempest
# test clients use when authenticating with different user/tenant
# combinations

# Set to True if your test environment's Keystone authentication service should
# be accessed over HTTPS
use_ssl = %IDENTITY_USE_SSL%
# This is the main host address of the authentication service API
host = %IDENTITY_HOST%
# Port that the authentication service API is running on
port = %IDENTITY_PORT%
# Version of the authentication service API (a string)
api_version = %IDENTITY_API_VERSION%
# Path to the authentication service tokens resource (do not modify unless you
# have a custom authentication API and are not using Keystone)
path = %IDENTITY_PATH%
# Should typically be left as keystone unless you have a non-Keystone
# authentication API service
strategy = %IDENTITY_STRATEGY%

[compute]
# This section contains configuration options used when executing tests
# against the OpenStack Compute API.

# Allows test cases to create/destroy tenants and users. This option
# enables isolated test cases and better parallel execution,
# but also requires that OpenStack Identity API admin credentials
# are known.
allow_tenant_isolation = %COMPUTE_ALLOW_TENANT_ISOLATION%

# Allows test cases to create/destroy tenants and users. This option
# enables isolated test cases and better parallel execution,
# but also requires that OpenStack Identity API admin credentials
# are known.
allow_tenant_reuse = %COMPUTE_ALLOW_TENANT_REUSE%

# This should be the username of a user WITHOUT administrative privileges
username = %USERNAME%
# The above non-administrative user's password
password = %PASSWORD%
# The above non-administrative user's tenant name
tenant_name = %TENANT_NAME%

# This should be the username of an alternate user WITHOUT
# administrative privileges
alt_username = %ALT_USERNAME%
# The above non-administrative user's password
alt_password = %ALT_PASSWORD%
# The above non-administrative user's tenant name
alt_tenant_name = %ALT_TENANT_NAME%

# Reference data for tests. The ref and ref_alt should be
# distinct images/flavors.
image_ref = %IMAGE_ID%
image_ref_alt = %IMAGE_ID_ALT%
flavor_ref = %FLAVOR_REF%
flavor_ref_alt = %FLAVOR_REF_ALT%

# Number of seconds to wait while looping to check the status of an
# instance that is building.
build_interval = %COMPUTE_BUILD_INTERVAL%

# Number of seconds to time out on waiting for an instance
# to build or reach an expected status
build_timeout = %COMPUTE_BUILD_TIMEOUT%

# The type of endpoint for a Compute API service. Unless you have a
# custom Keystone service catalog implementation, you probably want to leave
# this value as "compute"
catalog_type = %COMPUTE_CATALOG_TYPE%

# Does the Compute API support creation of images?
create_image_enabled = %COMPUTE_CREATE_IMAGE_ENABLED%

# For resize to work with libvirt/kvm, one of the following must be true:
# Single node: allow_resize_to_same_host=True must be set in nova.conf
# Cluster: the 'nova' user must have scp access between cluster nodes
resize_available = %COMPUTE_RESIZE_AVAILABLE%

# Does the compute API support changing the admin password?
change_password_available = %COMPUTE_CHANGE_PASSWORD_AVAILABLE%

# Level to log Compute API request/response details.
log_level = %COMPUTE_LOG_LEVEL%

# Whitebox options for compute. Whitebox options enable the
# whitebox test cases, which look at internal Nova database state,
# SSH into VMs to check instance state, etc.

# Should we run whitebox tests for Compute?
whitebox_enabled = %COMPUTE_WHITEBOX_ENABLED%

# Path of nova source directory
source_dir = %COMPUTE_SOURCE_DIR%

# Path of nova configuration file
config_path = %COMPUTE_CONFIG_PATH%

# Directory containing nova binaries such as nova-manage
bin_dir = %COMPUTE_BIN_DIR%

# Path to a private key file for SSH access to remote hosts
path_to_private_key = %COMPUTE_PATH_TO_PRIVATE_KEY%

# Connection string to the database of Compute service
db_uri = %COMPUTE_DB_URI%

# Run live migration tests (requires 2 hosts)
live_migration_available = %LIVE_MIGRATION_AVAILABLE%

# Use block live migration (Otherwise, non-block migration will be
# performed, which requires XenServer pools in case of using XS)
use_block_migration_for_live_migration = %USE_BLOCK_MIGRATION_FOR_LIVE_MIGRATION%

[image]
# This section contains configuration options used when executing tests
# against the OpenStack Images API

# The type of endpoint for an Image API service. Unless you have a
# custom Keystone service catalog implementation, you probably want to leave
# this value as "image"
catalog_type = %IMAGE_CATALOG_TYPE%

# The version of the OpenStack Images API to use
api_version = %IMAGE_API_VERSION%

# This is the main host address of the Image API
host = %IMAGE_HOST%

# Port that the Image API is running on
port = %IMAGE_PORT%

# This should be the username of a user WITHOUT administrative privileges
username = %USERNAME%
# The above non-administrative user's password
password = %PASSWORD%
# The above non-administrative user's tenant name
tenant_name = %TENANT_NAME%

[compute-admin]
# This section contains configuration options for an administrative
# user of the Compute API. These options are used in tests that stress
# the admin-only parts of the Compute API

# This should be the username of a user WITH administrative privileges
username = %COMPUTE_ADMIN_USERNAME%
# The above administrative user's password
password = %COMPUTE_ADMIN_PASSWORD%
# The above administrative user's tenant name
tenant_name = %COMPUTE_ADMIN_TENANT_NAME%

[identity-admin]
# This section contains configuration options for an administrative
# user of the Compute API. These options are used in tests that stress
# the admin-only parts of the Compute API

# This should be the username of a user WITH administrative privileges
username = %IDENTITY_ADMIN_USERNAME%
# The above administrative user's password
password = %IDENTITY_ADMIN_PASSWORD%
# The above administrative user's tenant name
tenant_name = %IDENTITY_ADMIN_TENANT_NAME%

[volume]
# This section contains the configuration options used when executing tests
# against the OpenStack Block Storage API service

# The type of endpoint for a Cinder or Block Storage API service.
# Unless you have a custom Keystone service catalog implementation, you
# probably want to leave this value as "volume"
catalog_type = %VOLUME_CATALOG_TYPE%
# Number of seconds to wait while looping to check the status of a
# volume that is being made available
build_interval = %VOLUME_BUILD_INTERVAL%
# Number of seconds to time out on waiting for a volume
# to be available or reach an expected status
build_timeout = %VOLUME_BUILD_TIMEOUT%

[object-storage]
# This section contains configuration options used when executing tests
# against the OpenStack Object Storage API.
# This should be the username of a user WITHOUT administrative privileges

# You can configure the credentials in the compute section

# The type of endpoint for an Object Storage API service. Unless you have a
# custom Keystone service catalog implementation, you probably want to leave
# this value as "object-store"
catalog_type = %OBJECT_CATALOG_TYPE%

[boto]
# This section contains configuration options used when executing tests
# with boto.

# EC2 URL
ec2_url = %BOTO_EC2_URL%
# S3 URL
s3_url = %BOTO_S3_URL%

# Use keystone ec2-* command to get those values for your test user and tenant
aws_access = %BOTO_AWS_ACCESS%
aws_secret = %BOTO_AWS_SECRET%

#Region
aws_region = %BOTO_AWS_REGION%

#Image materials for S3 upload
# ALL content of the specified directory will be uploaded to S3
s3_materials_path = %BOTO_S3_MATERIALS_PATH%

# The manifest.xml files, must be in the s3_materials_path directory
# Subdirectories not allowed!
# The filenames will be used as a Keys in the S3 Buckets

#ARI Ramdisk manifest. Must be in the above s3_materials_path directory
ari_manifest = %BOTO_ARI_MANIFEST%

#AMI Machine Image manifest. Must be in the above s3_materials_path directory
ami_manifest = %BOTO_AMI_MANIFEST%

#AKI Kernel Image manifest, Must be in the above s3_materials_path directory
aki_manifest = %BOTO_AKI_MANIFEST%

#Instance type
instance_type = %BOTO_FLAVOR_NAME%

#TCP/IP connection timeout
http_socket_timeout = %BOTO_SOCKET_TIMEOUT%

# Status change wait timout
build_timeout = %BOTO_BUILD_TIMEOUT%

# Status change wait interval
build_interval = %BOTO_BUILD_INTERVAL%
