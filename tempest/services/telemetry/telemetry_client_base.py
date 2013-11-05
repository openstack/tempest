# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import abc
import six
import urllib


@six.add_metaclass(abc.ABCMeta)
class TelemetryClientBase(object):

    """
    Tempest REST client for Ceilometer V2 API.
    Implements the following basic Ceilometer abstractions:
    resources
    meters
    alarms
    queries
    statistics
    """

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        self.rest_client = self.get_rest_client(config, username, password,
                                                auth_url, tenant_name)
        self.rest_client.service = \
            self.rest_client.config.telemetry.catalog_type
        self.headers = self.rest_client.headers
        self.version = '2'
        self.uri_prefix = "v%s" % self.version

    @abc.abstractmethod
    def get_rest_client(self, config, username, password,
                        auth_url, tenant_name):
        """
        :param config:
        :param username:
        :param password:
        :param auth_url:
        :param tenant_name:
        :return: RestClient
        """

    @abc.abstractmethod
    def deserialize(self, body):
        """
        :param body:
        :return: Deserialize body
        """

    @abc.abstractmethod
    def serialize(self, body):
        """
        :param body:
        :return: Serialize body
        """

    def post(self, uri, body):
        body = self.serialize(body)
        resp, body = self.rest_client.post(uri, body, self.headers)
        body = self.deserialize(body)
        return resp, body

    def put(self, uri, body):
        return self.rest_client.put(uri, body, self.headers)

    def get(self, uri):
        resp, body = self.rest_client.get(uri)
        body = self.deserialize(body)
        return resp, body

    def delete(self, uri):
        resp, body = self.rest_client.delete(uri)
        if body:
            body = self.deserialize(body)
        return resp, body

    def helper_list(self, uri, query=None, period=None):
        uri_dict = {}
        if query:
            uri_dict = {'q.field': query[0],
                        'q.op': query[1],
                        'q.value': query[2]}
        if period:
            uri_dict['period'] = period
        if uri_dict:
            uri += "?%s" % urllib.urlencode(uri_dict)
        return self.get(uri)

    def list_resources(self):
        uri = '%s/resources' % self.uri_prefix
        return self.get(uri)

    def list_meters(self):
        uri = '%s/meters' % self.uri_prefix
        return self.get(uri)

    def list_alarms(self):
        uri = '%s/alarms' % self.uri_prefix
        return self.get(uri)

    def list_statistics(self, meter, period=None, query=None):
        uri = "%s/meters/%s/statistics" % (self.uri_prefix, meter)
        return self.helper_list(uri, query, period)

    def list_samples(self, meter_id, query=None):
        uri = '%s/meters/%s' % (self.uri_prefix, meter_id)
        return self.helper_list(uri, query)

    def get_resource(self, resource_id):
        uri = '%s/resources/%s' % (self.uri_prefix, resource_id)
        return self.get(uri)

    def get_alarm(self, alarm_id):
        uri = '%s/meter/%s' % (self.uri_prefix, alarm_id)
        return self.get(uri)

    def delete_alarm(self, alarm_id):
        uri = "%s/alarms/%s" % (self.uri_prefix, alarm_id)
        return self.delete(uri)
