# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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
from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators


class MeteringTestJSON(base.BaseAdminNetworkTest):
    """Tests the following operations in the Neutron API:

        List, Show, Create, Delete Metering labels
        List, Show, Create, Delete Metering labels rules
    """

    @classmethod
    def skip_checks(cls):
        super(MeteringTestJSON, cls).skip_checks()
        if not utils.is_extension_enabled('metering', 'network'):
            msg = "metering extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        super(MeteringTestJSON, cls).resource_setup()
        description = "metering label created by tempest"
        name = data_utils.rand_name("metering-label")
        cls.metering_label = cls.create_metering_label(name, description)
        remote_ip_prefix = ("10.0.0.0/24" if cls._ip_version == 4
                            else "fd02::/64")
        direction = "ingress"
        cls.metering_label_rule = cls.create_metering_label_rule(
            remote_ip_prefix, direction,
            metering_label_id=cls.metering_label['id'])

    @classmethod
    def create_metering_label(cls, name, description):
        """Wrapper utility that returns a test metering label."""
        body = cls.admin_metering_labels_client.create_metering_label(
            description=description,
            name=name)
        metering_label = body['metering_label']
        cls.addClassResourceCleanup(
            test_utils.call_and_ignore_notfound_exc,
            cls.admin_metering_labels_client.delete_metering_label,
            metering_label['id'])
        return metering_label

    @classmethod
    def create_metering_label_rule(cls, remote_ip_prefix, direction,
                                   metering_label_id):
        """Wrapper utility that returns a test metering label rule."""
        client = cls.admin_metering_label_rules_client
        body = client.create_metering_label_rule(
            remote_ip_prefix=remote_ip_prefix, direction=direction,
            metering_label_id=metering_label_id)
        metering_label_rule = body['metering_label_rule']
        cls.addClassResourceCleanup(
            test_utils.call_and_ignore_notfound_exc,
            client.delete_metering_label_rule, metering_label_rule['id'])
        return metering_label_rule

    def _delete_metering_label(self, metering_label_id):
        # Deletes a label and verifies if it is deleted or not
        self.admin_metering_labels_client.delete_metering_label(
            metering_label_id)
        # Asserting that the label is not found in list after deletion
        labels = self.admin_metering_labels_client.list_metering_labels(
            id=metering_label_id)
        self.assertEmpty(labels['metering_labels'])

    def _delete_metering_label_rule(self, metering_label_rule_id):
        client = self.admin_metering_label_rules_client
        # Deletes a rule and verifies if it is deleted or not
        client.delete_metering_label_rule(metering_label_rule_id)
        # Asserting that the rule is not found in list after deletion
        rules = client.list_metering_label_rules(id=metering_label_rule_id)
        self.assertEqual(len(rules['metering_label_rules']), 0)

    @decorators.idempotent_id('e2fb2f8c-45bf-429a-9f17-171c70444612')
    def test_list_metering_labels(self):
        """Verify listing metering labels"""
        body = self.admin_metering_labels_client.list_metering_labels(id=33)
        metering_labels = body['metering_labels']
        self.assertEmpty(metering_labels)

    @decorators.idempotent_id('ec8e15ff-95d0-433b-b8a6-b466bddb1e50')
    def test_create_delete_metering_label_with_filters(self):
        """Verifies creating and deleting metering label with filters"""
        # Creates a label
        name = data_utils.rand_name('metering-label-')
        description = "label created by tempest"
        body = self.admin_metering_labels_client.create_metering_label(
            name=name, description=description)
        metering_label = body['metering_label']
        self.addCleanup(self._delete_metering_label,
                        metering_label['id'])
        # Assert whether created labels are found in labels list or fail
        # if created labels are not found in labels list
        labels = (self.admin_metering_labels_client.list_metering_labels(
                  id=metering_label['id']))
        self.assertEqual(len(labels['metering_labels']), 1)

    @decorators.idempotent_id('30abb445-0eea-472e-bd02-8649f54a5968')
    def test_show_metering_label(self):
        """Verifies the details of a metering label"""
        body = self.admin_metering_labels_client.show_metering_label(
            self.metering_label['id'])
        metering_label = body['metering_label']
        self.assertEqual(self.metering_label['id'], metering_label['id'])
        self.assertEqual(self.metering_label['tenant_id'],
                         metering_label['project_id'])
        self.assertEqual(self.metering_label['name'], metering_label['name'])
        self.assertEqual(self.metering_label['description'],
                         metering_label['description'])

    @decorators.idempotent_id('cc832399-6681-493b-9d79-0202831a1281')
    def test_list_metering_label_rules(self):
        """Verifies listing metering label rules"""
        client = self.admin_metering_label_rules_client
        # Verify rule filtering
        body = client.list_metering_label_rules(id=33)
        metering_label_rules = body['metering_label_rules']
        self.assertEmpty(metering_label_rules)

    @decorators.idempotent_id('f4d547cd-3aee-408f-bf36-454f8825e045')
    def test_create_delete_metering_label_rule_with_filters(self):
        """Verifies creating and deleting metering label rule with filters"""
        # Creates a rule
        remote_ip_prefix = ("10.0.1.0/24" if self._ip_version == 4
                            else "fd03::/64")
        client = self.admin_metering_label_rules_client
        body = (client.create_metering_label_rule(
                remote_ip_prefix=remote_ip_prefix,
                direction="ingress",
                metering_label_id=self.metering_label['id']))
        metering_label_rule = body['metering_label_rule']
        self.addCleanup(self._delete_metering_label_rule,
                        metering_label_rule['id'])
        # Assert whether created rules are found in rules list or fail
        # if created rules are not found in rules list
        rules = client.list_metering_label_rules(id=metering_label_rule['id'])
        self.assertEqual(len(rules['metering_label_rules']), 1)

    @decorators.idempotent_id('b7354489-96ea-41f3-9452-bace120fb4a7')
    def test_show_metering_label_rule(self):
        """Verifies the metering details of a rule"""
        client = self.admin_metering_label_rules_client
        body = (client.show_metering_label_rule(
                self.metering_label_rule['id']))
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


class MeteringIpV6TestJSON(MeteringTestJSON):
    _ip_version = 6
