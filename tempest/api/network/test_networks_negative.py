# Copyright 2013 Huawei Technologies Co.,LTD.
# Copyright 2012 OpenStack Foundation
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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class NetworksNegativeTestJSON(base.BaseNetworkTest):
    """Negative tests of network"""

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9293e937-824d-42d2-8d5b-e985ea67002a')
    def test_show_non_existent_network(self):
        """Test showing non existent network"""
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.networks_client.show_network,
                          non_exist_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d746b40c-5e09-4043-99f7-cba1be8b70df')
    def test_show_non_existent_subnet(self):
        """Test showing non existent subnet"""
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.subnets_client.show_subnet,
                          non_exist_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a954861d-cbfd-44e8-b0a9-7fab111f235d')
    def test_show_non_existent_port(self):
        """Test showing non existent port"""
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.ports_client.show_port,
                          non_exist_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('98bfe4e3-574e-4012-8b17-b2647063de87')
    def test_update_non_existent_network(self):
        """Test updating non existent network"""
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(
            lib_exc.NotFound, self.networks_client.update_network,
            non_exist_id, name="new_name")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('03795047-4a94-4120-a0a1-bd376e36fd4e')
    def test_delete_non_existent_network(self):
        """Test deleting non existent network"""
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.networks_client.delete_network,
                          non_exist_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('1cc47884-ac52-4415-a31c-e7ce5474a868')
    def test_update_non_existent_subnet(self):
        """Test updating non existent subnet"""
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.subnets_client.update_subnet,
                          non_exist_id, name='new_name')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a176c859-99fb-42ec-a208-8a85b552a239')
    def test_delete_non_existent_subnet(self):
        """Test deleting non existent subnet"""
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.subnets_client.delete_subnet, non_exist_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('13d3b106-47e6-4b9b-8d53-dae947f092fe')
    def test_create_port_on_non_existent_network(self):
        """Test creating port on non existent network"""
        non_exist_net_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.ports_client.create_port,
                          network_id=non_exist_net_id,
                          name=data_utils.rand_name(
                              self.__class__.__name__,
                              prefix=CONF.resource_name_prefix))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('cf8eef21-4351-4f53-adcd-cc5cb1e76b92')
    def test_update_non_existent_port(self):
        """Test updating non existent port"""
        non_exist_port_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.ports_client.update_port,
                          non_exist_port_id, name='new_name')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('49ec2bbd-ac2e-46fd-8054-798e679ff894')
    def test_delete_non_existent_port(self):
        """Test deleting non existent port"""
        non_exist_port_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.ports_client.delete_port, non_exist_port_id)
