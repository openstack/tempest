# Copyright 2014 NEC Corporation.
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

from tempest.api_schema.response.compute import version as schema
from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class VersionV3ClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(VersionV3ClientJSON, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_v3_type

    def get_version(self):
        resp, body = self.get('')
        body = json.loads(body)
        self.validate_response(schema.version, resp, body)
        return resp, body['version']
