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
from tempest.services.image.v1.json import images_client
from tempest.services.image.v2.json import images_client as images_v2_client
from tempest.services.messaging.json import messaging_client
from tempest.services.network.json import network_client
from tempest.services.object_storage import account_client
from tempest.services.object_storage import container_client
from tempest.services.object_storage import object_client
from tempest.services.orchestration.json import orchestration_client
from tempest.services.telemetry.json import alarming_client
from tempest.services.telemetry.json import telemetry_client
from tempest.services.volume.v1.json.admin import hosts_client \
    as volume_hosts_client
from tempest.services.volume.v1.json.admin import quotas_client \
    as volume_quotas_client
from tempest.services.volume.v1.json.admin import services_client \
    as volume_services_client
from tempest.services.volume.v1.json.admin import types_client \
    as volume_types_client
from tempest.services.volume.v1.json import availability_zone_client \
    as volume_az_client
from tempest.services.volume.v1.json import backups_client
from tempest.services.volume.v1.json import extensions_client \
    as volume_extensions_client
from tempest.services.volume.v1.json import qos_client
from tempest.services.volume.v1.json import snapshots_client
from tempest.services.volume.v1.json import volumes_client
from tempest.services.volume.v2.json.admin import hosts_client \
    as volume_v2_hosts_client
from tempest.services.volume.v2.json.admin import quotas_client \
    as volume_v2_quotas_client
from tempest.services.volume.v2.json.admin import services_client \
    as volume_v2_services_client
from tempest.services.volume.v2.json.admin import types_client \
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
            baremetal_client.BaremetalClient,
            data_processing_client.DataProcessingClient,
            db_flavor_client.DatabaseFlavorsClient,
            db_version_client.DatabaseVersionsClient,
            messaging_client.MessagingClient,
            network_client.NetworkClient,
            account_client.AccountClient,
            container_client.ContainerClient,
            object_client.ObjectClient,
            orchestration_client.OrchestrationClient,
            telemetry_client.TelemetryClient,
            alarming_client.AlarmingClient,
            qos_client.QosSpecsClient,
            volume_hosts_client.HostsClient,
            volume_quotas_client.QuotasClient,
            volume_services_client.ServicesClient,
            volume_types_client.TypesClient,
            volume_az_client.AvailabilityZoneClient,
            backups_client.BackupsClient,
            volume_extensions_client.ExtensionsClient,
            snapshots_client.SnapshotsClient,
            volumes_client.VolumesClient,
            volume_v2_hosts_client.HostsClient,
            volume_v2_quotas_client.QuotasClient,
            volume_v2_services_client.ServicesClient,
            volume_v2_types_client.TypesClient,
            volume_v2_az_client.AvailabilityZoneClient,
            volume_v2_backups_client.BackupsClient,
            volume_v2_extensions_client.ExtensionsClient,
            volume_v2_qos_client.QosSpecsClient,
            volume_v2_snapshots_client.SnapshotsClient,
            volume_v2_volumes_client.VolumesClient,
            identity_v2_identity_client.IdentityClient,
            credentials_client.CredentialsClient,
            endpoints_client.EndPointClient,
            identity_v3_identity_client.IdentityV3Client,
            policy_client.PolicyClient,
            region_client.RegionClient,
            service_client.ServiceClient,
            images_client.ImagesClient,
            images_v2_client.ImagesClientV2
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
