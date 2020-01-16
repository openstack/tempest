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
from tempest.lib.services.volume.v3.attachments_client import AttachmentsClient
from tempest.lib.services.volume.v3.availability_zone_client \
    import AvailabilityZoneClient
from tempest.lib.services.volume.v3.backups_client import BackupsClient
from tempest.lib.services.volume.v3.base_client import BaseClient
from tempest.lib.services.volume.v3.capabilities_client import \
    CapabilitiesClient
from tempest.lib.services.volume.v3.encryption_types_client import \
    EncryptionTypesClient
from tempest.lib.services.volume.v3.extensions_client import ExtensionsClient
from tempest.lib.services.volume.v3.group_snapshots_client import \
    GroupSnapshotsClient
from tempest.lib.services.volume.v3.group_types_client import GroupTypesClient
from tempest.lib.services.volume.v3.groups_client import GroupsClient
from tempest.lib.services.volume.v3.hosts_client import HostsClient
from tempest.lib.services.volume.v3.limits_client import LimitsClient
from tempest.lib.services.volume.v3.messages_client import MessagesClient
from tempest.lib.services.volume.v3.qos_client import QosSpecsClient
from tempest.lib.services.volume.v3.quota_classes_client import \
    QuotaClassesClient
from tempest.lib.services.volume.v3.quotas_client import QuotasClient
from tempest.lib.services.volume.v3.scheduler_stats_client import \
    SchedulerStatsClient
from tempest.lib.services.volume.v3.services_client import ServicesClient
from tempest.lib.services.volume.v3.snapshot_manage_client import \
    SnapshotManageClient
from tempest.lib.services.volume.v3.snapshots_client import SnapshotsClient
from tempest.lib.services.volume.v3.transfers_client import TransfersClient
from tempest.lib.services.volume.v3.types_client import TypesClient
from tempest.lib.services.volume.v3.versions_client import VersionsClient
from tempest.lib.services.volume.v3.volume_manage_client import \
    VolumeManageClient
from tempest.lib.services.volume.v3.volumes_client import VolumesClient
__all__ = ['AttachmentsClient', 'AvailabilityZoneClient', 'BackupsClient',
           'BaseClient', 'CapabilitiesClient', 'EncryptionTypesClient',
           'ExtensionsClient', 'GroupSnapshotsClient', 'GroupTypesClient',
           'GroupsClient', 'HostsClient', 'LimitsClient', 'MessagesClient',
           'QosSpecsClient', 'QuotaClassesClient', 'QuotasClient',
           'SchedulerStatsClient', 'ServicesClient', 'SnapshotManageClient',
           'SnapshotsClient', 'TransfersClient', 'TypesClient',
           'VersionsClient', 'VolumeManageClient', 'VolumesClient']
