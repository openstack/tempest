# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class DataProcessingClient(rest_client.RestClient):
    def __init__(self, auth_provider):
        super(DataProcessingClient, self).__init__(auth_provider)
        self.service = CONF.data_processing.catalog_type

    @classmethod
    def _request_and_parse(cls, req_fun, uri, res_name, *args, **kwargs):
        """Make a request using specified req_fun and parse response.

        It returns pair: resp and parsed resource(s) body.
        """
        resp, body = req_fun(uri, headers={
            'Content-Type': 'application/json'
        }, *args, **kwargs)
        body = json.loads(body)
        return resp, body[res_name]

    def list_node_group_templates(self):
        """List all node group templates for a user."""

        uri = 'node-group-templates'
        return self._request_and_parse(self.get, uri, 'node_group_templates')

    def get_node_group_template(self, tmpl_id):
        """Returns the details of a single node group template."""

        uri = 'node-group-templates/%s' % tmpl_id
        return self._request_and_parse(self.get, uri, 'node_group_template')

    def create_node_group_template(self, name, plugin_name, hadoop_version,
                                   node_processes, flavor_id,
                                   node_configs=None, **kwargs):
        """Creates node group template with specified params.

        It supports passing additional params using kwargs and returns created
        object.
        """
        uri = 'node-group-templates'
        body = kwargs.copy()
        body.update({
            'name': name,
            'plugin_name': plugin_name,
            'hadoop_version': hadoop_version,
            'node_processes': node_processes,
            'flavor_id': flavor_id,
            'node_configs': node_configs or dict(),
        })
        return self._request_and_parse(self.post, uri, 'node_group_template',
                                       body=json.dumps(body))

    def delete_node_group_template(self, tmpl_id):
        """Deletes the specified node group template by id."""

        uri = 'node-group-templates/%s' % tmpl_id
        return self.delete(uri)

    def list_plugins(self):
        """List all enabled plugins."""

        uri = 'plugins'
        return self._request_and_parse(self.get, uri, 'plugins')

    def get_plugin(self, plugin_name, plugin_version=None):
        """Returns the details of a single plugin."""

        uri = 'plugins/%s' % plugin_name
        if plugin_version:
            uri += '/%s' % plugin_version
        return self._request_and_parse(self.get, uri, 'plugin')

    def list_cluster_templates(self):
        """List all cluster templates for a user."""

        uri = 'cluster-templates'
        return self._request_and_parse(self.get, uri, 'cluster_templates')

    def get_cluster_template(self, tmpl_id):
        """Returns the details of a single cluster template."""

        uri = 'cluster-templates/%s' % tmpl_id
        return self._request_and_parse(self.get, uri, 'cluster_template')

    def create_cluster_template(self, name, plugin_name, hadoop_version,
                                node_groups, cluster_configs=None,
                                **kwargs):
        """Creates cluster template with specified params.

        It supports passing additional params using kwargs and returns created
        object.
        """
        uri = 'cluster-templates'
        body = kwargs.copy()
        body.update({
            'name': name,
            'plugin_name': plugin_name,
            'hadoop_version': hadoop_version,
            'node_groups': node_groups,
            'cluster_configs': cluster_configs or dict(),
        })
        return self._request_and_parse(self.post, uri, 'cluster_template',
                                       body=json.dumps(body))

    def delete_cluster_template(self, tmpl_id):
        """Deletes the specified cluster template by id."""

        uri = 'cluster-templates/%s' % tmpl_id
        return self.delete(uri)

    def list_data_sources(self):
        """List all data sources for a user."""

        uri = 'data-sources'
        return self._request_and_parse(self.get, uri, 'data_sources')

    def get_data_source(self, source_id):
        """Returns the details of a single data source."""

        uri = 'data-sources/%s' % source_id
        return self._request_and_parse(self.get, uri, 'data_source')

    def create_data_source(self, name, data_source_type, url, **kwargs):
        """Creates data source with specified params.

        It supports passing additional params using kwargs and returns created
        object.
        """
        uri = 'data-sources'
        body = kwargs.copy()
        body.update({
            'name': name,
            'type': data_source_type,
            'url': url
        })
        return self._request_and_parse(self.post, uri, 'data_source',
                                       body=json.dumps(body))

    def delete_data_source(self, source_id):
        """Deletes the specified data source by id."""

        uri = 'data-sources/%s' % source_id
        return self.delete(uri)
