# Copyright 2017 Mirantis Inc.
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

import time

from tempest.api.compute import base
from tempest.lib import decorators


class ServerDiagnosticsTest(base.BaseV2ComputeAdminTest):
    """Test server diagnostics with compute microversion less than 2.48"""

    min_microversion = None
    max_microversion = '2.47'

    @classmethod
    def setup_clients(cls):
        super(ServerDiagnosticsTest, cls).setup_clients()
        cls.client = cls.os_admin.servers_client

    @decorators.idempotent_id('31ff3486-b8a0-4f56-a6c0-aab460531db3')
    def test_get_server_diagnostics(self):
        """Test getting server diagnostics"""
        server_id = self.create_test_server(wait_until='ACTIVE')['id']
        diagnostics = self.client.show_server_diagnostics(server_id)

        # NOTE(snikitin): Before microversion 2.48 response data from each
        # hypervisor (libvirt, xen, vmware) was different. None of the fields
        # were equal. As this test is common for libvirt, xen and vmware CI
        # jobs we can't check any field in the response because all fields are
        # different.
        self.assertNotEmpty(diagnostics)


class ServerDiagnosticsV248Test(base.BaseV2ComputeAdminTest):
    """Test server diagnostics with compute microversion greater than 2.47"""

    min_microversion = '2.48'
    max_microversion = 'latest'

    @classmethod
    def setup_clients(cls):
        super(ServerDiagnosticsV248Test, cls).setup_clients()
        cls.client = cls.os_admin.servers_client

    @decorators.idempotent_id('64d0d48c-dff1-11e6-bf01-fe55135034f3')
    def test_get_server_diagnostics(self):
        """Test getting server diagnostics"""
        server_id = self.create_test_server(wait_until='ACTIVE')['id']
        # Response status and filed types will be checked by json schema
        self.client.show_server_diagnostics(server_id)

        # NOTE(snikitin): This is a special case for Xen hypervisor. In Xen
        # case we're getting diagnostics stats from the RRDs which are updated
        # every 5 seconds. It means that diagnostics information may be
        # incomplete during first 5 seconds of VM life. In such cases methods
        # which get diagnostics stats from Xen may raise exceptions or
        # return `NaN` values. Such behavior must be handled correctly.
        # Response must contain all diagnostics fields (may be with `None`
        # values) and response status must be 200. Line above checks it by
        # json schema.
        time.sleep(10)
        diagnostics = self.client.show_server_diagnostics(server_id)

        # NOTE(snikitin): After 10 seconds diagnostics fields must contain
        # not None values. But we will check only "memory_details.maximum"
        # field because only this field meets all the following conditions:
        # 1) This field may be unset because of Xen 5 seconds timeout.
        # 2) This field is present in responses from all three supported
        #    hypervisors (libvirt, xen, vmware).
        self.assertIsNotNone(diagnostics['memory_details']['maximum'])
