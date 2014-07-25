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
from tempest.common.utils import data_utils
from tempest import test


class ExtraDHCPOptionsTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the following operations with the Extra DHCP Options Neutron API
    extension:

        port create
        port list
        port show
        port update

    v2.0 of the Neutron API is assumed. It is also assumed that the Extra
    DHCP Options extension is enabled in the [network-feature-enabled]
    section of etc/tempest.conf
    """

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(ExtraDHCPOptionsTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('extra_dhcp_opt', 'network'):
            msg = "Extra DHCP Options extension not enabled."
            raise cls.skipException(msg)
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.port = cls.create_port(cls.network)

    @test.attr(type='smoke')
    def test_create_list_port_with_extra_dhcp_options(self):
        # Create a port with Extra DHCP Options
        extra_dhcp_opts = [
            {'opt_value': 'pxelinux.0', 'opt_name': 'bootfile-name'},
            {'opt_value': '123.123.123.123', 'opt_name': 'tftp-server'},
            {'opt_value': '123.123.123.45', 'opt_name': 'server-ip-address'}
        ]
        resp, body = self.client.create_port(
            network_id=self.network['id'],
            extra_dhcp_opts=extra_dhcp_opts)
        self.assertEqual('201', resp['status'])
        port_id = body['port']['id']
        self.addCleanup(self.client.delete_port, port_id)

        # Confirm port created has Extra DHCP Options
        resp, body = self.client.list_ports()
        self.assertEqual('200', resp['status'])
        ports = body['ports']
        port = [p for p in ports if p['id'] == port_id]
        self.assertTrue(port)
        self._confirm_extra_dhcp_options(port[0], extra_dhcp_opts)

    @test.attr(type='smoke')
    def test_update_show_port_with_extra_dhcp_options(self):
        # Update port with extra dhcp options
        extra_dhcp_opts = [
            {'opt_value': 'pxelinux.0', 'opt_name': 'bootfile-name'},
            {'opt_value': '123.123.123.123', 'opt_name': 'tftp-server'},
            {'opt_value': '123.123.123.45', 'opt_name': 'server-ip-address'}
        ]
        name = data_utils.rand_name('new-port-name')
        resp, body = self.client.update_port(
            self.port['id'], name=name, extra_dhcp_opts=extra_dhcp_opts)
        self.assertEqual('200', resp['status'])

        # Confirm extra dhcp options were added to the port
        resp, body = self.client.show_port(self.port['id'])
        self.assertEqual('200', resp['status'])
        self._confirm_extra_dhcp_options(body['port'], extra_dhcp_opts)

    def _confirm_extra_dhcp_options(self, port, extra_dhcp_opts):
        retrieved = port['extra_dhcp_opts']
        self.assertEqual(len(retrieved), len(extra_dhcp_opts))
        for retrieved_option in retrieved:
            for option in extra_dhcp_opts:
                if (retrieved_option['opt_value'] == option['opt_value'] and
                    retrieved_option['opt_name'] == option['opt_name']):
                    break
            else:
                self.fail('Extra DHCP option not found in port %s' %
                          str(retrieved_option))
