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

import netaddr

from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
import tempest.test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseNetworkTest(tempest.test.BaseTestCase):

    """
    Base class for the Neutron tests that use the Tempest Neutron REST client

    Per the Neutron API Guide, API v1.x was removed from the source code tree
    (docs.openstack.org/api/openstack-network/2.0/content/Overview-d1e71.html)
    Therefore, v2.x of the Neutron API is assumed. It is also assumed that the
    following options are defined in the [network] section of etc/tempest.conf:

        tenant_network_cidr with a block of cidr's from which smaller blocks
        can be allocated for tenant networks

        tenant_network_mask_bits with the mask bits to be used to partition the
        block defined by tenant-network_cidr

    Finally, it is assumed that the following option is defined in the
    [service_available] section of etc/tempest.conf

        neutron as True
    """

    force_tenant_isolation = False

    # Default to ipv4.
    _ip_version = 4

    @classmethod
    def setUpClass(cls):
        # Create no network resources for these test.
        cls.set_network_resources()
        super(BaseNetworkTest, cls).setUpClass()
        if not CONF.service_available.neutron:
            raise cls.skipException("Neutron support is required")

        os = cls.get_client_manager()

        cls.network_cfg = CONF.network
        cls.client = os.network_client
        cls.networks = []
        cls.subnets = []
        cls.ports = []
        cls.routers = []
        cls.pools = []
        cls.vips = []
        cls.members = []
        cls.health_monitors = []
        cls.vpnservices = []
        cls.ikepolicies = []
        cls.floating_ips = []
        cls.metering_labels = []
        cls.metering_label_rules = []

    @classmethod
    def tearDownClass(cls):
        # Clean up ike policies
        for ikepolicy in cls.ikepolicies:
            cls.client.delete_ikepolicy(ikepolicy['id'])
        # Clean up vpn services
        for vpnservice in cls.vpnservices:
            cls.client.delete_vpnservice(vpnservice['id'])
        # Clean up floating IPs
        for floating_ip in cls.floating_ips:
            cls.client.delete_floatingip(floating_ip['id'])
        # Clean up routers
        for router in cls.routers:
            resp, body = cls.client.list_router_interfaces(router['id'])
            interfaces = body['ports']
            for i in interfaces:
                cls.client.remove_router_interface_with_subnet_id(
                    router['id'], i['fixed_ips'][0]['subnet_id'])
            cls.client.delete_router(router['id'])
        # Clean up health monitors
        for health_monitor in cls.health_monitors:
            cls.client.delete_health_monitor(health_monitor['id'])
        # Clean up members
        for member in cls.members:
            cls.client.delete_member(member['id'])
        # Clean up vips
        for vip in cls.vips:
            cls.client.delete_vip(vip['id'])
        # Clean up pools
        for pool in cls.pools:
            cls.client.delete_pool(pool['id'])
        # Clean up metering label rules
        for metering_label_rule in cls.metering_label_rules:
            cls.admin_client.delete_metering_label_rule(
                metering_label_rule['id'])
        # Clean up metering labels
        for metering_label in cls.metering_labels:
            cls.admin_client.delete_metering_label(metering_label['id'])
        # Clean up ports
        for port in cls.ports:
            cls.client.delete_port(port['id'])
        # Clean up subnets
        for subnet in cls.subnets:
            cls.client.delete_subnet(subnet['id'])
        # Clean up networks
        for network in cls.networks:
            cls.client.delete_network(network['id'])
        cls.clear_isolated_creds()
        super(BaseNetworkTest, cls).tearDownClass()

    @classmethod
    def create_network(cls, network_name=None):
        """Wrapper utility that returns a test network."""
        network_name = network_name or data_utils.rand_name('test-network-')

        resp, body = cls.client.create_network(name=network_name)
        network = body['network']
        cls.networks.append(network)
        return network

    @classmethod
    def create_subnet(cls, network):
        """Wrapper utility that returns a test subnet."""
        # The cidr and mask_bits depend on the ip version.
        if cls._ip_version == 4:
            cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
            mask_bits = CONF.network.tenant_network_mask_bits
        elif cls._ip_version == 6:
            cidr = netaddr.IPNetwork(CONF.network.tenant_network_v6_cidr)
            mask_bits = CONF.network.tenant_network_v6_mask_bits
        # Find a cidr that is not in use yet and create a subnet with it
        for subnet_cidr in cidr.subnet(mask_bits):
            try:
                resp, body = cls.client.create_subnet(
                    network_id=network['id'],
                    cidr=str(subnet_cidr),
                    ip_version=cls._ip_version)
                break
            except exceptions.BadRequest as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        else:
            message = 'Available CIDR for subnet creation could not be found'
            raise exceptions.BuildErrorException(message)
        subnet = body['subnet']
        cls.subnets.append(subnet)
        return subnet

    @classmethod
    def create_port(cls, network):
        """Wrapper utility that returns a test port."""
        resp, body = cls.client.create_port(network_id=network['id'])
        port = body['port']
        cls.ports.append(port)
        return port

    @classmethod
    def create_router(cls, router_name=None, admin_state_up=False,
                      external_network_id=None, enable_snat=None):
        ext_gw_info = {}
        if external_network_id:
            ext_gw_info['network_id'] = external_network_id
        if enable_snat:
            ext_gw_info['enable_snat'] = enable_snat
        resp, body = cls.client.create_router(
            router_name, external_gateway_info=ext_gw_info,
            admin_state_up=admin_state_up)
        router = body['router']
        cls.routers.append(router)
        return router

    @classmethod
    def create_floatingip(cls, external_network_id):
        """Wrapper utility that returns a test floating IP."""
        resp, body = cls.client.create_floatingip(
            floating_network_id=external_network_id)
        fip = body['floatingip']
        cls.floating_ips.append(fip)
        return fip

    @classmethod
    def create_pool(cls, name, lb_method, protocol, subnet):
        """Wrapper utility that returns a test pool."""
        resp, body = cls.client.create_pool(
            name=name,
            lb_method=lb_method,
            protocol=protocol,
            subnet_id=subnet['id'])
        pool = body['pool']
        cls.pools.append(pool)
        return pool

    @classmethod
    def update_pool(cls, name):
        """Wrapper utility that returns a test pool."""
        resp, body = cls.client.update_pool(name=name)
        pool = body['pool']
        return pool

    @classmethod
    def create_vip(cls, name, protocol, protocol_port, subnet, pool):
        """Wrapper utility that returns a test vip."""
        resp, body = cls.client.create_vip(name=name,
                                           protocol=protocol,
                                           protocol_port=protocol_port,
                                           subnet_id=subnet['id'],
                                           pool_id=pool['id'])
        vip = body['vip']
        cls.vips.append(vip)
        return vip

    @classmethod
    def update_vip(cls, name):
        resp, body = cls.client.update_vip(name=name)
        vip = body['vip']
        return vip

    @classmethod
    def create_member(cls, protocol_port, pool):
        """Wrapper utility that returns a test member."""
        resp, body = cls.client.create_member(address="10.0.9.46",
                                              protocol_port=protocol_port,
                                              pool_id=pool['id'])
        member = body['member']
        cls.members.append(member)
        return member

    @classmethod
    def update_member(cls, admin_state_up):
        resp, body = cls.client.update_member(admin_state_up=admin_state_up)
        member = body['member']
        return member

    @classmethod
    def create_health_monitor(cls, delay, max_retries, Type, timeout):
        """Wrapper utility that returns a test health monitor."""
        resp, body = cls.client.create_health_monitor(delay=delay,
                                                      max_retries=max_retries,
                                                      type=Type,
                                                      timeout=timeout)
        health_monitor = body['health_monitor']
        cls.health_monitors.append(health_monitor)
        return health_monitor

    @classmethod
    def update_health_monitor(cls, admin_state_up):
        resp, body = cls.client.update_vip(admin_state_up=admin_state_up)
        health_monitor = body['health_monitor']
        return health_monitor

    @classmethod
    def create_router_interface(cls, router_id, subnet_id):
        """Wrapper utility that returns a router interface."""
        resp, interface = cls.client.add_router_interface_with_subnet_id(
            router_id, subnet_id)

    @classmethod
    def create_vpnservice(cls, subnet_id, router_id):
        """Wrapper utility that returns a test vpn service."""
        resp, body = cls.client.create_vpnservice(
            subnet_id, router_id, admin_state_up=True,
            name=data_utils.rand_name("vpnservice-"))
        vpnservice = body['vpnservice']
        cls.vpnservices.append(vpnservice)
        return vpnservice

    @classmethod
    def create_ikepolicy(cls, name):
        """Wrapper utility that returns a test ike policy."""
        resp, body = cls.client.create_ikepolicy(name)
        ikepolicy = body['ikepolicy']
        cls.ikepolicies.append(ikepolicy)
        return ikepolicy


class BaseAdminNetworkTest(BaseNetworkTest):

    @classmethod
    def setUpClass(cls):
        super(BaseAdminNetworkTest, cls).setUpClass()
        admin_username = CONF.compute_admin.username
        admin_password = CONF.compute_admin.password
        admin_tenant = CONF.compute_admin.tenant_name
        if not (admin_username and admin_password and admin_tenant):
            msg = ("Missing Administrative Network API credentials "
                   "in configuration.")
            raise cls.skipException(msg)
        if (CONF.compute.allow_tenant_isolation or
            cls.force_tenant_isolation is True):
            creds = cls.isolated_creds.get_admin_creds()
            admin_username, admin_tenant_name, admin_password = creds
            cls.os_adm = clients.Manager(username=admin_username,
                                         password=admin_password,
                                         tenant_name=admin_tenant_name,
                                         interface=cls._interface)
        else:
            cls.os_adm = clients.ComputeAdminManager(interface=cls._interface)
        cls.admin_client = cls.os_adm.network_client

    @classmethod
    def create_metering_label(cls, name, description):
        """Wrapper utility that returns a test metering label."""
        resp, body = cls.admin_client.create_metering_label(
            description=description,
            name=data_utils.rand_name("metering-label"))
        metering_label = body['metering_label']
        cls.metering_labels.append(metering_label)
        return metering_label

    @classmethod
    def create_metering_label_rule(cls, remote_ip_prefix, direction,
                                   metering_label_id):
        """Wrapper utility that returns a test metering label rule."""
        resp, body = cls.admin_client.create_metering_label_rule(
            remote_ip_prefix=remote_ip_prefix, direction=direction,
            metering_label_id=metering_label_id)
        metering_label_rule = body['metering_label_rule']
        cls.metering_label_rules.append(metering_label_rule)
        return metering_label_rule
