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
from tempest.lib import decorators

CONF = config.CONF


class NetworksTest(base.BaseV2ComputeAdminTest):
    """Tests Nova Networks API that usually requires admin privileges.

    API docs:
    https://developer.openstack.org/api-ref/compute/#networks-os-networks-deprecated
    """

    @classmethod
    def setup_clients(cls):
        super(NetworksTest, cls).setup_clients()
        cls.client = cls.os_admin.compute_networks_client

    @decorators.idempotent_id('d206d211-8912-486f-86e2-a9d090d1f416')
    def test_get_network(self):
        networks = self.client.list_networks()['networks']
        if CONF.compute.fixed_network_name:
            configured_network = [x for x in networks if x['label'] ==
                                  CONF.compute.fixed_network_name]
            self.assertEqual(1, len(configured_network),
                             "{0} networks with label {1}".format(
                                 len(configured_network),
                                 CONF.compute.fixed_network_name))
        elif CONF.network.public_network_id:
            configured_network = [x for x in networks if x['id'] ==
                                  CONF.network.public_network_id]
        else:
            raise self.skipException(
                "Environment has no known-for-sure existing network.")
        configured_network = configured_network[0]
        network = (self.client.show_network(configured_network['id'])
                   ['network'])
        self.assertEqual(configured_network['label'], network['label'])

    @decorators.idempotent_id('df3d1046-6fa5-4b2c-ad0c-cfa46a351cb9')
    def test_list_all_networks(self):
        networks = self.client.list_networks()['networks']
        # Check the configured network is in the list
        if CONF.compute.fixed_network_name:
            configured_network = CONF.compute.fixed_network_name
            self.assertIn(configured_network, [x['label'] for x in networks])
        else:
            network_labels = [x['label'] for x in networks]
            self.assertNotEmpty(network_labels)
