#!/usr/bin/env bash

with_venv=tools/with_venv.sh

export OS_USERNAME=${OS_USERNAME:-admin}
export OS_PASSWORD=${OS_PASSWORD:-contrail123}
export OS_TENANT_NAME=${OS_TENANT_NAME:-admin}
export OS_NO_CACHE=1

export TEMPEST_DIR=${TEMPEST_DIR:-$(pwd)}
export KEYSTONE_SERVICE_PROTOCOL=${AUTH_PROTOCOL:-http}
export KEYSTONE_SERVICE_HOST=${KEYSTONE_SERVICE_HOST:-127.0.0.1}
export OS_AUTH_URL=${KEYSTONE_SERVICE_PROTOCOL}://${KEYSTONE_SERVICE_HOST}:5000/v2.0/
export PUBLIC_NETWORK_NAME=${PUBLIC_NETWORK_NAME:-public_net}
export PUBLIC_NETWORK_RI_FQ_NAME=${PUBLIC_NETWORK_RI_FQ_NAME:-"default-domain:$OS_TENANT_NAME:$PUBLIC_NETWORK_NAME:$PUBLIC_NETWORK_NAME"}
export PUBLIC_NETWORK_RT=${PUBLIC_NETWORK_RT:-10003}
export ROUTER_ASN=${ROUTER_ASN:-64510}
export API_SERVER_IP=${API_SERVER_IP:-127.0.0.1}
export API_SERVER_HOST_USER=${API_SERVER_HOST_USER:-root}
export API_SERVER_HOST_PASSWORD=${API_SERVER_HOST_PASSWORD:-c0ntrail123}
export PUBLIC_NETWORK_SUBNET=${PUBLIC_NETWORK_SUBNET:-10.1.1.0/24}
export HTTP_IMAGE_PATH=${HTTP_IMAGE_PATH:-http://10.204.216.50/images/cirros/cirros-0.3.5-x86_64-disk.img}
export PUBLIC_ACCESS_AVAILABLE=${PUBLIC_ACCESS_AVAILABLE:-0}

FLAVOR_ID=7
FLAVOR_ID_ALT=8
SERVICE_HOST=$KEYSTONE_SERVICE_HOST

TEMPEST_CONFIG_DIR=${TEMPEST_CONFIG_DIR:-$TEMPEST_DIR/etc}
TEMPEST_CONFIG=$TEMPEST_CONFIG_DIR/tempest.conf

source $TEMPEST_DIR/contrail/functions
cd ${TEMPEST_DIR:-$(pwd)}

cp $TEMPEST_DIR/etc/tempest.conf.sample $TEMPEST_CONFIG
password=${OS_PASSWORD:-contrail123}
ALT_USERNAME=${ALT_USERNAME:-alt_demo}
ALT_TENANT_NAME=${ALT_TENANT_NAME:-alt_demo}
USERNAME="demo"
PASSWORD=$OS_PASSWORD
TENANT_NAME="demo"

ADMIN_USERNAME="admin"
ADMIN_PASSWORD=$OS_PASSWORD
ADMIN_TENANT_NAME="admin"

# ADD GLANCE IMAGE 
# set image_uuid and image_uuid_alt
image_uuid=`get_image_id $KEYSTONE_SERVICE_HOST "cirros" $HTTP_IMAGE_PATH`
image_uuid_alt=`get_image_id $KEYSTONE_SERVICE_HOST "cirros" $HTTP_IMAGE_PATH`
echo "Image id $image_uuid"

# Create tenant, user and public network
create_project $ALT_TENANT_NAME
create_user $ALT_USERNAME $password $ALT_TENANT_NAME "member"
create_public_network $PUBLIC_NETWORK_NAME $PUBLIC_NETWORK_SUBNET
create_flavor $FLAVOR_ID
create_flavor $FLAVOR_ID_ALT 1024 1 1 

compute_count=`get_compute_count`

#DASHBOARD
iniset $TEMPEST_CONFIG dashboard dashboard_url "http://$SERVICE_HOST/horizon"
iniset $TEMPEST_CONFIG dashboard login_url "http://$SERVICE_HOST/horizon/auth/login/"

iniset $TEMPEST_CONFIG DEFAULT debug True
iniset $TEMPEST_CONFIG DEFAULT log_file ./tempest.log

#IDENTITY
iniset $TEMPEST_CONFIG identity uri "$KEYSTONE_SERVICE_PROTOCOL://$KEYSTONE_SERVICE_HOST:5000/v2.0/"
iniset $TEMPEST_CONFIG identity uri_v3 "$KEYSTONE_SERVICE_PROTOCOL://$KEYSTONE_SERVICE_HOST:5000/v3/"
iniset $TEMPEST_CONFIG identity username $USERNAME
iniset $TEMPEST_CONFIG identity password $PASSWORD
iniset $TEMPEST_CONFIG identity tenant_name $TENANT_NAME
iniset $TEMPEST_CONFIG identity disable_ssl_certificate_validation True
iniset $TEMPEST_CONFIG identity alt_username $ALT_USERNAME
iniset $TEMPEST_CONFIG identity alt_password $password
iniset $TEMPEST_CONFIG identity alt_tenant_name $ALT_TENANT_NAME
iniset $TEMPEST_CONFIG identity auth_version v2 #ToDo: Forcing it to V2 for now

#AUTH
iniset $TEMPEST_CONFIG auth admin_username $ADMIN_USERNAME
iniset $TEMPEST_CONFIG auth admin_password $ADMIN_PASSWORD
iniset $TEMPEST_CONFIG auth admin_project_name $ADMIN_TENANT_NAME
iniset $TEMPEST_CONFIG auth use_dynamic_credentials True

iniset $TEMPEST_CONFIG image http_image $HTTP_IMAGE_PATH

#COMPUTE 
if [[ $AUTH_PROTOCOL -eq 'https' ]]; then
neutron="neutron --insecure"
else
neutron="neutron"
fi
public_network_id=$(${with_venv} ${neutron} net-list | grep $PUBLIC_NETWORK_NAME | \
            awk '{print $2}')

iniset $TEMPEST_CONFIG compute ssh_user ${DEFAULT_INSTANCE_USER:-cirros}
iniset $TEMPEST_CONFIG compute image_ref $image_uuid
iniset $TEMPEST_CONFIG validation image_ssh_user ${DEFAULT_INSTANCE_USER:-cirros}
iniset $TEMPEST_CONFIG validation image_ssh_password ${DEFAULT_INSTANCE_PASSWORD:-cubswin:)}
iniset $TEMPEST_CONFIG validation run_validation true
iniset $TEMPEST_CONFIG compute min_compute_nodes $compute_count

iniset $TEMPEST_CONFIG compute flavor_ref $FLAVOR_ID
iniset $TEMPEST_CONFIG compute flavor_ref_alt $FLAVOR_ID_ALT
iniset $TEMPEST_CONFIG compute image_ref_alt $image_uuid_alt
iniset $TEMPEST_CONFIG compute image_alt_ssh_user ${DEFAULT_INSTANCE_USER:-cirros}
iniset $TEMPEST_CONFIG compute image_alt_ssh_password ${DEFAULT_INSTANCE_PASSWORD:-cubswin:)}
iniset $TEMPEST_CONFIG compute allow_tenant_isolation ${TENANT_ISOLATION:-false}
iniset $TEMPEST_CONFIG network public_network_id "$public_network_id"
iniset $TEMPEST_CONFIG network floating_network_name $PUBLIC_NETWORK_NAME

iniset $TEMPEST_CONFIG network-feature-enabled api_extensions allowed-address-pairs,extra_dhcp_opt,security-group,floating_ips,port_security,ipv6,router,quotas,binding
iniset $TEMPEST_CONFIG compute-feature-enabled live_migration false
iniset $TEMPEST_CONFIG compute-feature-enabled cold_migration false
iniset $TEMPEST_CONFIG compute-feature-enabled scheduler_available_filters "RetryFilter, AvailabilityZoneFilter, RamFilter, DiskFilter, ComputeFilter, ComputeCapabilitiesFilter, ImagePropertiesFilter, ServerGroupAntiAffinityFilter, ServerGroupAffinityFilter"


iniset $TEMPEST_CONFIG identity-feature-enabled api_v2 false
iniset $TEMPEST_CONFIG identity-feature-enabled api_v2_admin false
iniset $TEMPEST_CONFIG identity-feature-enabled api_v3 false

if [ $PUBLIC_ACCESS_AVAILABLE -eq 1 ];
then
    iniset $TEMPEST_CONFIG network-feature-enabled floating_ips true
fi

iniset $TEMPEST_CONFIG service_available "neutron" "True"
iniset $TEMPEST_CONFIG service_available "nova" "True"
iniset $TEMPEST_CONFIG service_available "heat" "True"
iniset $TEMPEST_CONFIG service_available "glance" "True"
iniset $TEMPEST_CONFIG service_available "horizon" "False"
iniset $TEMPEST_CONFIG service_available "cinder" "False"
iniset $TEMPEST_CONFIG service_available "swift" "False"
iniset $TEMPEST_CONFIG service_available "sahara" "False"
iniset $TEMPEST_CONFIG service_available "trove" "False"
iniset $TEMPEST_CONFIG service_available "ceilometer" "False"
iniset $TEMPEST_CONFIG service_available "ironic" "False"
iniset $TEMPEST_CONFIG service_available "manila" "False"

