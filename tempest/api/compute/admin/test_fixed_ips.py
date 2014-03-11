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
    def setUpClass(cls):
        super(FixedIPsTestJson, cls).setUpClass()
        if CONF.service_available.neutron:
            msg = ("%s skipped as neutron is available" % cls.__name__)
            raise cls.skipException(msg)
        cls.client = cls.os_adm.fixed_ips_client
        resp, server = cls.create_test_server(wait_until='ACTIVE')
        resp, server = cls.servers_client.get_server(server['id'])
        for ip_set in server['addresses']:
            for ip in server['addresses'][ip_set]:
                if ip['OS-EXT-IPS:type'] == 'fixed':
                    cls.ip = ip['addr']
                    break
            if cls.ip:
                break

    @test.attr(type='gate')
    def test_list_fixed_ip_details(self):
        resp, fixed_ip = self.client.get_fixed_ip_details(self.ip)
        self.assertEqual(fixed_ip['address'], self.ip)

    @test.attr(type='gate')
    def test_set_reserve(self):
        body = {"reserve": "None"}
        resp, body = self.client.reserve_fixed_ip(self.ip, body)
        self.assertEqual(resp.status, 202)

    @test.attr(type='gate')
    def test_set_unreserve(self):
        body = {"unreserve": "None"}
        resp, body = self.client.reserve_fixed_ip(self.ip, body)
        self.assertEqual(resp.status, 202)


class FixedIPsTestXml(FixedIPsTestJson):
    _interface = 'xml'
