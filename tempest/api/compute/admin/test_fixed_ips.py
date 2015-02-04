# Copyright 2013 IBM Corp
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

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class FixedIPsTestJson(base.BaseV2ComputeAdminTest):

    @classmethod
    def skip_checks(cls):
        super(FixedIPsTestJson, cls).skip_checks()
        if CONF.service_available.neutron:
            msg = ("%s skipped as neutron is available" % cls.__name__)
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(FixedIPsTestJson, cls).setup_clients()
        cls.client = cls.os_adm.fixed_ips_client

    @classmethod
    def resource_setup(cls):
        super(FixedIPsTestJson, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        server = cls.servers_client.get_server(server['id'])
        for ip_set in server['addresses']:
            for ip in server['addresses'][ip_set]:
                if ip['OS-EXT-IPS:type'] == 'fixed':
                    cls.ip = ip['addr']
                    break
            if cls.ip:
                break

    @test.attr(type='gate')
    @test.idempotent_id('16b7d848-2f7c-4709-85a3-2dfb4576cc52')
    @test.services('network')
    def test_list_fixed_ip_details(self):
        fixed_ip = self.client.get_fixed_ip_details(self.ip)
        self.assertEqual(fixed_ip['address'], self.ip)

    @test.attr(type='gate')
    @test.idempotent_id('5485077b-7e46-4cec-b402-91dc3173433b')
    @test.services('network')
    def test_set_reserve(self):
        body = {"reserve": "None"}
        self.client.reserve_fixed_ip(self.ip, body)

    @test.attr(type='gate')
    @test.idempotent_id('7476e322-b9ff-4710-bf82-49d51bac6e2e')
    @test.services('network')
    def test_set_unreserve(self):
        body = {"unreserve": "None"}
        self.client.reserve_fixed_ip(self.ip, body)
