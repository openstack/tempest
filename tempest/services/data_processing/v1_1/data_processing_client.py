# Copyright (c) 2013 Mirantis Inc.
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

import json

from tempest.common import service_client


class DataProcessingClient(service_client.ServiceClient):

    def _request_and_check_resp(self, request_func, uri, resp_status):
        """Make a request using specified request_func and check response
        status code.

        It returns a ResponseBody.
        """
        resp, body = request_func(uri)
        self.expected_success(resp_status, resp.status)
        return service_client.ResponseBody(resp, body)

    def _request_and_check_resp_data(self, request_func, uri, resp_status):
        """Make a request using specified request_func and check response
        status code.

        It returns pair: resp and response data.
        """
        resp, body = request_func(uri)
        self.expected_success(resp_status, resp.status)
        return resp, body

    def _request_check_and_parse_resp(self, request_func, uri, resp_status,
                                      resource_name, *args, **kwargs):
        """Make a request using specified request_func, check response status
        code and parse response body.

        It returns a ResponseBody.
        """
        headers = {'Content-Type': 'application/json'}
        resp, body = request_func(uri, headers=headers, *args, **kwargs)
        self.expected_success(resp_status, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body[resource_name])

    def _request_check_and_parse_resp_list(self, request_func, uri,
                                           resp_status, resource_name,
                                           *args, **kwargs):
        """Make a request using specified request_func, check response status
        code and parse response body.

        It returns a ResponseBodyList.
        """
        headers = {'Content-Type': 'application/json'}
        resp, body = request_func(uri, headers=headers, *args, **kwargs)
        self.expected_success(resp_status, resp.status)
        body = json.loads(body)
        return service_client.ResponseBodyList(resp, body[resource_name])

    def list_node_group_templates(self):
        """List all node group templates for a user."""

        uri = 'node-group-templates'
        return self._request_check_and_parse_resp_list(self.get, uri,
                                                       200,
                                                       'node_group_templates')

    def get_node_group_template(self, tmpl_id):
        """Returns the details of a single node group template."""

        uri = 'node-group-templates/%s' % tmpl_id
        return self._request_check_and_parse_resp(self.get, uri,
                                                  200, 'node_group_template')

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
        return self._request_check_and_parse_resp(self.post, uri, 202,
                                                  'node_group_template',
                                                  body=json.dumps(body))

    def delete_node_group_template(self, tmpl_id):
        """Deletes the specified node group template by id."""

        uri = 'node-group-templates/%s' % tmpl_id
        return self._request_and_check_resp(self.delete, uri, 204)

    def list_plugins(self):
        """List all enabled plugins."""

        uri = 'plugins'
        return self._request_check_and_parse_resp_list(self.get,
                                                       uri, 200, 'plugins')

    def get_plugin(self, plugin_name, plugin_version=None):
        """Returns the details of a single plugin."""

        uri = 'plugins/%s' % plugin_name
        if plugin_version:
            uri += '/%s' % plugin_version
        return self._request_check_and_parse_resp(self.get, uri, 200, 'plugin')

    def list_cluster_templates(self):
        """List all cluster templates for a user."""

        uri = 'cluster-templates'
        return self._request_check_and_parse_resp_list(self.get, uri,
                                                       200,
                                                       'cluster_templates')

    def get_cluster_template(self, tmpl_id):
        """Returns the details of a single cluster template."""

        uri = 'cluster-templates/%s' % tmpl_id
        return self._request_check_and_parse_resp(self.get,
                                                  uri, 200, 'cluster_template')

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
        return self._request_check_and_parse_resp(self.post, uri, 202,
                                                  'cluster_template',
                                                  body=json.dumps(body))

    def delete_cluster_template(self, tmpl_id):
        """Deletes the specified cluster template by id."""

        uri = 'cluster-templates/%s' % tmpl_id
        return self._request_and_check_resp(self.delete, uri, 204)

    def list_data_sources(self):
        """List all data sources for a user."""

        uri = 'data-sources'
        return self._request_check_and_parse_resp_list(self.get,
                                                       uri, 200,
                                                       'data_sources')

    def get_data_source(self, source_id):
        """Returns the details of a single data source."""

        uri = 'data-sources/%s' % source_id
        return self._request_check_and_parse_resp(self.get,
                                                  uri, 200, 'data_source')

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
        return self._request_check_and_parse_resp(self.post, uri,
                                                  202, 'data_source',
                                                  body=json.dumps(body))

    def delete_data_source(self, source_id):
        """Deletes the specified data source by id."""

        uri = 'data-sources/%s' % source_id
        return self._request_and_check_resp(self.delete, uri, 204)

    def list_job_binary_internals(self):
        """List all job binary internals for a user."""

        uri = 'job-binary-internals'
        return self._request_check_and_parse_resp_list(self.get,
                                                       uri, 200, 'binaries')

    def get_job_binary_internal(self, job_binary_id):
        """Returns the details of a single job binary internal."""

        uri = 'job-binary-internals/%s' % job_binary_id
        return self._request_check_and_parse_resp(self.get, uri,
                                                  200, 'job_binary_internal')

    def create_job_binary_internal(self, name, data):
        """Creates job binary internal with specified params."""

        uri = 'job-binary-internals/%s' % name
        return self._request_check_and_parse_resp(self.put, uri, 202,
                                                  'job_binary_internal', data)

    def delete_job_binary_internal(self, job_binary_id):
        """Deletes the specified job binary internal by id."""

        uri = 'job-binary-internals/%s' % job_binary_id
        return self._request_and_check_resp(self.delete, uri, 204)

    def get_job_binary_internal_data(self, job_binary_id):
        """Returns data of a single job binary internal."""

        uri = 'job-binary-internals/%s/data' % job_binary_id
        return self._request_and_check_resp_data(self.get, uri, 200)

    def list_job_binaries(self):
        """List all job binaries for a user."""

        uri = 'job-binaries'
        return self._request_check_and_parse_resp_list(self.get,
                                                       uri, 200, 'binaries')

    def get_job_binary(self, job_binary_id):
        """Returns the details of a single job binary."""

        uri = 'job-binaries/%s' % job_binary_id
        return self._request_check_and_parse_resp(self.get,
                                                  uri, 200, 'job_binary')

    def create_job_binary(self, name, url, extra=None, **kwargs):
        """Creates job binary with specified params.

        It supports passing additional params using kwargs and returns created
        object.
        """
        uri = 'job-binaries'
        body = kwargs.copy()
        body.update({
            'name': name,
            'url': url,
            'extra': extra or dict(),
        })
        return self._request_check_and_parse_resp(self.post, uri,
                                                  202, 'job_binary',
                                                  body=json.dumps(body))

    def delete_job_binary(self, job_binary_id):
        """Deletes the specified job binary by id."""

        uri = 'job-binaries/%s' % job_binary_id
        return self._request_and_check_resp(self.delete, uri, 204)

    def get_job_binary_data(self, job_binary_id):
        """Returns data of a single job binary."""

        uri = 'job-binaries/%s/data' % job_binary_id
        return self._request_and_check_resp_data(self.get, uri, 200)

    def list_jobs(self):
        """List all jobs for a user."""

        uri = 'jobs'
        return self._request_check_and_parse_resp_list(self.get,
                                                       uri, 200, 'jobs')

    def get_job(self, job_id):
        """Returns the details of a single job."""

        uri = 'jobs/%s' % job_id
        return self._request_check_and_parse_resp(self.get, uri, 200, 'job')

    def create_job(self, name, job_type, mains, libs=None, **kwargs):
        """Creates job with specified params.

        It supports passing additional params using kwargs and returns created
        object.
        """
        uri = 'jobs'
        body = kwargs.copy()
        body.update({
            'name': name,
            'type': job_type,
            'mains': mains,
            'libs': libs or list(),
        })
        return self._request_check_and_parse_resp(self.post, uri, 202,
                                                  'job', body=json.dumps(body))

    def delete_job(self, job_id):
        """Deletes the specified job by id."""

        uri = 'jobs/%s' % job_id
        return self._request_and_check_resp(self.delete, uri, 204)
