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

from tempest.api.compute import base
from tempest.common import utils
from tempest import config

CONF = config.CONF


class BaseFloatingIPsTest(base.BaseV2ComputeTest):

    @classmethod
    def setup_credentials(cls):
        # Floating IP actions might need a full network configuration
        cls.set_network_resources(network=True, subnet=True,
                                  router=True, dhcp=True)
        super(BaseFloatingIPsTest, cls).setup_credentials()

    @classmethod
    def skip_checks(cls):
        super(BaseFloatingIPsTest, cls).skip_checks()
        if not utils.get_service_list()['network']:
            raise cls.skipException("network service not enabled.")
        if not CONF.network_feature_enabled.floating_ips:
            raise cls.skipException("Floating ips are not available")

    @classmethod
    def setup_clients(cls):
        super(BaseFloatingIPsTest, cls).setup_clients()
        cls.client = cls.floating_ips_client
        cls.pools_client = cls.floating_ip_pools_client
