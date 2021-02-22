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
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class VolumeMultiBackendTest(base.BaseVolumeAdminTest):
    """Test volume multi backends"""

    @classmethod
    def skip_checks(cls):
        super(VolumeMultiBackendTest, cls).skip_checks()

        if not CONF.volume_feature_enabled.multi_backend:
            raise cls.skipException("Cinder multi-backend feature disabled")

        if len(set(CONF.volume.backend_names)) < 2:
            raise cls.skipException("Requires at least two different "
                                    "backend names")

    @classmethod
    def resource_setup(cls):
        super(VolumeMultiBackendTest, cls).resource_setup()

        # read backend name from a list .
        backend_names = set(CONF.volume.backend_names)

        cls.volume_id_list_with_prefix = []
        cls.volume_id_list_without_prefix = []

        # Volume/Type creation (uses volume_backend_name)
        # It is not allowed to create the same backend name twice
        for backend_name in backend_names:
            # Volume/Type creation (uses backend_name)
            cls._create_type_and_volume(backend_name, False)
            # Volume/Type creation (uses capabilities:volume_backend_name)
            cls._create_type_and_volume(backend_name, True)

    @classmethod
    def _create_type_and_volume(cls, backend_name_key, with_prefix):
        # Volume/Type creation
        type_name = data_utils.rand_name(cls.__name__ + '-Type')
        vol_name = data_utils.rand_name(cls.__name__ + '-Volume')
        spec_key_with_prefix = "capabilities:volume_backend_name"
        spec_key_without_prefix = "volume_backend_name"
        if with_prefix:
            extra_specs = {spec_key_with_prefix: backend_name_key}
        else:
            extra_specs = {spec_key_without_prefix: backend_name_key}
        cls.create_volume_type(name=type_name,
                               extra_specs=extra_specs)

        params = {'name': vol_name, 'volume_type': type_name,
                  'size': CONF.volume.volume_size}
        cls.volume = cls.create_volume(**params)
        if with_prefix:
            cls.volume_id_list_with_prefix.append(cls.volume['id'])
        else:
            cls.volume_id_list_without_prefix.append(
                cls.volume['id'])
        waiters.wait_for_volume_resource_status(cls.admin_volume_client,
                                                cls.volume['id'], 'available')

    @decorators.idempotent_id('c1a41f3f-9dad-493e-9f09-3ff197d477cc')
    def test_backend_name_reporting(self):
        """Test backend name reporting for volume when type is without prefix

        1. Create volume type, with 'volume_backend_name' as extra spec key
        2. Create volume using the created volume type
        3. Check 'os-vol-host-attr:host' of the volume info, the value should
           contain '@' character, like 'cinder@CloveStorage#tecs_backend'
        """
        for volume_id in self.volume_id_list_without_prefix:
            self._test_backend_name_reporting_by_volume_id(volume_id)

    @decorators.idempotent_id('f38e647f-ab42-4a31-a2e7-ca86a6485215')
    def test_backend_name_reporting_with_prefix(self):
        """Test backend name reporting for volume when type is with prefix

        1. Create volume type, with 'capabilities:volume_backend_name' as
           extra spec key
        2. Create volume using the created volume type
        3. Check 'os-vol-host-attr:host' of the volume info, the value should
           contain '@' character, like 'cinder@CloveStorage#tecs_backend'
        """
        for volume_id in self.volume_id_list_with_prefix:
            self._test_backend_name_reporting_by_volume_id(volume_id)

    @decorators.idempotent_id('46435ab1-a0af-4401-8373-f14e66b0dd58')
    def test_backend_name_distinction(self):
        """Test volume backend distinction when type is without prefix

        1. For each backend, create volume type with 'volume_backend_name'
           as extra spec key
        2. Create volumes using the created volume types
        3. Check 'os-vol-host-attr:host' of each created volume is different.
        """
        self._test_backend_name_distinction(self.volume_id_list_without_prefix)

    @decorators.idempotent_id('4236305b-b65a-4bfc-a9d2-69cb5b2bf2ed')
    def test_backend_name_distinction_with_prefix(self):
        """Test volume backend distinction when type is with prefix

        1. For each backend, create volume type with
           'capabilities:volume_backend_name' as extra spec key
        2. Create volumes using the created volume types
        3. Check 'os-vol-host-attr:host' of each created volume is different.
        """
        self._test_backend_name_distinction(self.volume_id_list_with_prefix)

    def _get_volume_host(self, volume_id):
        return self.admin_volume_client.show_volume(
            volume_id)['volume']['os-vol-host-attr:host']

    def _test_backend_name_reporting_by_volume_id(self, volume_id):
        # this test checks if os-vol-attr:host is populated correctly after
        # the multi backend feature has been enabled
        # if multi-backend is enabled: os-vol-attr:host should be like:
        # host@backend_name
        volume = self.admin_volume_client.show_volume(volume_id)['volume']

        volume1_host = volume['os-vol-host-attr:host']
        msg = ("multi-backend reporting incorrect values for volume %s" %
               volume_id)
        self.assertGreater(len(volume1_host.split("@")), 1, msg)

    def _test_backend_name_distinction(self, volume_id_list):
        # this test checks that the volumes created at setUp don't
        # belong to the same backend (if they are, than the
        # volume backend distinction is not working properly)
        volume_hosts = [self._get_volume_host(volume) for volume in
                        volume_id_list]
        # assert that volumes are each created on separate hosts:
        msg = ("volumes %s were created in the same backend" % ", "
               .join(volume_hosts))
        self.assertCountEqual(volume_hosts, set(volume_hosts), msg)
