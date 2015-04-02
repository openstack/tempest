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

from tempest.common import cred_provider
from tempest.common import negative_rest_client
from tempest import config
from tempest import manager
from tempest.services.baremetal.v1.json.baremetal_client import \
    BaremetalClientJSON
from tempest.services import botoclients
from tempest.services.compute.json.agents_client import \
    AgentsClientJSON
from tempest.services.compute.json.aggregates_client import \
    AggregatesClientJSON
from tempest.services.compute.json.availability_zone_client import \
    AvailabilityZoneClientJSON
from tempest.services.compute.json.baremetal_nodes_client import \
    BaremetalNodesClientJSON
from tempest.services.compute.json.certificates_client import \
    CertificatesClientJSON
from tempest.services.compute.json.extensions_client import \
    ExtensionsClientJSON
from tempest.services.compute.json.fixed_ips_client import FixedIPsClientJSON
from tempest.services.compute.json.flavors_client import FlavorsClientJSON
from tempest.services.compute.json.floating_ips_client import \
    FloatingIPsClientJSON
from tempest.services.compute.json.hosts_client import HostsClientJSON
from tempest.services.compute.json.hypervisor_client import \
    HypervisorClientJSON
from tempest.services.compute.json.images_client import ImagesClientJSON
from tempest.services.compute.json.instance_usage_audit_log_client import \
    InstanceUsagesAuditLogClientJSON
from tempest.services.compute.json.interfaces_client import \
    InterfacesClientJSON
from tempest.services.compute.json.keypairs_client import KeyPairsClientJSON
from tempest.services.compute.json.limits_client import LimitsClientJSON
from tempest.services.compute.json.migrations_client import \
    MigrationsClientJSON
from tempest.services.compute.json.networks_client import NetworksClientJSON
from tempest.services.compute.json.quotas_client import QuotaClassesClientJSON
from tempest.services.compute.json.quotas_client import QuotasClientJSON
from tempest.services.compute.json.security_group_default_rules_client import \
    SecurityGroupDefaultRulesClientJSON
from tempest.services.compute.json.security_groups_client import \
    SecurityGroupsClientJSON
from tempest.services.compute.json.servers_client import ServersClientJSON
from tempest.services.compute.json.services_client import ServicesClientJSON
from tempest.services.compute.json.tenant_networks_client import \
    TenantNetworksClientJSON
from tempest.services.compute.json.tenant_usages_client import \
    TenantUsagesClientJSON
from tempest.services.compute.json.volumes_extensions_client import \
    VolumesExtensionsClientJSON
from tempest.services.data_processing.v1_1.data_processing_client import \
    DataProcessingClient
from tempest.services.database.json.flavors_client import \
    DatabaseFlavorsClientJSON
from tempest.services.database.json.limits_client import \
    DatabaseLimitsClientJSON
from tempest.services.database.json.versions_client import \
    DatabaseVersionsClientJSON
from tempest.services.identity.v2.json.identity_client import \
    IdentityClientJSON
from tempest.services.identity.v2.json.token_client import TokenClientJSON
from tempest.services.identity.v3.json.credentials_client import \
    CredentialsClientJSON
from tempest.services.identity.v3.json.endpoints_client import \
    EndPointClientJSON
from tempest.services.identity.v3.json.identity_client import \
    IdentityV3ClientJSON
from tempest.services.identity.v3.json.policy_client import PolicyClientJSON
from tempest.services.identity.v3.json.region_client import RegionClientJSON
from tempest.services.identity.v3.json.service_client import \
    ServiceClientJSON
from tempest.services.identity.v3.json.token_client import V3TokenClientJSON
from tempest.services.image.v1.json.image_client import ImageClientJSON
from tempest.services.image.v2.json.image_client import ImageClientV2JSON
from tempest.services.messaging.json.messaging_client import \
    MessagingClientJSON
from tempest.services.network.json.network_client import NetworkClientJSON
from tempest.services.object_storage.account_client import AccountClient
from tempest.services.object_storage.container_client import ContainerClient
from tempest.services.object_storage.object_client import ObjectClient
from tempest.services.orchestration.json.orchestration_client import \
    OrchestrationClient
from tempest.services.telemetry.json.telemetry_client import \
    TelemetryClientJSON
from tempest.services.volume.json.admin.volume_hosts_client import \
    VolumeHostsClientJSON
from tempest.services.volume.json.admin.volume_quotas_client import \
    VolumeQuotasClientJSON
from tempest.services.volume.json.admin.volume_services_client import \
    VolumesServicesClientJSON
from tempest.services.volume.json.admin.volume_types_client import \
    VolumeTypesClientJSON
from tempest.services.volume.json.availability_zone_client import \
    VolumeAvailabilityZoneClientJSON
from tempest.services.volume.json.backups_client import BackupsClientJSON
from tempest.services.volume.json.extensions_client import \
    ExtensionsClientJSON as VolumeExtensionClientJSON
from tempest.services.volume.json.qos_client import QosSpecsClientJSON
from tempest.services.volume.json.snapshots_client import SnapshotsClientJSON
from tempest.services.volume.json.volumes_client import VolumesClientJSON
from tempest.services.volume.v2.json.admin.volume_hosts_client import \
    VolumeHostsV2ClientJSON
from tempest.services.volume.v2.json.admin.volume_quotas_client import \
    VolumeQuotasV2Client
from tempest.services.volume.v2.json.admin.volume_services_client import \
    VolumesServicesV2ClientJSON
from tempest.services.volume.v2.json.admin.volume_types_client import \
    VolumeTypesV2ClientJSON
from tempest.services.volume.v2.json.availability_zone_client import \
    VolumeV2AvailabilityZoneClientJSON
from tempest.services.volume.v2.json.backups_client import BackupsClientV2JSON
from tempest.services.volume.v2.json.extensions_client import \
    ExtensionsV2ClientJSON as VolumeV2ExtensionClientJSON
from tempest.services.volume.v2.json.qos_client import QosSpecsV2ClientJSON
from tempest.services.volume.v2.json.snapshots_client import \
    SnapshotsV2ClientJSON
from tempest.services.volume.v2.json.volumes_client import VolumesV2ClientJSON

CONF = config.CONF
LOG = logging.getLogger(__name__)


class Manager(manager.Manager):

    """
    Top level manager for OpenStack tempest clients
    """

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

    def __init__(self, credentials=None, service=None):
        super(Manager, self).__init__(credentials=credentials)

        self._set_compute_clients()
        self._set_database_clients()
        self._set_identity_clients()
        self._set_volume_clients()
        self._set_object_storage_clients()

        self.baremetal_client = BaremetalClientJSON(
            self.auth_provider,
            CONF.baremetal.catalog_type,
            CONF.identity.region,
            endpoint_type=CONF.baremetal.endpoint_type,
            **self.default_params_with_timeout_values)
        self.network_client = NetworkClientJSON(
            self.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **self.default_params)
        self.messaging_client = MessagingClientJSON(
            self.auth_provider,
            CONF.messaging.catalog_type,
            CONF.identity.region,
            **self.default_params_with_timeout_values)
        if CONF.service_available.ceilometer:
            self.telemetry_client = TelemetryClientJSON(
                self.auth_provider,
                CONF.telemetry.catalog_type,
                CONF.identity.region,
                endpoint_type=CONF.telemetry.endpoint_type,
                **self.default_params_with_timeout_values)
        if CONF.service_available.glance:
            self.image_client = ImageClientJSON(
                self.auth_provider,
                CONF.image.catalog_type,
                CONF.image.region or CONF.identity.region,
                endpoint_type=CONF.image.endpoint_type,
                build_interval=CONF.image.build_interval,
                build_timeout=CONF.image.build_timeout,
                **self.default_params)
            self.image_client_v2 = ImageClientV2JSON(
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
            # EC2 and S3 clients, if used, will check onfigured AWS credentials
            # and generate new ones if needed
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

        self.agents_client = AgentsClientJSON(self.auth_provider, **params)
        self.networks_client = NetworksClientJSON(self.auth_provider, **params)
        self.migrations_client = MigrationsClientJSON(self.auth_provider,
                                                      **params)
        self.security_group_default_rules_client = (
            SecurityGroupDefaultRulesClientJSON(self.auth_provider, **params))
        self.certificates_client = CertificatesClientJSON(self.auth_provider,
                                                          **params)
        self.servers_client = ServersClientJSON(
            self.auth_provider,
            enable_instance_password=CONF.compute_feature_enabled
                .enable_instance_password,
            **params)
        self.limits_client = LimitsClientJSON(self.auth_provider, **params)
        self.images_client = ImagesClientJSON(self.auth_provider, **params)
        self.keypairs_client = KeyPairsClientJSON(self.auth_provider, **params)
        self.quotas_client = QuotasClientJSON(self.auth_provider, **params)
        self.quota_classes_client = QuotaClassesClientJSON(self.auth_provider,
                                                           **params)
        self.flavors_client = FlavorsClientJSON(self.auth_provider, **params)
        self.extensions_client = ExtensionsClientJSON(self.auth_provider,
                                                      **params)
        self.floating_ips_client = FloatingIPsClientJSON(self.auth_provider,
                                                         **params)
        self.security_groups_client = SecurityGroupsClientJSON(
            self.auth_provider, **params)
        self.interfaces_client = InterfacesClientJSON(self.auth_provider,
                                                      **params)
        self.fixed_ips_client = FixedIPsClientJSON(self.auth_provider,
                                                   **params)
        self.availability_zone_client = AvailabilityZoneClientJSON(
            self.auth_provider, **params)
        self.aggregates_client = AggregatesClientJSON(self.auth_provider,
                                                      **params)
        self.services_client = ServicesClientJSON(self.auth_provider, **params)
        self.tenant_usages_client = TenantUsagesClientJSON(self.auth_provider,
                                                           **params)
        self.hosts_client = HostsClientJSON(self.auth_provider, **params)
        self.hypervisor_client = HypervisorClientJSON(self.auth_provider,
                                                      **params)
        self.instance_usages_audit_log_client = \
            InstanceUsagesAuditLogClientJSON(self.auth_provider, **params)
        self.tenant_networks_client = \
            TenantNetworksClientJSON(self.auth_provider, **params)
        self.baremetal_nodes_client = BaremetalNodesClientJSON(
            self.auth_provider, **params)

        # NOTE: The following client needs special timeout values because
        # the API is a proxy for the other component.
        params_volume = copy.deepcopy(params)
        params_volume.update({
            'build_interval': CONF.volume.build_interval,
            'build_timeout': CONF.volume.build_timeout
        })
        self.volumes_extensions_client = VolumesExtensionsClientJSON(
            self.auth_provider, default_volume_size=CONF.volume.volume_size,
            **params_volume)

    def _set_database_clients(self):
        self.database_flavors_client = DatabaseFlavorsClientJSON(
            self.auth_provider,
            CONF.database.catalog_type,
            CONF.identity.region,
            **self.default_params_with_timeout_values)
        self.database_limits_client = DatabaseLimitsClientJSON(
            self.auth_provider,
            CONF.database.catalog_type,
            CONF.identity.region,
            **self.default_params_with_timeout_values)
        self.database_versions_client = DatabaseVersionsClientJSON(
            self.auth_provider,
            CONF.database.catalog_type,
            CONF.identity.region,
            **self.default_params_with_timeout_values)

    def _set_identity_clients(self):
        params = {
            'service': CONF.identity.catalog_type,
            'region': CONF.identity.region,
            'endpoint_type': 'adminURL'
        }
        params.update(self.default_params_with_timeout_values)

        self.identity_client = IdentityClientJSON(self.auth_provider,
                                                  **params)
        self.identity_v3_client = IdentityV3ClientJSON(self.auth_provider,
                                                       **params)
        self.endpoints_client = EndPointClientJSON(self.auth_provider,
                                                   **params)
        self.service_client = ServiceClientJSON(self.auth_provider, **params)
        self.policy_client = PolicyClientJSON(self.auth_provider, **params)
        self.region_client = RegionClientJSON(self.auth_provider, **params)
        self.credentials_client = CredentialsClientJSON(self.auth_provider,
                                                        **params)
        # Token clients do not use the catalog. They only need default_params.
        self.token_client = TokenClientJSON(CONF.identity.uri,
                                            **self.default_params)
        if CONF.identity_feature_enabled.api_v3:
            self.token_v3_client = V3TokenClientJSON(CONF.identity.uri_v3,
                                                     **self.default_params)

    def _set_volume_clients(self):
        params = {
            'service': CONF.volume.catalog_type,
            'region': CONF.volume.region or CONF.identity.region,
            'endpoint_type': CONF.volume.endpoint_type,
            'build_interval': CONF.volume.build_interval,
            'build_timeout': CONF.volume.build_timeout
        }
        params.update(self.default_params)

        self.volume_qos_client = QosSpecsClientJSON(self.auth_provider,
                                                    **params)
        self.volume_qos_v2_client = QosSpecsV2ClientJSON(
            self.auth_provider, **params)
        self.volume_services_v2_client = VolumesServicesV2ClientJSON(
            self.auth_provider, **params)
        self.backups_client = BackupsClientJSON(self.auth_provider, **params)
        self.backups_v2_client = BackupsClientV2JSON(self.auth_provider,
                                                     **params)
        self.snapshots_client = SnapshotsClientJSON(self.auth_provider,
                                                    **params)
        self.snapshots_v2_client = SnapshotsV2ClientJSON(self.auth_provider,
                                                         **params)
        self.volumes_client = VolumesClientJSON(
            self.auth_provider, default_volume_size=CONF.volume.volume_size,
            **params)
        self.volumes_v2_client = VolumesV2ClientJSON(
            self.auth_provider, default_volume_size=CONF.volume.volume_size,
            **params)
        self.volume_types_client = VolumeTypesClientJSON(self.auth_provider,
                                                         **params)
        self.volume_services_client = VolumesServicesClientJSON(
            self.auth_provider, **params)
        self.volume_hosts_client = VolumeHostsClientJSON(self.auth_provider,
                                                         **params)
        self.volume_hosts_v2_client = VolumeHostsV2ClientJSON(
            self.auth_provider, **params)
        self.volume_quotas_client = VolumeQuotasClientJSON(self.auth_provider,
                                                           **params)
        self.volume_quotas_v2_client = VolumeQuotasV2Client(self.auth_provider,
                                                            **params)
        self.volumes_extension_client = VolumeExtensionClientJSON(
            self.auth_provider, **params)
        self.volumes_v2_extension_client = VolumeV2ExtensionClientJSON(
            self.auth_provider, **params)
        self.volume_availability_zone_client = \
            VolumeAvailabilityZoneClientJSON(self.auth_provider, **params)
        self.volume_v2_availability_zone_client = \
            VolumeV2AvailabilityZoneClientJSON(self.auth_provider, **params)
        self.volume_types_v2_client = VolumeTypesV2ClientJSON(
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


class AdminManager(Manager):

    """
    Manager object that uses the admin credentials for its
    managed client objects
    """

    def __init__(self, service=None):
        super(AdminManager, self).__init__(
            credentials=cred_provider.get_configured_credentials(
                'identity_admin'),
            service=service)
