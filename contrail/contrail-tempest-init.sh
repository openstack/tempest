#!/usr/bin/env bash

with_venv=tools/with_venv.sh

export OS_USERNAME=${OS_USERNAME:-admin}
export OS_PASSWORD=${OS_PASSWORD:-contrail123}
export OS_TENANT_NAME=${OS_TENANT_NAME:-admin}
export OS_NO_CACHE=1

export TEMPEST_DIR=${TEMPEST_DIR:-$(pwd)}
export KEYSTONE_SERVICE_PROTOCOL=${KEYSTONE_SERVICE_PROTOCOL:-http}
export KEYSTONE_SERVICE_HOST=${KEYSTONE_SERVICE_HOST:-127.0.0.1}
export OS_AUTH_URL=http://${KEYSTONE_SERVICE_HOST}:5000/v2.0/
export PUBLIC_NETWORK_NAME=${PUBLIC_NETWORK_NAME:-public_net}
export PUBLIC_NETWORK_RI_FQ_NAME=${PUBLIC_NETWORK_RI_FQ_NAME:-"default-domain:$OS_TENANT_NAME:$PUBLIC_NETWORK_NAME:$PUBLIC_NETWORK_NAME"}
export PUBLIC_NETWORK_RT=${PUBLIC_NETWORK_RT:-10003}
export ROUTER_ASN=${ROUTER_ASN:-64510}
export API_SERVER_IP=${API_SERVER_IP:-127.0.0.1}
export API_SERVER_HOST_USER=${API_SERVER_HOST_USER:-root}
export API_SERVER_HOST_PASSWORD=${API_SERVER_HOST_PASSWORD:-c0ntrail123}
export PUBLIC_NETWORK_SUBNET=${PUBLIC_NETWORK_SUBNET:-10.1.1.0/24}
export HTTP_IMAGE_PATH=${HTTP_IMAGE_PATH:-http://10.204.216.51/images/cirros/cirros-0.3.1-x86_64-disk.img}

FLAVOR_ID=7
SERVICE_HOST=$KEYSTONE_SERVICE_HOST

TEMPEST_CONFIG_DIR=${TEMPEST_CONFIG_DIR:-$TEMPEST_DIR/etc}
TEMPEST_CONFIG=$TEMPEST_CONFIG_DIR/tempest.conf

source $TEMPEST_DIR/contrail/functions
cd ${TEMPEST_DIR:-$(pwd)}

cp $TEMPEST_DIR/etc/tempest.conf.sample $TEMPEST_CONFIG
password=${ADMIN_PASSWORD:-contrail123}
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

#DASHBOARD
iniset $TEMPEST_CONFIG dashboard dashboard_url "http://$SERVICE_HOST/"
iniset $TEMPEST_CONFIG dashboard login_url "http://$SERVICE_HOST/auth/login/"

iniset $TEMPEST_CONFIG DEFAULT debug True

#IDENTITY
iniset $TEMPEST_CONFIG identity uri "$KEYSTONE_SERVICE_PROTOCOL://$KEYSTONE_SERVICE_HOST:5000/v2.0/"
iniset $TEMPEST_CONFIG identity uri_v3 "$KEYSTONE_SERVICE_PROTOCOL://$KEYSTONE_SERVICE_HOST:5000/v3/"
iniset $TEMPEST_CONFIG identity username $USERNAME
iniset $TEMPEST_CONFIG identity password $PASSWORD
iniset $TEMPEST_CONFIG identity tenant_name $TENANT_NAME

iniset $TEMPEST_CONFIG identity alt_username $ALT_USERNAME
iniset $TEMPEST_CONFIG identity alt_password $password
iniset $TEMPEST_CONFIG identity alt_tenant_name $ALT_TENANT_NAME

#AUTH
iniset $TEMPEST_CONFIG auth admin_username $ADMIN_USERNAME
iniset $TEMPEST_CONFIG auth admin_password $ADMIN_PASSWORD
iniset $TEMPEST_CONFIG auth admin_project_name $ADMIN_TENANT_NAME
iniset $TEMPEST_CONFIG auth use_dynamic_credentials True

iniset $TEMPEST_CONFIG image http_image $HTTP_IMAGE_PATH

#COMPUTE 
public_network_id=$(${with_venv} neutron net-list | grep $PUBLIC_NETWORK_NAME | \
            awk '{print $2}')

iniset $TEMPEST_CONFIG compute ssh_user ${DEFAULT_INSTANCE_USER:-cirros}
iniset $TEMPEST_CONFIG compute image_ref $image_uuid
iniset $TEMPEST_CONFIG validation image_ssh_user ${DEFAULT_INSTANCE_USER:-cirros}
iniset $TEMPEST_CONFIG validation image_ssh_password ${DEFAULT_INSTANCE_PASSWORD:-cubswin:)}
iniset $TEMPEST_CONFIG compute flavor_ref $FLAVOR_ID
iniset $TEMPEST_CONFIG compute image_ref_alt $image_uuid_alt
iniset $TEMPEST_CONFIG compute image_alt_ssh_user ${DEFAULT_INSTANCE_USER:-cirros}
iniset $TEMPEST_CONFIG compute image_alt_ssh_password ${DEFAULT_INSTANCE_PASSWORD:-cubswin:)}
iniset $TEMPEST_CONFIG compute allow_tenant_isolation ${TENANT_ISOLATION:-false}
iniset $TEMPEST_CONFIG network public_network_id "$public_network_id"

# Disable IPv6 tests
iniset $TEMPEST_CONFIG network-feature-enabled ipv6 false

iniset $TEMPEST_CONFIG service_available "neutron" "True"
iniset $TEMPEST_CONFIG service_available "cinder" "False"
iniset $TEMPEST_CONFIG service_available "swift" "False"
iniset $TEMPEST_CONFIG service_available "heat" "False"


