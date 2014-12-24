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

from tempest import auth
from tempest.common import rest_client
from tempest import config
from tempest import manager
from tempest.openstack.common import log as logging
from tempest.services.baremetal.v1.client_json import BaremetalClientJSON
from tempest.services import botoclients
from tempest.services.compute.json.agents_client import \
    AgentsClientJSON
from tempest.services.compute.json.aggregates_client import \
    AggregatesClientJSON
from tempest.services.compute.json.availability_zone_client import \
    AvailabilityZoneClientJSON
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
from tempest.services.compute.json.tenant_usages_client import \
    TenantUsagesClientJSON
from tempest.services.compute.json.volumes_extensions_client import \
    VolumesExtensionsClientJSON
from tempest.services.data_processing.v1_1.client import DataProcessingClient
from tempest.services.database.json.flavors_client import \
    DatabaseFlavorsClientJSON
from tempest.services.database.json.versions_client import \
    DatabaseVersionsClientJSON
from tempest.services.identity.json.identity_client import IdentityClientJSON
from tempest.services.identity.json.identity_client import TokenClientJSON
from tempest.services.identity.v3.json.credentials_client import \
    CredentialsClientJSON
from tempest.services.identity.v3.json.endpoints_client import \
    EndPointClientJSON
from tempest.services.identity.v3.json.identity_client import \
    IdentityV3ClientJSON
from tempest.services.identity.v3.json.identity_client import V3TokenClientJSON
from tempest.services.identity.v3.json.policy_client import PolicyClientJSON
from tempest.services.identity.v3.json.region_client import RegionClientJSON
from tempest.services.identity.v3.json.service_client import \
    ServiceClientJSON
from tempest.services.image.v1.json.image_client import ImageClientJSON
from tempest.services.image.v2.json.image_client import ImageClientV2JSON
from tempest.services.messaging.json.messaging_client import \
    MessagingClientJSON
from tempest.services.network.json.network_client import NetworkClientJSON
from tempest.services.object_storage.account_client import AccountClient
from tempest.services.object_storage.account_client import \
    AccountClientCustomizedHeader
from tempest.services.object_storage.container_client import ContainerClient
from tempest.services.object_storage.object_client import ObjectClient
from tempest.services.object_storage.object_client import \
    ObjectClientCustomizedHeader
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

    def __init__(self, credentials=None, interface='json', service=None):
        # Set interface and client type first
        self.interface = interface
        # super cares for credentials validation
        super(Manager, self).__init__(credentials=credentials)

        self._set_compute_clients(self.interface)
        self._set_identity_clients(self.interface)
        self._set_volume_clients(self.interface)

        self.baremetal_client = BaremetalClientJSON(self.auth_provider)
        self.network_client = NetworkClientJSON(self.auth_provider)
        self.database_flavors_client = DatabaseFlavorsClientJSON(
            self.auth_provider)
        self.database_versions_client = DatabaseVersionsClientJSON(
            self.auth_provider)
        self.messaging_client = MessagingClientJSON(self.auth_provider)
        if CONF.service_available.ceilometer:
            self.telemetry_client = TelemetryClientJSON(
                self.auth_provider)
        self.negative_client = rest_client.NegativeRestClient(
            self.auth_provider, service)

        # TODO(andreaf) EC2 client still do their auth, v2 only
        ec2_client_args = (self.credentials.username,
                           self.credentials.password,
                           CONF.identity.uri,
                           self.credentials.tenant_name)

        # common clients
        self.account_client = AccountClient(self.auth_provider)
        if CONF.service_available.glance:
            self.image_client = ImageClientJSON(self.auth_provider)
            self.image_client_v2 = ImageClientV2JSON(self.auth_provider)
        self.container_client = ContainerClient(self.auth_provider)
        self.object_client = ObjectClient(self.auth_provider)
        self.orchestration_client = OrchestrationClient(
            self.auth_provider)
        self.ec2api_client = botoclients.APIClientEC2(*ec2_client_args)
        self.s3_client = botoclients.ObjectClientS3(*ec2_client_args)
        self.custom_object_client = ObjectClientCustomizedHeader(
            self.auth_provider)
        self.custom_account_client = \
            AccountClientCustomizedHeader(self.auth_provider)
        self.data_processing_client = DataProcessingClient(
            self.auth_provider)

    def _set_compute_clients(self, type):
        self._set_compute_json_clients()

        # Common compute clients
        self.agents_client = AgentsClientJSON(self.auth_provider)
        self.networks_client = NetworksClientJSON(self.auth_provider)
        self.migrations_client = MigrationsClientJSON(self.auth_provider)
        self.security_group_default_rules_client = (
            SecurityGroupDefaultRulesClientJSON(self.auth_provider))

    def _set_compute_json_clients(self):
        self.certificates_client = CertificatesClientJSON(self.auth_provider)
        self.servers_client = ServersClientJSON(self.auth_provider)
        self.limits_client = LimitsClientJSON(self.auth_provider)
        self.images_client = ImagesClientJSON(self.auth_provider)
        self.keypairs_client = KeyPairsClientJSON(self.auth_provider)
        self.quotas_client = QuotasClientJSON(self.auth_provider)
        self.quota_classes_client = QuotaClassesClientJSON(self.auth_provider)
        self.flavors_client = FlavorsClientJSON(self.auth_provider)
        self.extensions_client = ExtensionsClientJSON(self.auth_provider)
        self.volumes_extensions_client = VolumesExtensionsClientJSON(
            self.auth_provider)
        self.floating_ips_client = FloatingIPsClientJSON(self.auth_provider)
        self.security_groups_client = SecurityGroupsClientJSON(
            self.auth_provider)
        self.interfaces_client = InterfacesClientJSON(self.auth_provider)
        self.fixed_ips_client = FixedIPsClientJSON(self.auth_provider)
        self.availability_zone_client = AvailabilityZoneClientJSON(
            self.auth_provider)
        self.aggregates_client = AggregatesClientJSON(self.auth_provider)
        self.services_client = ServicesClientJSON(self.auth_provider)
        self.tenant_usages_client = TenantUsagesClientJSON(self.auth_provider)
        self.hosts_client = HostsClientJSON(self.auth_provider)
        self.hypervisor_client = HypervisorClientJSON(self.auth_provider)
        self.instance_usages_audit_log_client = \
            InstanceUsagesAuditLogClientJSON(self.auth_provider)

    def _set_identity_clients(self, type):
        self._set_identity_json_clients()

    def _set_identity_json_clients(self):
        self.identity_client = IdentityClientJSON(self.auth_provider)
        self.identity_v3_client = IdentityV3ClientJSON(self.auth_provider)
        self.endpoints_client = EndPointClientJSON(self.auth_provider)
        self.service_client = ServiceClientJSON(self.auth_provider)
        self.policy_client = PolicyClientJSON(self.auth_provider)
        self.region_client = RegionClientJSON(self.auth_provider)
        self.token_client = TokenClientJSON()
        if CONF.identity_feature_enabled.api_v3:
            self.token_v3_client = V3TokenClientJSON()
        self.credentials_client = CredentialsClientJSON(self.auth_provider)

    def _set_volume_clients(self, type):
        self._set_volume_json_clients()
        # Common volume clients
        # NOTE : As XML clients are not implemented for Qos-specs.
        # So, setting the qos_client here. Once client are implemented,
        # qos_client would be moved to its respective if/else.
        # Bug : 1312553
        self.volume_qos_client = QosSpecsClientJSON(self.auth_provider)
        self.volume_qos_v2_client = QosSpecsV2ClientJSON(
            self.auth_provider)
        self.volume_services_v2_client = VolumesServicesV2ClientJSON(
            self.auth_provider)

    def _set_volume_json_clients(self):
        self.backups_client = BackupsClientJSON(self.auth_provider)
        self.backups_v2_client = BackupsClientV2JSON(self.auth_provider)
        self.snapshots_client = SnapshotsClientJSON(self.auth_provider)
        self.snapshots_v2_client = SnapshotsV2ClientJSON(self.auth_provider)
        self.volumes_client = VolumesClientJSON(self.auth_provider)
        self.volumes_v2_client = VolumesV2ClientJSON(self.auth_provider)
        self.volume_types_client = VolumeTypesClientJSON(self.auth_provider)
        self.volume_services_client = VolumesServicesClientJSON(
            self.auth_provider)
        self.volume_hosts_client = VolumeHostsClientJSON(self.auth_provider)
        self.volume_hosts_v2_client = VolumeHostsV2ClientJSON(
            self.auth_provider)
        self.volume_quotas_client = VolumeQuotasClientJSON(self.auth_provider)
        self.volume_quotas_v2_client = VolumeQuotasV2Client(self.auth_provider)
        self.volumes_extension_client = VolumeExtensionClientJSON(
            self.auth_provider)
        self.volumes_v2_extension_client = VolumeV2ExtensionClientJSON(
            self.auth_provider)
        self.volume_availability_zone_client = \
            VolumeAvailabilityZoneClientJSON(self.auth_provider)
        self.volume_v2_availability_zone_client = \
            VolumeV2AvailabilityZoneClientJSON(self.auth_provider)
        self.volume_types_v2_client = VolumeTypesV2ClientJSON(
            self.auth_provider)


class AdminManager(Manager):

    """
    Manager object that uses the admin credentials for its
    managed client objects
    """

    def __init__(self, interface='json', service=None):
        super(AdminManager, self).__init__(
            credentials=auth.get_default_credentials('identity_admin'),
            interface=interface,
            service=service)
