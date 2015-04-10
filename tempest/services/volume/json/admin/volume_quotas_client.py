# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

from oslo_serialization import jsonutils

from tempest.common import service_client


class BaseVolumeQuotasClientJSON(service_client.ServiceClient):
    """
    Client class to send CRUD Volume Quotas API requests to a Cinder endpoint
    """

    TYPE = "json"

    def show_default_quota_set(self, tenant_id):
        """List the default volume quota set for a tenant."""

        url = 'os-quota-sets/%s/defaults' % tenant_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, self._parse_resp(body))

    def show_quota_set(self, tenant_id, params=None):
        """List the quota set for a tenant."""

        url = 'os-quota-sets/%s' % tenant_id
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, self._parse_resp(body))

    def show_quota_usage(self, tenant_id):
        """List the quota set for a tenant."""

        body = self.show_quota_set(tenant_id, params={'usage': True})
        return body

    def update_quota_set(self, tenant_id, gigabytes=None, volumes=None,
                         snapshots=None):
        post_body = {}

        if gigabytes is not None:
            post_body['gigabytes'] = gigabytes

        if volumes is not None:
            post_body['volumes'] = volumes

        if snapshots is not None:
            post_body['snapshots'] = snapshots

        post_body = jsonutils.dumps({'quota_set': post_body})
        resp, body = self.put('os-quota-sets/%s' % tenant_id, post_body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, self._parse_resp(body))

    def delete_quota_set(self, tenant_id):
        """Delete the tenant's quota set."""
        resp, body = self.delete('os-quota-sets/%s' % tenant_id)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body)


class VolumeQuotasClientJSON(BaseVolumeQuotasClientJSON):
    """
    Client class to send CRUD Volume Type API V1 requests to a Cinder endpoint
    """
