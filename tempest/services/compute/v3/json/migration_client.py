# Copyright 2014 NEC Corporation.
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

import urllib

from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class MigrationsV3ClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(MigrationsV3ClientJSON, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_v3_type

    def list_migrations(self, params=None):
        """Lists all migrations."""

        url = 'os-migrations'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        return resp, self._parse_resp(body)
