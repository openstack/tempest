# Copyright 2013 NEC Corporation.  All rights reserved.
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

from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class FixedIPsNegativeTestJson(base.BaseV2ComputeAdminTest):

    @classmethod
    def skip_checks(cls):
        super(FixedIPsNegativeTestJson, cls).skip_checks()
        if CONF.service_available.neutron:
            msg = ("%s skipped as neutron is available" % cls.__name__)
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(FixedIPsNegativeTestJson, cls).setup_clients()
        cls.client = cls.os_adm.fixed_ips_client
        cls.non_admin_client = cls.fixed_ips_client

    @classmethod
    def resource_setup(cls):
        super(FixedIPsNegativeTestJson, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        server = cls.servers_client.get_server(server['id'])
        for ip_set in server['addresses']:
            for ip in server['addresses'][ip_set]:
                if ip['OS-EXT-IPS:type'] == 'fixed':
                    cls.ip = ip['addr']
                    break
            if cls.ip:
                break

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('9f17f47d-daad-4adc-986e-12370c93e407')
    @test.services('network')
    def test_list_fixed_ip_details_with_non_admin_user(self):
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.get_fixed_ip_details, self.ip)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ce60042c-fa60-4836-8d43-1c8e3359dc47')
    @test.services('network')
    def test_set_reserve_with_non_admin_user(self):
        body = {"reserve": "None"}
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.reserve_fixed_ip,
                          self.ip, body)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f1f7a35b-0390-48c5-9803-5f27461439db')
    @test.services('network')
    def test_set_unreserve_with_non_admin_user(self):
        body = {"unreserve": "None"}
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.reserve_fixed_ip,
                          self.ip, body)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f51cf464-7fc5-4352-bc3e-e75cfa2cb717')
    @test.services('network')
    def test_set_reserve_with_invalid_ip(self):
        # NOTE(maurosr): since this exercises the same code snippet, we do it
        # only for reserve action
        body = {"reserve": "None"}
        # NOTE(eliqiao): in Juno, the exception is NotFound, but in master, we
        # change the error code to BadRequest, both exceptions should be
        # accepted by tempest
        self.assertRaises((lib_exc.NotFound, lib_exc.BadRequest),
                          self.client.reserve_fixed_ip,
                          "my.invalid.ip", body)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('fd26ef50-f135-4232-9d32-281aab3f9176')
    @test.services('network')
    def test_fixed_ip_with_invalid_action(self):
        body = {"invalid_action": "None"}
        self.assertRaises(lib_exc.BadRequest,
                          self.client.reserve_fixed_ip,
                          self.ip, body)
