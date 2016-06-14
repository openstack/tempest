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

from tempest.lib.services.compute.agents_client import AgentsClient
from tempest.lib.services.compute.aggregates_client import AggregatesClient
from tempest.lib.services.compute.availability_zone_client import \
    AvailabilityZoneClient
from tempest.lib.services.compute.baremetal_nodes_client import \
    BaremetalNodesClient
from tempest.lib.services.compute.certificates_client import \
    CertificatesClient
from tempest.lib.services.compute.extensions_client import \
    ExtensionsClient
from tempest.lib.services.compute.fixed_ips_client import FixedIPsClient
from tempest.lib.services.compute.flavors_client import FlavorsClient
from tempest.lib.services.compute.floating_ip_pools_client import \
    FloatingIPPoolsClient
from tempest.lib.services.compute.floating_ips_bulk_client import \
    FloatingIPsBulkClient
from tempest.lib.services.compute.floating_ips_client import \
    FloatingIPsClient
from tempest.lib.services.compute.hosts_client import HostsClient
from tempest.lib.services.compute.hypervisor_client import \
    HypervisorClient
from tempest.lib.services.compute.images_client import ImagesClient
from tempest.lib.services.compute.instance_usage_audit_log_client import \
    InstanceUsagesAuditLogClient
from tempest.lib.services.compute.interfaces_client import InterfacesClient
from tempest.lib.services.compute.keypairs_client import KeyPairsClient
from tempest.lib.services.compute.limits_client import LimitsClient
from tempest.lib.services.compute.migrations_client import MigrationsClient
from tempest.lib.services.compute.networks_client import NetworksClient
from tempest.lib.services.compute.quota_classes_client import \
    QuotaClassesClient
from tempest.lib.services.compute.quotas_client import QuotasClient
from tempest.lib.services.compute.security_group_default_rules_client import \
    SecurityGroupDefaultRulesClient
from tempest.lib.services.compute.security_group_rules_client import \
    SecurityGroupRulesClient
from tempest.lib.services.compute.security_groups_client import \
    SecurityGroupsClient
from tempest.lib.services.compute.server_groups_client import \
    ServerGroupsClient
from tempest.lib.services.compute.servers_client import ServersClient
from tempest.lib.services.compute.services_client import ServicesClient
from tempest.lib.services.compute.snapshots_client import SnapshotsClient
from tempest.lib.services.compute.tenant_networks_client import \
    TenantNetworksClient
from tempest.lib.services.compute.tenant_usages_client import \
    TenantUsagesClient
from tempest.lib.services.compute.versions_client import VersionsClient
from tempest.lib.services.compute.volumes_client import \
    VolumesClient

__all__ = ['AgentsClient', 'AggregatesClient', 'AvailabilityZoneClient',
           'BaremetalNodesClient', 'CertificatesClient', 'ExtensionsClient',
           'FixedIPsClient', 'FlavorsClient', 'FloatingIPPoolsClient',
           'FloatingIPsBulkClient', 'FloatingIPsClient', 'HostsClient',
           'HypervisorClient', 'ImagesClient', 'InstanceUsagesAuditLogClient',
           'InterfacesClient', 'KeyPairsClient', 'LimitsClient',
           'MigrationsClient', 'NetworksClient', 'QuotaClassesClient',
           'QuotasClient', 'SecurityGroupDefaultRulesClient',
           'SecurityGroupRulesClient', 'SecurityGroupsClient',
           'ServerGroupsClient', 'ServersClient', 'ServicesClient',
           'SnapshotsClient', 'TenantNetworksClient', 'TenantUsagesClient',
           'VersionsClient', 'VolumesClient']
