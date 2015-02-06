# Copyright 2014 Midokura SARL.
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

import yaml
import os

from tempest import clients
from tempest import exceptions
from neutronclient.common import exceptions as NeutronClientException
from tempest.common import credentials
from tempest.common.utils import data_utils
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest.openstack.common import log
from tempest.scenario import manager
from tempest.services.network import resources as net_resources

CONF = config.CONF
LOG = log.getLogger(__name__)


class AdvancedNetworkScenarioTest(manager.NetworkScenarioTest):
    """
    Base class for all Midokura network scenario tests
    """

    @classmethod
    def resource_setup(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(AdvancedNetworkScenarioTest, cls).resource_setup()

    """
    Creation Methods
    """
    def _create_security_group_rule_list(self, rule_dict=None, secgroup=None):
        client = self.network_client
        rules = []
        if not rule_dict:
            rulesets = []
        else:
            rulesets = rule_dict['security_group_rules']
        for ruleset in rulesets:
            for r_direction in ['ingress', 'egress']:
                ruleset['direction'] = r_direction
                try:
                    sg_rule = self._create_security_group_rule(
                        client=client, secgroup=secgroup, **ruleset)
                except NeutronClientException as ex:
                    if not (ex.status_code is 409 and 'Security group rule'
                            ' already exists' in ex.message):
                        raise ex
                else:
                    self.assertEqual(r_direction, sg_rule.direction)
                    rules.append(sg_rule)
        return rules

    def _assign_floating_ip(self, server, network_name):
        public_network_id = CONF.network.public_network_id
        server_ip = server['addresses'][network_name][0]['addr']
        port_id = self._get_custom_server_port_id(server,
                                                  ip_addr=server_ip)
        floating_ip = self.create_floating_ip(server,
                                              public_network_id,
                                              port_id=port_id)
        return floating_ip

    def _create_server(self, name, networks,
                       security_groups=None,
                       has_FIP=False):
        keypair = self.create_keypair()
        if security_groups is None:
            raise Exception("No security group")

        nics = list()
        for net in networks:
            nic = {'uuid': net['id']}
            nics.append(nic)
        create_kwargs = {
            'networks': nics,
            'key_name': keypair['name'],
            'security_groups': security_groups,
            'tenant_id': self.tenant_id,
        }
        server = self.create_server(name=name,
                                    create_kwargs=create_kwargs)
        FIP = None
        if has_FIP:
            # FIXME: when cirros is gone
            # We bind the fip to the first network, which is the first
            # nic on cirros image (the one attached to the "gateway network")
            FIP = self._assign_floating_ip(
                server=server,
                network_name=networks[0]['name'])

        return dict(server=server, keypair=keypair, FIP=FIP)

    """
    GateWay methods
    """
    def _set_access_point(self, tenant):
        """
        creates a server in a secgroup with rule allowing external ssh
        in order to access tenant internal network
        workaround ip namespace
        """
        networks = self._get_tenant_networks(tenant)
        network, _, _ = self.create_networks(tenant_id=tenant)
        # FIXME: look as soon as we change cirros image
        # cirros only ifup the first interface, thus we need to put
        # the "gateway" network at the front (so it's the first to ifup)
        networks.insert(0, network)

        name = 'access_point'
        name = data_utils.rand_name(name)

        self._create_security_group(tenant_id=tenant,
                                    namestart='gateway')
        security_groups = self._get_tenant_security_groups(tenant)
        serv_dict = self._create_server(name=name,
                                        networks=networks,
                                        security_groups=security_groups,
                                        has_FIP=True)

        tupla = (serv_dict['FIP'], serv_dict['server'])
        # FIXME: look as soon as we change cirros image
        self._fix_access_point(tupla,
                               serv_dict['keypair'])
        return serv_dict

    def _fix_access_point(self, access_point, keypair):
        """
        Hotfix for cirros images
        """
        access_point_ip, server = access_point
        private_key = keypair['private_key']
        ip = access_point_ip.floating_ip_address
        access_point_ssh = \
            remote_client.RemoteClient(
                server=ip,
                username='cirros',
                password='cubswin:)',
                pkey=private_key,
                )
        # fix for cirros image in order to enable a second eth
        for net in xrange(1, len(server['addresses'].keys())):
            if access_point_ssh.exec_command(
                    "cat /sys/class/net/eth{0}/operstate".format(net),
                    cmd_timeout=300) \
                    is not 'up\n':
                try:
                    result = access_point_ssh.exec_command(
                        "sudo /sbin/cirros-dhcpc up eth{0}".format(net),
                        cmd_timeout=300)
                    LOG.info(result)
                except exceptions.TimeoutException as inst:
                    LOG.warning("Silent TimeoutException!")
                    LOG.warning(inst)

    def build_gateway(self, tenant_id):
        return self._set_access_point(tenant_id)

    def setup_tunnel(self, tunnel_hops):
        """
        The details of the access point
        should be included in the tunnel_hops
        every element in the tunnel host is a
        tuple: (IP,PrivateKey)
        """
        GWS = []
        # last element is the final destination, which
        # is be passed tp the remote_client separately
        for host in tunnel_hops[:-1]:
            gw_host = {
                "username": "cirros",
                "ip": host[0],
                "password": "cubswin:)",
                "pkey": host[1],
                "key_filename": None
            }
            GWS.append(gw_host)

        ssh_client = remote_client.RemoteClient(
            server=tunnel_hops[-1][0],
            username='cirros',
            password='cubswin:)',
            pkey=tunnel_hops[-1][1],
            gws=GWS
        )
        return ssh_client

    """
    Get Methods
    """
    def _get_tenant(self, tenant):
        iso_creds = credentials.get_isolated_credentials(tenant)
        self.addCleanup(iso_creds.clear_isolated_creds)
        # Get admin credentials to be able to create resources
        tenant_admin_creds = iso_creds.get_credentials('admin')
        return tenant_admin_creds

    def _get_tenant_security_groups(self, tenant=None):
        if not tenant:
            tenant = self.tenant_id
        client = self.network_client
        sgs = client.list_security_groups(tenant_id=tenant)
        return sgs['security_groups']

    def _get_tenant_networks(self, tenant=None):
        if not tenant:
            tenant = self.tenant_id
        client = self.network_client
        nets = client.list_networks(tenant_id=tenant)
        return nets['networks']

    def _get_tenant_routers(self, tenant=None):
        if not tenant:
            tenant = self.tenant_id
        client = self.network_client
        routers = client.list_routers(tenant_id=tenant)
        return routers['routers']

    def _get_custom_server_port_id(self, server, ip_addr=None):
        ports = self._list_ports(device_id=server['id'])
        if ip_addr:
            for port in ports:
                if port['fixed_ips'][0]['ip_address'] == ip_addr:
                    return port['id']
        self.assertEqual(len(ports), 1,
                         "Unable to determine which port to target.")
        return ports[0]['id']

    def _get_tenant_router_by_name(self, r_name):
        routers = self._get_tenant_routers()
        d_router = filter(lambda x: x['name'].startswith(r_name), routers)[0]
        return net_resources.DeletableRouter(**d_router)

    def _get_network_by_name(self, net_name):
        nets = self._get_tenant_networks(tenant=self.tenant_id)
        return filter(lambda x: x['name'].startswith(net_name), nets)

    def _get_security_group_by_name(self, sg_name):
        sgs = self._get_tenant_security_groups(tenant=self.tenant_id)
        sg = filter(lambda x: x['name'].startswith(sg_name), sgs)[0]
        return net_resources.DeletableSecurityGroup(**sg)

    """
    Tool methods
    """
    def set_context(self, credentials):
        # TODO: we may need to get other clients to avoid auth problems
        self.mymanager = clients.Manager(credentials=credentials)
        self.floating_ips_client = self.mymanager.floating_ips_client
        self.keypairs_client = self.mymanager.keypairs_client
        self.security_groups_client = self.mymanager.security_groups_client
        self.servers_client = self.mymanager.servers_client
        self.interface_client = self.mymanager.interfaces_client
        self.network_client = self.mymanager.network_client
        self.networks_client = self.mymanager.networks_client

    def _toggle_dhcp(self, subnet_id, enable=False):
        result = self.network_client.update_subnet(subnet_id,
                                                   enable_dhcp=enable)
        subnet = result["subnet"]
        self.assertEqual(subnet["enable_dhcp"], enable)
        LOG.debug(result)

    def _ping_through_gateway(self, hops, destination, should_succed=True):
        LOG.info("Trying to ping between %s and %s"
                 % (hops[-1][0], destination[0]))
        ssh_client = self.setup_tunnel(hops)
        self.assertTrue(self._check_remote_connectivity(ssh_client,
                                                        destination[0],
                                                        should_succed))

    def _ssh_through_gateway(self, origin, destination):
        try:
            origin.append(destination)
            ssh_client = self.setup_tunnel(origin)
            try:
                result = ssh_client.get_ip_list()
                LOG.info(result)
                self.assertIn(destination[0], result)
            except exceptions.SSHExecCommandFailed as e:
                LOG.info(e.args)
        except Exception as inst:
            LOG.info(inst.args)
            raise

    def _locate_file(self, path):
        realpath = os.getcwd()
        for root, dirs, _ in os.walk(realpath):
            if path in dirs:
                return os.path.join(root, path)
    """
    YAML parsing methods
    """
    def _setup_topology(self, topology, tenant_id=None, tenant_name=None):
        if tenant_id:
            self.tenant_id = tenant_id
        networks = [n for n in topology['networks']]
        for network in networks:
            net = self._create_network(client=self.network_client,
                                       tenant_id=self.tenant_id,
                                       namestart=network['name'])
            for subnet in network['subnets']:
                routers = []
                for router in subnet['routers']:
                    router_names = [r['name'] for r in
                                    self._get_tenant_routers()]
                    if not any(map(lambda x: router['name'] in x,
                               router_names)):
                        if router['public']:
                            router = self._get_router(
                                client=self.network_client,
                                tenant_id=self.tenant_id)
                        else:
                            router = self._create_router(
                                namestart=router['name'],
                                tenant_id=self.tenant_id)
                    else:
                        router = \
                            self._get_tenant_router_by_name(router['name'])
                    routers.append(router)
                subnet_dic = \
                    dict(
                        name=subnet['name'],
                        ip_version=4,
                        network_id=net.id,
                        tenant_id=self.tenant_id,
                        cidr=subnet['cidr'],
                        dns_nameservers=subnet['dns_nameservers'],
                        host_routes=subnet['host_routes'],
                    )
                subnet = self._create_subnet(network=net, **subnet_dic)

                for router in routers:
                    subnet.add_to_router(router.id)

        for secgroup in topology['security_groups']:
            sgroups = self._get_tenant_security_groups(self.tenant_id)
            if secgroup['name'] in [r['name'] for r in sgroups]:
                sg = filter(
                    lambda x: x['name'].startswith(secgroup['name']),
                    sgroups)[0]
            else:
                sg = self._create_empty_security_group(
                    tenant_id=self.tenant_id,
                    namestart=secgroup['name'])
                self._create_security_group_rule_list(
                    rule_dict=secgroup,
                    secgroup=sg)
        test_topology = []
        for server in topology['servers']:
            s_nets = []
            for snet in server['networks']:
                s_nets.extend(self._get_network_by_name(snet['name']))
            s_sg = []
            for sg in server['security_groups']:
                s_sg.append(self._get_security_group_by_name(sg['name']))
            for x in range(server['quantity']):
                name = data_utils.rand_name('server-smoke-')
                s_server = self._create_server(name=name,
                                               networks=s_nets,
                                               security_groups=s_sg,
                                               has_FIP=server['floating_ip'])
                test_topology.append(s_server)

        if 'gateway' in topology.keys() and topology['gateway']:
            test_topology.append(self.build_gateway(self.tenant_id))

        return test_topology

    def setup_topology(self, yaml_topology):
        mpath = self._locate_file(yaml_topology.split('/')[-2])
        fullpath = os.path.join(mpath, yaml_topology.split('/')[-1])
        with open(fullpath, 'r') as yaml_topology:
            topology = yaml.load(yaml_topology)
            scenario = list()
            if 'tenants' in topology.keys():
                for tenant in topology['tenants']:
                    tenant_creds = self._get_tenant(tenant['name'])
                    self.set_context(tenant_creds)
                    topo = [x for x in topology['scenarios']
                            if x['name'] == tenant['scenario']][0]
                    scenario.append(dict(credentials=tenant_creds,
                                         servers_and_keys=self._setup_topology(
                                             topo,
                                             tenant_id=getattr(tenant_creds,
                                                               'tenant_id'))))
            else:
                scenario = self._setup_topology(topology)
        return scenario
