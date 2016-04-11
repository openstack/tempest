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

from collections import OrderedDict
import copy

import six

from tempest import config
from tempest import exceptions
from tempest.lib import exceptions as lib_exc
import tempest.test


CONF = config.CONF

"""Default templates.
There should always be at least a master1 and a worker1 node
group template."""
BASE_VANILLA_DESC = {
    'NODES': {
        'master1': {
            'count': 1,
            'node_processes': ['namenode', 'resourcemanager',
                               'hiveserver']
        },
        'master2': {
            'count': 1,
            'node_processes': ['oozie', 'historyserver',
                               'secondarynamenode']
        },
        'worker1': {
            'count': 1,
            'node_processes': ['datanode', 'nodemanager'],
            'node_configs': {
                'MapReduce': {
                    'yarn.app.mapreduce.am.resource.mb': 256,
                    'yarn.app.mapreduce.am.command-opts': '-Xmx256m'
                },
                'YARN': {
                    'yarn.scheduler.minimum-allocation-mb': 256,
                    'yarn.scheduler.maximum-allocation-mb': 1024,
                    'yarn.nodemanager.vmem-check-enabled': False
                }
            }
        }
    },
    'cluster_configs': {
        'HDFS': {
            'dfs.replication': 1
        }
    }
}

BASE_SPARK_DESC = {
    'NODES': {
        'master1': {
            'count': 1,
            'node_processes': ['namenode', 'master']
        },
        'worker1': {
            'count': 1,
            'node_processes': ['datanode', 'slave']
        }
    },
    'cluster_configs': {
        'HDFS': {
            'dfs.replication': 1
        }
    }
}

BASE_CDH_DESC = {
    'NODES': {
        'master1': {
            'count': 1,
            'node_processes': ['CLOUDERA_MANAGER']
        },
        'master2': {
            'count': 1,
            'node_processes': ['HDFS_NAMENODE',
                               'YARN_RESOURCEMANAGER']
        },
        'master3': {
            'count': 1,
            'node_processes': ['OOZIE_SERVER', 'YARN_JOBHISTORY',
                               'HDFS_SECONDARYNAMENODE',
                               'HIVE_METASTORE', 'HIVE_SERVER2']
        },
        'worker1': {
            'count': 1,
            'node_processes': ['YARN_NODEMANAGER', 'HDFS_DATANODE']
        }
    },
    'cluster_configs': {
        'HDFS': {
            'dfs_replication': 1
        }
    }
}


DEFAULT_TEMPLATES = {
    'vanilla': OrderedDict([
        ('2.6.0', copy.deepcopy(BASE_VANILLA_DESC)),
        ('2.7.1', copy.deepcopy(BASE_VANILLA_DESC)),
        ('1.2.1', {
            'NODES': {
                'master1': {
                    'count': 1,
                    'node_processes': ['namenode', 'jobtracker']
                },
                'worker1': {
                    'count': 1,
                    'node_processes': ['datanode', 'tasktracker'],
                    'node_configs': {
                        'HDFS': {
                            'Data Node Heap Size': 1024
                        },
                        'MapReduce': {
                            'Task Tracker Heap Size': 1024
                        }
                    }
                }
            },
            'cluster_configs': {
                'HDFS': {
                    'dfs.replication': 1
                },
                'MapReduce': {
                    'mapred.map.tasks.speculative.execution': False,
                    'mapred.child.java.opts': '-Xmx500m'
                },
                'general': {
                    'Enable Swift': False
                }
            }
        })
    ]),
    'hdp': OrderedDict([
        ('2.0.6', {
            'NODES': {
                'master1': {
                    'count': 1,
                    'node_processes': ['NAMENODE', 'SECONDARY_NAMENODE',
                                       'ZOOKEEPER_SERVER', 'AMBARI_SERVER',
                                       'HISTORYSERVER', 'RESOURCEMANAGER',
                                       'GANGLIA_SERVER', 'NAGIOS_SERVER',
                                       'OOZIE_SERVER']
                },
                'worker1': {
                    'count': 1,
                    'node_processes': ['HDFS_CLIENT', 'DATANODE',
                                       'YARN_CLIENT', 'ZOOKEEPER_CLIENT',
                                       'MAPREDUCE2_CLIENT', 'NODEMANAGER',
                                       'PIG', 'OOZIE_CLIENT']
                }
            },
            'cluster_configs': {
                'HDFS': {
                    'dfs.replication': 1
                }
            }
        })
    ]),
    'spark': OrderedDict([
        ('1.0.0', copy.deepcopy(BASE_SPARK_DESC)),
        ('1.3.1', copy.deepcopy(BASE_SPARK_DESC))
    ]),
    'cdh': OrderedDict([
        ('5.4.0', copy.deepcopy(BASE_CDH_DESC)),
        ('5.3.0', copy.deepcopy(BASE_CDH_DESC)),
        ('5', copy.deepcopy(BASE_CDH_DESC))
    ]),
}


class BaseDataProcessingTest(tempest.test.BaseTestCase):

    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseDataProcessingTest, cls).skip_checks()
        if not CONF.service_available.sahara:
            raise cls.skipException('Sahara support is required')
        cls.default_plugin = cls._get_default_plugin()

    @classmethod
    def setup_clients(cls):
        super(BaseDataProcessingTest, cls).setup_clients()
        cls.client = cls.os.data_processing_client

    @classmethod
    def resource_setup(cls):
        super(BaseDataProcessingTest, cls).resource_setup()

        cls.default_version = cls._get_default_version()
        if cls.default_plugin is not None and cls.default_version is None:
            raise exceptions.InvalidConfiguration(
                message="No known Sahara plugin version was found")
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
        resp_body = resp_body['node_group_template']
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
        resp_body = resp_body['cluster_template']
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
        resp_body = resp_body['data_source']
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
        resp_body = resp_body['job_binary_internal']
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
        resp_body = resp_body['job_binary']
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
        resp_body = resp_body['job']
        # store id of created job
        cls._jobs.append(resp_body['id'])

        return resp_body

    @classmethod
    def _get_default_plugin(cls):
        """Returns the default plugin used for testing."""
        if len(CONF.data_processing_feature_enabled.plugins) == 0:
            return None

        for plugin in CONF.data_processing_feature_enabled.plugins:
            if plugin in DEFAULT_TEMPLATES.keys():
                break
        else:
            plugin = ''
        return plugin

    @classmethod
    def _get_default_version(cls):
        """Returns the default plugin version used for testing.

        This is gathered separately from the plugin to allow
        the usage of plugin name in skip_checks. This method is
        rather invoked into resource_setup, which allows API calls
        and exceptions.
        """
        if not cls.default_plugin:
            return None
        plugin = cls.client.get_plugin(cls.default_plugin)['plugin']

        for version in DEFAULT_TEMPLATES[cls.default_plugin].keys():
            if version in plugin['versions']:
                break
        else:
            version = None

        return version

    @classmethod
    def get_node_group_template(cls, nodegroup='worker1'):
        """Returns a node group template for the default plugin."""
        try:
            plugin_data = (
                DEFAULT_TEMPLATES[cls.default_plugin][cls.default_version]
            )
            nodegroup_data = plugin_data['NODES'][nodegroup]
            node_group_template = {
                'description': 'Test node group template',
                'plugin_name': cls.default_plugin,
                'hadoop_version': cls.default_version,
                'node_processes': nodegroup_data['node_processes'],
                'flavor_id': cls.flavor_ref,
                'node_configs': nodegroup_data.get('node_configs', {}),
            }
            return node_group_template
        except (IndexError, KeyError):
            return None

    @classmethod
    def get_cluster_template(cls, node_group_template_ids=None):
        """Returns a cluster template for the default plugin.

        node_group_template_defined contains the type and ID of pre-defined
        node group templates that have to be used in the cluster template
        (instead of dynamically defining them with 'node_processes').
        """
        if node_group_template_ids is None:
            node_group_template_ids = {}
        try:
            plugin_data = (
                DEFAULT_TEMPLATES[cls.default_plugin][cls.default_version]
            )

            all_node_groups = []
            for ng_name, ng_data in six.iteritems(plugin_data['NODES']):
                node_group = {
                    'name': '%s-node' % (ng_name),
                    'flavor_id': cls.flavor_ref,
                    'count': ng_data['count']
                }
                if ng_name in node_group_template_ids.keys():
                    # node group already defined, use it
                    node_group['node_group_template_id'] = (
                        node_group_template_ids[ng_name]
                    )
                else:
                    # node_processes list defined on-the-fly
                    node_group['node_processes'] = ng_data['node_processes']
                if 'node_configs' in ng_data:
                    node_group['node_configs'] = ng_data['node_configs']
                all_node_groups.append(node_group)

            cluster_template = {
                'description': 'Test cluster template',
                'plugin_name': cls.default_plugin,
                'hadoop_version': cls.default_version,
                'cluster_configs': plugin_data.get('cluster_configs', {}),
                'node_groups': all_node_groups,
            }
            return cluster_template
        except (IndexError, KeyError):
            return None
