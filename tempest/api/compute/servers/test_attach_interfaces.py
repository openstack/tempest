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

from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import config
from tempest import exceptions
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
        ifs = self.client.list_interfaces(server['id'])
        body = self.client.wait_for_interface_status(
            server['id'], ifs[0]['port_id'], 'ACTIVE')
        ifs[0]['port_state'] = body['port_state']
        return server, ifs

    def _test_create_interface(self, server):
        iface = self.client.create_interface(server['id'])
        iface = self.client.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface)
        return iface

    def _test_create_interface_by_network_id(self, server, ifs):
        network_id = ifs[0]['net_id']
        iface = self.client.create_interface(server['id'],
                                             network_id=network_id)
        iface = self.client.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface, network_id=network_id)
        return iface

    def _test_show_interface(self, server, ifs):
        iface = ifs[0]
        _iface = self.client.show_interface(server['id'],
                                            iface['port_id'])
        self._check_interface(iface, port_id=_iface['port_id'],
                              network_id=_iface['net_id'],
                              fixed_ip=_iface['fixed_ips'][0]['ip_address'],
                              mac_addr=_iface['mac_addr'])

    def _test_delete_interface(self, server, ifs):
        # NOTE(danms): delete not the first or last, but one in the middle
        iface = ifs[1]
        self.client.delete_interface(server['id'], iface['port_id'])
        _ifs = self.client.list_interfaces(server['id'])
        start = int(time.time())

        while len(ifs) == len(_ifs):
            time.sleep(self.build_interval)
            _ifs = self.client.list_interfaces(server['id'])
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

    @test.attr(type='smoke')
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

        _ifs = self.client.list_interfaces(server['id'])
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
        self.client.add_fixed_ip(server['id'], network_id)
        # Remove the fixed IP from server.
        server_detail = self.os.servers_client.get_server(
            server['id'])
        # Get the Fixed IP from server.
        fixed_ip = None
        for ip_set in server_detail['addresses']:
            for ip in server_detail['addresses'][ip_set]:
                if ip['OS-EXT-IPS:type'] == 'fixed':
                    fixed_ip = ip['addr']
                    break
            if fixed_ip is not None:
                break
        self.client.remove_fixed_ip(server['id'], fixed_ip)
