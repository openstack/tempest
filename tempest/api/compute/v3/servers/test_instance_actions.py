# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation
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
from tempest import exceptions
from tempest.test import attr


class InstanceActionsV3TestJSON(base.BaseV3ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(InstanceActionsV3TestJSON, cls).setUpClass()
        cls.client = cls.servers_client
        resp, server = cls.create_test_server(wait_until='ACTIVE')
        cls.request_id = resp['x-compute-request-id']
        cls.server_id = server['id']

    @attr(type='gate')
    def test_list_instance_actions(self):
        # List actions of the provided server
        resp, body = self.client.reboot(self.server_id, 'HARD')
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        resp, body = self.client.list_instance_actions(self.server_id)
        self.assertEqual(200, resp.status)
        self.assertTrue(len(body) == 2, str(body))
        self.assertTrue(any([i for i in body if i['action'] == 'create']))
        self.assertTrue(any([i for i in body if i['action'] == 'reboot']))

    @attr(type='gate')
    def test_get_instance_action(self):
        # Get the action details of the provided server
        resp, body = self.client.get_instance_action(self.server_id,
                                                     self.request_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(self.server_id, body['instance_uuid'])
        self.assertEqual('create', body['action'])

    @attr(type=['negative', 'gate'])
    def test_list_instance_actions_invalid_server(self):
        # List actions of the invalid server id
        self.assertRaises(exceptions.NotFound,
                          self.client.list_instance_actions, 'server-999')

    @attr(type=['negative', 'gate'])
    def test_get_instance_action_invalid_request(self):
        # Get the action details of the provided server with invalid request
        self.assertRaises(exceptions.NotFound, self.client.get_instance_action,
                          self.server_id, '999')


class InstanceActionsV3TestXML(InstanceActionsV3TestJSON):
    _interface = 'xml'
