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

import testtools

from tempest.api.volume import base
from tempest.api.volume import test_volumes_extend as extend
from tempest.common import utils
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class EncryptedVolumesExtendAttachedTest(extend.BaseVolumesExtendAttachedTest,
                                         base.BaseVolumeAdminTest):
    """Tests extending the size of an attached encrypted volume."""

    @decorators.idempotent_id('e93243ec-7c37-4b5b-a099-ebf052c13216')
    @testtools.skipUnless(
        CONF.volume_feature_enabled.extend_attached_encrypted_volume,
        "Attached encrypted volume extend is disabled.")
    @utils.services('compute')
    def test_extend_attached_encrypted_volume_luksv1(self):
        volume = self.create_encrypted_volume(encryption_provider="luks")
        self._test_extend_attached_volume(volume)
