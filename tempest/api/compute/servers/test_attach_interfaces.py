# Copyright 2013 IBM Corp.
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

import time

from tempest.api.compute import base
from tempest.common import compute
from tempest.common.utils import net_utils
from tempest.common import waiters
from tempest import config
from tempest import exceptions
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF


class AttachInterfacesTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(AttachInterfacesTestJSON, cls).skip_checks()
        if not CONF.service_available.neutron:
            raise cls.skipException("Neutron is required")
        if not CONF.compute_feature_enabled.interface_attach:
            raise cls.skipException("Interface attachment is not available.")

    @classmethod
    def setup_credentials(cls):
        # This test class requires network and subnet
        cls.set_network_resources(network=True, subnet=True)
        super(AttachInterfacesTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(AttachInterfacesTestJSON, cls).setup_clients()
        cls.client = cls.os.interfaces_client
        cls.networks_client = cls.os.networks_client
        cls.subnets_client = cls.os.subnets_client
        cls.ports_client = cls.os.ports_client
        cls.servers_client = cls.servers_client

    def wait_for_interface_status(self, server, port_id, status):
        """Waits for an interface to reach a given status."""
        body = (self.client.show_interface(server, port_id)
                ['interfaceAttachment'])
        interface_status = body['port_state']
        start = int(time.time())

        while(interface_status != status):
            time.sleep(self.build_interval)
            body = (self.client.show_interface(server, port_id)
                    ['interfaceAttachment'])
            interface_status = body['port_state']

            timed_out = int(time.time()) - start >= self.build_timeout

            if interface_status != status and timed_out:
                message = ('Interface %s failed to reach %s status '
                           '(current %s) within the required time (%s s).' %
                           (port_id, status, interface_status,
                            self.build_timeout))
                raise exceptions.TimeoutException(message)

        return body

    # TODO(mriedem): move this into a common waiters utility module
    def wait_for_port_detach(self, port_id):
        """Waits for the port's device_id to be unset.

        :param port_id: The id of the port being detached.
        :returns: The final port dict from the show_port response.
        """
        port = self.ports_client.show_port(port_id)['port']
        device_id = port['device_id']
        start = int(time.time())

        # NOTE(mriedem): Nova updates the port's device_id to '' rather than
        # None, but it's not contractual so handle Falsey either way.
        while device_id:
            time.sleep(self.build_interval)
            port = self.ports_client.show_port(port_id)['port']
            device_id = port['device_id']

            timed_out = int(time.time()) - start >= self.build_timeout

            if device_id and timed_out:
                message = ('Port %s failed to detach (device_id %s) within '
                           'the required time (%s s).' %
                           (port_id, device_id, self.build_timeout))
                raise exceptions.TimeoutException(message)

        return port

    def _check_interface(self, iface, port_id=None, network_id=None,
                         fixed_ip=None, mac_addr=None):
        self.assertIn('port_state', iface)
        if port_id:
            self.assertEqual(iface['port_id'], port_id)
        if network_id:
            self.assertEqual(iface['net_id'], network_id)
        if fixed_ip:
            self.assertEqual(iface['fixed_ips'][0]['ip_address'], fixed_ip)
        if mac_addr:
            self.assertEqual(iface['mac_addr'], mac_addr)

    def _create_server_get_interfaces(self):
        server = self.create_test_server(wait_until='ACTIVE')
        ifs = (self.client.list_interfaces(server['id'])
               ['interfaceAttachments'])
        body = self.wait_for_interface_status(
            server['id'], ifs[0]['port_id'], 'ACTIVE')
        ifs[0]['port_state'] = body['port_state']
        return server, ifs

    def _test_create_interface(self, server):
        iface = (self.client.create_interface(server['id'])
                 ['interfaceAttachment'])
        iface = self.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface)
        return iface

    def _test_create_interface_by_network_id(self, server, ifs):
        network_id = ifs[0]['net_id']
        iface = self.client.create_interface(
            server['id'], net_id=network_id)['interfaceAttachment']
        iface = self.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface, network_id=network_id)
        return iface

    def _test_create_interface_by_port_id(self, server, ifs):
        network_id = ifs[0]['net_id']
        port = self.ports_client.create_port(network_id=network_id)
        port_id = port['port']['id']
        self.addCleanup(self.ports_client.delete_port, port_id)
        iface = self.client.create_interface(
            server['id'], port_id=port_id)['interfaceAttachment']
        iface = self.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface, port_id=port_id)
        return iface

    def _test_create_interface_by_fixed_ips(self, server, ifs):
        network_id = ifs[0]['net_id']
        subnet_id = ifs[0]['fixed_ips'][0]['subnet_id']
        ip_list = net_utils.get_unused_ip_addresses(self.ports_client,
                                                    self.subnets_client,
                                                    network_id,
                                                    subnet_id,
                                                    1)

        fixed_ips = [{'ip_address': ip_list[0]}]
        iface = self.client.create_interface(
            server['id'], net_id=network_id,
            fixed_ips=fixed_ips)['interfaceAttachment']
        self.addCleanup(self.ports_client.delete_port, iface['port_id'])
        iface = self.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface, fixed_ip=ip_list[0])
        return iface

    def _test_show_interface(self, server, ifs):
        iface = ifs[0]
        _iface = self.client.show_interface(
            server['id'], iface['port_id'])['interfaceAttachment']
        self._check_interface(iface, port_id=_iface['port_id'],
                              network_id=_iface['net_id'],
                              fixed_ip=_iface['fixed_ips'][0]['ip_address'],
                              mac_addr=_iface['mac_addr'])

    def _test_delete_interface(self, server, ifs):
        # NOTE(danms): delete not the first or last, but one in the middle
        iface = ifs[1]
        self.client.delete_interface(server['id'], iface['port_id'])
        _ifs = (self.client.list_interfaces(server['id'])
                ['interfaceAttachments'])
        start = int(time.time())

        while len(ifs) == len(_ifs):
            time.sleep(self.build_interval)
            _ifs = (self.client.list_interfaces(server['id'])
                    ['interfaceAttachments'])
            timed_out = int(time.time()) - start >= self.build_timeout
            if len(ifs) == len(_ifs) and timed_out:
                message = ('Failed to delete interface within '
                           'the required time: %s sec.' % self.build_timeout)
                raise exceptions.TimeoutException(message)

        self.assertNotIn(iface['port_id'], [i['port_id'] for i in _ifs])
        return _ifs

    def _compare_iface_list(self, list1, list2):
        # NOTE(danms): port_state will likely have changed, so just
        # confirm the port_ids are the same at least
        list1 = [x['port_id'] for x in list1]
        list2 = [x['port_id'] for x in list2]

        self.assertEqual(sorted(list1), sorted(list2))

    @test.idempotent_id('73fe8f02-590d-4bf1-b184-e9ca81065051')
    @test.services('network')
    def test_create_list_show_delete_interfaces(self):
        server, ifs = self._create_server_get_interfaces()
        interface_count = len(ifs)
        self.assertTrue(interface_count > 0)
        self._check_interface(ifs[0])

        try:
            iface = self._test_create_interface(server)
        except lib_exc.BadRequest as e:
            msg = ('Multiple possible networks found, use a Network ID to be '
                   'more specific.')
            if not CONF.compute.fixed_network_name and e.message == msg:
                raise
        else:
            ifs.append(iface)

        iface = self._test_create_interface_by_network_id(server, ifs)
        ifs.append(iface)

        iface = self._test_create_interface_by_port_id(server, ifs)
        ifs.append(iface)

        iface = self._test_create_interface_by_fixed_ips(server, ifs)
        ifs.append(iface)

        _ifs = (self.client.list_interfaces(server['id'])
                ['interfaceAttachments'])
        self._compare_iface_list(ifs, _ifs)

        self._test_show_interface(server, ifs)

        _ifs = self._test_delete_interface(server, ifs)
        self.assertEqual(len(ifs) - 1, len(_ifs))

    @test.attr(type='smoke')
    @test.idempotent_id('c7e0e60b-ee45-43d0-abeb-8596fd42a2f9')
    @test.services('network')
    def test_add_remove_fixed_ip(self):
        # Add and Remove the fixed IP to server.
        server, ifs = self._create_server_get_interfaces()
        interface_count = len(ifs)
        self.assertTrue(interface_count > 0)
        self._check_interface(ifs[0])
        network_id = ifs[0]['net_id']
        self.servers_client.add_fixed_ip(server['id'], networkId=network_id)
        # Remove the fixed IP from server.
        server_detail = self.os.servers_client.show_server(
            server['id'])['server']
        # Get the Fixed IP from server.
        fixed_ip = None
        for ip_set in server_detail['addresses']:
            for ip in server_detail['addresses'][ip_set]:
                if ip['OS-EXT-IPS:type'] == 'fixed':
                    fixed_ip = ip['addr']
                    break
            if fixed_ip is not None:
                break
        self.servers_client.remove_fixed_ip(server['id'], address=fixed_ip)

    @decorators.skip_because(bug='1607714')
    @test.idempotent_id('2f3a0127-95c7-4977-92d2-bc5aec602fb4')
    def test_reassign_port_between_servers(self):
        """Tests the following:

        1. Create a port in Neutron.
        2. Create two servers in Nova.
        3. Attach the port to the first server.
        4. Detach the port from the first server.
        5. Attach the port to the second server.
        6. Detach the port from the second server.
        """
        network = self.get_tenant_network()
        network_id = network['id']
        port = self.ports_client.create_port(network_id=network_id)
        port_id = port['port']['id']
        self.addCleanup(self.ports_client.delete_port, port_id)

        # create two servers
        _, servers = compute.create_test_server(
            self.os, tenant_network=network, wait_until='ACTIVE', min_count=2)
        # add our cleanups for the servers since we bypassed the base class
        for server in servers:
            self.addCleanup(waiters.wait_for_server_termination,
                            self.servers_client, server['id'])
            self.addCleanup(self.servers_client.delete_server, server['id'])

        for server in servers:
            # attach the port to the server
            iface = self.client.create_interface(
                server['id'], port_id=port_id)['interfaceAttachment']
            self._check_interface(iface, port_id=port_id)

            # detach the port from the server; this is a cast in the compute
            # API so we have to poll the port until the device_id is unset.
            self.client.delete_interface(server['id'], port_id)
            self.wait_for_port_detach(port_id)
