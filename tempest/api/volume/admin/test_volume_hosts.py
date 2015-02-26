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

from tempest.api.volume import base
from tempest import test


class VolumeHostsAdminV2TestsJSON(base.BaseVolumeAdminTest):

    @test.attr(type='gate')
    @test.idempotent_id('d5f3efa2-6684-4190-9ced-1c2f526352ad')
    def test_list_hosts(self):
        hosts = self.hosts_client.list_hosts()
        self.assertTrue(len(hosts) >= 2, "No. of hosts are < 2,"
                        "response of list hosts is: % s" % hosts)


class VolumeHostsAdminV1TestsJSON(VolumeHostsAdminV2TestsJSON):
    _api_version = 1
