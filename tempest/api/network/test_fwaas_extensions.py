# Copyright 2014 NEC Corporation. All rights reserved.
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
from tempest import test


class FWaaSExtensionTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        List firewall rules
        Create firewall rule
        Update firewall rule
        Delete firewall rule
        Show firewall rule
        List firewall policies
        Create firewall policy
        Update firewall policy
        Delete firewall policy
        Show firewall policy
        List firewall
        Create firewall
        Update firewall
        Delete firewall
        Show firewall
    """

    @classmethod
    def setUpClass(cls):
        super(FWaaSExtensionTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('fwaas', 'network'):
            msg = "FWaaS Extension not enabled."
            raise cls.skipException(msg)
        cls.fw_rule = cls.create_firewall_rule("allow", "tcp")
        cls.fw_policy = cls.create_firewall_policy()

    def _try_delete_policy(self, policy_id):
        # delete policy, if it exists
        try:
            self.client.delete_firewall_policy(policy_id)
        # if policy is not found, this means it was deleted in the test
        except exceptions.NotFound:
            pass

    def _try_delete_firewall(self, fw_id):
        # delete firewall, if it exists
        try:
            self.client.delete_firewall(fw_id)
        # if firewall is not found, this means it was deleted in the test
        except exceptions.NotFound:
            pass

    @test.attr(type='smoke')
    def test_list_firewall_rules(self):
        # List firewall rules
        resp, fw_rules = self.client.list_firewall_rules()
        self.assertEqual('200', resp['status'])
        fw_rules = fw_rules['firewall_rules']
        self.assertIn((self.fw_rule['id'],
                       self.fw_rule['name'],
                       self.fw_rule['action'],
                       self.fw_rule['protocol'],
                       self.fw_rule['ip_version'],
                       self.fw_rule['enabled']),
                      [(m['id'],
                        m['name'],
                        m['action'],
                        m['protocol'],
                        m['ip_version'],
                        m['enabled']) for m in fw_rules])

    @test.attr(type='smoke')
    def test_create_update_delete_firewall_rule(self):
        # Create firewall rule
        resp, body = self.client.create_firewall_rule(
            name=data_utils.rand_name("fw-rule"),
            action="allow",
            protocol="tcp")
        self.assertEqual('201', resp['status'])
        fw_rule_id = body['firewall_rule']['id']

        # Update firewall rule
        resp, body = self.client.update_firewall_rule(fw_rule_id,
                                                      shared=True)
        self.assertEqual('200', resp['status'])
        self.assertTrue(body["firewall_rule"]['shared'])

        # Delete firewall rule
        resp, _ = self.client.delete_firewall_rule(fw_rule_id)
        self.assertEqual('204', resp['status'])
        # Confirm deletion
        resp, fw_rules = self.client.list_firewall_rules()
        self.assertNotIn(fw_rule_id,
                         [m['id'] for m in fw_rules['firewall_rules']])

    @test.attr(type='smoke')
    def test_show_firewall_rule(self):
        # show a created firewall rule
        resp, fw_rule = self.client.show_firewall_rule(self.fw_rule['id'])
        self.assertEqual('200', resp['status'])
        for key, value in fw_rule['firewall_rule'].iteritems():
            self.assertEqual(self.fw_rule[key], value)

    @test.attr(type='smoke')
    def test_list_firewall_policies(self):
        resp, fw_policies = self.client.list_firewall_policies()
        self.assertEqual('200', resp['status'])
        fw_policies = fw_policies['firewall_policies']
        self.assertIn((self.fw_policy['id'],
                       self.fw_policy['name'],
                       self.fw_policy['firewall_rules']),
                      [(m['id'],
                        m['name'],
                        m['firewall_rules']) for m in fw_policies])

    @test.attr(type='smoke')
    def test_create_update_delete_firewall_policy(self):
        # Create firewall policy
        resp, body = self.client.create_firewall_policy(
            name=data_utils.rand_name("fw-policy"))
        self.assertEqual('201', resp['status'])
        fw_policy_id = body['firewall_policy']['id']
        self.addCleanup(self._try_delete_policy, fw_policy_id)

        # Update firewall policy
        resp, body = self.client.update_firewall_policy(fw_policy_id,
                                                        shared=True,
                                                        name="updated_policy")
        self.assertEqual('200', resp['status'])
        updated_fw_policy = body["firewall_policy"]
        self.assertTrue(updated_fw_policy['shared'])
        self.assertEqual("updated_policy", updated_fw_policy['name'])

        # Delete firewall policy
        resp, _ = self.client.delete_firewall_policy(fw_policy_id)
        self.assertEqual('204', resp['status'])
        # Confirm deletion
        resp, fw_policies = self.client.list_firewall_policies()
        fw_policies = fw_policies['firewall_policies']
        self.assertNotIn(fw_policy_id, [m['id'] for m in fw_policies])

    @test.attr(type='smoke')
    def test_show_firewall_policy(self):
        # show a created firewall policy
        resp, fw_policy = self.client.show_firewall_policy(
            self.fw_policy['id'])
        self.assertEqual('200', resp['status'])
        fw_policy = fw_policy['firewall_policy']
        for key, value in fw_policy.iteritems():
            self.assertEqual(self.fw_policy[key], value)

    @test.attr(type='smoke')
    def test_create_show_delete_firewall(self):
        # Create firewall
        resp, body = self.client.create_firewall(
            name=data_utils.rand_name("firewall"),
            firewall_policy_id=self.fw_policy['id'])
        self.assertEqual('201', resp['status'])
        created_firewall = body['firewall']
        firewall_id = created_firewall['id']
        self.addCleanup(self._try_delete_firewall, firewall_id)

        # show a created firewall
        resp, firewall = self.client.show_firewall(firewall_id)
        self.assertEqual('200', resp['status'])
        firewall = firewall['firewall']
        for key, value in firewall.iteritems():
            self.assertEqual(created_firewall[key], value)

        # list firewall
        resp, firewalls = self.client.list_firewalls()
        self.assertEqual('200', resp['status'])
        firewalls = firewalls['firewalls']
        self.assertIn((created_firewall['id'],
                       created_firewall['name'],
                       created_firewall['firewall_policy_id']),
                      [(m['id'],
                        m['name'],
                        m['firewall_policy_id']) for m in firewalls])

        # Delete firewall
        resp, _ = self.client.delete_firewall(firewall_id)
        self.assertEqual('204', resp['status'])
        # Confirm deletion
        # TODO(raies): Confirm deletion can be done only when,
        # deleted firewall status is not "PENDING_DELETE".


class FWaaSExtensionTestXML(FWaaSExtensionTestJSON):
    _interface = 'xml'
