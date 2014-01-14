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
from tempest import exceptions
from tempest.openstack.common import log as logging
import tempest.test

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

    @classmethod
    def setUpClass(cls):
        # Create no network resources for these test.
        cls.set_network_resources()
        super(BaseNetworkTest, cls).setUpClass()
        os = clients.Manager(interface=cls._interface)
        cls.network_cfg = os.config.network
        if not cls.config.service_available.neutron:
            raise cls.skipException("Neutron support is required")
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
            cls.client.delete_floating_ip(floating_ip['id'])
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
        # Clean up ports
        for port in cls.ports:
            cls.client.delete_port(port['id'])
        # Clean up subnets
        for subnet in cls.subnets:
            cls.client.delete_subnet(subnet['id'])
        # Clean up networks
        for network in cls.networks:
            cls.client.delete_network(network['id'])
        super(BaseNetworkTest, cls).tearDownClass()

    @classmethod
    def create_network(cls, network_name=None):
        """Wrapper utility that returns a test network."""
        network_name = network_name or data_utils.rand_name('test-network-')

        resp, body = cls.client.create_network(network_name)
        network = body['network']
        cls.networks.append(network)
        return network

    @classmethod
    def create_subnet(cls, network):
        """Wrapper utility that returns a test subnet."""
        cidr = netaddr.IPNetwork(cls.network_cfg.tenant_network_cidr)
        mask_bits = cls.network_cfg.tenant_network_mask_bits
        # Find a cidr that is not in use yet and create a subnet with it
        body = None
        failure = None
        for subnet_cidr in cidr.subnet(mask_bits):
            try:
                resp, body = cls.client.create_subnet(network['id'],
                                                      str(subnet_cidr))
                break
            except exceptions.BadRequest as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
                # save the failure in case all of the CIDRs are overlapping
                failure = e

        if not body and failure:
            raise failure

        subnet = body['subnet']
        cls.subnets.append(subnet)
        return subnet

    @classmethod
    def create_port(cls, network):
        """Wrapper utility that returns a test port."""
        resp, body = cls.client.create_port(network['id'])
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
    def create_floating_ip(cls, external_network_id, **kwargs):
        """Wrapper utility that returns a test floating IP."""
        resp, body = cls.client.create_floating_ip(
            external_network_id,
            **kwargs)
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
        resp, body = cls.client.create_vip(name, protocol, protocol_port,
                                           subnet['id'], pool['id'])
        vip = body['vip']
        cls.vips.append(vip)
        return vip

    @classmethod
    def create_member(cls, protocol_port, pool):
        """Wrapper utility that returns a test member."""
        resp, body = cls.client.create_member("10.0.9.46",
                                              protocol_port,
                                              pool['id'])
        member = body['member']
        cls.members.append(member)
        return member

    @classmethod
    def create_health_monitor(cls, delay, max_retries, Type, timeout):
        """Wrapper utility that returns a test health monitor."""
        resp, body = cls.client.create_health_monitor(delay,
                                                      max_retries,
                                                      Type, timeout)
        health_monitor = body['health_monitor']
        cls.health_monitors.append(health_monitor)
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
        admin_username = cls.config.compute_admin.username
        admin_password = cls.config.compute_admin.password
        admin_tenant = cls.config.compute_admin.tenant_name
        if not (admin_username and admin_password and admin_tenant):
            msg = ("Missing Administrative Network API credentials "
                   "in configuration.")
            raise cls.skipException(msg)
        cls.admin_manager = clients.AdminManager(interface=cls._interface)
        cls.admin_client = cls.admin_manager.network_client
