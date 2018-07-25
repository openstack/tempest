# Copyright 2018 NEC Corporation.
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
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class FlavorsV255TestJSON(base.BaseV2ComputeAdminTest):
    min_microversion = '2.55'
    max_microversion = 'latest'

    # NOTE(gmann): This class tests the flavors APIs
    # response schema for the 2.55 microversion.

    @decorators.idempotent_id('61976b25-488d-41dc-9dcb-cb9693a7b075')
    def test_crud_flavor(self):
        flavor_id = data_utils.rand_int_id(start=1000)
        # Checking create API response schema
        new_flavor_id = self.create_flavor(ram=512,
                                           vcpus=1,
                                           disk=10,
                                           id=flavor_id)['id']
        # Checking show API response schema
        self.flavors_client.show_flavor(new_flavor_id)
        # Checking update API response schema
        self.admin_flavors_client.update_flavor(new_flavor_id,
                                                description='new')
        # Checking list details API response schema
        self.flavors_client.list_flavors(detail=True)
        # Checking list API response schema
        self.flavors_client.list_flavors()


class FlavorsV261TestJSON(FlavorsV255TestJSON):
    min_microversion = '2.61'
    max_microversion = 'latest'

    # NOTE(gmann): This class tests the flavors APIs
    # response schema for the 2.61 microversion.
