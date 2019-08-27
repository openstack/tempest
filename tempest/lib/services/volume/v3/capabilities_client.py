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

from tempest.lib.api_schema.response.volume import capabilities as schema
from tempest.lib.common import rest_client


class CapabilitiesClient(rest_client.RestClient):

    def show_backend_capabilities(self, host):
        """Shows capabilities for a storage back end.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/index.html#show-back-end-capabilities
        """
        url = 'capabilities/%s' % host
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.show_backend_capabilities, resp, body)
        return rest_client.ResponseBody(resp, body)
