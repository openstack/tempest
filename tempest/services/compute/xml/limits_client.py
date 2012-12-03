# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 IBM
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

from tempest.common.rest_client import RestClientXML
from lxml import etree
from lxml import objectify

NS = "{http://docs.openstack.org/common/api/v1.0}"


class LimitsClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(LimitsClientXML, self).__init__(config, username, password,
                                              auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def get_absolute_limits(self):
        resp, body = self.get("limits", self.headers)
        body = objectify.fromstring(body)
        lim = NS + 'absolute'
        ret = {}

        for el in body[lim].iterchildren():
            attributes = el.attrib
            ret[attributes['name']] = attributes['value']
        return resp, ret

    def get_specific_absolute_limit(self, absolute_limit):
        resp, body = self.get("limits", self.headers)
        body = objectify.fromstring(body)
        lim = NS + 'absolute'
        ret = {}

        for el in body[lim].iterchildren():
            attributes = el.attrib
            ret[attributes['name']] = attributes['value']
        if absolute_limit not in ret:
            return None
        else:
            return ret[absolute_limit]
