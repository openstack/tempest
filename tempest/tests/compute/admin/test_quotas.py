# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from nose.plugins.attrib import attr

from tempest import exceptions
from tempest.services.compute.admin.json import quotas_client as adm_quotas
from tempest.tests.compute.base import BaseComputeTest


class QuotasTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        super(QuotasTest, cls).setUpClass()
        c_adm_user = cls.config.compute_admin.username
        c_adm_pass = cls.config.compute_admin.password
        c_adm_tenant = cls.config.compute_admin.tenant_name
        auth_url = cls.config.identity.uri

        cls.adm_client = adm_quotas.AdminQuotasClient(cls.config, c_adm_user,
                                                      c_adm_pass, auth_url,
                                                      c_adm_tenant)
        cls.client = cls.os.quotas_client
        cls.identity_admin_client = cls._get_identity_admin_client()
        resp, tenants = cls.identity_admin_client.list_tenants()

        if cls.config.compute.allow_tenant_isolation:
            cls.demo_tenant_id = cls.isolated_creds[0][0]['tenantId']
        else:
            cls.demo_tenant_id = [tnt['id'] for tnt in tenants if tnt['name']
                                  == cls.config.identity.tenant_name][0]

        cls.adm_tenant_id = [tnt['id'] for tnt in tenants if tnt['name'] ==
                             cls.config.compute_admin.tenant_name][0]

        cls.default_quota_set = {'injected_file_content_bytes': 10240,
                                 'metadata_items': 128, 'injected_files': 5,
                                 'ram': 51200, 'floating_ips': 10,
                                 'key_pairs': 100,
                                 'injected_file_path_bytes': 255,
                                 'instances': 10, 'security_group_rules': 20,
                                 'cores': 20, 'security_groups': 10}

    @classmethod
    def tearDownClass(cls):
        for server in cls.servers:
            try:
                cls.servers_client.delete_server(server['id'])
            except exceptions.NotFound:
                continue
        super(QuotasTest, cls).tearDownClass()

    @attr(type='smoke')
    def test_get_default_quotas(self):
        # Admin can get the default resource quota set for a tenant
        expected_quota_set = self.default_quota_set.copy()
        expected_quota_set['id'] = self.demo_tenant_id
        try:
            resp, quota_set = self.client.get_quota_set(self.demo_tenant_id)
            self.assertEqual(200, resp.status)
            self.assertSequenceEqual(expected_quota_set, quota_set)
        except Exception:
            self.fail("Admin could not get the default quota set for a tenant")

    def test_update_all_quota_resources_for_tenant(self):
        # Admin can update all the resource quota limits for a tenant
        new_quota_set = {'injected_file_content_bytes': 20480,
                         'metadata_items': 256, 'injected_files': 10,
                         'ram': 10240, 'floating_ips': 20, 'key_pairs': 200,
                         'injected_file_path_bytes': 512, 'instances': 20,
                         'security_group_rules': 20, 'cores': 2,
                         'security_groups': 20}
        try:
            # Update limits for all quota resources
            resp, quota_set = self.adm_client.update_quota_set(
                self.demo_tenant_id,
                **new_quota_set)
            self.assertEqual(200, resp.status)
            self.assertSequenceEqual(new_quota_set, quota_set)
        except Exception:
            self.fail("Admin could not update quota set for the tenant")
        finally:
            # Reset quota resource limits to default values
            resp, quota_set = self.adm_client.update_quota_set(
                self.demo_tenant_id,
                **self.default_quota_set)
            self.assertEqual(200, resp.status, "Failed to reset quota "
                             "defaults")

    def test_get_updated_quotas(self):
        # Verify that GET shows the updated quota set
        self.adm_client.update_quota_set(self.demo_tenant_id,
                                         ram='5120')
        try:
            resp, quota_set = self.client.get_quota_set(self.demo_tenant_id)
            self.assertEqual(200, resp.status)
            self.assertEqual(quota_set['ram'], 5120)
        except Exception:
            self.fail("Could not get the update quota limit for resource")
        finally:
            # Reset quota resource limits to default values
            resp, quota_set = self.adm_client.update_quota_set(
                self.demo_tenant_id,
                **self.default_quota_set)
            self.assertEqual(200, resp.status, "Failed to reset quota "
                             "defaults")

    def test_create_server_when_cpu_quota_is_full(self):
        # Disallow server creation when tenant's vcpu quota is full
        resp, quota_set = self.client.get_quota_set(self.demo_tenant_id)
        default_vcpu_quota = quota_set['cores']
        vcpu_quota = 0  # Set the quota to zero to conserve resources

        resp, quota_set = self.adm_client.update_quota_set(self.demo_tenant_id,
                                                           cores=vcpu_quota)
        try:
            self.create_server()
        except exceptions.OverLimit:
            pass
        else:
            self.fail("Could create servers over the VCPU quota limit")
        finally:
            self.adm_client.update_quota_set(self.demo_tenant_id,
                                             cores=default_vcpu_quota)

    def test_create_server_when_memory_quota_is_full(self):
        # Disallow server creation when tenant's memory quota is full
        resp, quota_set = self.client.get_quota_set(self.demo_tenant_id)
        default_mem_quota = quota_set['ram']
        mem_quota = 0  # Set the quota to zero to conserve resources

        self.adm_client.update_quota_set(self.demo_tenant_id,
                                         ram=mem_quota)
        try:
            self.create_server()
        except exceptions.OverLimit:
            pass
        else:
            self.fail("Could create servers over the memory quota limit")
        finally:
            self.adm_client.update_quota_set(self.demo_tenant_id,
                                             ram=default_mem_quota)
