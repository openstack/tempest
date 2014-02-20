# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Author: Sylvain Baubeau <sylvain.baubeau@enovance.com>
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

from tempest.openstack.common import jsonutils

from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class VolumeQuotasClientJSON(rest_client.RestClient):
    """
    Client class to send CRUD Volume Quotas API requests to a Cinder endpoint
    """

    TYPE = "json"

    def __init__(self, auth_provider):
        super(VolumeQuotasClientJSON, self).__init__(auth_provider)

        self.service = CONF.volume.catalog_type
        self.build_interval = CONF.volume.build_interval
        self.build_timeout = CONF.volume.build_timeout

    def get_default_quota_set(self, tenant_id):
        """List the default volume quota set for a tenant."""

        url = 'os-quota-sets/%s/defaults' % tenant_id
        resp, body = self.get(url)
        return resp, self._parse_resp(body)

    def get_quota_set(self, tenant_id, params=None):
        """List the quota set for a tenant."""

        url = 'os-quota-sets/%s' % tenant_id
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        return resp, self._parse_resp(body)

    def get_quota_usage(self, tenant_id):
        """List the quota set for a tenant."""

        resp, body = self.get_quota_set(tenant_id, params={'usage': True})
        return resp, body

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
        return resp, self._parse_resp(body)
