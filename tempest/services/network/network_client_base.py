# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

# the following map is used to construct proper URI
# for the given neutron resource
service_resource_prefix_map = {
    'networks': '',
    'subnets': '',
    'ports': '',
    'pools': 'lb',
    'vips': 'lb',
    'health_monitors': 'lb',
    'members': 'lb',
    'vpnservices': 'vpn',
    'ikepolicies': 'vpn'
}

# The following list represents resource names that do not require
# changing underscore to a hyphen
hyphen_exceptions = ["health_monitors"]

# map from resource name to a plural name
# needed only for those which can't be constructed as name + 's'
resource_plural_map = {
    'security_groups': 'security_groups',
    'security_group_rules': 'security_group_rules',
    'ikepolicy': 'ikepolicies',
    'floating_ip': 'floatingips',
    'quotas': 'quotas'
}


class NetworkClientBase(object):
    def __init__(self, config, username, password,
                 auth_url, tenant_name=None):
        self.rest_client = self.get_rest_client(
            config, username, password, auth_url, tenant_name)
        self.rest_client.service = self.rest_client.config.network.catalog_type
        self.version = '2.0'
        self.uri_prefix = "v%s" % (self.version)

    def get_rest_client(self, config, username, password,
                        auth_url, tenant_name):
        raise NotImplementedError

    def post(self, uri, body, headers=None):
        headers = headers or self.rest_client.headers
        return self.rest_client.post(uri, body, headers)

    def put(self, uri, body, headers=None):
        headers = headers or self.rest_client.headers
        return self.rest_client.put(uri, body, headers)

    def get(self, uri, headers=None):
        headers = headers or self.rest_client.headers
        return self.rest_client.get(uri, headers)

    def delete(self, uri, headers=None):
        headers = headers or self.rest_client.headers
        return self.rest_client.delete(uri, headers)

    def deserialize_list(self, body):
        raise NotImplementedError

    def deserialize_single(self, body):
        raise NotImplementedError

    def get_uri(self, plural_name):
        # get service prefix from resource name
        service_prefix = service_resource_prefix_map.get(
            plural_name)
        if plural_name not in hyphen_exceptions:
            plural_name = plural_name.replace("_", "-")
        if service_prefix:
            uri = '%s/%s/%s' % (self.uri_prefix, service_prefix,
                                plural_name)
        else:
            uri = '%s/%s' % (self.uri_prefix, plural_name)
        return uri

    def pluralize(self, resource_name):
        # get plural from map or just add 's'
        return resource_plural_map.get(resource_name, resource_name + 's')

    def _lister(self, plural_name):
        def _list(**filters):
            uri = self.get_uri(plural_name)
            if filters:
                uri += '?' + urllib.urlencode(filters)
            resp, body = self.get(uri)
            result = {plural_name: self.deserialize_list(body)}
            return resp, result

        return _list

    def _deleter(self, resource_name):
        def _delete(resource_id):
            plural = self.pluralize(resource_name)
            uri = '%s/%s' % (self.get_uri(plural), resource_id)
            return self.delete(uri)

        return _delete

    def _shower(self, resource_name):
        def _show(resource_id, field_list=[]):
            # field_list is a sequence of two-element tuples, with the
            # first element being 'fields'. An example:
            # [('fields', 'id'), ('fields', 'name')]
            plural = self.pluralize(resource_name)
            uri = '%s/%s' % (self.get_uri(plural), resource_id)
            if field_list:
                uri += '?' + urllib.urlencode(field_list)
            resp, body = self.get(uri)
            body = self.deserialize_single(body)
            return resp, body

        return _show

    def _creater(self, resource_name):
        def _create(**kwargs):
            plural = self.pluralize(resource_name)
            uri = self.get_uri(plural)
            post_data = self.serialize({resource_name: kwargs})
            resp, body = self.post(uri, post_data)
            body = self.deserialize_single(body)
            return resp, body

        return _create

    def _updater(self, resource_name):
        def _update(res_id, **kwargs):
            plural = self.pluralize(resource_name)
            uri = '%s/%s' % (self.get_uri(plural), res_id)
            post_data = self.serialize({resource_name: kwargs})
            resp, body = self.put(uri, post_data)
            body = self.deserialize_single(body)
            return resp, body

        return _update

    def __getattr__(self, name):
        method_prefixes = ["list_", "delete_", "show_", "create_", "update_"]
        method_functors = [self._lister,
                           self._deleter,
                           self._shower,
                           self._creater,
                           self._updater]
        for index, prefix in enumerate(method_prefixes):
            prefix_len = len(prefix)
            if name[:prefix_len] == prefix:
                return method_functors[index](name[prefix_len:])
        raise AttributeError(name)
