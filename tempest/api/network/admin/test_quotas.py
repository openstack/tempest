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
from tempest.common import identity
from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators


class QuotasTest(base.BaseAdminNetworkTest):
    """Tests the following operations in the Neutron API:

        list quotas for projects who have non-default quota values
        show quotas for a specified project
        update quotas for a specified project
        reset quotas to default values for a specified project

    v2.0 of the API is assumed.
    It is also assumed that the per-project quota extension API is configured
    in /etc/neutron/neutron.conf as follows:

        quota_driver = neutron.db.quota_db.DbQuotaDriver
    """

    @classmethod
    def skip_checks(cls):
        super(QuotasTest, cls).skip_checks()
        if not utils.is_extension_enabled('quotas', 'network'):
            msg = "quotas extension not enabled."
            raise cls.skipException(msg)

    def _check_quotas(self, new_quotas):
        # Add a project to conduct the test
        project = data_utils.rand_name('test_project_')
        description = data_utils.rand_name('desc_')
        project = identity.identity_utils(self.os_admin).create_project(
            name=project, description=description)
        project_id = project['id']
        self.addCleanup(identity.identity_utils(self.os_admin).delete_project,
                        project_id)

        # Change quotas for project
        quota_set = self.admin_quotas_client.update_quotas(
            project_id, **new_quotas)['quota']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_quotas_client.reset_quotas, project_id)
        for key, value in new_quotas.items():
            self.assertEqual(value, quota_set[key])

        # Confirm our project is listed among projects with non default quotas
        non_default_quotas = self.admin_quotas_client.list_quotas()
        found = False
        for qs in non_default_quotas['quotas']:
            if qs['tenant_id'] == project_id:
                found = True
        self.assertTrue(found)

        # Confirm from API quotas were changed as requested for project
        quota_set = self.admin_quotas_client.show_quotas(project_id)
        quota_set = quota_set['quota']
        for key, value in new_quotas.items():
            self.assertEqual(value, quota_set[key])

        # Reset quotas to default and confirm
        self.admin_quotas_client.reset_quotas(project_id)
        non_default_quotas = self.admin_quotas_client.list_quotas()
        for q in non_default_quotas['quotas']:
            self.assertNotEqual(project_id, q['tenant_id'])
        quota_set = self.admin_quotas_client.show_quotas(project_id)['quota']
        default_quotas = self.admin_quotas_client.show_default_quotas(
            project_id)['quota']
        self.assertEqual(default_quotas, quota_set)

    @decorators.idempotent_id('2390f766-836d-40ef-9aeb-e810d78207fb')
    def test_quotas(self):
        new_quotas = {'network': 0, 'port': 0}
        self._check_quotas(new_quotas)
