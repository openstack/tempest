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


class BaseRouterTest(base.BaseAdminNetworkTest):
    # NOTE(salv-orlando): This class inherits from BaseAdminNetworkTest
    # as some router operations, such as enabling or disabling SNAT
    # require admin credentials by default

    @classmethod
    def setUpClass(cls):
        super(BaseRouterTest, cls).setUpClass()

    def _delete_router(self, router_id):
        resp, _ = self.client.delete_router(router_id)
        self.assertEqual(204, resp.status)
        # Asserting that the router is not found in the list
        # after deletion
        resp, list_body = self.client.list_routers()
        self.assertEqual('200', resp['status'])
        routers_list = list()
        for router in list_body['routers']:
            routers_list.append(router['id'])
        self.assertNotIn(router_id, routers_list)

    def _remove_router_interface_with_subnet_id(self, router_id, subnet_id):
        resp, body = self.client.remove_router_interface_with_subnet_id(
            router_id, subnet_id)
        self.assertEqual('200', resp['status'])
        self.assertEqual(subnet_id, body['subnet_id'])

    def _remove_router_interface_with_port_id(self, router_id, port_id):
        resp, body = self.client.remove_router_interface_with_port_id(
            router_id, port_id)
        self.assertEqual('200', resp['status'])
        self.assertEqual(port_id, body['port_id'])
