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

from tempest.api.compute import base
from tempest import config
from tempest import exceptions
from tempest.test import attr

import time

CONF = config.CONF


class AttachInterfacesTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        if not CONF.service_available.neutron:
            raise cls.skipException("Neutron is required")
        # This test class requires network and subnet
        cls.set_network_resources(network=True, subnet=True)
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
        resp, server = self.create_test_server(wait_until='ACTIVE')
        resp, ifs = self.client.list_interfaces(server['id'])
        self.assertEqual(200, resp.status)
        resp, body = self.client.wait_for_interface_status(
            server['id'], ifs[0]['port_id'], 'ACTIVE')
        ifs[0]['port_state'] = body['port_state']
        return server, ifs

    def _test_create_interface(self, server):
        resp, iface = self.client.create_interface(server['id'])
        self.assertEqual(200, resp.status)
        resp, iface = self.client.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface)
        return iface

    def _test_create_interface_by_network_id(self, server, ifs):
        network_id = ifs[0]['net_id']
        resp, iface = self.client.create_interface(server['id'],
                                                   network_id=network_id)
        self.assertEqual(200, resp.status)
        resp, iface = self.client.wait_for_interface_status(
            server['id'], iface['port_id'], 'ACTIVE')
        self._check_interface(iface, network_id=network_id)
        return iface

    def _test_show_interface(self, server, ifs):
        iface = ifs[0]
        resp, _iface = self.client.show_interface(server['id'],
                                                  iface['port_id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(iface, _iface)

    def _test_delete_interface(self, server, ifs):
        # NOTE(danms): delete not the first or last, but one in the middle
        iface = ifs[1]
        resp, _ = self.client.delete_interface(server['id'], iface['port_id'])
        self.assertEqual(202, resp.status)
        _ifs = self.client.list_interfaces(server['id'])[1]
        start = int(time.time())

        while len(ifs) == len(_ifs):
            time.sleep(self.build_interval)
            _ifs = self.client.list_interfaces(server['id'])[1]
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

    @attr(type='smoke')
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
