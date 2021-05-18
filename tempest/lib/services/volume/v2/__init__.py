# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import warnings

from tempest.lib.services.volume.v2.availability_zone_client \
    import AvailabilityZoneClient
from tempest.lib.services.volume.v2.backups_client import BackupsClient
from tempest.lib.services.volume.v2.capabilities_client import \
    CapabilitiesClient
from tempest.lib.services.volume.v2.encryption_types_client import \
    EncryptionTypesClient
from tempest.lib.services.volume.v2.extensions_client import ExtensionsClient
from tempest.lib.services.volume.v2.hosts_client import HostsClient
from tempest.lib.services.volume.v2.limits_client import LimitsClient
from tempest.lib.services.volume.v2.qos_client import QosSpecsClient
from tempest.lib.services.volume.v2.quota_classes_client import \
    QuotaClassesClient
from tempest.lib.services.volume.v2.quotas_client import QuotasClient
from tempest.lib.services.volume.v2.scheduler_stats_client import \
    SchedulerStatsClient
from tempest.lib.services.volume.v2.services_client import ServicesClient
from tempest.lib.services.volume.v2.snapshot_manage_client import \
    SnapshotManageClient
from tempest.lib.services.volume.v2.snapshots_client import SnapshotsClient
from tempest.lib.services.volume.v2.transfers_client import TransfersClient
from tempest.lib.services.volume.v2.types_client import TypesClient
from tempest.lib.services.volume.v2.volume_manage_client import \
    VolumeManageClient
from tempest.lib.services.volume.v2.volumes_client import VolumesClient

__all__ = ['AvailabilityZoneClient', 'BackupsClient', 'EncryptionTypesClient',
           'ExtensionsClient', 'HostsClient', 'QosSpecsClient', 'QuotasClient',
           'ServicesClient', 'SnapshotsClient', 'TypesClient', 'VolumesClient',
           'LimitsClient', 'CapabilitiesClient', 'SchedulerStatsClient',
           'SnapshotManageClient', 'VolumeManageClient', 'TransfersClient',
           'QuotaClassesClient']

warnings.warn(
    "The tempest.lib.services.volume.v2 module (volume v2 APIs service "
    "clients) is deprecated in favor of tempest.lib.services.volume.v3 "
    "(volume v3 APIs service clients) and will be removed once Tempest stop "
    "supporting stable wallaby.", DeprecationWarning)
