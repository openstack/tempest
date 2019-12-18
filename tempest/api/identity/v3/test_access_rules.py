# Copyright 2019 SUSE LLC
#
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

from tempest.api.identity import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class AccessRulesV3Test(base.BaseIdentityV3Test):

    @classmethod
    def skip_checks(cls):
        super(AccessRulesV3Test, cls).skip_checks()
        if not CONF.identity_feature_enabled.access_rules:
            raise cls.skipException("Application credential access rules are "
                                    "not available in this environment")

    @classmethod
    def resource_setup(cls):
        super(AccessRulesV3Test, cls).resource_setup()
        cls.user_id = cls.os_primary.credentials.user_id
        cls.project_id = cls.os_primary.credentials.project_id

    def setUp(self):
        super(AccessRulesV3Test, self).setUp()
        ac = self.non_admin_app_creds_client
        access_rules = [
            {
                "path": "/v2.1/servers/*/ips",
                "method": "GET",
                "service": "compute"
            }
        ]
        self.app_cred = ac.create_application_credential(
            self.user_id,
            name=data_utils.rand_name('application_credential'),
            access_rules=access_rules
        )['application_credential']

    @decorators.idempotent_id('2354c498-5119-4ba5-9f0d-44f16f78fb0e')
    def test_list_access_rules(self):
        ar = self.non_admin_access_rules_client.list_access_rules(self.user_id)
        self.assertEqual(1, len(ar['access_rules']))

    @decorators.idempotent_id('795dd507-ca1e-40e9-ba90-ff0a08689ba4')
    def test_show_access_rule(self):
        access_rule_id = self.app_cred['access_rules'][0]['id']
        self.non_admin_access_rules_client.show_access_rule(
            self.user_id, access_rule_id)

    @decorators.idempotent_id('278757e9-e193-4bf8-adf2-0b0a229a17d0')
    def test_delete_access_rule(self):
        access_rule_id = self.app_cred['access_rules'][0]['id']
        app_cred_id = self.app_cred['id']
        self.assertRaises(
            lib_exc.Forbidden,
            self.non_admin_access_rules_client.delete_access_rule,
            self.user_id,
            access_rule_id)
        self.non_admin_app_creds_client.delete_application_credential(
            self.user_id, app_cred_id)
        ar = self.non_admin_access_rules_client.list_access_rules(self.user_id)
        self.assertEqual(1, len(ar['access_rules']))
        self.non_admin_access_rules_client.delete_access_rule(
            self.user_id, access_rule_id)
        ar = self.non_admin_access_rules_client.list_access_rules(self.user_id)
        self.assertEqual(0, len(ar['access_rules']))
