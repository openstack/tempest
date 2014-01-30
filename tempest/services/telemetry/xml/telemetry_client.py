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

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import xml_to_json
import tempest.services.telemetry.telemetry_client_base as client


class TelemetryClientXML(client.TelemetryClientBase):

    def get_rest_client(self, username,
                        password, auth_url, tenant_name=None):
        return RestClientXML(username, password, auth_url, tenant_name)

    def _parse_array(self, body):
        array = []
        for child in body.getchildren():
            array.append(xml_to_json(child))
        return array

    def serialize(self, body):
        return str(Document(body))

    def deserialize(self, body):
        return self._parse_array(etree.fromstring(body))
