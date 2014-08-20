from tempest.api.network import base
from tempest import config
from tempest import test
from tempest.openstack.common import log as logging
from tempest.common.utils.data_utils import get_ipv6_addr_by_EUI64, \
    rand_mac_address
from tempest import exceptions

CONF = config.CONF
LOG = logging.getLogger(__name__)


class NetworksTestDHCPv6JSON(base.BaseNetworkTest):
    _interface = 'json'
    _ip_version = 6

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(NetworksTestDHCPv6JSON, cls).setUpClass()
        cls.network = cls.create_network()

    def _clean_network(self, **kwargs):
        if "ports" in kwargs:
            for port in kwargs["ports"]:
                self.client.delete_port(port['id'])
        if "router_interfaces" in kwargs:
            for interface in kwargs["router_interfaces"]:
                self.client.remove_router_interface_with_subnet_id(*interface)
        if "subnets" in kwargs:
            for subnet in kwargs["subnets"]:
                self.client.delete_subnet(subnet['id'])
        if "routers" in kwargs:
            for router in kwargs["routers"]:
                self.client.delete_router(router['id'])

    @test.attr(type='smoke')
    def test_dhcpv6_stateless_eui64(self):
        """When subnets configured with RAs SLAAC (AOM=100) and DHCP stateless
        (AOM=110) both for radvd and dnsmasq, port shall receive IP address
        calculated from its MAC.
        """
        for ra_mode, add_mode in (
                ('slaac', 'slaac'),
                ('dhcpv6-stateless', 'dhcpv6-stateless'),
        ):
            kwargs = {'ipv6_ra_mode': ra_mode,
                      'ipv6_address_mode': add_mode}
            subnet = self.create_subnet(self.network, **kwargs)
            self.subnets.pop()
            port_mac = rand_mac_address()
            port = self.create_port(self.network, mac_address=port_mac)
            self.ports.pop()
            real_ip = next(iter(port['fixed_ips']))['ip_address']
            eui_ip = get_ipv6_addr_by_EUI64(subnet['cidr'], port_mac).format()
            self._clean_network(ports=[port], subnets=[subnet])
            self.assertEqual(eui_ip, real_ip,
                             ('Real port IP is %s, but shall be %s when '
                              'ipv6_ra_mode=%s and ipv6_address_mode=%s') % (
                                 real_ip, eui_ip,
                                 ra_mode if ra_mode else "Off",
                                 add_mode if add_mode else "Off"))

    @test.attr(type='smoke')
    def test_dhcpv6_stateless_only_ra(self):
        """When subnets configured with RAs SLAAC (AOM=100) and DHCP stateless
        (AOM=110) for radvd and dnsmasq is not configured, port shall receive
        IP address calculated from its MAC and mask advertised from RAs
        """
        for ra_mode, add_mode in (
                ('slaac', None),
                ('dhcpv6-stateless', None),
        ):
            kwargs = {'ipv6_ra_mode': ra_mode,
                      'ipv6_address_mode': add_mode}
            kwargs = {k: v for k, v in kwargs.iteritems() if v}
            subnet = self.create_subnet(self.network, **kwargs)
            self.subnets.pop()
            router = self.create_router(router_name="router1",
                                        admin_state_up=True)
            self.create_router_interface(router['id'],
                                         subnet['id'])
            self.routers.pop()
            port_mac = rand_mac_address()
            port = self.create_port(self.network, mac_address=port_mac)
            self.ports.pop()
            real_ip = next(iter(port['fixed_ips']))['ip_address']
            eui_ip = get_ipv6_addr_by_EUI64(subnet['cidr'], port_mac).format()
            self._clean_network(ports=[port],
                                subnets=[subnet],
                                router_interfaces=[(router['id'],
                                                    subnet['id'])],
                                routers=[router])
            self.assertEqual(eui_ip, real_ip,
                             ('Real port IP is %s, but shall be %s when '
                              'ipv6_ra_mode=%s and ipv6_address_mode=%s') % (
                                 real_ip,
                                 eui_ip,
                                 ra_mode if ra_mode else "Off",
                                 add_mode if add_mode else "Off"))

    @test.attr(type='smoke')
    def test_dhcpv6_stateless_no_ra(self):
        """When subnets configured with dnsmasq SLAAC and DHCP stateless
        and there is no radvd, port shall receive IP address calculated
        from its MAC and mask of subnet.
        """
        for ra_mode, add_mode in (
                (None, 'slaac'),
                (None, 'dhcpv6-stateless'),
        ):
            kwargs = {'ipv6_ra_mode': ra_mode,
                      'ipv6_address_mode': add_mode}
            kwargs = {k: v for k, v in kwargs.iteritems() if v}
            subnet = self.create_subnet(self.network, **kwargs)
            self.subnets.pop()
            port_mac = rand_mac_address()
            port = self.create_port(self.network, mac_address=port_mac)
            self.ports.pop()
            real_ip = next(iter(port['fixed_ips']))['ip_address']
            eui_ip = get_ipv6_addr_by_EUI64(subnet['cidr'], port_mac).format()
            self._clean_network(ports=[port], subnets=[subnet])
            self.assertEqual(eui_ip, real_ip,
                             ('Real port IP %s equal to EUI-64 %s when '
                              'ipv6_ra_mode=%s and ipv6_address_mode=%s') % (
                                 real_ip, eui_ip,
                                 ra_mode if ra_mode else "Off",
                                 add_mode if add_mode else "Off"))

    @test.attr(type='smoke')
    def test_dhcpv6_invalid_options(self):
        """Different configurations for radvd and dnsmasq are not allowed"""
        for ra_mode, add_mode in (
                ('dhcpv6-stateless', 'dhcpv6-stateful'),
                ('dhcpv6-stateless', 'slaac'),
                ('slaac', 'dhcpv6-stateful'),
                ('dhcpv6-stateful', 'dhcpv6-stateless'),
                ('dhcpv6-stateful', 'slaac'),
                ('slaac', 'dhcpv6-stateless'),
        ):
            kwargs = {'ipv6_ra_mode': ra_mode,
                      'ipv6_address_mode': add_mode}
            self.assertRaises(exceptions.BadRequest,
                              self.create_subnet,
                              self.network,
                              **kwargs)

    @test.attr(type='smoke')
    def test_dhcpv6_stateless_no_ra_no_dhcp(self):
        """If no radvd option and no dnsmasq option is configured
        port shall receive IP from fixed IPs list of subnet.
        """
        subnet = self.create_subnet(self.network)
        self.subnets.pop()
        port_mac = rand_mac_address()
        port = self.create_port(self.network, mac_address=port_mac)
        self.ports.pop()
        real_ip = next(iter(port['fixed_ips']))['ip_address']
        eui_ip = get_ipv6_addr_by_EUI64(subnet['cidr'], port_mac).format()
        self._clean_network(ports=[port], subnets=[subnet])
        self.assertNotEqual(eui_ip, real_ip,
                            ('Real port IP %s equal to EUI-64 %s when '
                             'ipv6_ra_mode=Off and ipv6_address_mode=Off') % (
                                real_ip, eui_ip))


class NetworksTestDHCPv6XML(NetworksTestDHCPv6JSON):
    _interface = 'xml'
