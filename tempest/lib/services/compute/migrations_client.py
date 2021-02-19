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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.compute.v2_1 import migrations as schema
from tempest.lib.api_schema.response.compute.v2_23 import migrations \
    as schemav223
from tempest.lib.api_schema.response.compute.v2_59 import migrations \
    as schemav259
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class MigrationsClient(base_compute_client.BaseComputeClient):
    schema_versions_info = [
        {'min': None, 'max': '2.22', 'schema': schema},
        {'min': '2.23', 'max': '2.58', 'schema': schemav223},
        {'min': '2.59', 'max': None, 'schema': schemav259}]

    def list_migrations(self, **params):
        """List all migrations.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#list-migrations
        """

        url = 'os-migrations'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.list_migrations, resp, body)
        return rest_client.ResponseBody(resp, body)
