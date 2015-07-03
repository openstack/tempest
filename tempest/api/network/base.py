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
from oslo_log import log as logging
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest import config
from tempest import exceptions
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
        cls.client = cls.os.network_client

    @classmethod
    def resource_setup(cls):
        super(BaseNetworkTest, cls).resource_setup()
        cls.network_cfg = CONF.network
        cls.networks = []
        cls.subnets = []
        cls.ports = []
        cls.routers = []
        cls.floating_ips = []
        cls.metering_labels = []
        cls.metering_label_rules = []
        cls.ethertype = "IPv" + str(cls._ip_version)

    @classmethod
    def resource_cleanup(cls):
        if CONF.service_available.neutron:
            # Clean up floating IPs
            for floating_ip in cls.floating_ips:
                cls._try_delete_resource(cls.client.delete_floatingip,
                                         floating_ip['id'])

            # Clean up metering label rules
            for metering_label_rule in cls.metering_label_rules:
                cls._try_delete_resource(
                    cls.admin_client.delete_metering_label_rule,
                    metering_label_rule['id'])
            # Clean up metering labels
            for metering_label in cls.metering_labels:
                cls._try_delete_resource(
                    cls.admin_client.delete_metering_label,
                    metering_label['id'])
            # Clean up ports
            for port in cls.ports:
                cls._try_delete_resource(cls.client.delete_port,
                                         port['id'])
            # Clean up routers
            for router in cls.routers:
                cls._try_delete_resource(cls.delete_router,
                                         router)
            # Clean up subnets
            for subnet in cls.subnets:
                cls._try_delete_resource(cls.client.delete_subnet,
                                         subnet['id'])
            # Clean up networks
            for network in cls.networks:
                cls._try_delete_resource(cls.client.delete_network,
                                         network['id'])
        super(BaseNetworkTest, cls).resource_cleanup()

    @classmethod
    def _try_delete_resource(self, delete_callable, *args, **kwargs):
        """Cleanup resources in case of test-failure

        Some resources are explicitly deleted by the test.
        If the test failed to delete a resource, this method will execute
        the appropriate delete methods. Otherwise, the method ignores NotFound
        exceptions thrown for resources that were correctly deleted by the
        test.

        :param delete_callable: delete method
        :param args: arguments for delete method
        :param kwargs: keyword arguments for delete method
        """
        try:
            delete_callable(*args, **kwargs)
        # if resource is not found, this means it was deleted in the test
        except lib_exc.NotFound:
            pass

    @classmethod
    def create_network(cls, network_name=None):
        """Wrapper utility that returns a test network."""
        network_name = network_name or data_utils.rand_name('test-network-')

        body = cls.client.create_network(name=network_name)
        network = body['network']
        cls.networks.append(network)
        return network

    @classmethod
    def create_subnet(cls, network, gateway='', cidr=None, mask_bits=None,
                      ip_version=None, client=None, **kwargs):
        """Wrapper utility that returns a test subnet."""

        # allow tests to use admin client
        if not client:
            client = cls.client

        # The cidr and mask_bits depend on the ip version.
        ip_version = ip_version if ip_version is not None else cls._ip_version
        gateway_not_set = gateway == ''
        if ip_version == 4:
            cidr = cidr or netaddr.IPNetwork(CONF.network.tenant_network_cidr)
            mask_bits = mask_bits or CONF.network.tenant_network_mask_bits
        elif ip_version == 6:
            cidr = (
                cidr or netaddr.IPNetwork(CONF.network.tenant_network_v6_cidr))
            mask_bits = mask_bits or CONF.network.tenant_network_v6_mask_bits
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
        cls.subnets.append(subnet)
        return subnet

    @classmethod
    def create_port(cls, network, **kwargs):
        """Wrapper utility that returns a test port."""
        body = cls.client.create_port(network_id=network['id'],
                                      **kwargs)
        port = body['port']
        cls.ports.append(port)
        return port

    @classmethod
    def update_port(cls, port, **kwargs):
        """Wrapper utility that updates a test port."""
        body = cls.client.update_port(port['id'],
                                      **kwargs)
        return body['port']

    @classmethod
    def create_router(cls, router_name=None, admin_state_up=False,
                      external_network_id=None, enable_snat=None,
                      **kwargs):
        ext_gw_info = {}
        if external_network_id:
            ext_gw_info['network_id'] = external_network_id
        if enable_snat:
            ext_gw_info['enable_snat'] = enable_snat
        body = cls.client.create_router(
            router_name, external_gateway_info=ext_gw_info,
            admin_state_up=admin_state_up, **kwargs)
        router = body['router']
        cls.routers.append(router)
        return router

    @classmethod
    def create_floatingip(cls, external_network_id):
        """Wrapper utility that returns a test floating IP."""
        body = cls.client.create_floatingip(
            floating_network_id=external_network_id)
        fip = body['floatingip']
        cls.floating_ips.append(fip)
        return fip

    @classmethod
    def create_router_interface(cls, router_id, subnet_id):
        """Wrapper utility that returns a router interface."""
        interface = cls.client.add_router_interface_with_subnet_id(
            router_id, subnet_id)
        return interface

    @classmethod
    def delete_router(cls, router):
        body = cls.client.list_router_interfaces(router['id'])
        interfaces = body['ports']
        for i in interfaces:
            try:
                cls.client.remove_router_interface_with_subnet_id(
                    router['id'], i['fixed_ips'][0]['subnet_id'])
            except lib_exc.NotFound:
                pass
        cls.client.delete_router(router['id'])


class BaseAdminNetworkTest(BaseNetworkTest):

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(BaseAdminNetworkTest, cls).setup_clients()
        cls.admin_client = cls.os_adm.network_client

    @classmethod
    def create_metering_label(cls, name, description):
        """Wrapper utility that returns a test metering label."""
        body = cls.admin_client.create_metering_label(
            description=description,
            name=data_utils.rand_name("metering-label"))
        metering_label = body['metering_label']
        cls.metering_labels.append(metering_label)
        return metering_label

    @classmethod
    def create_metering_label_rule(cls, remote_ip_prefix, direction,
                                   metering_label_id):
        """Wrapper utility that returns a test metering label rule."""
        body = cls.admin_client.create_metering_label_rule(
            remote_ip_prefix=remote_ip_prefix, direction=direction,
            metering_label_id=metering_label_id)
        metering_label_rule = body['metering_label_rule']
        cls.metering_label_rules.append(metering_label_rule)
        return metering_label_rule
