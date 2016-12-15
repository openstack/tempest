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
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF


class AttachVolumeNegativeTest(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(AttachVolumeNegativeTest, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @test.related_bug('1630783', status_code=500)
    @test.idempotent_id('a313b5cd-fbd0-49cc-94de-870e99f763c7')
    def test_delete_attached_volume(self):
        server = self.create_test_server(wait_until='ACTIVE')
        volume = self.create_volume()

        path = "/dev/%s" % CONF.compute.volume_device_name
        self.attach_volume(server, volume, device=path)

        self.assertRaises(lib_exc.BadRequest,
                          self.delete_volume, volume['id'])
