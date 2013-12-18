# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class NetworksNegativeTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    @attr(type=['negative', 'smoke'])
    def test_show_non_existent_network(self):
        non_exist_id = data_utils.rand_name('network')
        self.assertRaises(exceptions.NotFound, self.client.show_network,
                          non_exist_id)

    @attr(type=['negative', 'smoke'])
    def test_show_non_existent_subnet(self):
        non_exist_id = data_utils.rand_name('subnet')
        self.assertRaises(exceptions.NotFound, self.client.show_subnet,
                          non_exist_id)

    @attr(type=['negative', 'smoke'])
    def test_show_non_existent_port(self):
        non_exist_id = data_utils.rand_name('port')
        self.assertRaises(exceptions.NotFound, self.client.show_port,
                          non_exist_id)

    @attr(type=['negative', 'smoke'])
    def test_update_non_existent_network(self):
        non_exist_id = data_utils.rand_name('network')
        self.assertRaises(exceptions.NotFound, self.client.update_network,
                          non_exist_id, name="new_name")

    @attr(type=['negative', 'smoke'])
    def test_delete_non_existent_network(self):
        non_exist_id = data_utils.rand_name('network')
        self.assertRaises(exceptions.NotFound, self.client.delete_network,
                          non_exist_id)


class NetworksNegativeTestXML(NetworksNegativeTestJSON):
    _interface = 'xml'
