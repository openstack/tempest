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
import testtools

from tempest.api.network import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class ExternalNetworksAdminNegativeTestJSON(base.BaseAdminNetworkTest):
    """Negative tests of external network"""

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d402ae6c-0be0-4d8e-833b-a738895d98d0')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_create_port_with_precreated_floatingip_as_fixed_ip(self):
        """Test creating port with precreated floating ip as fixed ip

        NOTE: External networks can be used to create both floating-ip as
        well as instance-ip. So, creating an instance-ip with a value of a
        pre-created floating-ip should be denied.
        """
        # create a floating ip
        body = self.admin_floating_ips_client.create_floatingip(
            floating_network_id=CONF.network.public_network_id)
        created_floating_ip = body['floatingip']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_floating_ips_client.delete_floatingip,
                        created_floating_ip['id'])
        floating_ip_address = created_floating_ip['floating_ip_address']
        self.assertIsNotNone(floating_ip_address)

        # use the same value of floatingip as fixed-ip to create_port()
        fixed_ips = [{'ip_address': floating_ip_address}]

        # create a port which will internally create an instance-ip
        self.assertRaises(lib_exc.Conflict,
                          self.admin_ports_client.create_port,
                          name=data_utils.rand_name(self.__class__.__name__),
                          network_id=CONF.network.public_network_id,
                          fixed_ips=fixed_ips)
