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

from tempest.api_schema.response.compute.v3 import extensions as schema
from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class ExtensionsV3ClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(ExtensionsV3ClientJSON, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_v3_type

    def list_extensions(self):
        url = 'extensions'
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_extensions, resp, body)
        return resp, body['extensions']

    def is_enabled(self, extension):
        _, extensions = self.list_extensions()
        exts = extensions['extensions']
        return any([e for e in exts if e['name'] == extension])

    def get_extension(self, extension_alias):
        resp, body = self.get('extensions/%s' % extension_alias)
        body = json.loads(body)
        return resp, body['extension']
