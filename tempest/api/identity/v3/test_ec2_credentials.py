# Copyright 2020 SUSE LLC
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
from tempest.common import utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class EC2CredentialsTest(base.BaseIdentityV3Test):

    @classmethod
    def skip_checks(cls):
        super(EC2CredentialsTest, cls).skip_checks()
        if not utils.is_extension_enabled('OS-EC2', 'identity'):
            msg = "OS-EC2 identity extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        super(EC2CredentialsTest, cls).resource_setup()
        cls.creds = cls.os_primary.credentials

    @decorators.idempotent_id('b0f55a29-54e5-4166-999d-712347e0c920')
    def test_create_ec2_credential(self):
        """Create user ec2 credential."""
        resp = self.non_admin_users_client.create_user_ec2_credential(
            self.creds.user_id,
            tenant_id=self.creds.tenant_id)["credential"]
        access = resp['access']
        self.addCleanup(
            self.non_admin_users_client.delete_user_ec2_credential,
            self.creds.user_id, access)
        self.assertNotEmpty(resp['access'])
        self.assertNotEmpty(resp['secret'])
        self.assertEqual(self.creds.user_id, resp['user_id'])
        self.assertEqual(self.creds.tenant_id, resp['tenant_id'])

    @decorators.idempotent_id('897813f0-160c-4fdc-aabc-24ee635ce4a9')
    def test_list_ec2_credentials(self):
        """Get the list of user ec2 credentials."""
        created_creds = []
        # create first ec2 credentials
        creds1 = self.non_admin_users_client.create_user_ec2_credential(
            self.creds.user_id,
            tenant_id=self.creds.tenant_id)["credential"]
        created_creds.append(creds1['access'])
        self.addCleanup(
            self.non_admin_users_client.delete_user_ec2_credential,
            self.creds.user_id, creds1['access'])

        # create second ec2 credentials
        creds2 = self.non_admin_users_client.create_user_ec2_credential(
            self.creds.user_id,
            tenant_id=self.creds.tenant_id)["credential"]
        created_creds.append(creds2['access'])
        self.addCleanup(
            self.non_admin_users_client.delete_user_ec2_credential,
            self.creds.user_id, creds2['access'])

        # get the list of user ec2 credentials
        resp = self.non_admin_users_client.list_user_ec2_credentials(
            self.creds.user_id)["credentials"]
        fetched_creds = [cred['access'] for cred in resp]
        # created credentials should be in a fetched list
        missing = [cred for cred in created_creds
                   if cred not in fetched_creds]
        self.assertEmpty(missing,
                         "Failed to find ec2_credentials %s in fetched list" %
                         ', '.join(cred for cred in missing))

    @decorators.idempotent_id('8b8d1010-5958-48df-a6cd-5e3df72e6bcf')
    def test_show_ec2_credential(self):
        """Get the definite user ec2 credential."""
        resp = self.non_admin_users_client.create_user_ec2_credential(
            self.creds.user_id,
            tenant_id=self.creds.tenant_id)["credential"]
        self.addCleanup(
            self.non_admin_users_client.delete_user_ec2_credential,
            self.creds.user_id, resp['access'])

        ec2_creds = self.non_admin_users_client.show_user_ec2_credential(
            self.creds.user_id, resp['access']
        )["credential"]
        for key in ['access', 'secret', 'user_id', 'tenant_id']:
            self.assertEqual(ec2_creds[key], resp[key])

    @decorators.idempotent_id('9408d61b-8be0-4a8d-9b85-14f61edb456b')
    def test_delete_ec2_credential(self):
        """Delete user ec2 credential."""
        resp = self.non_admin_users_client.create_user_ec2_credential(
            self.creds.user_id,
            tenant_id=self.creds.tenant_id)["credential"]
        access = resp['access']
        self.non_admin_users_client.delete_user_ec2_credential(
            self.creds.user_id, access)
        self.assertRaises(
            lib_exc.NotFound,
            self.non_admin_users_client.show_user_ec2_credential,
            self.creds.user_id,
            access)
