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

import keystoneclient.exceptions
import keystoneclient.v2_0.client

from tempest import auth
from tempest.common.rest_client import NegativeRestClient
from tempest import config
from tempest import exceptions
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
from tempest.services.compute.json.quotas_client import QuotasClientJSON
from tempest.services.compute.json.security_groups_client import \
    SecurityGroupsClientJSON
from tempest.services.compute.json.servers_client import ServersClientJSON
from tempest.services.compute.json.services_client import ServicesClientJSON
from tempest.services.compute.json.tenant_usages_client import \
    TenantUsagesClientJSON
from tempest.services.compute.json.volumes_extensions_client import \
    VolumesExtensionsClientJSON
from tempest.services.compute.v3.json.agents_client import AgentsV3ClientJSON
from tempest.services.compute.v3.json.aggregates_client import \
    AggregatesV3ClientJSON
from tempest.services.compute.v3.json.availability_zone_client import \
    AvailabilityZoneV3ClientJSON
from tempest.services.compute.v3.json.certificates_client import \
    CertificatesV3ClientJSON
from tempest.services.compute.v3.json.extensions_client import \
    ExtensionsV3ClientJSON
from tempest.services.compute.v3.json.flavors_client import FlavorsV3ClientJSON
from tempest.services.compute.v3.json.hosts_client import HostsV3ClientJSON
from tempest.services.compute.v3.json.hypervisor_client import \
    HypervisorV3ClientJSON
from tempest.services.compute.v3.json.interfaces_client import \
    InterfacesV3ClientJSON
from tempest.services.compute.v3.json.keypairs_client import \
    KeyPairsV3ClientJSON
from tempest.services.compute.v3.json.migration_client import \
    MigrationsV3ClientJSON
from tempest.services.compute.v3.json.quotas_client import \
    QuotasV3ClientJSON
from tempest.services.compute.v3.json.servers_client import \
    ServersV3ClientJSON
from tempest.services.compute.v3.json.services_client import \
    ServicesV3ClientJSON
from tempest.services.compute.v3.json.version_client import \
    VersionV3ClientJSON
from tempest.services.compute.xml.aggregates_client import AggregatesClientXML
from tempest.services.compute.xml.availability_zone_client import \
    AvailabilityZoneClientXML
from tempest.services.compute.xml.certificates_client import \
    CertificatesClientXML
from tempest.services.compute.xml.extensions_client import ExtensionsClientXML
from tempest.services.compute.xml.fixed_ips_client import FixedIPsClientXML
from tempest.services.compute.xml.flavors_client import FlavorsClientXML
from tempest.services.compute.xml.floating_ips_client import \
    FloatingIPsClientXML
from tempest.services.compute.xml.hosts_client import HostsClientXML
from tempest.services.compute.xml.hypervisor_client import HypervisorClientXML
from tempest.services.compute.xml.images_client import ImagesClientXML
from tempest.services.compute.xml.instance_usage_audit_log_client import \
    InstanceUsagesAuditLogClientXML
from tempest.services.compute.xml.interfaces_client import \
    InterfacesClientXML
from tempest.services.compute.xml.keypairs_client import KeyPairsClientXML
from tempest.services.compute.xml.limits_client import LimitsClientXML
from tempest.services.compute.xml.quotas_client import QuotasClientXML
from tempest.services.compute.xml.security_groups_client \
    import SecurityGroupsClientXML
from tempest.services.compute.xml.servers_client import ServersClientXML
from tempest.services.compute.xml.services_client import ServicesClientXML
from tempest.services.compute.xml.tenant_usages_client import \
    TenantUsagesClientXML
from tempest.services.compute.xml.volumes_extensions_client import \
    VolumesExtensionsClientXML
from tempest.services.data_processing.v1_1.client import DataProcessingClient
from tempest.services.database.json.flavors_client import \
    DatabaseFlavorsClientJSON
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
from tempest.services.identity.v3.json.service_client import \
    ServiceClientJSON
from tempest.services.identity.v3.xml.credentials_client import \
    CredentialsClientXML
from tempest.services.identity.v3.xml.endpoints_client import EndPointClientXML
from tempest.services.identity.v3.xml.identity_client import \
    IdentityV3ClientXML
from tempest.services.identity.v3.xml.identity_client import V3TokenClientXML
from tempest.services.identity.v3.xml.policy_client import PolicyClientXML
from tempest.services.identity.v3.xml.service_client import \
    ServiceClientXML
from tempest.services.identity.xml.identity_client import IdentityClientXML
from tempest.services.identity.xml.identity_client import TokenClientXML
from tempest.services.image.v1.json.image_client import ImageClientJSON
from tempest.services.image.v2.json.image_client import ImageClientV2JSON
from tempest.services.network.json.network_client import NetworkClientJSON
from tempest.services.network.xml.network_client import NetworkClientXML
from tempest.services.object_storage.account_client import AccountClient
from tempest.services.object_storage.account_client import \
    AccountClientCustomizedHeader
from tempest.services.object_storage.container_client import ContainerClient
from tempest.services.object_storage.object_client import ObjectClient
from tempest.services.object_storage.object_client import \
    ObjectClientCustomizedHeader
from tempest.services.orchestration.json.orchestration_client import \
    OrchestrationClient
from tempest.services.queuing.json.queuing_client import QueuingClientJSON
from tempest.services.telemetry.json.telemetry_client import \
    TelemetryClientJSON
from tempest.services.telemetry.xml.telemetry_client import \
    TelemetryClientXML
from tempest.services.volume.json.admin.volume_hosts_client import \
    VolumeHostsClientJSON
from tempest.services.volume.json.admin.volume_quotas_client import \
    VolumeQuotasClientJSON
from tempest.services.volume.json.admin.volume_services_client import \
    VolumesServicesClientJSON
from tempest.services.volume.json.admin.volume_types_client import \
    VolumeTypesClientJSON
from tempest.services.volume.json.backups_client import BackupsClientJSON
from tempest.services.volume.json.extensions_client import \
    ExtensionsClientJSON as VolumeExtensionClientJSON
from tempest.services.volume.json.snapshots_client import SnapshotsClientJSON
from tempest.services.volume.json.volumes_client import VolumesClientJSON
from tempest.services.volume.v2.json.volumes_client import VolumesV2ClientJSON
from tempest.services.volume.v2.xml.volumes_client import VolumesV2ClientXML
from tempest.services.volume.xml.admin.volume_hosts_client import \
    VolumeHostsClientXML
from tempest.services.volume.xml.admin.volume_quotas_client import \
    VolumeQuotasClientXML
from tempest.services.volume.xml.admin.volume_services_client import \
    VolumesServicesClientXML
from tempest.services.volume.xml.admin.volume_types_client import \
    VolumeTypesClientXML
from tempest.services.volume.xml.backups_client import BackupsClientXML
from tempest.services.volume.xml.extensions_client import \
    ExtensionsClientXML as VolumeExtensionClientXML
from tempest.services.volume.xml.snapshots_client import SnapshotsClientXML
from tempest.services.volume.xml.volumes_client import VolumesClientXML

CONF = config.CONF
LOG = logging.getLogger(__name__)


class Manager(manager.Manager):

    """
    Top level manager for OpenStack tempest clients
    """

    def __init__(self, credentials=None, interface='json', service=None):
        # Set interface and client type first
        self.interface = interface
        self.client_type = 'tempest'
        # super cares for credentials validation
        super(Manager, self).__init__(credentials=credentials)

        if self.interface == 'xml':
            self.certificates_client = CertificatesClientXML(
                self.auth_provider)
            self.servers_client = ServersClientXML(self.auth_provider)
            self.limits_client = LimitsClientXML(self.auth_provider)
            self.images_client = ImagesClientXML(self.auth_provider)
            self.keypairs_client = KeyPairsClientXML(self.auth_provider)
            self.quotas_client = QuotasClientXML(self.auth_provider)
            self.flavors_client = FlavorsClientXML(self.auth_provider)
            self.extensions_client = ExtensionsClientXML(self.auth_provider)
            self.volumes_extensions_client = VolumesExtensionsClientXML(
                self.auth_provider)
            self.floating_ips_client = FloatingIPsClientXML(
                self.auth_provider)
            self.backups_client = BackupsClientXML(self.auth_provider)
            self.snapshots_client = SnapshotsClientXML(self.auth_provider)
            self.volumes_client = VolumesClientXML(self.auth_provider)
            self.volumes_v2_client = VolumesV2ClientXML(self.auth_provider)
            self.volume_types_client = VolumeTypesClientXML(
                self.auth_provider)
            self.identity_client = IdentityClientXML(self.auth_provider)
            self.identity_v3_client = IdentityV3ClientXML(
                self.auth_provider)
            self.security_groups_client = SecurityGroupsClientXML(
                self.auth_provider)
            self.interfaces_client = InterfacesClientXML(self.auth_provider)
            self.endpoints_client = EndPointClientXML(self.auth_provider)
            self.fixed_ips_client = FixedIPsClientXML(self.auth_provider)
            self.availability_zone_client = AvailabilityZoneClientXML(
                self.auth_provider)
            self.service_client = ServiceClientXML(self.auth_provider)
            self.volume_services_client = VolumesServicesClientXML(
                self.auth_provider)
            self.aggregates_client = AggregatesClientXML(self.auth_provider)
            self.services_client = ServicesClientXML(self.auth_provider)
            self.tenant_usages_client = TenantUsagesClientXML(
                self.auth_provider)
            self.policy_client = PolicyClientXML(self.auth_provider)
            self.hosts_client = HostsClientXML(self.auth_provider)
            self.hypervisor_client = HypervisorClientXML(self.auth_provider)
            self.network_client = NetworkClientXML(self.auth_provider)
            self.credentials_client = CredentialsClientXML(
                self.auth_provider)
            self.instance_usages_audit_log_client = \
                InstanceUsagesAuditLogClientXML(self.auth_provider)
            self.volume_hosts_client = VolumeHostsClientXML(
                self.auth_provider)
            self.volume_quotas_client = VolumeQuotasClientXML(
                self.auth_provider)
            self.volumes_extension_client = VolumeExtensionClientXML(
                self.auth_provider)
            if CONF.service_available.ceilometer:
                self.telemetry_client = TelemetryClientXML(
                    self.auth_provider)
            self.token_client = TokenClientXML()
            self.token_v3_client = V3TokenClientXML()

        elif self.interface == 'json':
            self.certificates_client = CertificatesClientJSON(
                self.auth_provider)
            self.certificates_v3_client = CertificatesV3ClientJSON(
                self.auth_provider)
            self.baremetal_client = BaremetalClientJSON(self.auth_provider)
            self.servers_client = ServersClientJSON(self.auth_provider)
            self.servers_v3_client = ServersV3ClientJSON(self.auth_provider)
            self.limits_client = LimitsClientJSON(self.auth_provider)
            self.images_client = ImagesClientJSON(self.auth_provider)
            self.keypairs_v3_client = KeyPairsV3ClientJSON(
                self.auth_provider)
            self.keypairs_client = KeyPairsClientJSON(self.auth_provider)
            self.keypairs_v3_client = KeyPairsV3ClientJSON(
                self.auth_provider)
            self.quotas_client = QuotasClientJSON(self.auth_provider)
            self.quotas_v3_client = QuotasV3ClientJSON(self.auth_provider)
            self.flavors_client = FlavorsClientJSON(self.auth_provider)
            self.flavors_v3_client = FlavorsV3ClientJSON(self.auth_provider)
            self.extensions_v3_client = ExtensionsV3ClientJSON(
                self.auth_provider)
            self.extensions_client = ExtensionsClientJSON(
                self.auth_provider)
            self.volumes_extensions_client = VolumesExtensionsClientJSON(
                self.auth_provider)
            self.floating_ips_client = FloatingIPsClientJSON(
                self.auth_provider)
            self.backups_client = BackupsClientJSON(self.auth_provider)
            self.snapshots_client = SnapshotsClientJSON(self.auth_provider)
            self.volumes_client = VolumesClientJSON(self.auth_provider)
            self.volumes_v2_client = VolumesV2ClientJSON(self.auth_provider)
            self.volume_types_client = VolumeTypesClientJSON(
                self.auth_provider)
            self.identity_client = IdentityClientJSON(self.auth_provider)
            self.identity_v3_client = IdentityV3ClientJSON(
                self.auth_provider)
            self.security_groups_client = SecurityGroupsClientJSON(
                self.auth_provider)
            self.interfaces_v3_client = InterfacesV3ClientJSON(
                self.auth_provider)
            self.interfaces_client = InterfacesClientJSON(
                self.auth_provider)
            self.endpoints_client = EndPointClientJSON(self.auth_provider)
            self.fixed_ips_client = FixedIPsClientJSON(self.auth_provider)
            self.availability_zone_v3_client = AvailabilityZoneV3ClientJSON(
                self.auth_provider)
            self.availability_zone_client = AvailabilityZoneClientJSON(
                self.auth_provider)
            self.services_v3_client = ServicesV3ClientJSON(
                self.auth_provider)
            self.service_client = ServiceClientJSON(self.auth_provider)
            self.volume_services_client = VolumesServicesClientJSON(
                self.auth_provider)
            self.agents_v3_client = AgentsV3ClientJSON(self.auth_provider)
            self.aggregates_v3_client = AggregatesV3ClientJSON(
                self.auth_provider)
            self.aggregates_client = AggregatesClientJSON(
                self.auth_provider)
            self.services_client = ServicesClientJSON(self.auth_provider)
            self.tenant_usages_client = TenantUsagesClientJSON(
                self.auth_provider)
            self.version_v3_client = VersionV3ClientJSON(self.auth_provider)
            self.migrations_v3_client = MigrationsV3ClientJSON(
                self.auth_provider)
            self.policy_client = PolicyClientJSON(self.auth_provider)
            self.hosts_client = HostsClientJSON(self.auth_provider)
            self.hypervisor_v3_client = HypervisorV3ClientJSON(
                self.auth_provider)
            self.hypervisor_client = HypervisorClientJSON(
                self.auth_provider)
            self.network_client = NetworkClientJSON(self.auth_provider)
            self.credentials_client = CredentialsClientJSON(
                self.auth_provider)
            self.instance_usages_audit_log_client = \
                InstanceUsagesAuditLogClientJSON(self.auth_provider)
            self.volume_hosts_client = VolumeHostsClientJSON(
                self.auth_provider)
            self.volume_quotas_client = VolumeQuotasClientJSON(
                self.auth_provider)
            self.volumes_extension_client = VolumeExtensionClientJSON(
                self.auth_provider)
            self.hosts_v3_client = HostsV3ClientJSON(self.auth_provider)
            self.database_flavors_client = DatabaseFlavorsClientJSON(
                self.auth_provider)
            self.queuing_client = QueuingClientJSON(self.auth_provider)
            if CONF.service_available.ceilometer:
                self.telemetry_client = TelemetryClientJSON(
                    self.auth_provider)
            self.token_client = TokenClientJSON()
            self.token_v3_client = V3TokenClientJSON()
            self.negative_client = NegativeRestClient(self.auth_provider)
            self.negative_client.service = service

        else:
            msg = "Unsupported interface type `%s'" % interface
            raise exceptions.InvalidConfiguration(msg)

        # TODO(andreaf) EC2 client still do their auth, v2 only
        ec2_client_args = (self.credentials.username,
                           self.credentials.password,
                           CONF.identity.uri,
                           self.credentials.tenant_name)

        # common clients
        self.account_client = AccountClient(self.auth_provider)
        self.agents_client = AgentsClientJSON(self.auth_provider)
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
        self.migrations_client = MigrationsClientJSON(self.auth_provider)


class AltManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self, interface='json', service=None):
        super(AltManager, self).__init__(
            credentials=auth.get_default_credentials('alt_user'),
            interface=interface,
            service=service)


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


class ComputeAdminManager(Manager):

    """
    Manager object that uses the compute_admin credentials for its
    managed client objects
    """

    def __init__(self, interface='json', service=None):
        base = super(ComputeAdminManager, self)
        base.__init__(
            credentials=auth.get_default_credentials('compute_admin'),
            interface=interface,
            service=service)


class OfficialClientManager(manager.Manager):
    """
    Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """

    NOVACLIENT_VERSION = '2'
    CINDERCLIENT_VERSION = '1'
    HEATCLIENT_VERSION = '1'
    IRONICCLIENT_VERSION = '1'
    SAHARACLIENT_VERSION = '1.1'

    def __init__(self, credentials):
        # FIXME(andreaf) Auth provider for client_type 'official' is
        # not implemented yet, setting to 'tempest' for now.
        self.client_type = 'tempest'
        self.interface = None
        # super cares for credentials validation
        super(OfficialClientManager, self).__init__(credentials=credentials)
        self.baremetal_client = self._get_baremetal_client()
        self.compute_client = self._get_compute_client(credentials)
        self.identity_client = self._get_identity_client(credentials)
        self.image_client = self._get_image_client()
        self.network_client = self._get_network_client()
        self.volume_client = self._get_volume_client(credentials)
        self.object_storage_client = self._get_object_storage_client(
            credentials)
        self.orchestration_client = self._get_orchestration_client(
            credentials)
        self.data_processing_client = self._get_data_processing_client(
            credentials)

    def _get_roles(self):
        admin_credentials = auth.get_default_credentials('identity_admin')
        keystone_admin = self._get_identity_client(admin_credentials)

        username = self.credentials.username
        tenant_name = self.credentials.tenant_name
        user_id = keystone_admin.users.find(name=username).id
        tenant_id = keystone_admin.tenants.find(name=tenant_name).id

        roles = keystone_admin.roles.roles_for_user(
            user=user_id, tenant=tenant_id)

        return [r.name for r in roles]

    def _get_compute_client(self, credentials):
        # Novaclient will not execute operations for anyone but the
        # identified user, so a new client needs to be created for
        # each user that operations need to be performed for.
        if not CONF.service_available.nova:
            return None
        import novaclient.client

        auth_url = CONF.identity.uri
        dscv = CONF.identity.disable_ssl_certificate_validation
        region = CONF.identity.region

        client_args = (credentials.username, credentials.password,
                       credentials.tenant_name, auth_url)

        # Create our default Nova client to use in testing
        service_type = CONF.compute.catalog_type
        endpoint_type = CONF.compute.endpoint_type
        return novaclient.client.Client(self.NOVACLIENT_VERSION,
                                        *client_args,
                                        service_type=service_type,
                                        endpoint_type=endpoint_type,
                                        region_name=region,
                                        no_cache=True,
                                        insecure=dscv,
                                        http_log_debug=True)

    def _get_image_client(self):
        if not CONF.service_available.glance:
            return None
        import glanceclient
        token = self.identity_client.auth_token
        region = CONF.identity.region
        endpoint_type = CONF.image.endpoint_type
        endpoint = self.identity_client.service_catalog.url_for(
            attr='region', filter_value=region,
            service_type=CONF.image.catalog_type, endpoint_type=endpoint_type)
        dscv = CONF.identity.disable_ssl_certificate_validation
        return glanceclient.Client('1', endpoint=endpoint, token=token,
                                   insecure=dscv)

    def _get_volume_client(self, credentials):
        if not CONF.service_available.cinder:
            return None
        import cinderclient.client
        auth_url = CONF.identity.uri
        region = CONF.identity.region
        endpoint_type = CONF.volume.endpoint_type
        dscv = CONF.identity.disable_ssl_certificate_validation
        return cinderclient.client.Client(self.CINDERCLIENT_VERSION,
                                          credentials.username,
                                          credentials.password,
                                          credentials.tenant_name,
                                          auth_url,
                                          region_name=region,
                                          endpoint_type=endpoint_type,
                                          insecure=dscv,
                                          http_log_debug=True)

    def _get_object_storage_client(self, credentials):
        if not CONF.service_available.swift:
            return None
        import swiftclient
        auth_url = CONF.identity.uri
        # add current tenant to swift operator role group.
        admin_credentials = auth.get_default_credentials('identity_admin')
        keystone_admin = self._get_identity_client(admin_credentials)

        # enable test user to operate swift by adding operator role to him.
        roles = keystone_admin.roles.list()
        operator_role = CONF.object_storage.operator_role
        member_role = [role for role in roles if role.name == operator_role][0]
        # NOTE(maurosr): This is surrounded in the try-except block cause
        # neutron tests doesn't have tenant isolation.
        try:
            keystone_admin.roles.add_user_role(self.identity_client.user_id,
                                               member_role.id,
                                               self.identity_client.tenant_id)
        except keystoneclient.exceptions.Conflict:
            pass

        endpoint_type = CONF.object_storage.endpoint_type
        os_options = {'endpoint_type': endpoint_type}
        return swiftclient.Connection(auth_url, credentials.username,
                                      credentials.password,
                                      tenant_name=credentials.tenant_name,
                                      auth_version='2',
                                      os_options=os_options)

    def _get_orchestration_client(self, credentials):
        if not CONF.service_available.heat:
            return None
        import heatclient.client

        keystone = self._get_identity_client(credentials)
        region = CONF.identity.region
        endpoint_type = CONF.orchestration.endpoint_type
        token = keystone.auth_token
        service_type = CONF.orchestration.catalog_type
        try:
            endpoint = keystone.service_catalog.url_for(
                attr='region',
                filter_value=region,
                service_type=service_type,
                endpoint_type=endpoint_type)
        except keystoneclient.exceptions.EndpointNotFound:
            return None
        else:
            return heatclient.client.Client(self.HEATCLIENT_VERSION,
                                            endpoint,
                                            token=token,
                                            username=credentials.username,
                                            password=credentials.password)

    def _get_identity_client(self, credentials):
        # This identity client is not intended to check the security
        # of the identity service, so use admin credentials by default.

        auth_url = CONF.identity.uri
        dscv = CONF.identity.disable_ssl_certificate_validation

        return keystoneclient.v2_0.client.Client(
            username=credentials.username,
            password=credentials.password,
            tenant_name=credentials.tenant_name,
            auth_url=auth_url,
            insecure=dscv)

    def _get_baremetal_client(self):
        # ironic client is currently intended to by used by admin users
        if not CONF.service_available.ironic:
            return None
        import ironicclient.client
        roles = self._get_roles()
        if CONF.identity.admin_role not in roles:
            return None

        auth_url = CONF.identity.uri
        api_version = self.IRONICCLIENT_VERSION
        insecure = CONF.identity.disable_ssl_certificate_validation
        service_type = CONF.baremetal.catalog_type
        endpoint_type = CONF.baremetal.endpoint_type
        creds = {
            'os_username': self.credentials.username,
            'os_password': self.credentials.password,
            'os_tenant_name': self.credentials.tenant_name
        }

        try:
            return ironicclient.client.get_client(
                api_version=api_version,
                os_auth_url=auth_url,
                insecure=insecure,
                os_service_type=service_type,
                os_endpoint_type=endpoint_type,
                **creds)
        except keystoneclient.exceptions.EndpointNotFound:
            return None

    def _get_network_client(self):
        # The intended configuration is for the network client to have
        # admin privileges and indicate for whom resources are being
        # created via a 'tenant_id' parameter.  This will often be
        # preferable to authenticating as a specific user because
        # working with certain resources (public routers and networks)
        # often requires admin privileges anyway.
        if not CONF.service_available.neutron:
            return None
        import neutronclient.v2_0.client

        credentials = auth.get_default_credentials('identity_admin')

        auth_url = CONF.identity.uri
        dscv = CONF.identity.disable_ssl_certificate_validation
        endpoint_type = CONF.network.endpoint_type

        return neutronclient.v2_0.client.Client(
            username=credentials.username,
            password=credentials.password,
            tenant_name=credentials.tenant_name,
            endpoint_type=endpoint_type,
            auth_url=auth_url,
            insecure=dscv)

    def _get_data_processing_client(self, credentials):
        if not CONF.service_available.sahara:
            # Sahara isn't available
            return None

        import saharaclient.client

        endpoint_type = CONF.data_processing.endpoint_type
        catalog_type = CONF.data_processing.catalog_type
        auth_url = CONF.identity.uri

        client = saharaclient.client.Client(
            self.SAHARACLIENT_VERSION,
            credentials.username,
            credentials.password,
            project_name=credentials.tenant_name,
            endpoint_type=endpoint_type,
            service_type=catalog_type,
            auth_url=auth_url)

        return client
