# Copyright 2016 Red Hat, Inc.
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

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class SchedulerStatsClient(rest_client.RestClient):

    def list_pools(self, detail=False):
        """List all the volumes pools (hosts).

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-all-back-end-storage-pools
        """
        url = 'scheduler-stats/get_pools'
        if detail:
            url += '?detail=True'
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)
