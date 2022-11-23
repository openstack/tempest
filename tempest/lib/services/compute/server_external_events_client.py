# Copyright 2022 NEC Corporation.  All rights reserved.
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

from tempest.lib.api_schema.response.compute.v2_1 import \
    server_external_events as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class ServerExternalEventsClient(base_compute_client.BaseComputeClient):

    def create_server_external_events(self, events):
        """Create Server External Events.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#run-events
        """
        post_body = json.dumps({'events': events})
        resp, body = self.post("os-server-external-events", post_body)
        body = json.loads(body)
        self.validate_response(schema.create, resp, body)
        return rest_client.ResponseBody(resp, body)
