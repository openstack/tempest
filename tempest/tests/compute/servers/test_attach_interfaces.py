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

from tempest.tests.compute import base

import time


class AttachInterfacesTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        if not cls.config.network.quantum_available:
            raise cls.skipException("Quantum is required")
        super(AttachInterfacesTestJSON, cls).setUpClass()
        cls.client = cls.os.interfaces_client

    def _check_interface(self, iface, port_id=None, network_id=None,
                         fixed_ip=None):
        self.assertIn('port_state', iface)
        if port_id:
            self.assertEqual(iface['port_id'], port_id)
        if network_id:
            self.assertEqual(iface['net_id'], network_id)
        if fixed_ip:
            self.assertEqual(iface['fixed_ips'][0]['ip_address'], fixed_ip)

    def _create_server_get_interfaces(self):
        resp, server = self.create_server()
        self.os.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        resp, ifs = self.client.list_interfaces(server['id'])
        resp, body = self.client.wait_for_interface_status(
            server['id'], ifs[0]['port_id'], 'ACTIVE')
        ifs[0]['port_state'] = body['port_state']
        return server, ifs

    def _test_create_interface(self, server):
        resp, iface = self.client.create_interface(server['id'])
        resp, iface = self.client.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface)
        return iface

    def _test_create_interface_by_network_id(self, server, ifs):
        network_id = ifs[0]['net_id']
        resp, iface = self.client.create_interface(server['id'],
                                                   network_id=network_id)
        resp, iface = self.client.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface, network_id=network_id)
        return iface

    def _test_show_interface(self, server, ifs):
        iface = ifs[0]
        resp, _iface = self.client.show_interface(server['id'],
                                                  iface['port_id'])
        self.assertEqual(iface, _iface)

    def _test_delete_interface(self, server, ifs):
        # NOTE(danms): delete not the first or last, but one in the middle
        iface = ifs[1]
        self.client.delete_interface(server['id'], iface['port_id'])
        for i in range(0, 5):
            _r, _ifs = self.client.list_interfaces(server['id'])
            if len(ifs) != len(_ifs):
                break
            time.sleep(1)

        self.assertEqual(len(_ifs), len(ifs) - 1)
        for _iface in _ifs:
            self.assertNotEqual(iface['port_id'], _iface['port_id'])
        return _ifs

    def _compare_iface_list(self, list1, list2):
        # NOTE(danms): port_state will likely have changed, so just
        # confirm the port_ids are the same at least
        list1 = [x['port_id'] for x in list1]
        list2 = [x['port_id'] for x in list2]

        self.assertEqual(sorted(list1), sorted(list2))

    def test_create_list_show_delete_interfaces(self):
        server, ifs = self._create_server_get_interfaces()
        interface_count = len(ifs)
        self.assertTrue(interface_count > 0)
        self._check_interface(ifs[0])

        iface = self._test_create_interface(server)
        ifs.append(iface)

        iface = self._test_create_interface_by_network_id(server, ifs)
        ifs.append(iface)

        resp, _ifs = self.client.list_interfaces(server['id'])
        self._compare_iface_list(ifs, _ifs)

        self._test_show_interface(server, ifs)

        _ifs = self._test_delete_interface(server, ifs)
        self.assertEqual(len(ifs) - 1, len(_ifs))


class AttachInterfacesTestXML(AttachInterfacesTestJSON):
    _interface = 'xml'
