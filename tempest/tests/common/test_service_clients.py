# Copyright 2015 NEC Corporation.  All rights reserved.
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

import mock
import random
import six

from tempest.services.baremetal.v1.json import baremetal_client
from tempest.services.compute.json import agents_client
from tempest.services.compute.json import aggregates_client
from tempest.services.compute.json import availability_zone_client
from tempest.services.compute.json import certificates_client
from tempest.services.compute.json import extensions_client
from tempest.services.compute.json import fixed_ips_client
from tempest.services.compute.json import flavors_client
from tempest.services.compute.json import floating_ips_client
from tempest.services.compute.json import hosts_client
from tempest.services.compute.json import hypervisor_client
from tempest.services.compute.json import images_client
from tempest.services.compute.json import instance_usage_audit_log_client
from tempest.services.compute.json import interfaces_client
from tempest.services.compute.json import keypairs_client
from tempest.services.compute.json import limits_client
from tempest.services.compute.json import migrations_client
from tempest.services.compute.json import networks_client as nova_net_client
from tempest.services.compute.json import quotas_client
from tempest.services.compute.json import security_group_default_rules_client \
    as nova_secgrop_default_client
from tempest.services.compute.json import security_groups_client
from tempest.services.compute.json import servers_client
from tempest.services.compute.json import services_client
from tempest.services.compute.json import tenant_usages_client
from tempest.services.compute.json import volumes_extensions_client \
    as compute_volumes_extensions_client
from tempest.services.data_processing.v1_1 import data_processing_client
from tempest.services.database.json import flavors_client as db_flavor_client
from tempest.services.database.json import versions_client as db_version_client
from tempest.services.identity.v2.json import identity_client as \
    identity_v2_identity_client
from tempest.services.identity.v3.json import credentials_client
from tempest.services.identity.v3.json import endpoints_client
from tempest.services.identity.v3.json import identity_client as \
    identity_v3_identity_client
from tempest.services.identity.v3.json import policy_client
from tempest.services.identity.v3.json import region_client
from tempest.services.identity.v3.json import service_client
from tempest.services.image.v1.json import image_client
from tempest.services.image.v2.json import image_client as image_v2_client
from tempest.services.messaging.json import messaging_client
from tempest.services.network.json import network_client
from tempest.services.object_storage import account_client
from tempest.services.object_storage import container_client
from tempest.services.object_storage import object_client
from tempest.services.orchestration.json import orchestration_client
from tempest.services.telemetry.json import telemetry_client
from tempest.services.volume.json.admin import volume_hosts_client
from tempest.services.volume.json.admin import volume_quotas_client
from tempest.services.volume.json.admin import volume_services_client
from tempest.services.volume.json.admin import volume_types_client
from tempest.services.volume.json import availability_zone_client \
    as volume_az_client
from tempest.services.volume.json import backups_client
from tempest.services.volume.json import extensions_client \
    as volume_extensions_client
from tempest.services.volume.json import qos_client
from tempest.services.volume.json import snapshots_client
from tempest.services.volume.json import volumes_client
from tempest.services.volume.v2.json.admin import volume_hosts_client \
    as volume_v2_hosts_client
from tempest.services.volume.v2.json.admin import volume_quotas_client \
    as volume_v2_quotas_client
from tempest.services.volume.v2.json.admin import volume_services_client \
    as volume_v2_services_client
from tempest.services.volume.v2.json.admin import volume_types_client \
    as volume_v2_types_client
from tempest.services.volume.v2.json import availability_zone_client \
    as volume_v2_az_client
from tempest.services.volume.v2.json import backups_client \
    as volume_v2_backups_client
from tempest.services.volume.v2.json import extensions_client \
    as volume_v2_extensions_client
from tempest.services.volume.v2.json import qos_client as volume_v2_qos_client
from tempest.services.volume.v2.json import snapshots_client \
    as volume_v2_snapshots_client
from tempest.services.volume.v2.json import volumes_client as \
    volume_v2_volumes_client
from tempest.tests import base


class TestServiceClient(base.TestCase):

    @mock.patch('tempest_lib.common.rest_client.RestClient.__init__')
    def test_service_client_creations_with_specified_args(self, mock_init):
        test_clients = [
            baremetal_client.BaremetalClientJSON,
            agents_client.AgentsClientJSON,
            aggregates_client.AggregatesClientJSON,
            availability_zone_client.AvailabilityZoneClientJSON,
            certificates_client.CertificatesClientJSON,
            extensions_client.ExtensionsClientJSON,
            fixed_ips_client.FixedIPsClientJSON,
            flavors_client.FlavorsClientJSON,
            floating_ips_client.FloatingIPsClientJSON,
            hosts_client.HostsClientJSON,
            hypervisor_client.HypervisorClientJSON,
            images_client.ImagesClientJSON,
            instance_usage_audit_log_client.InstanceUsagesAuditLogClientJSON,
            interfaces_client.InterfacesClientJSON,
            keypairs_client.KeyPairsClientJSON,
            limits_client.LimitsClientJSON,
            migrations_client.MigrationsClientJSON,
            nova_net_client.NetworksClientJSON,
            quotas_client.QuotasClientJSON,
            quotas_client.QuotaClassesClientJSON,
            nova_secgrop_default_client.SecurityGroupDefaultRulesClientJSON,
            security_groups_client.SecurityGroupsClientJSON,
            servers_client.ServersClientJSON,
            services_client.ServicesClientJSON,
            tenant_usages_client.TenantUsagesClientJSON,
            compute_volumes_extensions_client.VolumesExtensionsClientJSON,
            data_processing_client.DataProcessingClient,
            db_flavor_client.DatabaseFlavorsClientJSON,
            db_version_client.DatabaseVersionsClientJSON,
            messaging_client.MessagingClientJSON,
            network_client.NetworkClientJSON,
            account_client.AccountClient,
            container_client.ContainerClient,
            object_client.ObjectClient,
            orchestration_client.OrchestrationClient,
            telemetry_client.TelemetryClientJSON,
            qos_client.QosSpecsClientJSON,
            volume_hosts_client.VolumeHostsClientJSON,
            volume_quotas_client.VolumeQuotasClientJSON,
            volume_services_client.VolumesServicesClientJSON,
            volume_types_client.VolumeTypesClientJSON,
            volume_az_client.VolumeAvailabilityZoneClientJSON,
            backups_client.BackupsClientJSON,
            volume_extensions_client.ExtensionsClientJSON,
            snapshots_client.SnapshotsClientJSON,
            volumes_client.VolumesClientJSON,
            volume_v2_hosts_client.VolumeHostsV2ClientJSON,
            volume_v2_quotas_client.VolumeQuotasV2Client,
            volume_v2_services_client.VolumesServicesV2ClientJSON,
            volume_v2_types_client.VolumeTypesV2ClientJSON,
            volume_v2_az_client.VolumeV2AvailabilityZoneClientJSON,
            volume_v2_backups_client.BackupsClientV2JSON,
            volume_v2_extensions_client.ExtensionsV2ClientJSON,
            volume_v2_qos_client.QosSpecsV2ClientJSON,
            volume_v2_snapshots_client.SnapshotsV2ClientJSON,
            volume_v2_volumes_client.VolumesV2ClientJSON,
            identity_v2_identity_client.IdentityClientJSON,
            credentials_client.CredentialsClientJSON,
            endpoints_client.EndPointClientJSON,
            identity_v3_identity_client.IdentityV3ClientJSON,
            policy_client.PolicyClientJSON,
            region_client.RegionClientJSON,
            service_client.ServiceClientJSON,
            image_client.ImageClientJSON,
            image_v2_client.ImageClientV2JSON
        ]

        for client in test_clients:
            fake_string = six.text_type(random.randint(1, 0x7fffffff))
            auth = 'auth' + fake_string
            service = 'service' + fake_string
            region = 'region' + fake_string
            params = {
                'endpoint_type': 'URL' + fake_string,
                'build_interval': random.randint(1, 100),
                'build_timeout': random.randint(1, 100),
                'disable_ssl_certificate_validation':
                    True if random.randint(0, 1) else False,
                'ca_certs': None,
                'trace_requests': 'foo' + fake_string
            }
            client(auth, service, region, **params)
            mock_init.assert_called_once_with(auth, service, region, **params)
            mock_init.reset_mock()
