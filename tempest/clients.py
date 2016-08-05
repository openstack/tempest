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
from tempest.common import negative_rest_client
from tempest import config
from tempest import exceptions
from tempest.lib import auth
from tempest.lib import exceptions as lib_exc
from tempest.lib.services import clients
from tempest.services import baremetal
from tempest.services import data_processing
from tempest.services import identity
from tempest.services import object_storage
from tempest.services import orchestration
from tempest.services import volume

CONF = config.CONF
LOG = logging.getLogger(__name__)


class Manager(clients.ServiceClients):
    """Top level manager for OpenStack tempest clients"""

    default_params = config.service_client_config()

    # TODO(andreaf) This is only used by data_processing and baremetal clients,
    # and should be removed once they are out of Tempest
    default_params_with_timeout_values = {
        'build_interval': CONF.compute.build_interval,
        'build_timeout': CONF.compute.build_timeout
    }
    default_params_with_timeout_values.update(default_params)

    def __init__(self, credentials, service=None, scope='project'):
        """Initialization of Manager class.

        Setup all services clients and make them available for tests cases.
        :param credentials: type Credentials or TestResources
        :param service: Service name
        :param scope: default scope for tokens produced by the auth provider
        """
        _, identity_uri = get_auth_provider_class(credentials)
        super(Manager, self).__init__(
            credentials=credentials, identity_uri=identity_uri, scope=scope,
            region=CONF.identity.region,
            client_parameters=self._prepare_configuration())
        # TODO(andreaf) When clients are initialised without the right
        # parameters available, the calls below will trigger a KeyError.
        # We should catch that and raise a better error.
        self._set_compute_clients()
        self._set_identity_clients()
        self._set_volume_clients()
        self._set_object_storage_clients()
        self._set_image_clients()
        self._set_network_clients()

        self.baremetal_client = baremetal.BaremetalClient(
            self.auth_provider,
            CONF.baremetal.catalog_type,
            CONF.identity.region,
            endpoint_type=CONF.baremetal.endpoint_type,
            **self.default_params_with_timeout_values)
        self.orchestration_client = orchestration.OrchestrationClient(
            self.auth_provider,
            CONF.orchestration.catalog_type,
            CONF.orchestration.region or CONF.identity.region,
            endpoint_type=CONF.orchestration.endpoint_type,
            build_interval=CONF.orchestration.build_interval,
            build_timeout=CONF.orchestration.build_timeout,
            **self.default_params)
        self.data_processing_client = data_processing.DataProcessingClient(
            self.auth_provider,
            CONF.data_processing.catalog_type,
            CONF.identity.region,
            endpoint_type=CONF.data_processing.endpoint_type,
            **self.default_params_with_timeout_values)
        self.negative_client = negative_rest_client.NegativeRestClient(
            self.auth_provider, service, **self.default_params)

    def _prepare_configuration(self):
        """Map values from CONF into Manager parameters

        This uses `config.service_client_config` for all services to collect
        most configuration items needed to init the clients.
        """
        # NOTE(andreaf) Configuration items will be passed in future patches
        # into ClientFactory objects, but for now we update all the
        # _set_*_client methods to consume them so we can verify that the
        # configuration collected is correct

        configuration = {}

        # Setup the parameters for all Tempest services.
        # NOTE(andreaf) Since client.py is an internal module of Tempest,
        # it doesn't have to consider plugin configuration.
        all_tempest_modules = (set(clients.tempest_modules()) |
                               clients._tempest_internal_modules())
        for service in all_tempest_modules:
            try:
                # NOTE(andreaf) Use the unversioned service name to fetch
                # the configuration since configuration is not versioned.
                service_for_config = service.split('.')[0]
                if service_for_config not in configuration:
                    configuration[service_for_config] = (
                        config.service_client_config(service_for_config))
            except lib_exc.UnknownServiceClient:
                LOG.warn(
                    'Could not load configuration for service %s' % service)

        return configuration

    def _set_network_clients(self):
        self.network_agents_client = self.network.AgentsClient()
        self.network_extensions_client = self.network.ExtensionsClient()
        self.networks_client = self.network.NetworksClient()
        self.subnetpools_client = self.network.SubnetpoolsClient()
        self.subnets_client = self.network.SubnetsClient()
        self.ports_client = self.network.PortsClient()
        self.network_quotas_client = self.network.QuotasClient()
        self.floating_ips_client = self.network.FloatingIPsClient()
        self.metering_labels_client = self.network.MeteringLabelsClient()
        self.metering_label_rules_client = (
            self.network.MeteringLabelRulesClient())
        self.routers_client = self.network.RoutersClient()
        self.security_group_rules_client = (
            self.network.SecurityGroupRulesClient())
        self.security_groups_client = self.network.SecurityGroupsClient()
        self.network_versions_client = self.network.NetworkVersionsClient()

    def _set_image_clients(self):
        if CONF.service_available.glance:
            self.image_client = self.image_v1.ImagesClient()
            self.image_member_client = self.image_v1.ImageMembersClient()
            self.image_client_v2 = self.image_v2.ImagesClient()
            self.image_member_client_v2 = self.image_v2.ImageMembersClient()
            self.namespaces_client = self.image_v2.NamespacesClient()
            self.resource_types_client = self.image_v2.ResourceTypesClient()
            self.schemas_client = self.image_v2.SchemasClient()

    def _set_compute_clients(self):
        self.agents_client = self.compute.AgentsClient()
        self.compute_networks_client = self.compute.NetworksClient()
        self.migrations_client = self.compute.MigrationsClient()
        self.security_group_default_rules_client = (
            self.compute.SecurityGroupDefaultRulesClient())
        self.certificates_client = self.compute.CertificatesClient()
        eip = CONF.compute_feature_enabled.enable_instance_password
        self.servers_client = self.compute.ServersClient(
            enable_instance_password=eip)
        self.server_groups_client = self.compute.ServerGroupsClient()
        self.limits_client = self.compute.LimitsClient()
        self.compute_images_client = self.compute.ImagesClient()
        self.keypairs_client = self.compute.KeyPairsClient()
        self.quotas_client = self.compute.QuotasClient()
        self.quota_classes_client = self.compute.QuotaClassesClient()
        self.flavors_client = self.compute.FlavorsClient()
        self.extensions_client = self.compute.ExtensionsClient()
        self.floating_ip_pools_client = self.compute.FloatingIPPoolsClient()
        self.floating_ips_bulk_client = self.compute.FloatingIPsBulkClient()
        self.compute_floating_ips_client = self.compute.FloatingIPsClient()
        self.compute_security_group_rules_client = (
            self.compute.SecurityGroupRulesClient())
        self.compute_security_groups_client = (
            self.compute.SecurityGroupsClient())
        self.interfaces_client = self.compute.InterfacesClient()
        self.fixed_ips_client = self.compute.FixedIPsClient()
        self.availability_zone_client = self.compute.AvailabilityZoneClient()
        self.aggregates_client = self.compute.AggregatesClient()
        self.services_client = self.compute.ServicesClient()
        self.tenant_usages_client = self.compute.TenantUsagesClient()
        self.hosts_client = self.compute.HostsClient()
        self.hypervisor_client = self.compute.HypervisorClient()
        self.instance_usages_audit_log_client = (
            self.compute.InstanceUsagesAuditLogClient())
        self.tenant_networks_client = self.compute.TenantNetworksClient()
        self.baremetal_nodes_client = self.compute.BaremetalNodesClient()

        # NOTE: The following client needs special timeout values because
        # the API is a proxy for the other component.
        params_volume = {}
        for _key in ('build_interval', 'build_timeout'):
            _value = self.parameters['volume'].get(_key)
            if _value:
                params_volume[_key] = _value
        self.volumes_extensions_client = self.compute.VolumesClient(
            **params_volume)
        self.compute_versions_client = self.compute.VersionsClient(
            **params_volume)
        self.snapshots_extensions_client = self.compute.SnapshotsClient(
            **params_volume)

    def _set_identity_clients(self):
        params = self.parameters['identity']

        # Clients below use the admin endpoint type of Keystone API v2
        params_v2_admin = copy.copy(params)
        params_v2_admin['endpoint_type'] = CONF.identity.v2_admin_endpoint_type
        self.endpoints_client = identity.v2.EndpointsClient(self.auth_provider,
                                                            **params_v2_admin)
        self.identity_client = identity.v2.IdentityClient(self.auth_provider,
                                                          **params_v2_admin)
        self.tenants_client = identity.v2.TenantsClient(self.auth_provider,
                                                        **params_v2_admin)
        self.roles_client = identity.v2.RolesClient(self.auth_provider,
                                                    **params_v2_admin)
        self.users_client = identity.v2.UsersClient(self.auth_provider,
                                                    **params_v2_admin)
        self.identity_services_client = identity.v2.ServicesClient(
            self.auth_provider, **params_v2_admin)

        # Clients below use the public endpoint type of Keystone API v2
        params_v2_public = copy.copy(params)
        params_v2_public['endpoint_type'] = (
            CONF.identity.v2_public_endpoint_type)
        self.identity_public_client = identity.v2.IdentityClient(
            self.auth_provider, **params_v2_public)
        self.tenants_public_client = identity.v2.TenantsClient(
            self.auth_provider, **params_v2_public)
        self.users_public_client = identity.v2.UsersClient(
            self.auth_provider, **params_v2_public)

        # Clients below use the endpoint type of Keystone API v3, which is set
        # in endpoint_type
        params_v3 = copy.copy(params)
        params_v3['endpoint_type'] = CONF.identity.v3_endpoint_type
        self.domains_client = identity.v3.DomainsClient(self.auth_provider,
                                                        **params_v3)
        self.identity_v3_client = identity.v3.IdentityClient(
            self.auth_provider, **params_v3)
        self.trusts_client = identity.v3.TrustsClient(self.auth_provider,
                                                      **params_v3)
        self.users_v3_client = identity.v3.UsersClient(self.auth_provider,
                                                       **params_v3)
        self.endpoints_v3_client = identity.v3.EndPointsClient(
            self.auth_provider, **params_v3)
        self.roles_v3_client = identity.v3.RolesClient(self.auth_provider,
                                                       **params_v3)
        self.identity_services_v3_client = identity.v3.ServicesClient(
            self.auth_provider, **params_v3)
        self.policies_client = identity.v3.PoliciesClient(self.auth_provider,
                                                          **params_v3)
        self.projects_client = identity.v3.ProjectsClient(self.auth_provider,
                                                          **params_v3)
        self.regions_client = identity.v3.RegionsClient(self.auth_provider,
                                                        **params_v3)
        self.credentials_client = identity.v3.CredentialsClient(
            self.auth_provider, **params_v3)
        self.groups_client = identity.v3.GroupsClient(self.auth_provider,
                                                      **params_v3)

        # Token clients do not use the catalog. They only need default_params.
        # They read auth_url, so they should only be set if the corresponding
        # API version is marked as enabled
        if CONF.identity_feature_enabled.api_v2:
            if CONF.identity.uri:
                self.token_client = identity.v2.TokenClient(
                    CONF.identity.uri, **self.default_params)
            else:
                msg = 'Identity v2 API enabled, but no identity.uri set'
                raise exceptions.InvalidConfiguration(msg)
        if CONF.identity_feature_enabled.api_v3:
            if CONF.identity.uri_v3:
                self.token_v3_client = identity.v3.V3TokenClient(
                    CONF.identity.uri_v3, **self.default_params)
            else:
                msg = 'Identity v3 API enabled, but no identity.uri_v3 set'
                raise exceptions.InvalidConfiguration(msg)

    def _set_volume_clients(self):
        # Mandatory parameters (always defined)
        params = self.parameters['volume']

        self.volume_qos_client = volume.v1.QosSpecsClient(self.auth_provider,
                                                          **params)
        self.volume_qos_v2_client = volume.v2.QosSpecsClient(
            self.auth_provider, **params)
        self.volume_services_client = volume.v1.ServicesClient(
            self.auth_provider, **params)
        self.volume_services_v2_client = volume.v2.ServicesClient(
            self.auth_provider, **params)
        self.backups_client = volume.v1.BackupsClient(self.auth_provider,
                                                      **params)
        self.backups_v2_client = volume.v2.BackupsClient(self.auth_provider,
                                                         **params)
        self.snapshots_client = volume.v1.SnapshotsClient(self.auth_provider,
                                                          **params)
        self.snapshots_v2_client = volume.v2.SnapshotsClient(
            self.auth_provider, **params)
        self.volumes_client = volume.v1.VolumesClient(
            self.auth_provider, default_volume_size=CONF.volume.volume_size,
            **params)
        self.volumes_v2_client = volume.v2.VolumesClient(
            self.auth_provider, default_volume_size=CONF.volume.volume_size,
            **params)
        self.volume_messages_client = volume.v3.MessagesClient(
            self.auth_provider, **params)
        self.volume_types_client = volume.v1.TypesClient(self.auth_provider,
                                                         **params)
        self.volume_types_v2_client = volume.v2.TypesClient(self.auth_provider,
                                                            **params)
        self.volume_hosts_client = volume.v1.HostsClient(self.auth_provider,
                                                         **params)
        self.volume_hosts_v2_client = volume.v2.HostsClient(self.auth_provider,
                                                            **params)
        self.volume_quotas_client = volume.v1.QuotasClient(self.auth_provider,
                                                           **params)
        self.volume_quotas_v2_client = volume.v2.QuotasClient(
            self.auth_provider, **params)
        self.volumes_extension_client = volume.v1.ExtensionsClient(
            self.auth_provider, **params)
        self.volumes_v2_extension_client = volume.v2.ExtensionsClient(
            self.auth_provider, **params)
        self.volume_availability_zone_client = \
            volume.v1.AvailabilityZoneClient(self.auth_provider, **params)
        self.volume_v2_availability_zone_client = \
            volume.v2.AvailabilityZoneClient(self.auth_provider, **params)

    def _set_object_storage_clients(self):
        # Mandatory parameters (always defined)
        params = self.parameters['object-storage']

        self.account_client = object_storage.AccountClient(self.auth_provider,
                                                           **params)
        self.container_client = object_storage.ContainerClient(
            self.auth_provider, **params)
        self.object_client = object_storage.ObjectClient(self.auth_provider,
                                                         **params)


def get_auth_provider_class(credentials):
    if isinstance(credentials, auth.KeystoneV3Credentials):
        return auth.KeystoneV3AuthProvider, CONF.identity.uri_v3
    else:
        return auth.KeystoneV2AuthProvider, CONF.identity.uri


def get_auth_provider(credentials, pre_auth=False, scope='project'):
    # kwargs for auth provider match the common ones used by service clients
    default_params = config.service_client_config()
    if credentials is None:
        raise exceptions.InvalidCredentials(
            'Credentials must be specified')
    auth_provider_class, auth_url = get_auth_provider_class(
        credentials)
    _auth_provider = auth_provider_class(credentials, auth_url,
                                         scope=scope,
                                         **default_params)
    if pre_auth:
        _auth_provider.set_auth()
    return _auth_provider
