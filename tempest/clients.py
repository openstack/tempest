# Copyright 2012 OpenStack Foundation
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

import copy

from oslo_log import log as logging
from tempest_lib.services.compute.agents_client import AgentsClient
from tempest_lib.services.compute.aggregates_client import AggregatesClient
from tempest_lib.services.compute.availability_zone_client import \
    AvailabilityZoneClient
from tempest_lib.services.compute.baremetal_nodes_client import \
    BaremetalNodesClient
from tempest_lib.services.compute.certificates_client import \
    CertificatesClient
from tempest_lib.services.compute.extensions_client import \
    ExtensionsClient
from tempest_lib.services.compute.fixed_ips_client import FixedIPsClient
from tempest_lib.services.compute.flavors_client import FlavorsClient
from tempest_lib.services.compute.floating_ip_pools_client import \
    FloatingIPPoolsClient
from tempest_lib.services.compute.floating_ips_bulk_client import \
    FloatingIPsBulkClient
from tempest_lib.services.compute.hosts_client import HostsClient
from tempest_lib.services.compute.hypervisor_client import \
    HypervisorClient
from tempest_lib.services.compute.images_client import ImagesClient
from tempest_lib.services.compute.instance_usage_audit_log_client import \
    InstanceUsagesAuditLogClient
from tempest_lib.services.compute.limits_client import LimitsClient
from tempest_lib.services.compute.migrations_client import MigrationsClient
from tempest_lib.services.compute.networks_client import NetworksClient \
    as ComputeNetworksClient
from tempest_lib.services.compute.quota_classes_client import \
    QuotaClassesClient
from tempest_lib.services.compute.quotas_client import QuotasClient
from tempest_lib.services.compute.security_group_default_rules_client import \
    SecurityGroupDefaultRulesClient
from tempest_lib.services.compute.security_groups_client import \
    SecurityGroupsClient
from tempest_lib.services.compute.services_client import ServicesClient
from tempest_lib.services.compute.snapshots_client import \
    SnapshotsClient as ComputeSnapshotsClient
from tempest_lib.services.compute.tenant_networks_client import \
    TenantNetworksClient
from tempest_lib.services.compute.tenant_usages_client import \
    TenantUsagesClient
from tempest_lib.services.identity.v2.token_client import TokenClient
from tempest_lib.services.identity.v3.token_client import V3TokenClient

from tempest.common import negative_rest_client
from tempest import config
from tempest import exceptions
from tempest import manager
from tempest.services.baremetal.v1.json.baremetal_client import \
    BaremetalClient
from tempest.services import botoclients
from tempest.services.compute.json.floating_ips_client import \
    FloatingIPsClient as ComputeFloatingIPsClient
from tempest.services.compute.json.interfaces_client import \
    InterfacesClient
from tempest.services.compute.json.keypairs_client import KeyPairsClient
from tempest.services.compute.json.security_group_rules_client import \
    SecurityGroupRulesClient
from tempest.services.compute.json.server_groups_client import \
    ServerGroupsClient
from tempest.services.compute.json.servers_client import ServersClient
from tempest.services.compute.json.versions_client import VersionsClient
from tempest.services.compute.json.volumes_client import \
    VolumesClient as ComputeVolumesClient
from tempest.services.data_processing.v1_1.data_processing_client import \
    DataProcessingClient
from tempest.services.database.json.flavors_client import \
    DatabaseFlavorsClient
from tempest.services.database.json.limits_client import \
    DatabaseLimitsClient
from tempest.services.database.json.versions_client import \
    DatabaseVersionsClient
from tempest.services.identity.v2.json.identity_client import \
    IdentityClient
from tempest.services.identity.v3.json.credentials_client import \
    CredentialsClient
from tempest.services.identity.v3.json.endpoints_client import \
    EndPointClient
from tempest.services.identity.v3.json.identity_client import \
    IdentityV3Client
from tempest.services.identity.v3.json.policy_client import PolicyClient
from tempest.services.identity.v3.json.region_client import RegionClient
from tempest.services.identity.v3.json.service_client import \
    ServiceClient
from tempest.services.image.v1.json.image_client import ImageClient
from tempest.services.image.v2.json.image_client import ImageClientV2
from tempest.services.messaging.json.messaging_client import \
    MessagingClient
from tempest.services.network.json.network_client import NetworkClient
from tempest.services.network.json.networks_client import NetworksClient
from tempest.services.network.json.ports_client import PortsClient
from tempest.services.network.json.subnets_client import SubnetsClient
from tempest.services.object_storage.account_client import AccountClient
from tempest.services.object_storage.container_client import ContainerClient
from tempest.services.object_storage.object_client import ObjectClient
from tempest.services.orchestration.json.orchestration_client import \
    OrchestrationClient
from tempest.services.telemetry.json.telemetry_client import \
    TelemetryClient
from tempest.services.volume.json.admin.volume_hosts_client import \
    VolumeHostsClient
from tempest.services.volume.json.admin.volume_quotas_client import \
    VolumeQuotasClient
from tempest.services.volume.json.admin.volume_services_client import \
    VolumesServicesClient
from tempest.services.volume.json.admin.volume_types_client import \
    VolumeTypesClient
from tempest.services.volume.json.availability_zone_client import \
    VolumeAvailabilityZoneClient
from tempest.services.volume.json.backups_client import BackupsClient
from tempest.services.volume.json.extensions_client import \
    ExtensionsClient as VolumeExtensionClient
from tempest.services.volume.json.qos_client import QosSpecsClient
from tempest.services.volume.json.snapshots_client import SnapshotsClient
from tempest.services.volume.json.volumes_client import VolumesClient
from tempest.services.volume.v2.json.admin.volume_hosts_client import \
    VolumeHostsV2Client
from tempest.services.volume.v2.json.admin.volume_quotas_client import \
    VolumeQuotasV2Client
from tempest.services.volume.v2.json.admin.volume_services_client import \
    VolumesServicesV2Client
from tempest.services.volume.v2.json.admin.volume_types_client import \
    VolumeTypesV2Client
from tempest.services.volume.v2.json.availability_zone_client import \
    VolumeV2AvailabilityZoneClient
from tempest.services.volume.v2.json.backups_client import BackupsClientV2
from tempest.services.volume.v2.json.extensions_client import \
    ExtensionsV2Client as VolumeV2ExtensionClient
from tempest.services.volume.v2.json.qos_client import QosSpecsV2Client
from tempest.services.volume.v2.json.snapshots_client import \
    SnapshotsV2Client
from tempest.services.volume.v2.json.volumes_client import VolumesV2Client

CONF = config.CONF
LOG = logging.getLogger(__name__)


class Manager(manager.Manager):
    """Top level manager for OpenStack tempest clients"""

    default_params = {
        'disable_ssl_certificate_validation':
            CONF.identity.disable_ssl_certificate_validation,
        'ca_certs': CONF.identity.ca_certificates_file,
        'trace_requests': CONF.debug.trace_requests
    }

    # NOTE: Tempest uses timeout values of compute API if project specific
    # timeout values don't exist.
    default_params_with_timeout_values = {
        'build_interval': CONF.compute.build_interval,
        'build_timeout': CONF.compute.build_timeout
    }
    default_params_with_timeout_values.update(default_params)

    def __init__(self, credentials, service=None):
        super(Manager, self).__init__(credentials=credentials)

        self._set_compute_clients()
        self._set_database_clients()
        self._set_identity_clients()
        self._set_volume_clients()
        self._set_object_storage_clients()

        self.baremetal_client = BaremetalClient(
            self.auth_provider,
            CONF.baremetal.catalog_type,
            CONF.identity.region,
            endpoint_type=CONF.baremetal.endpoint_type,
            **self.default_params_with_timeout_values)
        self.network_client = NetworkClient(
            self.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **self.default_params)
        self.networks_client = NetworksClient(
            self.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **self.default_params)
        self.subnets_client = SubnetsClient(
            self.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **self.default_params)
        self.ports_client = PortsClient(
            self.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **self.default_params)
        self.messaging_client = MessagingClient(
            self.auth_provider,
            CONF.messaging.catalog_type,
            CONF.identity.region,
            **self.default_params_with_timeout_values)
        if CONF.service_available.ceilometer:
            self.telemetry_client = TelemetryClient(
                self.auth_provider,
                CONF.telemetry.catalog_type,
                CONF.identity.region,
                endpoint_type=CONF.telemetry.endpoint_type,
                **self.default_params_with_timeout_values)
        if CONF.service_available.glance:
            self.image_client = ImageClient(
                self.auth_provider,
                CONF.image.catalog_type,
                CONF.image.region or CONF.identity.region,
                endpoint_type=CONF.image.endpoint_type,
                build_interval=CONF.image.build_interval,
                build_timeout=CONF.image.build_timeout,
                **self.default_params)
            self.image_client_v2 = ImageClientV2(
                self.auth_provider,
                CONF.image.catalog_type,
                CONF.image.region or CONF.identity.region,
                endpoint_type=CONF.image.endpoint_type,
                build_interval=CONF.image.build_interval,
                build_timeout=CONF.image.build_timeout,
                **self.default_params)
        self.orchestration_client = OrchestrationClient(
            self.auth_provider,
            CONF.orchestration.catalog_type,
            CONF.orchestration.region or CONF.identity.region,
            endpoint_type=CONF.orchestration.endpoint_type,
            build_interval=CONF.orchestration.build_interval,
            build_timeout=CONF.orchestration.build_timeout,
            **self.default_params)
        self.data_processing_client = DataProcessingClient(
            self.auth_provider,
            CONF.data_processing.catalog_type,
            CONF.identity.region,
            endpoint_type=CONF.data_processing.endpoint_type,
            **self.default_params_with_timeout_values)
        self.negative_client = negative_rest_client.NegativeRestClient(
            self.auth_provider, service, **self.default_params)

        # Generating EC2 credentials in tempest is only supported
        # with identity v2
        if CONF.identity_feature_enabled.api_v2 and \
                CONF.identity.auth_version == 'v2':
            # EC2 and S3 clients, if used, will check configured AWS
            # credentials and generate new ones if needed
            self.ec2api_client = botoclients.APIClientEC2(self.identity_client)
            self.s3_client = botoclients.ObjectClientS3(self.identity_client)

    def _set_compute_clients(self):
        params = {
            'service': CONF.compute.catalog_type,
            'region': CONF.compute.region or CONF.identity.region,
            'endpoint_type': CONF.compute.endpoint_type,
            'build_interval': CONF.compute.build_interval,
            'build_timeout': CONF.compute.build_timeout
        }
        params.update(self.default_params)

        self.agents_client = AgentsClient(self.auth_provider, **params)
        self.compute_networks_client = ComputeNetworksClient(
            self.auth_provider, **params)
        self.migrations_client = MigrationsClient(self.auth_provider,
                                                  **params)
        self.security_group_default_rules_client = (
            SecurityGroupDefaultRulesClient(self.auth_provider, **params))
        self.certificates_client = CertificatesClient(self.auth_provider,
                                                      **params)
        self.servers_client = ServersClient(
            self.auth_provider,
            enable_instance_password=CONF.compute_feature_enabled
                .enable_instance_password,
            **params)
        self.server_groups_client = ServerGroupsClient(
            self.auth_provider, **params)
        self.limits_client = LimitsClient(self.auth_provider, **params)
        self.images_client = ImagesClient(self.auth_provider, **params)
        self.keypairs_client = KeyPairsClient(self.auth_provider, **params)
        self.quotas_client = QuotasClient(self.auth_provider, **params)
        self.quota_classes_client = QuotaClassesClient(self.auth_provider,
                                                       **params)
        self.flavors_client = FlavorsClient(self.auth_provider, **params)
        self.extensions_client = ExtensionsClient(self.auth_provider,
                                                  **params)
        self.floating_ip_pools_client = FloatingIPPoolsClient(
            self.auth_provider, **params)
        self.floating_ips_bulk_client = FloatingIPsBulkClient(
            self.auth_provider, **params)
        self.compute_floating_ips_client = ComputeFloatingIPsClient(
            self.auth_provider, **params)
        self.security_group_rules_client = SecurityGroupRulesClient(
            self.auth_provider, **params)
        self.security_groups_client = SecurityGroupsClient(
            self.auth_provider, **params)
        self.interfaces_client = InterfacesClient(self.auth_provider,
                                                  **params)
        self.fixed_ips_client = FixedIPsClient(self.auth_provider,
                                               **params)
        self.availability_zone_client = AvailabilityZoneClient(
            self.auth_provider, **params)
        self.aggregates_client = AggregatesClient(self.auth_provider,
                                                  **params)
        self.services_client = ServicesClient(self.auth_provider, **params)
        self.tenant_usages_client = TenantUsagesClient(self.auth_provider,
                                                       **params)
        self.hosts_client = HostsClient(self.auth_provider, **params)
        self.hypervisor_client = HypervisorClient(self.auth_provider,
                                                  **params)
        self.instance_usages_audit_log_client = \
            InstanceUsagesAuditLogClient(self.auth_provider, **params)
        self.tenant_networks_client = \
            TenantNetworksClient(self.auth_provider, **params)
        self.baremetal_nodes_client = BaremetalNodesClient(
            self.auth_provider, **params)

        # NOTE: The following client needs special timeout values because
        # the API is a proxy for the other component.
        params_volume = copy.deepcopy(params)
        params_volume.update({
            'build_interval': CONF.volume.build_interval,
            'build_timeout': CONF.volume.build_timeout
        })
        self.volumes_extensions_client = ComputeVolumesClient(
            self.auth_provider, **params_volume)
        self.compute_versions_client = VersionsClient(self.auth_provider,
                                                      **params_volume)
        self.snapshots_extensions_client = ComputeSnapshotsClient(
            self.auth_provider, **params_volume)

    def _set_database_clients(self):
        self.database_flavors_client = DatabaseFlavorsClient(
            self.auth_provider,
            CONF.database.catalog_type,
            CONF.identity.region,
            **self.default_params_with_timeout_values)
        self.database_limits_client = DatabaseLimitsClient(
            self.auth_provider,
            CONF.database.catalog_type,
            CONF.identity.region,
            **self.default_params_with_timeout_values)
        self.database_versions_client = DatabaseVersionsClient(
            self.auth_provider,
            CONF.database.catalog_type,
            CONF.identity.region,
            **self.default_params_with_timeout_values)

    def _set_identity_clients(self):
        params = {
            'service': CONF.identity.catalog_type,
            'region': CONF.identity.region
        }
        params.update(self.default_params_with_timeout_values)
        params_v2_admin = params.copy()
        params_v2_admin['endpoint_type'] = CONF.identity.v2_admin_endpoint_type
        # Client uses admin endpoint type of Keystone API v2
        self.identity_client = IdentityClient(self.auth_provider,
                                              **params_v2_admin)
        params_v2_public = params.copy()
        params_v2_public['endpoint_type'] = (
            CONF.identity.v2_public_endpoint_type)
        # Client uses public endpoint type of Keystone API v2
        self.identity_public_client = IdentityClient(self.auth_provider,
                                                     **params_v2_public)
        params_v3 = params.copy()
        params_v3['endpoint_type'] = CONF.identity.v3_endpoint_type
        # Client uses the endpoint type of Keystone API v3
        self.identity_v3_client = IdentityV3Client(self.auth_provider,
                                                   **params_v3)
        self.endpoints_client = EndPointClient(self.auth_provider,
                                               **params)
        self.service_client = ServiceClient(self.auth_provider, **params)
        self.policy_client = PolicyClient(self.auth_provider, **params)
        self.region_client = RegionClient(self.auth_provider, **params)
        self.credentials_client = CredentialsClient(self.auth_provider,
                                                    **params)
        # Token clients do not use the catalog. They only need default_params.
        # They read auth_url, so they should only be set if the corresponding
        # API version is marked as enabled
        if CONF.identity_feature_enabled.api_v2:
            if CONF.identity.uri:
                self.token_client = TokenClient(
                    CONF.identity.uri, **self.default_params)
            else:
                msg = 'Identity v2 API enabled, but no identity.uri set'
                raise exceptions.InvalidConfiguration(msg)
        if CONF.identity_feature_enabled.api_v3:
            if CONF.identity.uri_v3:
                self.token_v3_client = V3TokenClient(
                    CONF.identity.uri_v3, **self.default_params)
            else:
                msg = 'Identity v3 API enabled, but no identity.uri_v3 set'
                raise exceptions.InvalidConfiguration(msg)

    def _set_volume_clients(self):
        params = {
            'service': CONF.volume.catalog_type,
            'region': CONF.volume.region or CONF.identity.region,
            'endpoint_type': CONF.volume.endpoint_type,
            'build_interval': CONF.volume.build_interval,
            'build_timeout': CONF.volume.build_timeout
        }
        params.update(self.default_params)

        self.volume_qos_client = QosSpecsClient(self.auth_provider,
                                                **params)
        self.volume_qos_v2_client = QosSpecsV2Client(
            self.auth_provider, **params)
        self.volume_services_v2_client = VolumesServicesV2Client(
            self.auth_provider, **params)
        self.backups_client = BackupsClient(self.auth_provider, **params)
        self.backups_v2_client = BackupsClientV2(self.auth_provider,
                                                 **params)
        self.snapshots_client = SnapshotsClient(self.auth_provider,
                                                **params)
        self.snapshots_v2_client = SnapshotsV2Client(self.auth_provider,
                                                     **params)
        self.volumes_client = VolumesClient(
            self.auth_provider, default_volume_size=CONF.volume.volume_size,
            **params)
        self.volumes_v2_client = VolumesV2Client(
            self.auth_provider, default_volume_size=CONF.volume.volume_size,
            **params)
        self.volume_types_client = VolumeTypesClient(self.auth_provider,
                                                     **params)
        self.volume_services_client = VolumesServicesClient(
            self.auth_provider, **params)
        self.volume_hosts_client = VolumeHostsClient(self.auth_provider,
                                                     **params)
        self.volume_hosts_v2_client = VolumeHostsV2Client(
            self.auth_provider, **params)
        self.volume_quotas_client = VolumeQuotasClient(self.auth_provider,
                                                       **params)
        self.volume_quotas_v2_client = VolumeQuotasV2Client(self.auth_provider,
                                                            **params)
        self.volumes_extension_client = VolumeExtensionClient(
            self.auth_provider, **params)
        self.volumes_v2_extension_client = VolumeV2ExtensionClient(
            self.auth_provider, **params)
        self.volume_availability_zone_client = \
            VolumeAvailabilityZoneClient(self.auth_provider, **params)
        self.volume_v2_availability_zone_client = \
            VolumeV2AvailabilityZoneClient(self.auth_provider, **params)
        self.volume_types_v2_client = VolumeTypesV2Client(
            self.auth_provider, **params)

    def _set_object_storage_clients(self):
        params = {
            'service': CONF.object_storage.catalog_type,
            'region': CONF.object_storage.region or CONF.identity.region,
            'endpoint_type': CONF.object_storage.endpoint_type
        }
        params.update(self.default_params_with_timeout_values)

        self.account_client = AccountClient(self.auth_provider, **params)
        self.container_client = ContainerClient(self.auth_provider, **params)
        self.object_client = ObjectClient(self.auth_provider, **params)
