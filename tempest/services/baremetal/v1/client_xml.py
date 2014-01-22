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
from tempest.services.baremetal.v1 import base_v1 as base
from tempest.services.compute.xml import common as xml


class BaremetalClientXML(rest_client.RestClientXML, base.BaremetalClientV1):
    """Tempest REST client for Ironic XML API v1."""

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(BaremetalClientXML, self).__init__(config, username, password,
                                                 auth_url, tenant_name)

        self.serialize = self.json_to_xml
        self.deserialize = xml.xml_to_json

    def json_to_xml(self, object_type, object_dict):
        """
        Brainlessly converts a specification of an object to XML string.

        :param object_type: Kind of the object.
        :param object_dict: Specification of the object attributes as a dict.
        :return: An XML string that corresponds to the specification.

        """
        root = xml.Element(object_type)

        for attr_name, value in object_dict:
            # Handle nested dictionaries
            if isinstance(value, dict):
                value = self.json_to_xml(attr_name, value)

            root.append(xml.Element(attr_name, value))

        return str(xml.Document(root))

    def _patch_request(self, resource_name, uuid, patch_object):
        """Changes Content-Type header to application/json for jsonpatch."""

        self.headers['Content-Type'] = 'application/json'
        try:
            super(self)._patch_request(self, resource_name, uuid, patch_object)
        finally:
            self.headers['Content-Type'] = 'application/xml'
