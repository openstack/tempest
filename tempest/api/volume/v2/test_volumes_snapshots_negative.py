# Copyright 2017 Red Hat, Inc.
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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF


class VolumesSnapshotNegativeTest(base.BaseVolumeTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesSnapshotNegativeTest, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    @test.attr(type=['negative'])
    @decorators.idempotent_id('27b5f37f-bf69-4e8c-986e-c44f3d6819b8')
    def test_list_snapshots_invalid_param_sort(self):
        self.assertRaises(lib_exc.BadRequest,
                          self.snapshots_client.list_snapshots,
                          sort_key='invalid')

    @test.attr(type=['negative'])
    @decorators.idempotent_id('b68deeda-ca79-4a32-81af-5c51179e553a')
    def test_list_snapshots_invalid_param_marker(self):
        self.assertRaises(lib_exc.NotFound,
                          self.snapshots_client.list_snapshots,
                          marker=data_utils.rand_uuid())
