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
from tempest.lib.services import compute
from tempest.lib.services import network
from tempest import manager
from tempest.services import baremetal
from tempest.services import data_processing
from tempest.services import identity
from tempest.services import image
from tempest.services import object_storage
from tempest.services import orchestration
from tempest.services import volume

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

    def __init__(self, credentials, service=None, scope='project'):
        """Initialization of Manager class.

        Setup all services clients and make them available for tests cases.
        :param credentials: type Credentials or TestResources
        :param service: Service name
        :param scope: default scope for tokens produced by the auth provider
        """
        super(Manager, self).__init__(credentials=credentials, scope=scope)
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

    def _set_network_clients(self):
        params = {
            'service': CONF.network.catalog_type,
            'region': CONF.network.region or CONF.identity.region,
            'endpoint_type': CONF.network.endpoint_type,
            'build_interval': CONF.network.build_interval,
            'build_timeout': CONF.network.build_timeout
        }
        params.update(self.default_params)
        self.network_agents_client = network.AgentsClient(
            self.auth_provider, **params)
        self.network_extensions_client = network.ExtensionsClient(
            self.auth_provider, **params)
        self.networks_client = network.NetworksClient(
            self.auth_provider, **params)
        self.subnetpools_client = network.SubnetpoolsClient(
            self.auth_provider, **params)
        self.subnets_client = network.SubnetsClient(
            self.auth_provider, **params)
        self.ports_client = network.PortsClient(
            self.auth_provider, **params)
        self.network_quotas_client = network.QuotasClient(
            self.auth_provider, **params)
        self.floating_ips_client = network.FloatingIPsClient(
            self.auth_provider, **params)
        self.metering_labels_client = network.MeteringLabelsClient(
            self.auth_provider, **params)
        self.metering_label_rules_client = network.MeteringLabelRulesClient(
            self.auth_provider, **params)
        self.routers_client = network.RoutersClient(
            self.auth_provider, **params)
        self.security_group_rules_client = network.SecurityGroupRulesClient(
            self.auth_provider, **params)
        self.security_groups_client = network.SecurityGroupsClient(
            self.auth_provider, **params)
        self.network_versions_client = network.NetworkVersionsClient(
            self.auth_provider, **params)

    def _set_image_clients(self):
        params = {
            'service': CONF.image.catalog_type,
            'region': CONF.image.region or CONF.identity.region,
            'endpoint_type': CONF.image.endpoint_type,
            'build_interval': CONF.image.build_interval,
            'build_timeout': CONF.image.build_timeout
        }
        params.update(self.default_params)

        if CONF.service_available.glance:
            self.image_client = image.v1.ImagesClient(
                self.auth_provider, **params)
            self.image_member_client = image.v1.ImageMembersClient(
                self.auth_provider, **params)
            self.image_client_v2 = image.v2.ImagesClient(
                self.auth_provider, **params)
            self.image_member_client_v2 = image.v2.ImageMembersClient(
                self.auth_provider, **params)
            self.namespaces_client = image.v2.NamespacesClient(
                self.auth_provider, **params)
            self.resource_types_client = image.v2.ResourceTypesClient(
                self.auth_provider, **params)
            self.schemas_client = image.v2.SchemasClient(
                self.auth_provider, **params)

    def _set_compute_clients(self):
        params = {
            'service': CONF.compute.catalog_type,
            'region': CONF.compute.region or CONF.identity.region,
            'endpoint_type': CONF.compute.endpoint_type,
            'build_interval': CONF.compute.build_interval,
            'build_timeout': CONF.compute.build_timeout
        }
        params.update(self.default_params)

        self.agents_client = compute.AgentsClient(self.auth_provider, **params)
        self.compute_networks_client = compute.NetworksClient(
            self.auth_provider, **params)
        self.migrations_client = compute.MigrationsClient(self.auth_provider,
                                                          **params)
        self.security_group_default_rules_client = (
            compute.SecurityGroupDefaultRulesClient(self.auth_provider,
                                                    **params))
        self.certificates_client = compute.CertificatesClient(
            self.auth_provider, **params)
        self.servers_client = compute.ServersClient(
            self.auth_provider,
            enable_instance_password=CONF.compute_feature_enabled
                .enable_instance_password,
            **params)
        self.server_groups_client = compute.ServerGroupsClient(
            self.auth_provider, **params)
        self.limits_client = compute.LimitsClient(self.auth_provider, **params)
        self.compute_images_client = compute.ImagesClient(self.auth_provider,
                                                          **params)
        self.keypairs_client = compute.KeyPairsClient(self.auth_provider,
                                                      **params)
        self.quotas_client = compute.QuotasClient(self.auth_provider, **params)
        self.quota_classes_client = compute.QuotaClassesClient(
            self.auth_provider, **params)
        self.flavors_client = compute.FlavorsClient(self.auth_provider,
                                                    **params)
        self.extensions_client = compute.ExtensionsClient(self.auth_provider,
                                                          **params)
        self.floating_ip_pools_client = compute.FloatingIPPoolsClient(
            self.auth_provider, **params)
        self.floating_ips_bulk_client = compute.FloatingIPsBulkClient(
            self.auth_provider, **params)
        self.compute_floating_ips_client = compute.FloatingIPsClient(
            self.auth_provider, **params)
        self.compute_security_group_rules_client = (
            compute.SecurityGroupRulesClient(self.auth_provider, **params))
        self.compute_security_groups_client = compute.SecurityGroupsClient(
            self.auth_provider, **params)
        self.interfaces_client = compute.InterfacesClient(self.auth_provider,
                                                          **params)
        self.fixed_ips_client = compute.FixedIPsClient(self.auth_provider,
                                                       **params)
        self.availability_zone_client = compute.AvailabilityZoneClient(
            self.auth_provider, **params)
        self.aggregates_client = compute.AggregatesClient(self.auth_provider,
                                                          **params)
        self.services_client = compute.ServicesClient(self.auth_provider,
                                                      **params)
        self.tenant_usages_client = compute.TenantUsagesClient(
            self.auth_provider, **params)
        self.hosts_client = compute.HostsClient(self.auth_provider, **params)
        self.hypervisor_client = compute.HypervisorClient(self.auth_provider,
                                                          **params)
        self.instance_usages_audit_log_client = (
            compute.InstanceUsagesAuditLogClient(self.auth_provider, **params))
        self.tenant_networks_client = compute.TenantNetworksClient(
            self.auth_provider, **params)
        self.baremetal_nodes_client = compute.BaremetalNodesClient(
            self.auth_provider, **params)

        # NOTE: The following client needs special timeout values because
        # the API is a proxy for the other component.
        params_volume = copy.deepcopy(params)
        params_volume.update({
            'build_interval': CONF.volume.build_interval,
            'build_timeout': CONF.volume.build_timeout
        })
        self.volumes_extensions_client = compute.VolumesClient(
            self.auth_provider, **params_volume)
        self.compute_versions_client = compute.VersionsClient(
            self.auth_provider, **params_volume)
        self.snapshots_extensions_client = compute.SnapshotsClient(
            self.auth_provider, **params_volume)

    def _set_identity_clients(self):
        params = {
            'service': CONF.identity.catalog_type,
            'region': CONF.identity.region
        }
        params.update(self.default_params_with_timeout_values)

        # Clients below use the admin endpoint type of Keystone API v2
        params_v2_admin = params.copy()
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
        params_v2_public = params.copy()
        params_v2_public['endpoint_type'] = (
            CONF.identity.v2_public_endpoint_type)
        self.identity_public_client = identity.v2.IdentityClient(
            self.auth_provider, **params_v2_public)
        self.tenants_public_client = identity.v2.TenantsClient(
            self.auth_provider, **params_v2_public)
        self.users_public_client = identity.v2.UsersClient(
            self.auth_provider, **params_v2_public)

        # Clients below use the endpoint type of Keystone API v3
        params_v3 = params.copy()
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
        params = {
            'service': CONF.volume.catalog_type,
            'region': CONF.volume.region or CONF.identity.region,
            'endpoint_type': CONF.volume.endpoint_type,
            'build_interval': CONF.volume.build_interval,
            'build_timeout': CONF.volume.build_timeout
        }
        params.update(self.default_params)

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
        params = {
            'service': CONF.object_storage.catalog_type,
            'region': CONF.object_storage.region or CONF.identity.region,
            'endpoint_type': CONF.object_storage.endpoint_type
        }
        params.update(self.default_params_with_timeout_values)

        self.account_client = object_storage.AccountClient(self.auth_provider,
                                                           **params)
        self.container_client = object_storage.ContainerClient(
            self.auth_provider, **params)
        self.object_client = object_storage.ObjectClient(self.auth_provider,
                                                         **params)
