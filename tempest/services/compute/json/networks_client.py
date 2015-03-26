# Copyright 2012 OpenStack Foundation
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

import json

from tempest.common import service_client


class NetworksClientJSON(service_client.ServiceClient):

    def list_networks(self, name=None):
        resp, body = self.get("os-networks")
        body = json.loads(body)
        self.expected_success(200, resp.status)
        if name:
            networks = [n for n in body['networks'] if n['label'] == name]
        else:
            networks = body['networks']
        return service_client.ResponseBodyList(resp, networks)

    def get_network(self, network_id):
        resp, body = self.get("os-networks/%s" % str(network_id))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['network'])
