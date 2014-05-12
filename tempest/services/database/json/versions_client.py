# Copyright 2014 OpenStack Foundation
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

import urllib

from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class DatabaseVersionsClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(DatabaseVersionsClientJSON, self).__init__(auth_provider)
        self.skip_path()
        self.service = CONF.database.catalog_type

    def list_db_versions(self, params=None):
        """List all versions."""
        url = ''
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        return resp, self._parse_resp(body)
