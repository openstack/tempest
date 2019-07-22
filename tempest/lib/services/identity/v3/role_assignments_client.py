# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class RoleAssignmentsClient(rest_client.RestClient):
    api_version = "v3"

    def list_role_assignments(self, effective=False, **kwargs):
        """List role assignments.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#list-role-assignments

        :param effective: If True, returns the effective assignments, including
                          any assignments gained by virtue of group membership
                          or inherited roles.
        """
        url = 'role_assignments'
        if kwargs:
            # NOTE(rodrigods): "effective" is a key-only query parameter and
            # is treated below.
            if 'effective' in kwargs:
                del kwargs['effective']
            url += '?%s' % urllib.urlencode(kwargs)
        if effective:
            url += '&effective'

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
