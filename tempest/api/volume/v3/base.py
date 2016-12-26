# Copyright 2016 Andrew Kerr
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
from tempest.api.volume import api_microversion_fixture
from tempest.api.volume import base
from tempest import config
from tempest.lib.common import api_version_utils

CONF = config.CONF


class VolumesV3Test(api_version_utils.BaseMicroversionTest,
                    base.BaseVolumeTest):
    """Base test case class for all v3 Cinder API tests."""

    _api_version = 3

    @classmethod
    def skip_checks(cls):
        super(VolumesV3Test, cls).skip_checks()
        api_version_utils.check_skip_with_microversion(
            cls.min_microversion, cls.max_microversion,
            CONF.volume.min_microversion, CONF.volume.max_microversion)

    @classmethod
    def resource_setup(cls):
        super(VolumesV3Test, cls).resource_setup()
        cls.request_microversion = (
            api_version_utils.select_request_microversion(
                cls.min_microversion,
                CONF.volume.min_microversion))

    @classmethod
    def setup_clients(cls):
        super(VolumesV3Test, cls).setup_clients()
        cls.messages_client = cls.os.volume_v3_messages_client

    def setUp(self):
        super(VolumesV3Test, self).setUp()
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            self.request_microversion))


class VolumesV3AdminTest(VolumesV3Test,
                         base.BaseVolumeAdminTest):
    """Base test case class for all v3 Volume Admin API tests."""

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(VolumesV3AdminTest, cls).setup_clients()
        cls.admin_messages_client = cls.os_adm.volume_v3_messages_client
        cls.admin_volume_types_client = cls.os_adm.volume_types_v2_client
