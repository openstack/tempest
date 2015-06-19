# Copyright 2015 Cisco Systems, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from oslo_log import log as logging
from tempest import config
from tempest import exceptions as tempest_exceptions
from tempest.scenario import manager
from tempest import test
import tempest_lib
import time

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestNewComputeNodeOnline(manager.NetworkScenarioTest):
    @classmethod
    def resource_setup(cls):
        super(TestNewComputeNodeOnline, cls).resource_setup()
        compute_nodes = cls.admin_manager.hosts_client.list_hosts()
        cls.avail_zone_name = 'connect-avail-{}'
        cls.num_networks = 3
        cls.compute_nodes = map(lambda x: x.get('host_name'),
                                filter(lambda y: y.get('service') == 'compute',
                                       compute_nodes))

    def _boot_server(self, zone_id, network):

        server_kwargs = {
            'networks': [{'uuid': network['id']}],
            'key_name': self.key_pair['name'],
            'security_groups': [{'name': self.sec_group['name']}],
            'availability_zone': self.avail_zone_name.format(zone_id)
        }
        server = self.create_server(name='srv-avail-zone-{}'.format(zone_id),
                                    create_kwargs=server_kwargs)
        floating_ip = self.create_floating_ip(server,
                                              CONF.network.public_network_id)
        return floating_ip

    def _prepare_test_environment(self):
        for idx, node in enumerate(self.compute_nodes):
            create_kwargs = {
                'name': 'connect-agg-{}'.format(idx),
                'availability_zone': self.avail_zone_name.format(idx)
            }
            aggregate = self.admin_manager.aggregates_client. \
                create_aggregate(**create_kwargs)
            self.addCleanup(self.admin_manager.aggregates_client.
                            delete_aggregate, aggregate['id'])
            self.admin_manager.aggregates_client.add_host(
                aggregate['id'], node)
            self.addCleanup(self.admin_manager.aggregates_client.remove_host,
                            aggregate['id'], node)
        host_to_shutdown = self.compute_nodes[-1]
        self.admin_manager.services_client.disable_service(
            host_to_shutdown, 'nova-compute')
        try:
            self.admin_manager.hosts_client.shutdown_host(host_to_shutdown)
        except tempest_lib.exceptions.NotImplemented as ex:
            LOG.warning("Can't shutdown compute node: {}".format(ex))
        self.key_pair = self.create_keypair()
        self.sec_group = self._create_security_group()
        networks = self._list_networks(tenant_id=self.tenant_id)
        self.assertNotEmpty(networks)
        self.public_network = networks[0]
        self.old_ips = []
        self.nets = []
        routers = self._list_routers(tenant_id=self.tenant_id)
        self.assertNotEmpty(routers)
        router = routers[0]
        for idx in range(self.num_networks):
            network = self._create_network(tenant_id=self.tenant_id)
            subnet = self._create_subnet(network)
            self.network_client.add_router_interface_with_subnet_id(
                router['id'], subnet['id']
            )
            self.addCleanup(
                self.network_client.remove_router_interface_with_subnet_id,
                router['id'], subnet['id'])
            self.nets.append(network)
            zone_id = idx % 2
            floating_ip = self._boot_server(zone_id, network)
            self.old_ips.append(floating_ip)

        try:
            self.admin_manager.hosts_client.startup_host(host_to_shutdown)
        except tempest_lib.exceptions.NotImplemented as ex:
            LOG.warning("Can't startup compute host: {}".format(ex))

        self.admin_manager.services_client.enable_service(
            host_to_shutdown, 'nova-compute')
        self.new_ips = []
        for net in self.nets:
            floating_ip = self._boot_server(2, net)
            self.new_ips.append(floating_ip)

    @test.idempotent_id('7da90f8c-b716-426f-ae44-ca2f266272eb')
    @test.services('compute', 'network')
    def test_connectivity_between_servers(self):
        """
            Get list of compute nodes
            if number less than 3 - skip test
            Put each compute node in own availability zone
            disable one of compute nodes
            boot vms with networks on available compute nodes.
            bring disabled compute node online
            boot new vms there and ping old vms
        """
        if len(self.compute_nodes) < 3:
            raise tempest_exceptions.InvalidConfiguration(
                "TestNewComputeNodesOnline."
                "test_connectivity_between_vms: "
                "Not enough compute nodes."
            )
        self._prepare_test_environment()
        time.sleep(60)
        for pair in zip(self.old_ips, self.new_ips):
            connect_old = self._ssh_to_server(pair[0].floating_ip_address,
                                              self.key_pair['private_key']
                                              )
            connect_old.ping_host(pair[1].fixed_ip_address)
            connect_new = self._ssh_to_server(pair[1].floating_ip_address,
                                              self.key_pair['private_key']
                                              )
            connect_new.ping_host(pair[0].fixed_ip_address)
