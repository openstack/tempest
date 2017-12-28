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

from tempest import config
from tempest import exceptions
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions as lib_exc
import tempest.test

CONF = config.CONF


class BaseNetworkTest(tempest.test.BaseTestCase):
    """Base class for the Neutron tests.

    Per the Neutron API Guide, API v1.x was removed from the source code tree
    (docs.openstack.org/api/openstack-network/2.0/content/Overview-d1e71.html)
    Therefore, v2.x of the Neutron API is assumed. It is also assumed that the
    following options are defined in the [network] section of etc/tempest.conf:

        project_network_cidr with a block of cidr's from which smaller blocks
        can be allocated for project networks

        project_network_mask_bits with the mask bits to be used to partition
        the block defined by project-network_cidr

    Finally, it is assumed that the following option is defined in the
    [service_available] section of etc/tempest.conf

        neutron as True
    """

    force_tenant_isolation = False
    credentials = ['primary']

    # Default to ipv4.
    _ip_version = 4

    @classmethod
    def skip_checks(cls):
        super(BaseNetworkTest, cls).skip_checks()
        if not CONF.service_available.neutron:
            raise cls.skipException("Neutron support is required")
        if cls._ip_version == 6 and not CONF.network_feature_enabled.ipv6:
            raise cls.skipException("IPv6 Tests are disabled.")

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these test.
        cls.set_network_resources()
        super(BaseNetworkTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(BaseNetworkTest, cls).setup_clients()
        cls.agents_client = cls.os_primary.network_agents_client
        cls.network_extensions_client =\
            cls.os_primary.network_extensions_client
        cls.networks_client = cls.os_primary.networks_client
        cls.routers_client = cls.os_primary.routers_client
        cls.subnetpools_client = cls.os_primary.subnetpools_client
        cls.subnets_client = cls.os_primary.subnets_client
        cls.ports_client = cls.os_primary.ports_client
        cls.quotas_client = cls.os_primary.network_quotas_client
        cls.floating_ips_client = cls.os_primary.floating_ips_client
        cls.security_groups_client = cls.os_primary.security_groups_client
        cls.security_group_rules_client = (
            cls.os_primary.security_group_rules_client)
        cls.network_versions_client = cls.os_primary.network_versions_client
        cls.service_providers_client = cls.os_primary.service_providers_client
        cls.tags_client = cls.os_primary.tags_client

    @classmethod
    def resource_setup(cls):
        super(BaseNetworkTest, cls).resource_setup()
        cls.subnets = []
        cls.ports = []
        cls.routers = []
        cls.ethertype = "IPv" + str(cls._ip_version)
        if cls._ip_version == 4:
            cls.cidr = netaddr.IPNetwork(CONF.network.project_network_cidr)
            cls.mask_bits = CONF.network.project_network_mask_bits
        elif cls._ip_version == 6:
            cls.cidr = netaddr.IPNetwork(CONF.network.project_network_v6_cidr)
            cls.mask_bits = CONF.network.project_network_v6_mask_bits

    @classmethod
    def create_network(cls, network_name=None, **kwargs):
        """Wrapper utility that returns a test network."""
        network_name = network_name or data_utils.rand_name(
            cls.__name__ + '-test-network')

        body = cls.networks_client.create_network(name=network_name, **kwargs)
        network = body['network']
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.networks_client.delete_network,
                                    network['id'])
        return network

    @classmethod
    def create_subnet(cls, network, gateway='', cidr=None, mask_bits=None,
                      ip_version=None, client=None, **kwargs):
        """Wrapper utility that returns a test subnet."""
        # allow tests to use admin client
        if not client:
            client = cls.subnets_client

        # The cidr and mask_bits depend on the ip version.
        ip_version = ip_version if ip_version is not None else cls._ip_version
        gateway_not_set = gateway == ''
        if ip_version == 4:
            cidr = cidr or netaddr.IPNetwork(CONF.network.project_network_cidr)
            mask_bits = mask_bits or CONF.network.project_network_mask_bits
        elif ip_version == 6:
            cidr = (cidr or
                    netaddr.IPNetwork(CONF.network.project_network_v6_cidr))
            mask_bits = mask_bits or CONF.network.project_network_v6_mask_bits
        # Find a cidr that is not in use yet and create a subnet with it
        for subnet_cidr in cidr.subnet(mask_bits):
            if gateway_not_set:
                gateway_ip = str(netaddr.IPAddress(subnet_cidr) + 1)
            else:
                gateway_ip = gateway
            try:
                body = client.create_subnet(
                    network_id=network['id'],
                    cidr=str(subnet_cidr),
                    ip_version=ip_version,
                    gateway_ip=gateway_ip,
                    **kwargs)
                break
            except lib_exc.BadRequest as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        else:
            message = 'Available CIDR for subnet creation could not be found'
            raise exceptions.BuildErrorException(message)
        subnet = body['subnet']
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.subnets_client.delete_subnet,
                                    subnet['id'])
        cls.subnets.append(subnet)
        return subnet

    @classmethod
    def create_port(cls, network, **kwargs):
        """Wrapper utility that returns a test port."""
        body = cls.ports_client.create_port(network_id=network['id'],
                                            **kwargs)
        port = body['port']
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.ports_client.delete_port, port['id'])
        cls.ports.append(port)
        return port

    @classmethod
    def update_port(cls, port, **kwargs):
        """Wrapper utility that updates a test port."""
        body = cls.ports_client.update_port(port['id'],
                                            **kwargs)
        return body['port']

    @classmethod
    def create_router(cls, router_name=None, admin_state_up=False,
                      external_network_id=None, enable_snat=None,
                      **kwargs):
        router_name = router_name or data_utils.rand_name(
            cls.__name__ + "-router")

        ext_gw_info = {}
        if external_network_id:
            ext_gw_info['network_id'] = external_network_id
        if enable_snat is not None:
            ext_gw_info['enable_snat'] = enable_snat
        body = cls.routers_client.create_router(
            name=router_name, external_gateway_info=ext_gw_info,
            admin_state_up=admin_state_up, **kwargs)
        router = body['router']
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.delete_router, router)
        cls.routers.append(router)
        return router

    @classmethod
    def create_floatingip(cls, external_network_id):
        """Wrapper utility that returns a test floating IP."""
        body = cls.floating_ips_client.create_floatingip(
            floating_network_id=external_network_id)
        fip = body['floatingip']
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.floating_ips_client.delete_floatingip,
                                    fip['id'])
        return fip

    @classmethod
    def create_router_interface(cls, router_id, subnet_id):
        """Wrapper utility that returns a router interface."""
        interface = cls.routers_client.add_router_interface(
            router_id, subnet_id=subnet_id)
        return interface

    @classmethod
    def delete_router(cls, router):
        body = cls.ports_client.list_ports(device_id=router['id'])
        interfaces = body['ports']
        for i in interfaces:
            test_utils.call_and_ignore_notfound_exc(
                cls.routers_client.remove_router_interface, router['id'],
                subnet_id=i['fixed_ips'][0]['subnet_id'])
        cls.routers_client.delete_router(router['id'])


class BaseAdminNetworkTest(BaseNetworkTest):

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(BaseAdminNetworkTest, cls).setup_clients()
        cls.admin_agents_client = cls.os_admin.network_agents_client
        cls.admin_networks_client = cls.os_admin.networks_client
        cls.admin_routers_client = cls.os_admin.routers_client
        cls.admin_subnets_client = cls.os_admin.subnets_client
        cls.admin_ports_client = cls.os_admin.ports_client
        cls.admin_quotas_client = cls.os_admin.network_quotas_client
        cls.admin_floating_ips_client = cls.os_admin.floating_ips_client
        cls.admin_metering_labels_client = cls.os_admin.metering_labels_client
        cls.admin_metering_label_rules_client = (
            cls.os_admin.metering_label_rules_client)
