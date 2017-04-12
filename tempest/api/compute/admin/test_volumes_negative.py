# Copyright 2016 NEC Corporation.  All rights reserved.
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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class VolumesAdminNegativeTest(base.BaseV2ComputeAdminTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesAdminNegativeTest, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def resource_setup(cls):
        super(VolumesAdminNegativeTest, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until='ACTIVE')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('309b5ecd-0585-4a7e-a36f-d2b2bf55259d')
    def test_update_attached_volume_with_nonexistent_volume_in_uri(self):
        volume = self.create_volume()
        nonexistent_volume = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.admin_servers_client.update_attached_volume,
                          self.server['id'], nonexistent_volume,
                          volumeId=volume['id'])

    @decorators.related_bug('1629110', status_code=400)
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7dcac15a-b107-46d3-a5f6-cb863f4e454a')
    def test_update_attached_volume_with_nonexistent_volume_in_body(self):
        volume = self.create_volume()
        self.attach_volume(self.server, volume)

        nonexistent_volume = data_utils.rand_uuid()
        self.assertRaises(lib_exc.BadRequest,
                          self.admin_servers_client.update_attached_volume,
                          self.server['id'], volume['id'],
                          volumeId=nonexistent_volume)
