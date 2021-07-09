# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

from tempest.lib.services.network.agents_client import AgentsClient
from tempest.lib.services.network.extensions_client import ExtensionsClient
from tempest.lib.services.network.floating_ips_client import FloatingIPsClient
from tempest.lib.services.network.log_resource_client import LogResourceClient
from tempest.lib.services.network.loggable_resource_client import \
    LoggableResourceClient
from tempest.lib.services.network.metering_label_rules_client import \
    MeteringLabelRulesClient
from tempest.lib.services.network.metering_labels_client import \
    MeteringLabelsClient
from tempest.lib.services.network.networks_client import NetworksClient
from tempest.lib.services.network.ports_client import PortsClient
from tempest.lib.services.network.qos_client import QosClient
from tempest.lib.services.network.qos_minimum_bandwidth_rules_client import \
    QosMinimumBandwidthRulesClient
from tempest.lib.services.network.quotas_client import QuotasClient
from tempest.lib.services.network.routers_client import RoutersClient
from tempest.lib.services.network.security_group_rules_client import \
    SecurityGroupRulesClient
from tempest.lib.services.network.security_groups_client import \
    SecurityGroupsClient
from tempest.lib.services.network.segments_client import SegmentsClient
from tempest.lib.services.network.service_providers_client import \
    ServiceProvidersClient
from tempest.lib.services.network.subnetpools_client import SubnetpoolsClient
from tempest.lib.services.network.subnets_client import SubnetsClient
from tempest.lib.services.network.tags_client import TagsClient
from tempest.lib.services.network.trunks_client import TrunksClient
from tempest.lib.services.network.versions_client import NetworkVersionsClient

__all__ = ['AgentsClient', 'ExtensionsClient', 'FloatingIPsClient',
           'MeteringLabelRulesClient', 'MeteringLabelsClient',
           'NetworksClient', 'NetworkVersionsClient', 'PortsClient',
           'QosClient', 'QosMinimumBandwidthRulesClient', 'QuotasClient',
           'RoutersClient', 'SecurityGroupRulesClient', 'SecurityGroupsClient',
           'SegmentsClient', 'ServiceProvidersClient', 'SubnetpoolsClient',
           'SubnetsClient', 'TagsClient', 'TrunksClient', 'LogResourceClient',
           'LoggableResourceClient']
