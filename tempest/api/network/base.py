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

import netaddr

from tempest import clients
from tempest.common import isolated_creds
from tempest.common.utils.data_utils import rand_name
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
        super(BaseNetworkTest, cls).setUpClass()
        cls.isolated_creds = isolated_creds.IsolatedCreds(cls.__name__)
        if not cls.config.service_available.neutron:
            raise cls.skipException("Neutron support is required")
        if cls.config.compute.allow_tenant_isolation:
            creds = cls.isolated_creds.get_primary_creds()
            username, tenant_name, password = creds
            os = clients.Manager(username=username,
                                 password=password,
                                 tenant_name=tenant_name,
                                 interface=cls._interface)
        else:
            os = clients.Manager(interface=cls._interface)
        cls.network_cfg = os.config.network
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

    @classmethod
    def tearDownClass(cls):
        has_exception = False
        for vpnservice in cls.vpnservices:
            try:
                cls.client.delete_vpn_service(vpnservice['id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True

        for router in cls.routers:
            try:
                resp, body = cls.client.list_router_interfaces(router['id'])
                interfaces = body['ports']
                for i in interfaces:
                    cls.client.remove_router_interface_with_subnet_id(
                        router['id'], i['fixed_ips'][0]['subnet_id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True
            try:
                cls.client.delete_router(router['id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True

        for health_monitor in cls.health_monitors:
            try:
                cls.client.delete_health_monitor(health_monitor['id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True
        for member in cls.members:
            try:
                cls.client.delete_member(member['id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True
        for vip in cls.vips:
            try:
                cls.client.delete_vip(vip['id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True
        for pool in cls.pools:
            try:
                cls.client.delete_pool(pool['id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True
        for port in cls.ports:
            try:
                cls.client.delete_port(port['id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True
        for subnet in cls.subnets:
            try:
                cls.client.delete_subnet(subnet['id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True
        for network in cls.networks:
            try:
                cls.client.delete_network(network['id'])
            except Exception as exc:
                LOG.exception(exc)
                has_exception = True
        super(BaseNetworkTest, cls).tearDownClass()
        if has_exception:
            raise exceptions.TearDownException()

    @classmethod
    def create_network(cls, network_name=None):
        """Wrapper utility that returns a test network."""
        network_name = network_name or rand_name('test-network-')

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
    def create_pool(cls, name, lb_method, protocol, subnet):
        """Wrapper utility that returns a test pool."""
        resp, body = cls.client.create_pool(name, lb_method, protocol,
                                            subnet['id'])
        pool = body['pool']
        cls.pools.append(pool)
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
        resp, body = cls.client.create_vpn_service(
            subnet_id, router_id, admin_state_up=True,
            name=rand_name("vpnservice-"))
        vpnservice = body['vpnservice']
        cls.vpnservices.append(vpnservice)
        return vpnservice
