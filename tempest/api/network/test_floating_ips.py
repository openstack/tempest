# Copyright 2013 OpenStack Foundation
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

from tempest.api.network import base
from tempest.common import utils
from tempest.common.utils import data_utils
from tempest.common.utils import net_utils
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators

CONF = config.CONF


class FloatingIPTestJSON(base.BaseNetworkTest):
    """Tests the following operations in the Neutron API:

        Create a Floating IP
        Update a Floating IP
        Delete a Floating IP
        List all Floating IPs
        Show Floating IP details
        Associate a Floating IP with a port and then delete that port
        Associate a Floating IP with a port and then with a port on another
        router

    v2.0 of the Neutron API is assumed. It is also assumed that the following
    options are defined in the [network] section of etc/tempest.conf:

        public_network_id which is the id for the external network present
    """

    @classmethod
    def skip_checks(cls):
        super(FloatingIPTestJSON, cls).skip_checks()
        if not utils.is_extension_enabled('router', 'network'):
            msg = "router extension not enabled."
            raise cls.skipException(msg)
        if not CONF.network.public_network_id:
            msg = "The public_network_id option must be specified."
            raise cls.skipException(msg)
        if not CONF.network_feature_enabled.floating_ips:
            raise cls.skipException("Floating ips are not available")

    @classmethod
    def resource_setup(cls):
        super(FloatingIPTestJSON, cls).resource_setup()
        cls.ext_net_id = CONF.network.public_network_id

        # Create network, subnet, router and add interface
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network, enable_dhcp=False)
        cls.router = cls.create_router(external_network_id=cls.ext_net_id)
        cls.create_router_interface(cls.router['id'], cls.subnet['id'])
        # Create two ports one each for Creation and Updating of floatingIP
        cls.ports = []
        for i in range(2):
            port = cls.create_port(cls.network)
            cls.ports.append(port)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('62595970-ab1c-4b7f-8fcc-fddfe55e8718')
    def test_create_list_show_update_delete_floating_ip(self):
        """Test create/list/show/update/delete floating ip"""
        # Creates a floating IP
        body = self.floating_ips_client.create_floatingip(
            floating_network_id=self.ext_net_id,
            port_id=self.ports[0]['id'])
        created_floating_ip = body['floatingip']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.floating_ips_client.delete_floatingip,
            created_floating_ip['id'])
        self.assertIsNotNone(created_floating_ip['id'])
        self.assertIsNotNone(created_floating_ip['project_id'])
        self.assertIsNotNone(created_floating_ip['floating_ip_address'])
        self.assertEqual(created_floating_ip['port_id'], self.ports[0]['id'])
        self.assertEqual(created_floating_ip['floating_network_id'],
                         self.ext_net_id)
        self.assertIn(created_floating_ip['fixed_ip_address'],
                      [ip['ip_address'] for ip in self.ports[0]['fixed_ips']])
        # Verifies the details of a floating_ip
        floating_ip = self.floating_ips_client.show_floatingip(
            created_floating_ip['id'])
        shown_floating_ip = floating_ip['floatingip']
        self.assertEqual(shown_floating_ip['id'], created_floating_ip['id'])
        self.assertEqual(shown_floating_ip['floating_network_id'],
                         self.ext_net_id)
        self.assertEqual(shown_floating_ip['project_id'],
                         created_floating_ip['project_id'])
        self.assertEqual(shown_floating_ip['floating_ip_address'],
                         created_floating_ip['floating_ip_address'])
        self.assertEqual(shown_floating_ip['port_id'], self.ports[0]['id'])

        # Verify the floating ip exists in the list of all floating_ips
        floating_ips = self.floating_ips_client.list_floatingips()
        floatingip_id_list = list()
        for f in floating_ips['floatingips']:
            floatingip_id_list.append(f['id'])
        self.assertIn(created_floating_ip['id'], floatingip_id_list)
        # Associate floating IP to the other port
        floating_ip = self.floating_ips_client.update_floatingip(
            created_floating_ip['id'],
            port_id=self.ports[1]['id'])
        updated_floating_ip = floating_ip['floatingip']
        self.assertEqual(updated_floating_ip['port_id'], self.ports[1]['id'])
        self.assertEqual(updated_floating_ip['fixed_ip_address'],
                         self.ports[1]['fixed_ips'][0]['ip_address'])
        self.assertEqual(updated_floating_ip['router_id'], self.router['id'])

        # Disassociate floating IP from the port
        floating_ip = self.floating_ips_client.update_floatingip(
            created_floating_ip['id'],
            port_id=None)
        updated_floating_ip = floating_ip['floatingip']
        self.assertIsNone(updated_floating_ip['port_id'])
        self.assertIsNone(updated_floating_ip['fixed_ip_address'])
        self.assertIsNone(updated_floating_ip['router_id'])

        # Explicity test deletion of floating IP
        self.floating_ips_client.delete_floatingip(created_floating_ip['id'])

    @decorators.idempotent_id('e1f6bffd-442f-4668-b30e-df13f2705e77')
    def test_floating_ip_delete_port(self):
        """Test deleting floating ip's port

        1. Create a floating ip
        2. Create a port
        3. Update the floating ip's port_id to the created port
        4. Delete the port
        5. Verify that the port details are cleared from the floating ip
        """
        # Create a floating IP
        body = self.floating_ips_client.create_floatingip(
            floating_network_id=self.ext_net_id)
        created_floating_ip = body['floatingip']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.floating_ips_client.delete_floatingip,
            created_floating_ip['id'])
        # Create a port
        port = self.ports_client.create_port(
            network_id=self.network['id'],
            name=data_utils.rand_name(self.__class__.__name__))
        created_port = port['port']
        floating_ip = self.floating_ips_client.update_floatingip(
            created_floating_ip['id'],
            port_id=created_port['id'])
        # Delete port
        self.ports_client.delete_port(created_port['id'])
        # Verifies the details of the floating_ip
        floating_ip = self.floating_ips_client.show_floatingip(
            created_floating_ip['id'])
        shown_floating_ip = floating_ip['floatingip']
        # Confirm the fields are back to None
        self.assertEqual(shown_floating_ip['id'], created_floating_ip['id'])
        self.assertIsNone(shown_floating_ip['port_id'])
        self.assertIsNone(shown_floating_ip['fixed_ip_address'])
        self.assertIsNone(shown_floating_ip['router_id'])

    @decorators.idempotent_id('1bb2f731-fe5a-4b8c-8409-799ade1bed4d')
    def test_floating_ip_update_different_router(self):
        """Test associating a floating ip to a port on different router"""
        # Associate a floating IP to a port on a router
        body = self.floating_ips_client.create_floatingip(
            floating_network_id=self.ext_net_id,
            port_id=self.ports[1]['id'])
        created_floating_ip = body['floatingip']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.floating_ips_client.delete_floatingip,
            created_floating_ip['id'])
        self.assertEqual(created_floating_ip['router_id'], self.router['id'])
        network_name = data_utils.rand_name(self.__class__.__name__)
        network2 = self.networks_client.create_network(
            name=network_name)['network']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.networks_client.delete_network,
            network2['id'])
        subnet2 = self.create_subnet(network2)
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.subnets_client.delete_subnet, subnet2['id'])
        router2 = self.create_router(external_network_id=self.ext_net_id)
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.routers_client.delete_router, router2['id'])
        self.create_router_interface(router2['id'], subnet2['id'])
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.routers_client.remove_router_interface,
            router2['id'], subnet_id=subnet2['id'])
        port_other_router = self.create_port(network2)
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.ports_client.delete_port,
            port_other_router['id'])
        # Associate floating IP to the other port on another router
        floating_ip = self.floating_ips_client.update_floatingip(
            created_floating_ip['id'],
            port_id=port_other_router['id'])
        updated_floating_ip = floating_ip['floatingip']
        self.assertEqual(updated_floating_ip['router_id'], router2['id'])
        self.assertEqual(updated_floating_ip['port_id'],
                         port_other_router['id'])
        self.assertIsNotNone(updated_floating_ip['fixed_ip_address'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('36de4bd0-f09c-43e3-a8e1-1decc1ffd3a5')
    def test_create_floating_ip_specifying_a_fixed_ip_address(self):
        """Test creating floating ip with specified fixed ip"""
        body = self.floating_ips_client.create_floatingip(
            floating_network_id=self.ext_net_id,
            port_id=self.ports[1]['id'],
            fixed_ip_address=self.ports[1]['fixed_ips'][0]['ip_address'])
        created_floating_ip = body['floatingip']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.floating_ips_client.delete_floatingip,
            created_floating_ip['id'])
        self.assertIsNotNone(created_floating_ip['id'])
        self.assertEqual(created_floating_ip['fixed_ip_address'],
                         self.ports[1]['fixed_ips'][0]['ip_address'])
        floating_ip = self.floating_ips_client.update_floatingip(
            created_floating_ip['id'],
            port_id=None)
        self.assertIsNone(floating_ip['floatingip']['port_id'])

    @decorators.idempotent_id('45c4c683-ea97-41ef-9c51-5e9802f2f3d7')
    def test_create_update_floatingip_with_port_multiple_ip_address(self):
        """Test updating floating ip's fixed_ips to another ip of same port

        First we create a port with 2 fixed ips, then we create a floating ip
        with one of the fixed ips, and then we update the floating ip to
        another fixed ip of that port.
        """
        # Find out ips that can be used for tests
        list_ips = net_utils.get_unused_ip_addresses(
            self.ports_client,
            self.subnets_client,
            self.subnet['network_id'],
            self.subnet['id'],
            2)
        fixed_ips = [{'ip_address': list_ips[0]}, {'ip_address': list_ips[1]}]
        # Create port
        body = self.ports_client.create_port(
            network_id=self.network['id'],
            name=data_utils.rand_name(self.__class__.__name__),
            fixed_ips=fixed_ips)
        port = body['port']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.ports_client.delete_port, port['id'])
        # Create floating ip
        body = self.floating_ips_client.create_floatingip(
            floating_network_id=self.ext_net_id,
            port_id=port['id'],
            fixed_ip_address=list_ips[0])
        floating_ip = body['floatingip']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.floating_ips_client.delete_floatingip,
                        floating_ip['id'])
        self.assertIsNotNone(floating_ip['id'])
        self.assertEqual(floating_ip['fixed_ip_address'], list_ips[0])
        # Update floating ip
        body = self.floating_ips_client.update_floatingip(
            floating_ip['id'], port_id=port['id'],
            fixed_ip_address=list_ips[1])
        update_floating_ip = body['floatingip']
        self.assertEqual(update_floating_ip['fixed_ip_address'],
                         list_ips[1])
