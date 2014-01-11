# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Author: Emilien Macchi <emilien.macchi@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.api.network import base
from tempest.common.utils import data_utils
from tempest.openstack.common import log as logging
from tempest import test


LOG = logging.getLogger(__name__)


class MeteringJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        List, Show, Create, Delete Metering labels
        List, Show, Create, Delete Metering labels rules
    """

    @classmethod
    def setUpClass(cls):
        super(MeteringJSON, cls).setUpClass()
        if not test.is_extension_enabled('metering', 'network'):
            msg = "metering extension not enabled."
            raise cls.skipException(msg)
        description = "metering label created by tempest"
        name = data_utils.rand_name("metering-label")
        try:
            cls.metering_label = cls.create_metering_label(name, description)
            remote_ip_prefix = "10.0.0.0/24"
            direction = "ingress"
            cls.metering_label_rule = cls.create_metering_label_rule(
                remote_ip_prefix, direction,
                metering_label_id=cls.metering_label['id'])
        except Exception:
            LOG.exception('setUpClass failed')
            cls.tearDownClass()
            raise

    def _delete_metering_label(self, metering_label_id):
        # Deletes a label and verifies if it is deleted or not
        resp, body = self.admin_client.delete_metering_label(metering_label_id)
        self.assertEqual(204, resp.status)
        # Asserting that the label is not found in list after deletion
        resp, labels = (self.admin_client.list_metering_labels(
                        id=metering_label_id))
        self.assertEqual(len(labels['metering_labels']), 0)

    def _delete_metering_label_rule(self, metering_label_rule_id):
        # Deletes a rule and verifies if it is deleted or not
        resp, body = (self.admin_client.delete_metering_label_rule(
                      metering_label_rule_id))
        self.assertEqual(204, resp.status)
        # Asserting that the rule is not found in list after deletion
        resp, rules = (self.admin_client.list_metering_label_rules(
                       id=metering_label_rule_id))
        self.assertEqual(len(rules['metering_label_rules']), 0)

    @test.attr(type='smoke')
    def test_list_metering_labels(self):
        # Verify label filtering
        resp, body = self.admin_client.list_metering_labels(id=33)
        self.assertEqual('200', resp['status'])
        metering_labels = body['metering_labels']
        self.assertEqual(0, len(metering_labels))

    @test.attr(type='smoke')
    def test_create_delete_metering_label_with_filters(self):
        # Creates a label
        name = data_utils.rand_name('metering-label-')
        description = "label created by tempest"
        resp, body = (self.admin_client.create_metering_label(name=name,
                      description=description))
        self.assertEqual('201', resp['status'])
        metering_label = body['metering_label']
        self.addCleanup(self._delete_metering_label,
                        metering_label['id'])
        # Assert whether created labels are found in labels list or fail
        # if created labels are not found in labels list
        resp, labels = (self.admin_client.list_metering_labels(
                        id=metering_label['id']))
        self.assertEqual(len(labels['metering_labels']), 1)

    @test.attr(type='smoke')
    def test_show_metering_label(self):
        # Verifies the details of a label
        resp, body = (self.admin_client.show_metering_label(
                      self.metering_label['id']))
        self.assertEqual('200', resp['status'])
        metering_label = body['metering_label']
        self.assertEqual(self.metering_label['id'], metering_label['id'])
        self.assertEqual(self.metering_label['tenant_id'],
                         metering_label['tenant_id'])
        self.assertEqual(self.metering_label['name'], metering_label['name'])
        self.assertEqual(self.metering_label['description'],
                         metering_label['description'])

    @test.attr(type='smoke')
    def test_list_metering_label_rules(self):
        # Verify rule filtering
        resp, body = self.admin_client.list_metering_label_rules(id=33)
        self.assertEqual('200', resp['status'])
        metering_label_rules = body['metering_label_rules']
        self.assertEqual(0, len(metering_label_rules))

    @test.attr(type='smoke')
    def test_create_delete_metering_label_rule_with_filters(self):
        # Creates a rule
        resp, body = (self.admin_client.create_metering_label_rule(
                      remote_ip_prefix="10.0.1.0/24",
                      direction="ingress",
                      metering_label_id=self.metering_label['id']))
        self.assertEqual('201', resp['status'])
        metering_label_rule = body['metering_label_rule']
        self.addCleanup(self._delete_metering_label_rule,
                        metering_label_rule['id'])
        # Assert whether created rules are found in rules list or fail
        # if created rules are not found in rules list
        resp, rules = (self.admin_client.list_metering_label_rules(
                       id=metering_label_rule['id']))
        self.assertEqual(len(rules['metering_label_rules']), 1)

    @test.attr(type='smoke')
    def test_show_metering_label_rule(self):
        # Verifies the details of a rule
        resp, body = (self.admin_client.show_metering_label_rule(
                      self.metering_label_rule['id']))
        self.assertEqual('200', resp['status'])
        metering_label_rule = body['metering_label_rule']
        self.assertEqual(self.metering_label_rule['id'],
                         metering_label_rule['id'])
        self.assertEqual(self.metering_label_rule['remote_ip_prefix'],
                         metering_label_rule['remote_ip_prefix'])
        self.assertEqual(self.metering_label_rule['direction'],
                         metering_label_rule['direction'])
        self.assertEqual(self.metering_label_rule['metering_label_id'],
                         metering_label_rule['metering_label_id'])
        self.assertFalse(metering_label_rule['excluded'])


class MeteringXML(MeteringJSON):
    interface = 'xml'
