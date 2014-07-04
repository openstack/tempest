# Copyright 2014 Mirantis.inc
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


import tempfile
import time
import urllib2

from tempest.api.network import common as net_common
from tempest.common import commands
from tempest import config
from tempest import exceptions
from tempest.scenario import manager
from tempest import test

config = config.CONF


class TestLoadBalancerBasic(manager.NetworkScenarioTest):

    """
    This test checks basic load balancing.

    The following is the scenario outline:
    1. Create an instance
    2. SSH to the instance and start two servers
    3. Create a load balancer with two members and with ROUND_ROBIN algorithm
       associate the VIP with a floating ip
    4. Send 10 requests to the floating ip and check that they are shared
       between the two servers and that both of them get equal portions
    of the requests
    """

    @classmethod
    def check_preconditions(cls):
        super(TestLoadBalancerBasic, cls).check_preconditions()
        cfg = config.network
        if not test.is_extension_enabled('lbaas', 'network'):
            msg = 'LBaaS Extension is not enabled'
            cls.enabled = False
            raise cls.skipException(msg)
        if not (cfg.tenant_networks_reachable or cfg.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(TestLoadBalancerBasic, cls).setUpClass()
        cls.check_preconditions()
        cls.servers_keypairs = {}
        cls.members = []
        cls.floating_ips = {}
        cls.server_ips = {}
        cls.port1 = 80
        cls.port2 = 88

    def setUp(self):
        super(TestLoadBalancerBasic, self).setUp()
        self.server_ips = {}
        self.server_fixed_ips = {}
        self._create_security_group()

    def _create_security_group(self):
        self.security_group = self._create_security_group_neutron(
            tenant_id=self.tenant_id)
        self._create_security_group_rules_for_port(self.port1)
        self._create_security_group_rules_for_port(self.port2)

    def _create_security_group_rules_for_port(self, port):
        rule = {
            'direction': 'ingress',
            'protocol': 'tcp',
            'port_range_min': port,
            'port_range_max': port,
        }
        self._create_security_group_rule(
            client=self.network_client,
            secgroup=self.security_group,
            tenant_id=self.tenant_id,
            **rule)

    def _create_server(self, name):
        keypair = self.create_keypair(name='keypair-%s' % name)
        security_groups = [self.security_group.name]
        net = self._list_networks(tenant_id=self.tenant_id)[0]
        create_kwargs = {
            'nics': [
                {'net-id': net['id']},
            ],
            'key_name': keypair.name,
            'security_groups': security_groups,
        }
        server = self.create_server(name=name,
                                    create_kwargs=create_kwargs)
        self.servers_keypairs[server.id] = keypair
        if (config.network.public_network_id and not
                config.network.tenant_networks_reachable):
            public_network_id = config.network.public_network_id
            floating_ip = self._create_floating_ip(
                server, public_network_id)
            self.floating_ips[floating_ip] = server
            self.server_ips[server.id] = floating_ip.floating_ip_address
        else:
            self.server_ips[server.id] = server.networks[net['name']][0]
        self.server_fixed_ips[server.id] = server.networks[net['name']][0]
        self.assertTrue(self.servers_keypairs)
        return server

    def _create_servers(self):
        for count in range(2):
            self._create_server(name=("server%s" % (count + 1)))
        self.assertEqual(len(self.servers_keypairs), 2)

    def _start_servers(self):
        """
        Start two backends

        1. SSH to the instance
        2. Start two http backends listening on ports 80 and 88 respectively
        """

        for server_id, ip in self.server_ips.iteritems():
            private_key = self.servers_keypairs[server_id].private_key
            server_name = self.compute_client.servers.get(server_id).name
            username = config.scenario.ssh_user
            ssh_client = self.get_remote_client(
                server_or_ip=ip,
                private_key=private_key)

            # Write a backend's responce into a file
            resp = """echo -ne "HTTP/1.1 200 OK\r\nContent-Length: 7\r\n""" \
                   """Connection: close\r\nContent-Type: text/html; """ \
                   """charset=UTF-8\r\n\r\n%s"; cat >/dev/null"""

            with tempfile.NamedTemporaryFile() as script:
                script.write(resp % server_name)
                script.flush()
                with tempfile.NamedTemporaryFile() as key:
                    key.write(private_key)
                    key.flush()
                    commands.copy_file_to_host(script.name,
                                               "/tmp/script1",
                                               ip,
                                               username, key.name)

            # Start netcat
            start_server = """sudo nc -ll -p %(port)s -e sh """ \
                           """/tmp/%(script)s &"""
            cmd = start_server % {'port': self.port1,
                                  'script': 'script1'}
            ssh_client.exec_command(cmd)

            if len(self.server_ips) == 1:
                with tempfile.NamedTemporaryFile() as script:
                    script.write(resp % 'server2')
                    script.flush()
                    with tempfile.NamedTemporaryFile() as key:
                        key.write(private_key)
                        key.flush()
                        commands.copy_file_to_host(script.name,
                                                   "/tmp/script2", ip,
                                                   username, key.name)
                cmd = start_server % {'port': self.port2,
                                      'script': 'script2'}
                ssh_client.exec_command(cmd)

    def _check_connection(self, check_ip, port=80):
        def try_connect(ip, port):
            try:
                resp = urllib2.urlopen("http://{0}:{1}/".format(ip, port))
                if resp.getcode() == 200:
                    return True
                return False
            except IOError:
                return False
        timeout = config.compute.ping_timeout
        start = time.time()
        while not try_connect(check_ip, port):
            if (time.time() - start) > timeout:
                message = "Timed out trying to connect to %s" % check_ip
                raise exceptions.TimeoutException(message)

    def _create_pool(self):
        """Create a pool with ROUND_ROBIN algorithm."""
        # get tenant subnet and verify there's only one
        subnet = self._list_subnets(tenant_id=self.tenant_id)[0]
        self.subnet = net_common.DeletableSubnet(client=self.network_client,
                                                 **subnet)
        self.pool = super(TestLoadBalancerBasic, self)._create_pool(
            lb_method='ROUND_ROBIN',
            protocol='HTTP',
            subnet_id=self.subnet.id)
        self.assertTrue(self.pool)

    def _create_members(self):
        """
        Create two members.

        In case there is only one server, create both members with the same ip
        but with different ports to listen on.
        """

        for server_id, ip in self.server_fixed_ips.iteritems():
            if len(self.server_fixed_ips) == 1:
                member1 = self._create_member(address=ip,
                                              protocol_port=self.port1,
                                              pool_id=self.pool.id)
                member2 = self._create_member(address=ip,
                                              protocol_port=self.port2,
                                              pool_id=self.pool.id)
                self.members.extend([member1, member2])
            else:
                member = self._create_member(address=ip,
                                             protocol_port=self.port1,
                                             pool_id=self.pool.id)
                self.members.append(member)
        self.assertTrue(self.members)

    def _assign_floating_ip_to_vip(self, vip):
        public_network_id = config.network.public_network_id
        port_id = vip.port_id
        floating_ip = self._create_floating_ip(vip, public_network_id,
                                               port_id=port_id)
        self.floating_ips.setdefault(vip.id, [])
        self.floating_ips[vip.id].append(floating_ip)

    def _create_load_balancer(self):
        self._create_pool()
        self._create_members()
        self.vip = self._create_vip(protocol='HTTP',
                                    protocol_port=80,
                                    subnet_id=self.subnet.id,
                                    pool_id=self.pool.id)
        self.status_timeout(NeutronRetriever(self.network_client,
                                             self.network_client.vip_path,
                                             net_common.DeletableVip),
                            self.vip.id,
                            expected_status='ACTIVE')
        if (config.network.public_network_id and not
                config.network.tenant_networks_reachable):
            self._assign_floating_ip_to_vip(self.vip)
            self.vip_ip = self.floating_ips[
                self.vip.id][0]['floating_ip_address']
        else:
            self.vip_ip = self.vip.address

        # Currently the ovs-agent is not enforcing security groups on the
        # vip port - see https://bugs.launchpad.net/neutron/+bug/1163569
        # However the linuxbridge-agent does, and it is necessary to add a
        # security group with a rule that allows tcp port 80 to the vip port.
        body = {'port': {'security_groups': [self.security_group.id]}}
        self.network_client.update_port(self.vip.port_id, body)

    def _check_load_balancing(self):
        """
        1. Send 10 requests on the floating ip associated with the VIP
        2. Check that the requests are shared between
           the two servers and that both of them get equal portions
           of the requests
        """

        self._check_connection(self.vip_ip)
        self._send_requests(self.vip_ip, set(["server1", "server2"]))

    def _send_requests(self, vip_ip, expected, num_req=10):
        count = 0
        while count < num_req:
            resp = []
            for i in range(len(self.members)):
                resp.append(
                    urllib2.urlopen(
                        "http://{0}/".format(vip_ip)).read())
            count += 1
            self.assertEqual(expected,
                             set(resp))

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_load_balancer_basic(self):
        self._create_server('server1')
        self._start_servers()
        self._create_load_balancer()
        self._check_load_balancing()


class NeutronRetriever(object):
    """
    Helper class to make possible handling neutron objects returned by GET
    requests as attribute dicts.

    Whet get() method is called, the returned dictionary is wrapped into
    a corresponding DeletableResource class which provides attribute access
    to dictionary values.

    Usage:
        This retriever is used to allow using status_timeout from
        tempest.manager with Neutron objects.
    """

    def __init__(self, network_client, path, resource):
        self.network_client = network_client
        self.path = path
        self.resource = resource

    def get(self, thing_id):
        obj = self.network_client.get(self.path % thing_id)
        return self.resource(client=self.network_client, **obj.values()[0])
