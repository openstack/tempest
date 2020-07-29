# Copyright 2015 GlobalLogic.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.api.network import base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class SubnetPoolsTestJSON(base.BaseNetworkTest):
    """Tests the following operations in the subnetpools API:

        Create a subnet pool.
        Update a subnet pool.
        Delete a subnet pool.
        Lists subnet pool.
        Show subnet pool details.

    v2.0 of the Neutron API is assumed. It is assumed that subnet_allocation
    options mentioned in the [network-feature-enabled] section and
    default_network option mentioned in the [network] section of
    etc/tempest.conf:

    """

    @classmethod
    def skip_checks(cls):
        super(SubnetPoolsTestJSON, cls).skip_checks()
        if not utils.is_extension_enabled('subnet_allocation', 'network'):
            msg = "subnet_allocation extension not enabled."
            raise cls.skipException(msg)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('62595970-ab1c-4b7f-8fcc-fddfe55e9811')
    def test_create_list_show_update_delete_subnetpools(self):
        """Test create/list/show/update/delete of subnet pools"""
        subnetpool_name = data_utils.rand_name('subnetpools')
        # create subnet pool
        prefix = CONF.network.default_network
        body = self.subnetpools_client.create_subnetpool(name=subnetpool_name,
                                                         prefixes=prefix)
        subnetpool_id = body["subnetpool"]["id"]
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.subnetpools_client.delete_subnetpool,
                        subnetpool_id)
        self.assertEqual(subnetpool_name, body["subnetpool"]["name"])
        # get detail about subnet pool
        body = self.subnetpools_client.show_subnetpool(subnetpool_id)
        self.assertEqual(subnetpool_name, body["subnetpool"]["name"])
        # update the subnet pool
        subnetpool_name = data_utils.rand_name('subnetpools_update')
        body = self.subnetpools_client.update_subnetpool(subnetpool_id,
                                                         name=subnetpool_name)
        self.assertEqual(subnetpool_name, body["subnetpool"]["name"])
        # delete subnet pool
        body = self.subnetpools_client.delete_subnetpool(subnetpool_id)
        self.assertRaises(lib_exc.NotFound,
                          self.subnetpools_client.show_subnetpool,
                          subnetpool_id)
