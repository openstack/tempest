# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 NTT Data
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

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import xml_to_json
from tempest.services.compute.xml.common import XMLNS_11


class QuotasClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(QuotasClientXML, self).__init__(config, username, password,
                                              auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def _format_quota(self, q):
        quota = {}
        for k, v in q.items():
            try:
                v = int(v)
            except ValueError:
                pass

            quota[k] = v

        return quota

    def _parse_array(self, node):
        return [self._format_quota(xml_to_json(x)) for x in node]

    def get_quota_set(self, tenant_id):
        """List the quota set for a tenant."""

        url = 'os-quota-sets/%s' % str(tenant_id)
        resp, body = self.get(url, self.headers)
        body = xml_to_json(etree.fromstring(body))
        body = self._format_quota(body)
        return resp, body
