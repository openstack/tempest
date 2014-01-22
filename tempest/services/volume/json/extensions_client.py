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

from tempest.common.rest_client import RestClient


class ExtensionsClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ExtensionsClientJSON, self).__init__(config, username, password,
                                                   auth_url, tenant_name)
        self.service = self.config.volume.catalog_type

    def list_extensions(self):
        url = 'extensions'
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['extensions']
