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

from tempest.api.compute import base
from tempest.common import utils
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class FixedIPsNegativeTestJson(base.BaseV2ComputeAdminTest):
    """Negative tests of fixed ips API"""

    @classmethod
    def skip_checks(cls):
        super(FixedIPsNegativeTestJson, cls).skip_checks()
        if CONF.service_available.neutron:
            msg = ("%s skipped as neutron is available" % cls.__name__)
            raise cls.skipException(msg)
        if not utils.get_service_list()['network']:
            raise cls.skipException("network service not enabled.")

    @classmethod
    def setup_clients(cls):
        super(FixedIPsNegativeTestJson, cls).setup_clients()
        cls.client = cls.os_admin.fixed_ips_client
        cls.non_admin_client = cls.fixed_ips_client

    @classmethod
    def resource_setup(cls):
        super(FixedIPsNegativeTestJson, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        server = cls.servers_client.show_server(server['id'])['server']
        cls.ip = None
        for ip_set in server['addresses']:
            for ip in server['addresses'][ip_set]:
                if ip['OS-EXT-IPS:type'] == 'fixed':
                    cls.ip = ip['addr']
                    break
            if cls.ip:
                break
        if cls.ip is None:
            raise cls.skipException("No fixed ip found for server: %s"
                                    % server['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9f17f47d-daad-4adc-986e-12370c93e407')
    def test_list_fixed_ip_details_with_non_admin_user(self):
        """Test listing fixed ip with detail by non-admin user is forbidden"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.show_fixed_ip, self.ip)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ce60042c-fa60-4836-8d43-1c8e3359dc47')
    def test_set_reserve_with_non_admin_user(self):
        """Test reserving fixed ip by non-admin user is forbidden"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.reserve_fixed_ip,
                          self.ip, reserve="None")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f1f7a35b-0390-48c5-9803-5f27461439db')
    def test_set_unreserve_with_non_admin_user(self):
        """Test unreserving fixed ip by non-admin user is forbidden"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.reserve_fixed_ip,
                          self.ip, unreserve="None")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f51cf464-7fc5-4352-bc3e-e75cfa2cb717')
    def test_set_reserve_with_invalid_ip(self):
        """Test reserving invalid fixed ip should fail"""
        # NOTE(maurosr): since this exercises the same code snippet, we do it
        # only for reserve action
        # NOTE(eliqiao): in Juno, the exception is NotFound, but in master, we
        # change the error code to BadRequest, both exceptions should be
        # accepted by tempest
        self.assertRaises((lib_exc.NotFound, lib_exc.BadRequest),
                          self.client.reserve_fixed_ip,
                          "my.invalid.ip", reserve="None")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('fd26ef50-f135-4232-9d32-281aab3f9176')
    def test_fixed_ip_with_invalid_action(self):
        """Test operating fixed ip with invalid action should fail"""
        self.assertRaises(lib_exc.BadRequest,
                          self.client.reserve_fixed_ip,
                          self.ip, invalid_action="None")
