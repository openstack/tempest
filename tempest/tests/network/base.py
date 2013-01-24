# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import testtools

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions


class BaseNetworkTest(testtools.TestCase):

    @classmethod
    def setUpClass(cls):
        os = clients.Manager()
        client = os.network_client
        config = os.config
        networks = []
        enabled = True

        # Validate that there is even an endpoint configured
        # for networks, and mark the attr for skipping if not
        try:
            client.list_networks()
        except exceptions.EndpointNotFound:
            enabled = False
            skip_msg = "No OpenStack Network API endpoint"
            raise cls.skipException(skip_msg)

    @classmethod
    def tearDownClass(cls):
        for network in cls.networks:
            cls.client.delete_network(network['id'])

    def create_network(self, network_name=None):
        """Wrapper utility that returns a test network."""
        network_name = network_name or rand_name('test-network')

        resp, body = self.client.create_network(network_name)
        network = body['network']
        self.networks.append(network)
        return network
