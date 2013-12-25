# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
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
from tempest.services.compute.v3.json.availability_zone_client import \
    AvailabilityZoneV3ClientJSON
from tempest.services.compute.v3.json.certificates_client import \
    CertificatesV3ClientJSON
from tempest.services.compute.v3.json.extensions_client import \
    ExtensionsV3ClientJSON
from tempest.services.compute.v3.json.hypervisor_client import \
    HypervisorV3ClientJSON
from tempest.services.compute.v3.json.interfaces_client import \
    InterfacesV3ClientJSON
from tempest.services.compute.v3.json.keypairs_client import \
    KeyPairsV3ClientJSON
from tempest.services.compute.v3.json.servers_client import \
    ServersV3ClientJSON
from tempest.services.compute.v3.json.services_client import \
    ServicesV3ClientJSON
from tempest.services.compute.v3.json.tenant_usages_client import \
    TenantUsagesV3ClientJSON
from tempest.services.compute.v3.xml.availability_zone_client import \
    AvailabilityZoneV3ClientXML
from tempest.services.compute.v3.xml.certificates_client import \
    CertificatesV3ClientXML
from tempest.services.compute.v3.xml.extensions_client import \
    ExtensionsV3ClientXML
from tempest.services.compute.v3.xml.hypervisor_client import \
    HypervisorV3ClientXML
from tempest.services.compute.v3.xml.interfaces_client import \
    InterfacesV3ClientXML
from tempest.services.compute.v3.xml.keypairs_client import KeyPairsV3ClientXML
from tempest.services.compute.v3.xml.servers_client import ServersV3ClientXML
from tempest.services.compute.v3.xml.services_client import \
    ServicesV3ClientXML
from tempest.services.compute.v3.xml.tenant_usages_client import \
    TenantUsagesV3ClientXML
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
from tempest.services.volume.json.admin.volume_hosts_client import \
    VolumeHostsClientJSON
from tempest.services.volume.json.admin.volume_types_client import \
    VolumeTypesClientJSON
from tempest.services.volume.json.extensions_client import \
    ExtensionsClientJSON as VolumeExtensionClientJSON
from tempest.services.volume.json.snapshots_client import SnapshotsClientJSON
from tempest.services.volume.json.volumes_client import VolumesClientJSON
from tempest.services.volume.xml.admin.volume_hosts_client import \
    VolumeHostsClientXML
from tempest.services.volume.xml.admin.volume_types_client import \
    VolumeTypesClientXML
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
                 interface='json'):
        """
        We allow overriding of the credentials used within the various
        client classes managed by the Manager object. Left as None, the
        standard username/password/tenant_name is used.

        :param username: Override of the username
        :param password: Override of the password
        :param tenant_name: Override of the tenant name
        """
        self.config = CONF
        # If no creds are provided, we fall back on the defaults
        # in the config file for the Compute API.
        self.username = username or CONF.identity.username
        self.password = password or CONF.identity.password
        self.tenant_name = tenant_name or CONF.identity.tenant_name

        if None in (self.username, self.password, self.tenant_name):
            msg = ("Missing required credentials. "
                   "username: %(u)s, password: %(p)s, "
                   "tenant_name: %(t)s" %
                   {'u': username, 'p': password, 't': tenant_name})
            raise exceptions.InvalidConfiguration(msg)

        self.auth_url = CONF.identity.uri
        self.auth_url_v3 = CONF.identity.uri_v3

        client_args = (CONF, self.username, self.password,
                       self.auth_url, self.tenant_name)

        if self.auth_url_v3:
            auth_version = 'v3'
            client_args_v3_auth = (CONF, self.username,
                                   self.password, self.auth_url_v3,
                                   self.tenant_name, auth_version)
        else:
            client_args_v3_auth = None

        self.servers_client_v3_auth = None

        if interface == 'xml':
            self.certificates_client = CertificatesClientXML(*client_args)
            self.certificates_v3_client = CertificatesV3ClientXML(*client_args)
            self.servers_client = ServersClientXML(*client_args)
            self.servers_v3_client = ServersV3ClientXML(*client_args)
            self.limits_client = LimitsClientXML(*client_args)
            self.images_client = ImagesClientXML(*client_args)
            self.keypairs_v3_client = KeyPairsV3ClientXML(*client_args)
            self.keypairs_client = KeyPairsClientXML(*client_args)
            self.quotas_client = QuotasClientXML(*client_args)
            self.flavors_client = FlavorsClientXML(*client_args)
            self.extensions_v3_client = ExtensionsV3ClientXML(*client_args)
            self.extensions_client = ExtensionsClientXML(*client_args)
            self.volumes_extensions_client = VolumesExtensionsClientXML(
                *client_args)
            self.floating_ips_client = FloatingIPsClientXML(*client_args)
            self.snapshots_client = SnapshotsClientXML(*client_args)
            self.volumes_client = VolumesClientXML(*client_args)
            self.volume_types_client = VolumeTypesClientXML(*client_args)
            self.identity_client = IdentityClientXML(*client_args)
            self.identity_v3_client = IdentityV3ClientXML(*client_args)
            self.token_client = TokenClientXML(CONF)
            self.security_groups_client = SecurityGroupsClientXML(
                *client_args)
            self.interfaces_v3_client = InterfacesV3ClientXML(*client_args)
            self.interfaces_client = InterfacesClientXML(*client_args)
            self.endpoints_client = EndPointClientXML(*client_args)
            self.fixed_ips_client = FixedIPsClientXML(*client_args)
            self.availability_zone_v3_client = AvailabilityZoneV3ClientXML(
                *client_args)
            self.availability_zone_client = AvailabilityZoneClientXML(
                *client_args)
            self.services_v3_client = ServicesV3ClientXML(*client_args)
            self.service_client = ServiceClientXML(*client_args)
            self.aggregates_client = AggregatesClientXML(*client_args)
            self.services_client = ServicesClientXML(*client_args)
            self.tenant_usages_v3_client = TenantUsagesV3ClientXML(
                *client_args)
            self.tenant_usages_client = TenantUsagesClientXML(*client_args)
            self.policy_client = PolicyClientXML(*client_args)
            self.hypervisor_v3_client = HypervisorV3ClientXML(*client_args)
            self.hypervisor_client = HypervisorClientXML(*client_args)
            self.token_v3_client = V3TokenClientXML(*client_args)
            self.network_client = NetworkClientXML(*client_args)
            self.credentials_client = CredentialsClientXML(*client_args)
            self.instance_usages_audit_log_client = \
                InstanceUsagesAuditLogClientXML(*client_args)
            self.volume_hosts_client = VolumeHostsClientXML(*client_args)
            self.volumes_extension_client = VolumeExtensionClientXML(
                *client_args)

            if client_args_v3_auth:
                self.servers_client_v3_auth = ServersClientXML(
                    *client_args_v3_auth)

        elif interface == 'json':
            self.certificates_client = CertificatesClientJSON(*client_args)
            self.certificates_v3_client = CertificatesV3ClientJSON(
                *client_args)
            self.servers_client = ServersClientJSON(*client_args)
            self.servers_v3_client = ServersV3ClientJSON(*client_args)
            self.limits_client = LimitsClientJSON(*client_args)
            self.images_client = ImagesClientJSON(*client_args)
            self.keypairs_v3_client = KeyPairsV3ClientJSON(*client_args)
            self.keypairs_client = KeyPairsClientJSON(*client_args)
            self.quotas_client = QuotasClientJSON(*client_args)
            self.flavors_client = FlavorsClientJSON(*client_args)
            self.extensions_v3_client = ExtensionsV3ClientJSON(*client_args)
            self.extensions_client = ExtensionsClientJSON(*client_args)
            self.volumes_extensions_client = VolumesExtensionsClientJSON(
                *client_args)
            self.floating_ips_client = FloatingIPsClientJSON(*client_args)
            self.snapshots_client = SnapshotsClientJSON(*client_args)
            self.volumes_client = VolumesClientJSON(*client_args)
            self.volume_types_client = VolumeTypesClientJSON(*client_args)
            self.identity_client = IdentityClientJSON(*client_args)
            self.identity_v3_client = IdentityV3ClientJSON(*client_args)
            self.token_client = TokenClientJSON(CONF)
            self.security_groups_client = SecurityGroupsClientJSON(
                *client_args)
            self.interfaces_v3_client = InterfacesV3ClientJSON(*client_args)
            self.interfaces_client = InterfacesClientJSON(*client_args)
            self.endpoints_client = EndPointClientJSON(*client_args)
            self.fixed_ips_client = FixedIPsClientJSON(*client_args)
            self.availability_zone_v3_client = AvailabilityZoneV3ClientJSON(
                *client_args)
            self.availability_zone_client = AvailabilityZoneClientJSON(
                *client_args)
            self.services_v3_client = ServicesV3ClientJSON(*client_args)
            self.service_client = ServiceClientJSON(*client_args)
            self.aggregates_client = AggregatesClientJSON(*client_args)
            self.services_client = ServicesClientJSON(*client_args)
            self.tenant_usages_v3_client = TenantUsagesV3ClientJSON(
                *client_args)
            self.tenant_usages_client = TenantUsagesClientJSON(*client_args)
            self.policy_client = PolicyClientJSON(*client_args)
            self.hypervisor_v3_client = HypervisorV3ClientJSON(*client_args)
            self.hypervisor_client = HypervisorClientJSON(*client_args)
            self.token_v3_client = V3TokenClientJSON(*client_args)
            self.network_client = NetworkClientJSON(*client_args)
            self.credentials_client = CredentialsClientJSON(*client_args)
            self.instance_usages_audit_log_client = \
                InstanceUsagesAuditLogClientJSON(*client_args)
            self.volume_hosts_client = VolumeHostsClientJSON(*client_args)
            self.volumes_extension_client = VolumeExtensionClientJSON(
                *client_args)

            if client_args_v3_auth:
                self.servers_client_v3_auth = ServersClientJSON(
                    *client_args_v3_auth)
        else:
            msg = "Unsupported interface type `%s'" % interface
            raise exceptions.InvalidConfiguration(msg)

        # common clients
        self.hosts_client = HostsClientJSON(*client_args)
        self.account_client = AccountClient(*client_args)
        if CONF.service_available.glance:
            self.image_client = ImageClientJSON(*client_args)
            self.image_client_v2 = ImageClientV2JSON(*client_args)
        self.container_client = ContainerClient(*client_args)
        self.object_client = ObjectClient(*client_args)
        self.orchestration_client = OrchestrationClient(*client_args)
        self.ec2api_client = botoclients.APIClientEC2(*client_args)
        self.s3_client = botoclients.ObjectClientS3(*client_args)
        self.custom_object_client = ObjectClientCustomizedHeader(*client_args)
        self.custom_account_client = \
            AccountClientCustomizedHeader(*client_args)
        self.data_processing_client = DataProcessingClient(*client_args)


class AltManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self, interface='json'):
        super(AltManager, self).__init__(CONF.identity.alt_username,
                                         CONF.identity.alt_password,
                                         CONF.identity.alt_tenant_name,
                                         interface=interface)


class AdminManager(Manager):

    """
    Manager object that uses the admin credentials for its
    managed client objects
    """

    def __init__(self, interface='json'):
        super(AdminManager, self).__init__(CONF.identity.admin_username,
                                           CONF.identity.admin_password,
                                           CONF.identity.admin_tenant_name,
                                           interface=interface)


class ComputeAdminManager(Manager):

    """
    Manager object that uses the compute_admin credentials for its
    managed client objects
    """

    def __init__(self, interface='json'):
        base = super(ComputeAdminManager, self)
        base.__init__(CONF.compute_admin.username,
                      CONF.compute_admin.password,
                      CONF.compute_admin.tenant_name,
                      interface=interface)


class OrchestrationManager(Manager):
    """
    Manager object that uses the admin credentials for its
    so that heat templates can create users
    """
    def __init__(self, interface='json'):
        base = super(OrchestrationManager, self)
        base.__init__(CONF.identity.admin_username,
                      CONF.identity.admin_password,
                      CONF.identity.tenant_name,
                      interface=interface)
