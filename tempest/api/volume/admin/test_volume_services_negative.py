# Copyright 2018 FiberHome Telecommunication Technologies CO.,LTD
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

from tempest.api.volume import base
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class VolumeServicesNegativeTest(base.BaseVolumeAdminTest):

    @classmethod
    def resource_setup(cls):
        super(VolumeServicesNegativeTest, cls).resource_setup()
        services = cls.admin_volume_services_client.list_services()['services']
        cls.host = services[0]['host']
        cls.binary = services[0]['binary']

    @decorators.attr(type='negative')
    @decorators.idempotent_id('3246ce65-ba70-4159-aa3b-082c28e4b484')
    def test_enable_service_with_invalid_host(self):
        self.assertRaises(lib_exc.NotFound,
                          self.admin_volume_services_client.enable_service,
                          host='invalid_host', binary=self.binary)

    @decorators.attr(type='negative')
    @decorators.idempotent_id('c571f179-c6e6-4c50-a0ab-368b628a8ac1')
    def test_disable_service_with_invalid_binary(self):
        self.assertRaises(lib_exc.NotFound,
                          self.admin_volume_services_client.disable_service,
                          host=self.host, binary='invalid_binary')

    @decorators.attr(type='negative')
    @decorators.idempotent_id('77767b36-5e8f-4c68-a0b5-2308cc21ec64')
    def test_disable_log_reason_with_no_reason(self):
        self.assertRaises(lib_exc.BadRequest,
                          self.admin_volume_services_client.disable_log_reason,
                          host=self.host, binary=self.binary,
                          disabled_reason=None)

    @decorators.attr(type='negative')
    @decorators.idempotent_id('712bfab8-1f44-4eb5-a632-fa70bf78f05e')
    def test_freeze_host_with_invalid_host(self):
        self.assertRaises(lib_exc.BadRequest,
                          self.admin_volume_services_client.freeze_host,
                          host='invalid_host')

    @decorators.attr(type='negative')
    @decorators.idempotent_id('7c6287c9-d655-47e1-9a11-76f6657a6dce')
    def test_thaw_host_with_invalid_host(self):
        self.assertRaises(lib_exc.BadRequest,
                          self.admin_volume_services_client.thaw_host,
                          host='invalid_host')
