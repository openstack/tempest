apt-get install -y git
apt-get install -y libffi-dev
apt-get install -y gcc
if [ ! -d "tempest" ]; then
   git clone git://github.com/vedujoshi/tempest
else
   (cd tempest ; git pull)
fi
  
#(cd tempest;git checkout remotes/origin/stable/havana)

DEST="$PWD/tempest"
DATA_DIR=${DEST}/data
KEYSTONE_SERVICE_PROTOCOL="http"
KEYSTONE_SERVICE_HOST="10.204.217.70"
PUBLIC_NETWORK_NAME="public_net"
PUBLIC_NETWORK_SUBNET="10.204.216.64/29"
HTTP_IMAGE_PATH="http://10.204.216.51/images/cirros/cirros-0.3.1-x86_64-uec.tar.gz"
SERVICE_HOST=$KEYSTONE_SERVICE_HOST

TEMPEST_DIR=$DEST
TEMPEST_CONFIG_DIR=${TEMPEST_CONFIG_DIR:-$TEMPEST_DIR/etc}
TEMPEST_CONFIG=$TEMPEST_CONFIG_DIR/tempest.conf
TEMPEST_STATE_PATH=${TEMPEST_STATE_PATH:=$DATA_DIR/tempest}

source $TEMPEST_DIR/contrail/functions
#source /etc/contrail/openstackrc
source ~/openstackrc

cp $TEMPEST_DIR/etc/tempest.conf.sample $TEMPEST_CONFIG
password=${ADMIN_PASSWORD:-contrail123}
ALT_USERNAME=${ALT_USERNAME:-alt_demo}
ALT_TENANT_NAME=${ALT_TENANT_NAME:-alt_demo}
USERNAME="demo"
PASSWORD="contrail123"
TENANT_NAME="demo"

ADMIN_USERNAME="admin"
ADMIN_PASSWORD="contrail123"
ADMIN_TENANT_NAME="admin"

# ADD GLANCE IMAGE 
# set image_uuid and image_uuid_alt
image_uuid=`get_image_id "cirros" $image_path`
image_uuid_alt=`get_image_id "cirros" $image_path`
echo "Image id $image_uuid"

# Create tenant, user and public network
create_project $ALT_TENANT_NAME
create_user $ALT_USERNAME $password $ALT_TENANT_NAME "member"
create_public_network $PUBLIC_NETWORK_NAME $PUBLIC_NETWORK_SUBNET

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

iniset $TEMPEST_CONFIG identity admin_username $ADMIN_USERNAME
iniset $TEMPEST_CONFIG identity admin_password $ADMIN_PASSWORD
iniset $TEMPEST_CONFIG identity admin_tenant_name $ADMIN_TENANT_NAME

iniset $TEMPEST_CONFIG image http_image $HTTP_IMAGE_PATH

#COMPUTE 
public_network_id=$(source ~/openstackrc; neutron net-list | grep $PUBLIC_NETWORK_NAME | \
            awk '{print $2}')

iniset $TEMPEST_CONFIG compute ssh_user ${DEFAULT_INSTANCE_USER:-cirros}
iniset $TEMPEST_CONFIG compute image_ref $image_uuid
iniset $TEMPEST_CONFIG compute image_ssh_user ${DEFAULT_INSTANCE_USER:-cirros}
iniset $TEMPEST_CONFIG compute image_ssh_password ${DEFAULT_INSTANCE_PASSWORD:-cubswin:)}
iniset $TEMPEST_CONFIG compute image_ref_alt $image_uuid_alt
iniset $TEMPEST_CONFIG compute image_alt_ssh_user ${DEFAULT_INSTANCE_USER:-cirros}
iniset $TEMPEST_CONFIG compute image_alt_ssh_password ${DEFAULT_INSTANCE_PASSWORD:-cubswin:)}
iniset $TEMPEST_CONFIG network public_network_id "$public_network_id"



iniset $TEMPEST_CONFIG service_available "neutron" "True"
iniset $TEMPEST_CONFIG service_available "cinder" "False"
iniset $TEMPEST_CONFIG service_available "swift" "False"
iniset $TEMPEST_CONFIG service_available "heat" "False"


