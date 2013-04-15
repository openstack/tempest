# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest import exceptions
from tempest.test import attr
from tempest.tests.compute import base


class FixedIPsBase(base.BaseComputeAdminTest):
    _interface = 'json'
    ip = None

    @classmethod
    def setUpClass(cls):
        super(FixedIPsBase, cls).setUpClass()
        # NOTE(maurosr): The idea here is: the server creation is just an
        # auxiliary element to the ip details or reservation, there was no way
        # (at least none in my mind) to get an valid and existing ip except
        # by creating a server and using its ip. So the intention is to create
        # fewer server possible (one) and use it to both: json and xml tests.
        # This decreased time to run both tests, in my test machine, from 53
        # secs to 29 (agains 23 secs when running only json tests)
        if cls.ip is None:
            cls.client = cls.os_adm.fixed_ips_client
            cls.non_admin_client = cls.fixed_ips_client
            resp, server = cls.create_server(wait_until='ACTIVE')
            resp, server = cls.servers_client.get_server(server['id'])
            for ip_set in server['addresses']:
                for ip in server['addresses'][ip_set]:
                    if ip['OS-EXT-IPS:type'] == 'fixed':
                        cls.ip = ip['addr']
                        break
                if cls.ip:
                    break


class FixedIPsTestJson(FixedIPsBase):
    _interface = 'json'

    @attr(type='positive')
    def test_list_fixed_ip_details(self):
        resp, fixed_ip = self.client.get_fixed_ip_details(self.ip)
        self.assertEqual(fixed_ip['address'], self.ip)

    @attr(type='negative')
    def test_list_fixed_ip_details_with_non_admin_user(self):
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.get_fixed_ip_details, self.ip)

    @attr(type='positive')
    def test_set_reserve(self):
        body = {"reserve": "None"}
        resp, body = self.client.reserve_fixed_ip(self.ip, body)
        self.assertEqual(resp.status, 202)

    @attr(type='positive')
    def test_set_unreserve(self):
        body = {"unreserve": "None"}
        resp, body = self.client.reserve_fixed_ip(self.ip, body)
        self.assertEqual(resp.status, 202)

    @attr(type='negative')
    def test_set_reserve_with_non_admin_user(self):
        body = {"reserve": "None"}
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.reserve_fixed_ip,
                          self.ip, body)

    @attr(type='negative')
    def test_set_unreserve_with_non_admin_user(self):
        body = {"unreserve": "None"}
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.reserve_fixed_ip,
                          self.ip, body)

    @attr(type='negative')
    def test_set_reserve_with_invalid_ip(self):
        # NOTE(maurosr): since this exercises the same code snippet, we do it
        # only for reserve action
        body = {"reserve": "None"}
        self.assertRaises(exceptions.NotFound,
                          self.client.reserve_fixed_ip,
                          "my.invalid.ip", body)

    @attr(type='negative')
    def test_fixed_ip_with_invalid_action(self):
        body = {"invalid_action": "None"}
        self.assertRaises(exceptions.BadRequest,
                          self.client.reserve_fixed_ip,
                          self.ip, body)


class FixedIPsTestXml(FixedIPsTestJson):
    _interface = 'xml'
