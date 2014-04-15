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

from tempest.common import rest_client
from tempest.common import xml_utils
from tempest import config
from tempest import exceptions

CONF = config.CONF


class AggregatesClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(AggregatesClientXML, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def _format_aggregate(self, g):
        agg = xml_utils.xml_to_json(g)
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
        resp, body = self.get("os-aggregates")
        aggregates = self._parse_array(etree.fromstring(body))
        return resp, aggregates

    def get_aggregate(self, aggregate_id):
        """Get details of the given aggregate."""
        resp, body = self.get("os-aggregates/%s" % str(aggregate_id))
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate

    def create_aggregate(self, name, availability_zone=None):
        """Creates a new aggregate."""
        if availability_zone is not None:
            post_body = xml_utils.Element("aggregate", name=name,
                                          availability_zone=availability_zone)
        else:
            post_body = xml_utils.Element("aggregate", name=name)
        resp, body = self.post('os-aggregates',
                               str(xml_utils.Document(post_body)))
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate

    def update_aggregate(self, aggregate_id, name, availability_zone=None):
        """Update a aggregate."""
        if availability_zone is not None:
            put_body = xml_utils.Element("aggregate", name=name,
                                         availability_zone=availability_zone)
        else:
            put_body = xml_utils.Element("aggregate", name=name)
        resp, body = self.put('os-aggregates/%s' % str(aggregate_id),
                              str(xml_utils.Document(put_body)))
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate

    def delete_aggregate(self, aggregate_id):
        """Deletes the given aggregate."""
        return self.delete("os-aggregates/%s" % str(aggregate_id))

    def is_resource_deleted(self, id):
        try:
            self.get_aggregate(id)
        except exceptions.NotFound:
            return True
        return False

    def add_host(self, aggregate_id, host):
        """Adds a host to the given aggregate."""
        post_body = xml_utils.Element("add_host", host=host)
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               str(xml_utils.Document(post_body)))
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate

    def remove_host(self, aggregate_id, host):
        """Removes a host from the given aggregate."""
        post_body = xml_utils.Element("remove_host", host=host)
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               str(xml_utils.Document(post_body)))
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate

    def set_metadata(self, aggregate_id, meta):
        """Replaces the aggregate's existing metadata with new metadata."""
        post_body = xml_utils.Element("set_metadata")
        metadata = xml_utils.Element("metadata")
        post_body.append(metadata)
        for k, v in meta.items():
            meta = xml_utils.Element(k)
            meta.append(xml_utils.Text(v))
            metadata.append(meta)
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               str(xml_utils.Document(post_body)))
        aggregate = self._format_aggregate(etree.fromstring(body))
        return resp, aggregate
