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
from tempest.lib.services.network.metering_label_rules_client import \
    MeteringLabelRulesClient
from tempest.lib.services.network.metering_labels_client import \
    MeteringLabelsClient
from tempest.lib.services.network.networks_client import NetworksClient
from tempest.lib.services.network.ports_client import PortsClient
from tempest.lib.services.network.quotas_client import QuotasClient
from tempest.lib.services.network.routers_client import RoutersClient
from tempest.lib.services.network.security_group_rules_client import \
    SecurityGroupRulesClient
from tempest.lib.services.network.security_groups_client import \
    SecurityGroupsClient
from tempest.lib.services.network.subnetpools_client import SubnetpoolsClient
from tempest.lib.services.network.subnets_client import SubnetsClient
from tempest.lib.services.network.versions_client import NetworkVersionsClient

__all__ = ['AgentsClient', 'ExtensionsClient', 'FloatingIPsClient',
           'MeteringLabelRulesClient', 'MeteringLabelsClient',
           'NetworksClient', 'PortsClient', 'QuotasClient', 'RoutersClient',
           'SecurityGroupRulesClient', 'SecurityGroupsClient',
           'SubnetpoolsClient', 'SubnetsClient', 'NetworkVersionsClient']
