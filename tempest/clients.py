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
from tempest.common.rest_client import NegativeRestClient
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.services.baremetal.v1.client_json import BaremetalClientJSON
from tempest.services import botoclients
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
from tempest.services.compute.json.quotas_client import QuotasClientJSON
from tempest.services.compute.json.security_groups_client import \
    SecurityGroupsClientJSON
from tempest.services.compute.json.servers_client import ServersClientJSON
from tempest.services.compute.json.services_client import ServicesClientJSON
from tempest.services.compute.json.tenant_usages_client import \
    TenantUsagesClientJSON
from tempest.services.compute.json.volumes_extensions_client import \
    VolumesExtensionsClientJSON
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
from tempest.services.telemetry.json.telemetry_client import \
    TelemetryClientJSON
from tempest.services.telemetry.xml.telemetry_client import \
    TelemetryClientXML
from tempest.services.volume.json.admin.volume_hosts_client import \
    VolumeHostsClientJSON
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
from tempest.services.volume.xml.admin.volume_types_client import \
    VolumeTypesClientXML
from tempest.services.volume.xml.backups_client import BackupsClientXML
from tempest.services.volume.xml.extensions_client import \
    ExtensionsClientXML as VolumeExtensionClientXML
from tempest.services.volume.xml.snapshots_client import SnapshotsClientXML
from tempest.services.volume.xml.volumes_client import VolumesClientXML

CONF = config.CONF
LOG = logging.getLogger(__name__)


class Manager(object):

    """
    Top level manager for OpenStack Compute clients
    """

    def __init__(self, username=None, password=None, tenant_name=None,
                 interface='json', service=None):
        """
        We allow overriding of the credentials used within the various
        client classes managed by the Manager object. Left as None, the
        standard username/password/tenant_name is used.

        :param username: Override of the username
        :param password: Override of the password
        :param tenant_name: Override of the tenant name
        """
        self.interface = interface
        self.auth_version = CONF.identity.auth_version
        # FIXME(andreaf) Change Manager __init__ to accept a credentials dict
        if username is None or password is None:
            # Tenant None is a valid use case
            self.credentials = self.get_default_credentials()
        else:
            self.credentials = dict(username=username, password=password,
                                    tenant_name=tenant_name)
        if self.auth_version == 'v3':
            self.credentials['domain_name'] = 'Default'
        # Setup an auth provider
        auth_provider = self.get_auth_provider(self.credentials)

        if self.interface == 'xml':
            self.certificates_client = CertificatesClientXML(
                auth_provider)
            self.servers_client = ServersClientXML(auth_provider)
            self.limits_client = LimitsClientXML(auth_provider)
            self.images_client = ImagesClientXML(auth_provider)
            self.keypairs_client = KeyPairsClientXML(auth_provider)
            self.quotas_client = QuotasClientXML(auth_provider)
            self.flavors_client = FlavorsClientXML(auth_provider)
            self.extensions_client = ExtensionsClientXML(auth_provider)
            self.volumes_extensions_client = VolumesExtensionsClientXML(
                auth_provider)
            self.floating_ips_client = FloatingIPsClientXML(
                auth_provider)
            self.backups_client = BackupsClientXML(auth_provider)
            self.snapshots_client = SnapshotsClientXML(auth_provider)
            self.volumes_client = VolumesClientXML(auth_provider)
            self.volumes_v2_client = VolumesV2ClientXML(auth_provider)
            self.volume_types_client = VolumeTypesClientXML(
                auth_provider)
            self.identity_client = IdentityClientXML(auth_provider)
            self.identity_v3_client = IdentityV3ClientXML(
                auth_provider)
            self.security_groups_client = SecurityGroupsClientXML(
                auth_provider)
            self.interfaces_client = InterfacesClientXML(auth_provider)
            self.endpoints_client = EndPointClientXML(auth_provider)
            self.fixed_ips_client = FixedIPsClientXML(auth_provider)
            self.availability_zone_client = AvailabilityZoneClientXML(
                auth_provider)
            self.service_client = ServiceClientXML(auth_provider)
            self.aggregates_client = AggregatesClientXML(auth_provider)
            self.services_client = ServicesClientXML(auth_provider)
            self.tenant_usages_client = TenantUsagesClientXML(
                auth_provider)
            self.policy_client = PolicyClientXML(auth_provider)
            self.hosts_client = HostsClientXML(auth_provider)
            self.hypervisor_client = HypervisorClientXML(auth_provider)
            self.network_client = NetworkClientXML(auth_provider)
            self.credentials_client = CredentialsClientXML(
                auth_provider)
            self.instance_usages_audit_log_client = \
                InstanceUsagesAuditLogClientXML(auth_provider)
            self.volume_hosts_client = VolumeHostsClientXML(
                auth_provider)
            self.volumes_extension_client = VolumeExtensionClientXML(
                auth_provider)
            if CONF.service_available.ceilometer:
                self.telemetry_client = TelemetryClientXML(
                    auth_provider)
            self.token_client = TokenClientXML()
            self.token_v3_client = V3TokenClientXML()

        elif self.interface == 'json':
            self.certificates_client = CertificatesClientJSON(
                auth_provider)
            self.certificates_v3_client = CertificatesV3ClientJSON(
                auth_provider)
            self.baremetal_client = BaremetalClientJSON(auth_provider)
            self.servers_client = ServersClientJSON(auth_provider)
            self.servers_v3_client = ServersV3ClientJSON(auth_provider)
            self.limits_client = LimitsClientJSON(auth_provider)
            self.images_client = ImagesClientJSON(auth_provider)
            self.keypairs_v3_client = KeyPairsV3ClientJSON(
                auth_provider)
            self.keypairs_client = KeyPairsClientJSON(auth_provider)
            self.keypairs_v3_client = KeyPairsV3ClientJSON(
                auth_provider)
            self.quotas_client = QuotasClientJSON(auth_provider)
            self.quotas_v3_client = QuotasV3ClientJSON(auth_provider)
            self.flavors_client = FlavorsClientJSON(auth_provider)
            self.flavors_v3_client = FlavorsV3ClientJSON(auth_provider)
            self.extensions_v3_client = ExtensionsV3ClientJSON(
                auth_provider)
            self.extensions_client = ExtensionsClientJSON(
                auth_provider)
            self.volumes_extensions_client = VolumesExtensionsClientJSON(
                auth_provider)
            self.floating_ips_client = FloatingIPsClientJSON(
                auth_provider)
            self.backups_client = BackupsClientJSON(auth_provider)
            self.snapshots_client = SnapshotsClientJSON(auth_provider)
            self.volumes_client = VolumesClientJSON(auth_provider)
            self.volumes_v2_client = VolumesV2ClientJSON(auth_provider)
            self.volume_types_client = VolumeTypesClientJSON(
                auth_provider)
            self.identity_client = IdentityClientJSON(auth_provider)
            self.identity_v3_client = IdentityV3ClientJSON(
                auth_provider)
            self.security_groups_client = SecurityGroupsClientJSON(
                auth_provider)
            self.interfaces_v3_client = InterfacesV3ClientJSON(
                auth_provider)
            self.interfaces_client = InterfacesClientJSON(
                auth_provider)
            self.endpoints_client = EndPointClientJSON(auth_provider)
            self.fixed_ips_client = FixedIPsClientJSON(auth_provider)
            self.availability_zone_v3_client = AvailabilityZoneV3ClientJSON(
                auth_provider)
            self.availability_zone_client = AvailabilityZoneClientJSON(
                auth_provider)
            self.services_v3_client = ServicesV3ClientJSON(
                auth_provider)
            self.service_client = ServiceClientJSON(auth_provider)
            self.aggregates_v3_client = AggregatesV3ClientJSON(
                auth_provider)
            self.aggregates_client = AggregatesClientJSON(
                auth_provider)
            self.services_client = ServicesClientJSON(auth_provider)
            self.tenant_usages_client = TenantUsagesClientJSON(
                auth_provider)
            self.version_v3_client = VersionV3ClientJSON(auth_provider)
            self.policy_client = PolicyClientJSON(auth_provider)
            self.hosts_client = HostsClientJSON(auth_provider)
            self.hypervisor_v3_client = HypervisorV3ClientJSON(
                auth_provider)
            self.hypervisor_client = HypervisorClientJSON(
                auth_provider)
            self.network_client = NetworkClientJSON(auth_provider)
            self.credentials_client = CredentialsClientJSON(
                auth_provider)
            self.instance_usages_audit_log_client = \
                InstanceUsagesAuditLogClientJSON(auth_provider)
            self.volume_hosts_client = VolumeHostsClientJSON(
                auth_provider)
            self.volumes_extension_client = VolumeExtensionClientJSON(
                auth_provider)
            self.hosts_v3_client = HostsV3ClientJSON(auth_provider)
            if CONF.service_available.ceilometer:
                self.telemetry_client = TelemetryClientJSON(
                    auth_provider)
            self.token_client = TokenClientJSON()
            self.token_v3_client = V3TokenClientJSON()
            self.negative_client = NegativeRestClient(auth_provider)
            self.negative_client.service = service

        else:
            msg = "Unsupported interface type `%s'" % interface
            raise exceptions.InvalidConfiguration(msg)

        # TODO(andreaf) EC2 client still do their auth, v2 only
        ec2_client_args = (self.credentials.get('username'),
                           self.credentials.get('password'),
                           CONF.identity.uri,
                           self.credentials.get('tenant_name'))

        # common clients
        self.account_client = AccountClient(auth_provider)
        if CONF.service_available.glance:
            self.image_client = ImageClientJSON(auth_provider)
            self.image_client_v2 = ImageClientV2JSON(auth_provider)
        self.container_client = ContainerClient(auth_provider)
        self.object_client = ObjectClient(auth_provider)
        self.orchestration_client = OrchestrationClient(
            auth_provider)
        self.ec2api_client = botoclients.APIClientEC2(*ec2_client_args)
        self.s3_client = botoclients.ObjectClientS3(*ec2_client_args)
        self.custom_object_client = ObjectClientCustomizedHeader(
            auth_provider)
        self.custom_account_client = \
            AccountClientCustomizedHeader(auth_provider)
        self.data_processing_client = DataProcessingClient(
            auth_provider)

    @classmethod
    def get_auth_provider_class(cls, auth_version):
        if auth_version == 'v2':
            return auth.KeystoneV2AuthProvider
        else:
            return auth.KeystoneV3AuthProvider

    def get_default_credentials(self):
        return dict(
            username=CONF.identity.username,
            password=CONF.identity.password,
            tenant_name=CONF.identity.tenant_name
        )

    def get_auth_provider(self, credentials=None):
        auth_params = dict(client_type='tempest',
                           interface=self.interface)
        auth_provider_class = self.get_auth_provider_class(self.auth_version)
        # If invalid / incomplete credentials are provided, use default ones
        if credentials is None or \
                not auth_provider_class.check_credentials(credentials):
            credentials = self.credentials
        auth_params['credentials'] = credentials
        return auth_provider_class(**auth_params)


class AltManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self, interface='json', service=None):
        super(AltManager, self).__init__(CONF.identity.alt_username,
                                         CONF.identity.alt_password,
                                         CONF.identity.alt_tenant_name,
                                         interface=interface,
                                         service=service)


class AdminManager(Manager):

    """
    Manager object that uses the admin credentials for its
    managed client objects
    """

    def __init__(self, interface='json', service=None):
        super(AdminManager, self).__init__(CONF.identity.admin_username,
                                           CONF.identity.admin_password,
                                           CONF.identity.admin_tenant_name,
                                           interface=interface,
                                           service=service)


class ComputeAdminManager(Manager):

    """
    Manager object that uses the compute_admin credentials for its
    managed client objects
    """

    def __init__(self, interface='json', service=None):
        base = super(ComputeAdminManager, self)
        base.__init__(CONF.compute_admin.username,
                      CONF.compute_admin.password,
                      CONF.compute_admin.tenant_name,
                      interface=interface,
                      service=service)


class OrchestrationManager(Manager):
    """
    Manager object that uses the admin credentials for its
    so that heat templates can create users
    """
    def __init__(self, interface='json', service=None):
        base = super(OrchestrationManager, self)
        # heat currently needs an admin user so that stacks can create users
        # however the tests need the demo tenant so that the neutron
        # private network is the default. DO NOT change this auth combination
        # until heat can run with the demo user.
        base.__init__(CONF.identity.admin_username,
                      CONF.identity.admin_password,
                      CONF.identity.tenant_name,
                      interface=interface,
                      service=service)
