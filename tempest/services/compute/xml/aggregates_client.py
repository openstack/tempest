# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation.
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
from tempest import exceptions
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import xml_to_json


class AggregatesClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(AggregatesClientXML, self).__init__(config, username, password,
                                                  auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def _format_aggregate(self, g):
        agg = xml_to_json(g)
        aggregate = {}
        for key, value in agg.items():
            if key == 'hosts':
                aggregate['hosts'] = []
                for k, v in value.items():
                    aggregate['hosts'].append(v)
            elif key == 'availability_zone':
                aggregate[key] = None if value == 'None' else value
            else:
                aggregate[key] = value
        return aggregate

    def _parse_array(self, node):
        return [self._format_aggregate(x) for x in node]

    def list_aggregates(self):
        """Get aggregate list."""
        resp, body = self.get("os-aggregates", self.headers)
        aggregates = self._parse_array(etree.fromstring(body))
        return resp, aggregates

    def get_aggregate(self, aggregate_id):
        """Get details of the given aggregate."""
        resp, body = self.get("os-aggregates/%s" % str(aggregate_id),
                              self.headers)
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate

    def create_aggregate(self, name, availability_zone=None):
        """Creates a new aggregate."""
        post_body = Element("aggregate",
                            name=name,
                            availability_zone=availability_zone)
        resp, body = self.post('os-aggregates',
                               str(Document(post_body)),
                               self.headers)
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate

    def update_aggregate(self, aggregate_id, name, availability_zone=None):
        """Update a aggregate."""
        put_body = Element("aggregate",
                           name=name,
                           availability_zone=availability_zone)
        resp, body = self.put('os-aggregates/%s' % str(aggregate_id),
                              str(Document(put_body)),
                              self.headers)
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate

    def delete_aggregate(self, aggregate_id):
        """Deletes the given aggregate."""
        return self.delete("os-aggregates/%s" % str(aggregate_id),
                           self.headers)

    def is_resource_deleted(self, id):
        try:
            self.get_aggregate(id)
        except exceptions.NotFound:
            return True
        return False

    def add_host(self, aggregate_id, host):
        """Adds a host to the given aggregate."""
        post_body = Element("add_host", host=host)
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               str(Document(post_body)),
                               self.headers)
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate

    def remove_host(self, aggregate_id, host):
        """Removes a host from the given aggregate."""
        post_body = Element("remove_host", host=host)
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               str(Document(post_body)),
                               self.headers)
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate
