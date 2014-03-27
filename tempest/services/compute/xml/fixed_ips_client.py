# Copyright 2013 IBM Corp
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


from tempest.common import rest_client
from tempest.common import xml_utils
from tempest import config

CONF = config.CONF


class FixedIPsClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(FixedIPsClientXML, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def get_fixed_ip_details(self, fixed_ip):
        url = "os-fixed-ips/%s" % (fixed_ip)
        resp, body = self.get(url)
        body = self._parse_resp(body)
        return resp, body

    def reserve_fixed_ip(self, ip, body):
        """This reserves and unreserves fixed ips."""
        url = "os-fixed-ips/%s/action" % (ip)
        # NOTE(maurosr): First converts the dict body to a json string then
        # accept any action key value here to permit tests to cover cases with
        # invalid actions raising badrequest.
        key, value = body.popitem()
        xml_body = xml_utils.Element(key)
        xml_body.append(xml_utils.Text(value))
        resp, body = self.post(url, str(xml_utils.Document(xml_body)))
        return resp, body
