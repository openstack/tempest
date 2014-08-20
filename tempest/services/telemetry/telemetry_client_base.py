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
import urllib

import six

from tempest import config

CONF = config.CONF


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

    def __init__(self, auth_provider):
        self.rest_client = self.get_rest_client(auth_provider)
        self.rest_client.service = CONF.telemetry.catalog_type
        self.version = '2'
        self.uri_prefix = "v%s" % self.version

    @abc.abstractmethod
    def get_rest_client(self, auth_provider):
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
        resp, body = self.rest_client.post(uri, body)
        body = self.deserialize(body)
        return resp, body

    def put(self, uri, body):
        body = self.serialize(body)
        resp, body = self.rest_client.put(uri, body)
        body = self.deserialize(body)
        return resp, body

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

    def list_resources(self, query=None):
        uri = '%s/resources' % self.uri_prefix
        return self.helper_list(uri, query)

    def list_meters(self, query=None):
        uri = '%s/meters' % self.uri_prefix
        return self.helper_list(uri, query)

    def list_alarms(self, query=None):
        uri = '%s/alarms' % self.uri_prefix
        return self.helper_list(uri, query)

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
        uri = '%s/alarms/%s' % (self.uri_prefix, alarm_id)
        return self.get(uri)

    def delete_alarm(self, alarm_id):
        uri = "%s/alarms/%s" % (self.uri_prefix, alarm_id)
        return self.delete(uri)

    def create_alarm(self, **kwargs):
        uri = "%s/alarms" % self.uri_prefix
        return self.post(uri, kwargs)

    def update_alarm(self, alarm_id, **kwargs):
        uri = "%s/alarms/%s" % (self.uri_prefix, alarm_id)
        return self.put(uri, kwargs)

    def alarm_get_state(self, alarm_id):
        uri = "%s/alarms/%s/state" % (self.uri_prefix, alarm_id)
        return self.get(uri)

    def alarm_set_state(self, alarm_id, state):
        uri = "%s/alarms/%s/state" % (self.uri_prefix, alarm_id)
        return self.put(uri, state)
