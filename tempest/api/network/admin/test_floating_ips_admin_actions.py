# Copyright 2014 OpenStack Foundation
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
from tempest import clients
from tempest import config
from tempest import test

CONF = config.CONF


class FloatingIPAdminTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'
    force_tenant_isolation = True

    @classmethod
    def setUpClass(cls):
        super(FloatingIPAdminTestJSON, cls).setUpClass()
        cls.ext_net_id = CONF.network.public_network_id
        cls.floating_ip = cls.create_floatingip(cls.ext_net_id)
        cls.alt_manager = clients.Manager(cls.isolated_creds.get_alt_creds())
        cls.alt_client = cls.alt_manager.network_client

    @test.attr(type='smoke')
    def test_list_floating_ips_from_admin_and_nonadmin(self):
        # Create floating ip from admin user
        _, floating_ip_admin = self.admin_client.create_floatingip(
            floating_network_id=self.ext_net_id)
        self.addCleanup(self.admin_client.delete_floatingip,
                        floating_ip_admin['floatingip']['id'])
        # Create floating ip from alt user
        _, body = self.alt_client.create_floatingip(
            floating_network_id=self.ext_net_id)
        floating_ip_alt = body['floatingip']
        self.addCleanup(self.alt_client.delete_floatingip,
                        floating_ip_alt['id'])
        # List floating ips from admin
        _, body = self.admin_client.list_floatingips()
        floating_ip_ids_admin = [f['id'] for f in body['floatingips']]
        # Check that admin sees all floating ips
        self.assertIn(self.floating_ip['id'], floating_ip_ids_admin)
        self.assertIn(floating_ip_admin['floatingip']['id'],
                      floating_ip_ids_admin)
        self.assertIn(floating_ip_alt['id'], floating_ip_ids_admin)
        # List floating ips from nonadmin
        resp, body = self.client.list_floatingips()
        floating_ip_ids = [f['id'] for f in body['floatingips']]
        # Check that nonadmin user doesn't see floating ip created from admin
        # and floating ip that is created in another tenant (alt user)
        self.assertIn(self.floating_ip['id'], floating_ip_ids)
        self.assertNotIn(floating_ip_admin['floatingip']['id'],
                         floating_ip_ids)
        self.assertNotIn(floating_ip_alt['id'], floating_ip_ids)


class FloatingIPAdminTestXML(FloatingIPAdminTestJSON):
    _interface = 'xml'
