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

import ast

from lxml import etree

from tempest.common import xml_utils as xml
from tempest import config
from tempest.services.volume.json.admin import volume_quotas_client

CONF = config.CONF


class VolumeQuotasClientXML(volume_quotas_client.VolumeQuotasClientJSON):
    """
    Client class to send CRUD Volume Quotas API requests to a Cinder endpoint
    """

    TYPE = "xml"

    def _format_quota(self, q):
        quota = {}
        for k, v in q.items():
            try:
                v = ast.literal_eval(v)
            except (ValueError, SyntaxError):
                pass

            quota[k] = v

        return quota

    def get_quota_usage(self, tenant_id):
        """List the quota set for a tenant."""

        resp, body = self.get_quota_set(tenant_id, params={'usage': True})
        self.expected_success(200, resp.status)
        return resp, self._format_quota(body)

    def update_quota_set(self, tenant_id, gigabytes=None, volumes=None,
                         snapshots=None):
        post_body = {}
        element = xml.Element("quota_set")

        if gigabytes is not None:
            post_body['gigabytes'] = gigabytes

        if volumes is not None:
            post_body['volumes'] = volumes

        if snapshots is not None:
            post_body['snapshots'] = snapshots

        xml.deep_dict_to_xml(element, post_body)
        resp, body = self.put('os-quota-sets/%s' % tenant_id,
                              str(xml.Document(element)))
        body = xml.xml_to_json(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, self._format_quota(body)

    def delete_quota_set(self, tenant_id):
        """Delete the tenant's quota set."""
        resp, body = self.delete('os-quota-sets/%s' % tenant_id)
        self.expected_success(200, resp.status)
