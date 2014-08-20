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

from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class NetworksClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(NetworksClientJSON, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def list_networks(self):
        resp, body = self.get("os-networks")
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['networks']

    def get_network(self, network_id):
        resp, body = self.get("os-networks/%s" % str(network_id))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['network']
