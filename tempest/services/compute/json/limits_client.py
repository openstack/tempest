# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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
from tempest.common.rest_client import RestClient


class LimitsClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(LimitsClientJSON, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def get_limits(self):
        resp, body = self.get("limits")
        body = json.loads(body)
        return resp, body['limits']

    def get_max_server_meta(self):
        resp, limits_dict = self.get_limits()
        return resp, limits_dict['absolute']['maxServerMeta']

    def get_personality_file_limit(self):
        resp, limits_dict = self.get_limits()
        return resp, limits_dict['absolute']['maxPersonality']

    def get_personality_size_limit(self):
        resp, limits_dict = self.get_limits()
        return resp, limits_dict['absolute']['maxPersonalitySize']
