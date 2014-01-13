# Copyright 2014 OpenStack Foundation
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
from tempest import test


class AllowedAddressPairTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the Neutron Allowed Address Pair API extension using the Tempest
    ReST client. The following API operations are tested with this extension:

        create port
        list ports
        update port
        show port

    v2.0 of the Neutron API is assumed. It is also assumed that the following
    options are defined in the [network-feature-enabled] section of
    etc/tempest.conf

        api_extensions
    """

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(AllowedAddressPairTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('allowed-address-pairs', 'network'):
            msg = "Allowed Address Pairs extension not enabled."
            raise cls.skipException(msg)
        cls.network = cls.create_network()
        cls.create_subnet(cls.network)
        port = cls.create_port(cls.network)
        cls.ip_address = port['fixed_ips'][0]['ip_address']
        cls.mac_address = port['mac_address']

    @test.attr(type='smoke')
    def test_create_list_port_with_address_pair(self):
        # Create port with allowed address pair attribute
        allowed_address_pairs = [{'ip_address': self.ip_address,
                                  'mac_address': self.mac_address}]
        resp, body = self.client.create_port(
            network_id=self.network['id'],
            allowed_address_pairs=allowed_address_pairs)
        self.assertEqual('201', resp['status'])
        port_id = body['port']['id']
        self.addCleanup(self.client.delete_port, port_id)

        # Confirm port was created with allowed address pair attribute
        resp, body = self.client.list_ports()
        self.assertEqual('200', resp['status'])
        ports = body['ports']
        port = [p for p in ports if p['id'] == port_id]
        msg = 'Created port not found in list of ports returned by Neutron'
        self.assertTrue(port, msg)
        self._confirm_allowed_address_pair(port[0], self.ip_address)

    def _confirm_allowed_address_pair(self, port, ip):
        msg = 'Port allowed address pairs should not be empty'
        self.assertTrue(port['allowed_address_pairs'], msg)
        ip_address = port['allowed_address_pairs'][0]['ip_address']
        mac_address = port['allowed_address_pairs'][0]['mac_address']
        self.assertEqual(ip_address, ip)
        self.assertEqual(mac_address, self.mac_address)


class AllowedAddressPairTestXML(AllowedAddressPairTestJSON):
    _interface = 'xml'
