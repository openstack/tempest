# Copyright 2013 OpenStack Foundation
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

from tempest.api.network import base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class RoutersAdminNegativeTest(base.BaseAdminNetworkTest):
    """Admin negative tests of routers"""

    @classmethod
    def skip_checks(cls):
        super(RoutersAdminNegativeTest, cls).skip_checks()
        if not utils.is_extension_enabled('router', 'network'):
            msg = "router extension not enabled."
            raise cls.skipException(msg)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7101cc02-058a-11e7-93e1-fa163e4fa634')
    @utils.requires_ext(extension='ext-gw-mode', service='network')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_router_set_gateway_used_ip_returns_409(self):
        """Test creating router with gateway set to used ip should fail"""
        # At first create a address from public_network_id
        port = self.admin_ports_client.create_port(
            name=data_utils.rand_name(self.__class__.__name__),
            network_id=CONF.network.public_network_id)['port']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_ports_client.delete_port,
                        port_id=port['id'])
        # Add used ip and subnet_id in external_fixed_ips
        fixed_ip = {
            'subnet_id': port['fixed_ips'][0]['subnet_id'],
            'ip_address': port['fixed_ips'][0]['ip_address']
        }
        external_gateway_info = {
            'network_id': CONF.network.public_network_id,
            'external_fixed_ips': [fixed_ip]
        }
        # Create a router and set gateway to used ip
        self.assertRaises(lib_exc.Conflict,
                          self.admin_routers_client.create_router,
                          external_gateway_info=external_gateway_info)


class RoutersAdminNegativeIpV6Test(RoutersAdminNegativeTest):
    _ip_version = 6
