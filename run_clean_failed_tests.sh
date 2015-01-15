#!/bin/bash
#########
# This scripts cleans all the crap that may remain after
# failing a tempest test. It's not bullet-proof but saves some time
# to get openstack to a clean state.
# TODO: remove also security groups
#########
if [ $# -ne 1 ]; then
    echo "Usage: cleanup_failed_tests.sh [path to keystone creds]"
    exit 1
fi

source $1 admin

# Deleting user ids created by tempest
USER_IDS=$(keystone user-list|grep -E ".*Test.*@example.com" | awk -F" | " '{print $2}')
for i in $USER_IDS; do
    echo "Deleting user $i"
    keystone user-delete $i
done

# Remove tenants which are not admin, demo, etc.
PROJECT_IDS=$(keystone tenant-list | grep -vE "admin|alt_demo|demo|service" | awk -F" | " '{print $2}')

for i in $PROJECT_IDS; do
    echo "Deleting tenant $i"
    keystone tenant-delete $i
done

# Remove instances, router and network without a tenant_id associated (removed previously)
INSTANCE_IDS=$(nova list --all-tenants | grep Running | awk -F" | " '{print $2}')
for j in $INSTANCE_IDS; do
    TENANT_ID=$(nova show $j | grep tenant_id | awk -F"|" '{print $3}')
    keystone tenant-get $TENANT_ID 2>&1 > /dev/null
    if [ $? -eq 1 ]; then
        echo "Deleting instance $j"
        nova delete $j
    fi
done

# Remove floating ips
FLOATING_IDS=$(neutron floatingip-list | grep -vE "id|-----" | awk -F" | " '{print $2}')
for i in $FLOATING_IDS; do
    neutron floatingip-delete $i
done

ROUTER_IDS=$(neutron router-list -F id | grep -vE "id|-------" | awk -F " | " '{print $2}')
for i in $ROUTER_IDS; do
    TENANT_ID=$(neutron router-show $i -c tenant_id -f value)
    keystone tenant-get $TENANT_ID 2>&1 > /dev/null
    if [ $? -eq 1 ]; then
        PORT_IDS=$(neutron router-port-list $i -c id | grep -vE "id|----" |awk -F " | " '{print $2}')
        for j in $PORT_IDS; do
            echo "Removing interface $j from router $i ..."
            neutron router-interface-delete $i port=$j
        done
        echo "Removing router $i ..."
        neutron router-delete $i
    fi
done

NET_IDS=$(neutron net-list -F id | grep -vE "id|------" | awk -F " | " '{print $2}')
for i in $NET_IDS; do
    TENANT_ID=$(neutron net-show $i -c tenant_id -f value)
    keystone tenant-get $TENANT_ID 2>&1 > /dev/null
    if [ $? -eq 1 ]; then
        echo "Removing net $i ..."
        neutron net-delete $i
    fi
done

