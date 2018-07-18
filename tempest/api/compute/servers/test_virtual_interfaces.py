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

import netaddr
import testtools

from tempest.api.compute import base
from tempest.common import utils
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions

CONF = config.CONF


# TODO(mriedem): Remove this test class once the nova queens branch goes into
# extended maintenance mode.
class VirtualInterfacesTestJSON(base.BaseV2ComputeTest):
    max_microversion = '2.43'

    depends_on_nova_network = True

    @classmethod
    def setup_credentials(cls):
        # This test needs a network and a subnet
        cls.set_network_resources(network=True, subnet=True)
        super(VirtualInterfacesTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(VirtualInterfacesTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(VirtualInterfacesTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until='ACTIVE')

    @decorators.idempotent_id('96c4e2ef-5e4d-4d7f-87f5-fed6dca18016')
    @utils.services('network')
    def test_list_virtual_interfaces(self):
        # Positive test:Should be able to GET the virtual interfaces list
        # for a given server_id

        if CONF.service_available.neutron:
            with testtools.ExpectedException(exceptions.BadRequest):
                self.client.list_virtual_interfaces(self.server['id'])
        else:
            output = self.client.list_virtual_interfaces(self.server['id'])
            virt_ifaces = output['virtual_interfaces']
            self.assertNotEmpty(virt_ifaces,
                                'Expected virtual interfaces, got 0 '
                                'interfaces.')
            for virt_iface in virt_ifaces:
                mac_address = virt_iface['mac_address']
                self.assertTrue(netaddr.valid_mac(mac_address),
                                "Invalid mac address detected. mac address: %s"
                                % mac_address)
