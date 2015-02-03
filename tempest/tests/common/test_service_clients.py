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
from tempest.services.compute.json import volumes_extensions_client
from tempest.services.database.json import flavors_client as db_flavor_client
from tempest.services.database.json import versions_client as db_version_client
from tempest.services.network.json import network_client
from tempest.services.orchestration.json import orchestration_client
from tempest.tests import base


class TestServiceClient(base.TestCase):

    @mock.patch('tempest_lib.common.rest_client.RestClient.__init__')
    def test_service_client_creations_with_specified_args(self, mock_init):
        test_clients = [
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
            volumes_extensions_client.VolumesExtensionsClientJSON,
            db_flavor_client.DatabaseFlavorsClientJSON,
            db_version_client.DatabaseVersionsClientJSON,
            network_client.NetworkClientJSON,
            orchestration_client.OrchestrationClient]

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
