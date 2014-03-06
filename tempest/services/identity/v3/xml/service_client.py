# Copyright 2013 OpenStack Foundation
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

from tempest.common import rest_client
from tempest import config
from tempest.services.compute.xml import common

CONF = config.CONF

XMLNS = "http://docs.openstack.org/identity/api/v3"


class ServiceClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(ServiceClientXML, self).__init__(auth_provider)
        self.service = CONF.identity.catalog_type
        self.endpoint_url = 'adminURL'
        self.api_version = "v3"

    def _parse_body(self, body):
        data = common.xml_to_json(body)
        return data

    def update_service(self, service_id, **kwargs):
        """Updates a service_id."""
        resp, body = self.get_service(service_id)
        name = kwargs.get('name', body['name'])
        description = kwargs.get('description', body['description'])
        type = kwargs.get('type', body['type'])
        update_service = common.Element("service",
                                        xmlns=XMLNS,
                                        id=service_id,
                                        name=name,
                                        description=description,
                                        type=type)
        resp, body = self.patch('services/%s' % service_id,
                                str(common.Document(update_service)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_service(self, service_id):
        """Get Service."""
        url = 'services/%s' % service_id
        resp, body = self.get(url)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def create_service(self, serv_type, name=None, description=None):
        post_body = common.Element("service",
                                   xmlns=XMLNS,
                                   name=name,
                                   description=description,
                                   type=serv_type)
        resp, body = self.post("services", str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_service(self, serv_id):
        url = "services/" + serv_id
        resp, body = self.delete(url)
        return resp, body
