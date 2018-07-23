# Copyright 2013 NEC Corporation.  All rights reserved.
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

from tempest.api.compute import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class ServicesAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):
    """Tests Services API. List and Enable/Disable require admin privileges."""
    max_microversion = '2.52'

    @classmethod
    def setup_clients(cls):
        super(ServicesAdminNegativeTestJSON, cls).setup_clients()
        cls.client = cls.os_admin.services_client
        cls.non_admin_client = cls.services_client

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('1126d1f8-266e-485f-a687-adc547492646')
    def test_list_services_with_non_admin_user(self):
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.list_services)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d0884a69-f693-4e79-a9af-232d15643bf7')
    def test_get_service_by_invalid_params(self):
        # Expect all services to be returned when the request contains invalid
        # parameters.
        services = self.client.list_services()['services']
        services_xxx = (self.client.list_services(xxx='nova-compute')
                        ['services'])
        self.assertEqual(len(services), len(services_xxx))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('1e966d4a-226e-47c7-b601-0b18a27add54')
    def test_get_service_by_invalid_service_and_valid_host(self):
        services = self.client.list_services()['services']
        host_name = services[0]['host']
        services = self.client.list_services(host=host_name,
                                             binary='xxx')['services']
        self.assertEmpty(services)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('64e7e7fb-69e8-4cb6-a71d-8d5eb0c98655')
    def test_get_service_with_valid_service_and_invalid_host(self):
        services = self.client.list_services()['services']
        binary_name = services[0]['binary']
        services = self.client.list_services(host='xxx',
                                             binary=binary_name)['services']
        self.assertEmpty(services)


class ServicesAdminNegativeV253TestJSON(ServicesAdminNegativeTestJSON):
    min_microversion = '2.53'
    max_microversion = 'latest'

    # NOTE(felipemonteiro): This class tests the services APIs response schema
    # for the 2.53 microversion. Schema testing is done for `list_services`
    # tests.

    @classmethod
    def resource_setup(cls):
        super(ServicesAdminNegativeV253TestJSON, cls).resource_setup()
        cls.fake_service_id = data_utils.rand_uuid()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('508671aa-c929-4479-bd10-8680d40dd0a6')
    def test_enable_service_with_invalid_service_id(self):
        self.assertRaises(lib_exc.NotFound,
                          self.client.update_service,
                          service_id=self.fake_service_id,
                          status='enabled')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a9eeeade-42b3-419f-87aa-c9342aa068cf')
    def test_disable_service_with_invalid_service_id(self):
        self.assertRaises(lib_exc.NotFound,
                          self.client.update_service,
                          service_id=self.fake_service_id,
                          status='disabled')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f46a9d91-1e85-4b96-8e7a-db7706fa2e9a')
    def test_disable_log_reason_with_invalid_service_id(self):
        # disabled_reason requires that status='disabled' be provided.
        self.assertRaises(lib_exc.NotFound,
                          self.client.update_service,
                          service_id=self.fake_service_id,
                          status='disabled',
                          disabled_reason='maintenance')
