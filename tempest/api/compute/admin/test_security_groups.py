# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NTT Data
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

import testtools

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest.test import attr

CONF = config.CONF


class SecurityGroupsTestAdminJSON(base.BaseV2ComputeAdminTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(SecurityGroupsTestAdminJSON, cls).setUpClass()
        cls.adm_client = cls.os_adm.security_groups_client
        cls.client = cls.security_groups_client

    def _delete_security_group(self, securitygroup_id, admin=True):
        if admin:
            resp, _ = self.adm_client.delete_security_group(securitygroup_id)
        else:
            resp, _ = self.client.delete_security_group(securitygroup_id)

        self.assertEqual(202, resp.status)

    @testtools.skipIf(CONF.service_available.neutron,
                      "Skipped because neutron do not support all_tenants"
                      "search filter.")
    @attr(type='smoke')
    def test_list_security_groups_list_all_tenants_filter(self):
        # Admin can list security groups of all tenants
        # List of all security groups created
        security_group_list = []
        # Create two security groups for a non-admin tenant
        for i in range(2):
            name = data_utils.rand_name('securitygroup-')
            description = data_utils.rand_name('description-')
            resp, securitygroup = (self.client
                                   .create_security_group(name, description))
            self.assertEqual(200, resp.status)
            self.addCleanup(self._delete_security_group,
                            securitygroup['id'], admin=False)
            security_group_list.append(securitygroup)

        client_tenant_id = securitygroup['tenant_id']
        # Create two security groups for admin tenant
        for i in range(2):
            name = data_utils.rand_name('securitygroup-')
            description = data_utils.rand_name('description-')
            resp, adm_securitygroup = (self.adm_client
                                       .create_security_group(name,
                                                              description))
            self.assertEqual(200, resp.status)
            self.addCleanup(self._delete_security_group,
                            adm_securitygroup['id'])
            security_group_list.append(adm_securitygroup)

        # Fetch all security groups based on 'all_tenants' search filter
        param = {'all_tenants': 'true'}
        resp, fetched_list = self.adm_client.list_security_groups(params=param)
        self.assertEqual(200, resp.status)
        sec_group_id_list = map(lambda sg: sg['id'], fetched_list)
        # Now check if all created Security Groups are present in fetched list
        for sec_group in security_group_list:
            self.assertIn(sec_group['id'], sec_group_id_list)

        # Fetch all security groups for non-admin user with 'all_tenants'
        # search filter
        resp, fetched_list = self.client.list_security_groups(params=param)
        self.assertEqual(200, resp.status)
        # Now check if all created Security Groups are present in fetched list
        for sec_group in fetched_list:
            self.assertEqual(sec_group['tenant_id'], client_tenant_id,
                             "Failed to get all security groups for "
                             "non admin user.")


class SecurityGroupsTestAdminXML(SecurityGroupsTestAdminJSON):
    _interface = 'xml'
