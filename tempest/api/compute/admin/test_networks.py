# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

CONF = config.CONF


class NetworksTest(base.BaseComputeAdminTest):
    _api_version = 2

    """
    Tests Nova Networks API that usually requires admin privileges.
    API docs:
    http://developer.openstack.org/api-ref-compute-v2-ext.html#ext-os-networks
    """

    @classmethod
    def setUpClass(cls):
        super(NetworksTest, cls).setUpClass()
        cls.client = cls.os_adm.networks_client

    def test_get_network(self):
        resp, networks = self.client.list_networks()
        configured_network = [x for x in networks if x['label'] ==
                              CONF.compute.fixed_network_name]
        self.assertEqual(1, len(configured_network),
                         "{0} networks with label {1}".format(
                             len(configured_network),
                             CONF.compute.fixed_network_name))
        configured_network = configured_network[0]
        _, network = self.client.get_network(configured_network['id'])
        self.assertEqual(configured_network['label'], network['label'])

    def test_list_all_networks(self):
        _, networks = self.client.list_networks()
        # Check the configured network is in the list
        configured_network = CONF.compute.fixed_network_name
        self.assertIn(configured_network, [x['label'] for x in networks])
