# Copyright 2014 NEC Technologies India Ltd.
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

import netaddr

from tempest.api.compute import base
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class FloatingIPsBulkAdminTestJSON(base.BaseV2ComputeAdminTest):
    """
    Tests Floating IPs Bulk APIs Create, List and  Delete that
    require admin privileges.
    API documentation - http://docs.openstack.org/api/openstack-compute/2/
    content/ext-os-floating-ips-bulk.html
    """

    @classmethod
    def setup_clients(cls):
        super(FloatingIPsBulkAdminTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.floating_ips_client

    @classmethod
    def resource_setup(cls):
        super(FloatingIPsBulkAdminTestJSON, cls).resource_setup()
        cls.ip_range = CONF.compute.floating_ip_range
        cls.verify_unallocated_floating_ip_range(cls.ip_range)

    @classmethod
    def verify_unallocated_floating_ip_range(cls, ip_range):
        # Verify whether configure floating IP range is not already allocated.
        body = cls.client.list_floating_ips_bulk()
        allocated_ips_list = map(lambda x: x['address'], body)
        for ip_addr in netaddr.IPNetwork(ip_range).iter_hosts():
            if str(ip_addr) in allocated_ips_list:
                msg = ("Configured unallocated floating IP range is already "
                       "allocated. Configure the correct unallocated range "
                       "as 'floating_ip_range'")
                raise exceptions.InvalidConfiguration(msg)
        return

    def _delete_floating_ips_bulk(self, ip_range):
        try:
            self.client.delete_floating_ips_bulk(ip_range)
        except Exception:
            pass

    @test.attr(type='gate')
    @test.idempotent_id('2c8f145f-8012-4cb8-ac7e-95a587f0e4ab')
    @test.services('network')
    def test_create_list_delete_floating_ips_bulk(self):
        # Create, List  and delete the Floating IPs Bulk
        pool = 'test_pool'
        # NOTE(GMann): Reserving the IP range but those are not attached
        # anywhere. Using the below mentioned interface which is not ever
        # expected to be used. Clean Up has been done for created IP range
        interface = 'eth0'
        body = self.client.create_floating_ips_bulk(self.ip_range,
                                                    pool,
                                                    interface)
        self.addCleanup(self._delete_floating_ips_bulk, self.ip_range)
        self.assertEqual(self.ip_range, body['ip_range'])
        ips_list = self.client.list_floating_ips_bulk()
        self.assertNotEqual(0, len(ips_list))
        for ip in netaddr.IPNetwork(self.ip_range).iter_hosts():
            self.assertIn(str(ip), map(lambda x: x['address'], ips_list))
        body = self.client.delete_floating_ips_bulk(self.ip_range)
        self.assertEqual(self.ip_range, body.data)
