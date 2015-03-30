# Copyright (c) 2014 Mirantis Inc.
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

from tempest_lib import exceptions as lib_exc

from tempest import config
import tempest.test


CONF = config.CONF


class BaseDataProcessingTest(tempest.test.BaseTestCase):

    @classmethod
    def skip_checks(cls):
        super(BaseDataProcessingTest, cls).skip_checks()
        if not CONF.service_available.sahara:
            raise cls.skipException('Sahara support is required')

    @classmethod
    def setup_credentials(cls):
        super(BaseDataProcessingTest, cls).setup_credentials()
        cls.os = cls.get_client_manager()

    @classmethod
    def setup_clients(cls):
        super(BaseDataProcessingTest, cls).setup_clients()
        cls.client = cls.os.data_processing_client

    @classmethod
    def resource_setup(cls):
        super(BaseDataProcessingTest, cls).resource_setup()

        cls.flavor_ref = CONF.compute.flavor_ref

        # add lists for watched resources
        cls._node_group_templates = []
        cls._cluster_templates = []
        cls._data_sources = []
        cls._job_binary_internals = []
        cls._job_binaries = []
        cls._jobs = []

    @classmethod
    def resource_cleanup(cls):
        cls.cleanup_resources(getattr(cls, '_cluster_templates', []),
                              cls.client.delete_cluster_template)
        cls.cleanup_resources(getattr(cls, '_node_group_templates', []),
                              cls.client.delete_node_group_template)
        cls.cleanup_resources(getattr(cls, '_jobs', []), cls.client.delete_job)
        cls.cleanup_resources(getattr(cls, '_job_binaries', []),
                              cls.client.delete_job_binary)
        cls.cleanup_resources(getattr(cls, '_job_binary_internals', []),
                              cls.client.delete_job_binary_internal)
        cls.cleanup_resources(getattr(cls, '_data_sources', []),
                              cls.client.delete_data_source)
        super(BaseDataProcessingTest, cls).resource_cleanup()

    @staticmethod
    def cleanup_resources(resource_id_list, method):
        for resource_id in resource_id_list:
            try:
                method(resource_id)
            except lib_exc.NotFound:
                # ignore errors while auto removing created resource
                pass

    @classmethod
    def create_node_group_template(cls, name, plugin_name, hadoop_version,
                                   node_processes, flavor_id,
                                   node_configs=None, **kwargs):
        """Creates watched node group template with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_node_group_template(name, plugin_name,
                                                          hadoop_version,
                                                          node_processes,
                                                          flavor_id,
                                                          node_configs,
                                                          **kwargs)
        # store id of created node group template
        cls._node_group_templates.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_cluster_template(cls, name, plugin_name, hadoop_version,
                                node_groups, cluster_configs=None, **kwargs):
        """Creates watched cluster template with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_cluster_template(name, plugin_name,
                                                       hadoop_version,
                                                       node_groups,
                                                       cluster_configs,
                                                       **kwargs)
        # store id of created cluster template
        cls._cluster_templates.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_data_source(cls, name, type, url, **kwargs):
        """Creates watched data source with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_data_source(name, type, url, **kwargs)
        # store id of created data source
        cls._data_sources.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_job_binary_internal(cls, name, data):
        """Creates watched job binary internal with specified params.

        It returns created object. All resources created in this method will
        be automatically removed in tearDownClass method.
        """
        resp_body = cls.client.create_job_binary_internal(name, data)
        # store id of created job binary internal
        cls._job_binary_internals.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_job_binary(cls, name, url, extra=None, **kwargs):
        """Creates watched job binary with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_job_binary(name, url, extra, **kwargs)
        # store id of created job binary
        cls._job_binaries.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_job(cls, name, job_type, mains, libs=None, **kwargs):
        """Creates watched job with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_job(name,
                                          job_type, mains, libs, **kwargs)
        # store id of created job
        cls._jobs.append(resp_body['id'])

        return resp_body
