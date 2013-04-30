# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import subprocess

import netaddr

from quantumclient.common import exceptions as exc
from tempest.common.utils.data_utils import rand_name
from tempest import test


class AttributeDict(dict):

    """
    Provide attribute access (dict.key) to dictionary values.
    """

    def __getattr__(self, name):
        """Allow attribute access for all keys in the dict."""
        if name in self:
            return self[name]
        return super(AttributeDict, self).__getattribute__(name)


class DeletableResource(AttributeDict):

    """
    Support deletion of quantum resources (networks, subnets) via a
    delete() method, as is supported by keystone and nova resources.
    """

    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        super(DeletableResource, self).__init__(*args, **kwargs)

    def __str__(self):
        return '<%s id="%s" name="%s">' % (self.__class__.__name__,
                                           self.id, self.name)

    def delete(self):
        raise NotImplemented()


class DeletableNetwork(DeletableResource):

    def delete(self):
        self.client.delete_network(self.id)


class DeletableSubnet(DeletableResource):

    _router_ids = set()

    def add_to_router(self, router_id):
        self._router_ids.add(router_id)
        body = dict(subnet_id=self.id)
        self.client.add_interface_router(router_id, body=body)

    def delete(self):
        for router_id in self._router_ids.copy():
            body = dict(subnet_id=self.id)
            self.client.remove_interface_router(router_id, body=body)
            self._router_ids.remove(router_id)
        self.client.delete_subnet(self.id)


class DeletableRouter(DeletableResource):

    def add_gateway(self, network_id):
        body = dict(network_id=network_id)
        self.client.add_gateway_router(self.id, body=body)

    def delete(self):
        self.client.remove_gateway_router(self.id)
        self.client.delete_router(self.id)


class DeletableFloatingIp(DeletableResource):

    def delete(self):
        self.client.delete_floatingip(self.id)


class DeletablePort(DeletableResource):

    def delete(self):
        self.client.delete_port(self.id)


class TestNetworkSmokeCommon(test.DefaultClientSmokeTest):
    """
    Base class for network smoke tests
    """

    @classmethod
    def check_preconditions(cls):
        if (cls.config.network.quantum_available):
            cls.enabled = True
            #verify that quantum_available is telling the truth
            try:
                cls.network_client.list_networks()
            except exc.EndpointNotFound:
                cls.enabled = False
                raise
        else:
            cls.enabled = False
            msg = 'Quantum not available'
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(TestNetworkSmokeCommon, cls).setUpClass()
        cfg = cls.config.network
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.username,
            cls.config.identity.password,
            cls.config.identity.tenant_name).tenant_id

    def _create_keypair(self, client, namestart='keypair-smoke-'):
        kp_name = rand_name(namestart)
        keypair = client.keypairs.create(kp_name)
        try:
            self.assertEqual(keypair.id, kp_name)
            self.set_resource(kp_name, keypair)
        except AttributeError:
            self.fail("Keypair object not successfully created.")
        return keypair

    def _create_security_group(self, client, namestart='secgroup-smoke-'):
        # Create security group
        sg_name = rand_name(namestart)
        sg_desc = sg_name + " description"
        secgroup = client.security_groups.create(sg_name, sg_desc)
        try:
            self.assertEqual(secgroup.name, sg_name)
            self.assertEqual(secgroup.description, sg_desc)
            self.set_resource(sg_name, secgroup)
        except AttributeError:
            self.fail("SecurityGroup object not successfully created.")

        # Add rules to the security group
        rulesets = [
            {
                # ssh
                'ip_protocol': 'tcp',
                'from_port': 22,
                'to_port': 22,
                'cidr': '0.0.0.0/0',
                'group_id': secgroup.id
            },
            {
                # ping
                'ip_protocol': 'icmp',
                'from_port': -1,
                'to_port': -1,
                'cidr': '0.0.0.0/0',
                'group_id': secgroup.id
            }
        ]
        for ruleset in rulesets:
            try:
                client.security_group_rules.create(secgroup.id, **ruleset)
            except Exception:
                self.fail("Failed to create rule in security group.")

        return secgroup

    def _create_network(self, tenant_id, namestart='network-smoke-'):
        name = rand_name(namestart)
        body = dict(
            network=dict(
                name=name,
                tenant_id=tenant_id,
            ),
        )
        result = self.network_client.create_network(body=body)
        network = DeletableNetwork(client=self.network_client,
                                   **result['network'])
        self.assertEqual(network.name, name)
        self.set_resource(name, network)
        return network

    def _list_networks(self):
        nets = self.network_client.list_networks()
        return nets['networks']

    def _list_subnets(self):
        subnets = self.network_client.list_subnets()
        return subnets['subnets']

    def _list_routers(self):
        routers = self.network_client.list_routers()
        return routers['routers']

    def _create_subnet(self, network, namestart='subnet-smoke-'):
        """
        Create a subnet for the given network within the cidr block
        configured for tenant networks.
        """
        cfg = self.config.network
        tenant_cidr = netaddr.IPNetwork(cfg.tenant_network_cidr)
        result = None
        # Repeatedly attempt subnet creation with sequential cidr
        # blocks until an unallocated block is found.
        for subnet_cidr in tenant_cidr.subnet(cfg.tenant_network_mask_bits):
            body = dict(
                subnet=dict(
                    ip_version=4,
                    network_id=network.id,
                    tenant_id=network.tenant_id,
                    cidr=str(subnet_cidr),
                ),
            )
            try:
                result = self.network_client.create_subnet(body=body)
                break
            except exc.QuantumClientException as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        self.assertIsNotNone(result, 'Unable to allocate tenant network')
        subnet = DeletableSubnet(client=self.network_client,
                                 **result['subnet'])
        self.assertEqual(subnet.cidr, str(subnet_cidr))
        self.set_resource(rand_name(namestart), subnet)
        return subnet

    def _create_port(self, network, namestart='port-quotatest-'):
        name = rand_name(namestart)
        body = dict(
            port=dict(name=name,
                      network_id=network.id,
                      tenant_id=network.tenant_id))
        try:
            result = self.network_client.create_port(body=body)
        except Exception as e:
            raise
        self.assertIsNotNone(result, 'Unable to allocate port')
        port = DeletablePort(client=self.network_client,
                             **result['port'])
        self.set_resource(name, port)
        return port

    def _create_server(self, client, network, name, key_name, security_groups):
        flavor_id = self.config.compute.flavor_ref
        base_image_id = self.config.compute.image_ref
        create_kwargs = {
            'nics': [
                {'net-id': network.id},
            ],
            'key_name': key_name,
            'security_groups': security_groups,
        }
        server = client.servers.create(name, base_image_id, flavor_id,
                                       **create_kwargs)
        try:
            self.assertEqual(server.name, name)
            self.set_resource(name, server)
        except AttributeError:
            self.fail("Server not successfully created.")
        test.status_timeout(self, client.servers, server.id, 'ACTIVE')
        # The instance retrieved on creation is missing network
        # details, necessitating retrieval after it becomes active to
        # ensure correct details.
        server = client.servers.get(server.id)
        self.set_resource(name, server)
        return server

    def _create_floating_ip(self, server, external_network_id):
        result = self.network_client.list_ports(device_id=server.id)
        ports = result.get('ports', [])
        self.assertEqual(len(ports), 1,
                         "Unable to determine which port to target.")
        port_id = ports[0]['id']
        body = dict(
            floatingip=dict(
                floating_network_id=external_network_id,
                port_id=port_id,
                tenant_id=server.tenant_id,
            )
        )
        result = self.network_client.create_floatingip(body=body)
        floating_ip = DeletableFloatingIp(client=self.network_client,
                                          **result['floatingip'])
        self.set_resource(rand_name('floatingip-'), floating_ip)
        return floating_ip

    def _ping_ip_address(self, ip_address):
        cmd = ['ping', '-c1', '-w1', ip_address]

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.wait()
            if proc.returncode == 0:
                return True

        # TODO(mnewby) Allow configuration of execution and sleep duration.
        return test.call_until_true(ping, 20, 1)
