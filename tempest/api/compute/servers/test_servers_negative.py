# Copyright 2012 OpenStack Foundation
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

import sys

import testtools

from tempest.api.compute import base
from tempest.common import compute
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class ServersNegativeTestJSON(base.BaseV2ComputeTest):

    def setUp(self):
        super(ServersNegativeTestJSON, self).setUp()
        try:
            waiters.wait_for_server_status(self.client, self.server_id,
                                           'ACTIVE')
        except Exception:
            self.__class__.server_id = self.recreate_server(self.server_id)

    def tearDown(self):
        self.server_check_teardown()
        super(ServersNegativeTestJSON, self).tearDown()

    @classmethod
    def setup_clients(cls):
        super(ServersNegativeTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServersNegativeTestJSON, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

        server = cls.create_test_server()
        cls.client.delete_server(server['id'])
        waiters.wait_for_server_termination(cls.client, server['id'])
        cls.deleted_server_id = server['id']

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('dbbfd247-c40c-449e-8f6c-d2aa7c7da7cf')
    def test_server_name_blank(self):
        # Create a server with name parameter empty

        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          name='')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b8a7235e-5246-4a8f-a08e-b34877c6586f')
    @testtools.skipUnless(CONF.compute_feature_enabled.personality,
                          'Nova personality feature disabled')
    def test_personality_file_contents_not_encoded(self):
        # Use an unencoded file when creating a server with personality

        file_contents = 'This is a test file.'
        person = [{'path': '/etc/testfile.txt',
                   'contents': file_contents}]

        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          personality=person)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('fcba1052-0a50-4cf3-b1ac-fae241edf02f')
    def test_create_with_invalid_image(self):
        # Create a server with an unknown image

        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          image_id=-1)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('18f5227f-d155-4429-807c-ccb103887537')
    def test_create_with_invalid_flavor(self):
        # Create a server with an unknown flavor

        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          flavor=-1,)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7f70a4d1-608f-4794-9e56-cb182765972c')
    def test_invalid_access_ip_v4_address(self):
        # An access IPv4 address must match a valid address pattern

        IPv4 = '1.1.1.1.1.1'
        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server, accessIPv4=IPv4)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5226dd80-1e9c-4d8a-b5f9-b26ca4763fd0')
    def test_invalid_ip_v6_address(self):
        # An access IPv6 address must match a valid address pattern

        IPv6 = 'notvalid'

        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server, accessIPv6=IPv6)

    @decorators.idempotent_id('7ea45b3e-e770-46fa-bfcc-9daaf6d987c0')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @decorators.attr(type=['negative'])
    def test_resize_nonexistent_server(self):
        # Resize a non-existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.client.resize_server,
                          nonexistent_server, self.flavor_ref)

    @decorators.idempotent_id('ced1a1d7-2ab6-45c9-b90f-b27d87b30efd')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @decorators.attr(type=['negative'])
    def test_resize_server_with_non_existent_flavor(self):
        # Resize a server with non-existent flavor
        nonexistent_flavor = data_utils.rand_uuid()
        self.assertRaises(lib_exc.BadRequest, self.client.resize_server,
                          self.server_id, flavor_ref=nonexistent_flavor)

    @decorators.idempotent_id('45436a7d-a388-4a35-a9d8-3adc5d0d940b')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @decorators.attr(type=['negative'])
    def test_resize_server_with_null_flavor(self):
        # Resize a server with null flavor
        self.assertRaises(lib_exc.BadRequest, self.client.resize_server,
                          self.server_id, flavor_ref="")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d4c023a0-9c55-4747-9dd5-413b820143c7')
    def test_reboot_non_existent_server(self):
        # Reboot a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.reboot_server,
                          nonexistent_server, type='SOFT')

    @decorators.idempotent_id('d1417e7f-a509-41b5-a102-d5eed8613369')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @decorators.attr(type=['negative'])
    def test_pause_paused_server(self):
        # Pause a paused server.
        self.client.pause_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'PAUSED')
        self.assertRaises(lib_exc.Conflict,
                          self.client.pause_server,
                          self.server_id)
        self.client.unpause_server(self.server_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('98fa0458-1485-440f-873b-fe7f0d714930')
    def test_rebuild_deleted_server(self):
        # Rebuild a deleted server
        self.assertRaises(lib_exc.NotFound,
                          self.client.rebuild_server,
                          self.deleted_server_id, self.image_ref)

    @decorators.related_bug('1660878', status_code=409)
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('581a397d-5eab-486f-9cf9-1014bbd4c984')
    def test_reboot_deleted_server(self):
        # Reboot a deleted server
        self.assertRaises(lib_exc.NotFound, self.client.reboot_server,
                          self.deleted_server_id, type='SOFT')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d86141a7-906e-4731-b187-d64a2ea61422')
    def test_rebuild_non_existent_server(self):
        # Rebuild a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.client.rebuild_server,
                          nonexistent_server,
                          self.image_ref)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('fd57f159-68d6-4c2a-902b-03070828a87e')
    def test_create_numeric_server_name(self):
        server_name = 12345
        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          name=server_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c3e0fb12-07fc-4d76-a22e-37409887afe8')
    def test_create_server_name_length_exceeds_256(self):
        # Create a server with name length exceeding 255 characters

        server_name = 'a' * 256
        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          name=server_name)

    @decorators.attr(type=['negative'])
    @decorators.related_bug('1651064', status_code=500)
    @utils.services('volume')
    @decorators.idempotent_id('12146ac1-d7df-4928-ad25-b1f99e5286cd')
    def test_create_server_invalid_bdm_in_2nd_dict(self):
        volume = self.create_volume()
        bdm_1st = {"source_type": "image",
                   "delete_on_termination": True,
                   "boot_index": 0,
                   "uuid": self.image_ref,
                   "destination_type": "local"}
        bdm_2nd = {"source_type": "volume",
                   "uuid": volume["id"],
                   "destination_type": "invalid"}
        bdm = [bdm_1st, bdm_2nd]

        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          image_id=self.image_ref,
                          block_device_mapping_v2=bdm)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('4e72dc2d-44c5-4336-9667-f7972e95c402')
    def test_create_with_invalid_network_uuid(self):
        # Pass invalid network uuid while creating a server

        networks = [{'fixed_ip': '10.0.1.1', 'uuid': 'a-b-c-d-e-f-g-h-i-j'}]

        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          networks=networks)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7a2efc39-530c-47de-b875-2dd01c8d39bd')
    def test_create_with_non_existent_keypair(self):
        # Pass a non-existent keypair while creating a server

        key_name = data_utils.rand_name('key')
        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          key_name=key_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7fc74810-0bd2-4cd7-8244-4f33a9db865a')
    def test_create_server_metadata_exceeds_length_limit(self):
        # Pass really long metadata while creating a server

        metadata = {'a': 'b' * 260}
        self.assertRaises((lib_exc.BadRequest, lib_exc.OverLimit),
                          self.create_test_server,
                          metadata=metadata)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('aa8eed43-e2cb-4ebf-930b-da14f6a21d81')
    def test_update_name_of_non_existent_server(self):
        # Update name of a non-existent server

        nonexistent_server = data_utils.rand_uuid()
        new_name = data_utils.rand_name(
            self.__class__.__name__ + '-server') + '_updated'

        self.assertRaises(lib_exc.NotFound, self.client.update_server,
                          nonexistent_server, name=new_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('38204696-17c6-44da-9590-40f87fb5a899')
    def test_update_server_set_empty_name(self):
        # Update name of the server to an empty string

        new_name = ''

        self.assertRaises(lib_exc.BadRequest, self.client.update_server,
                          self.server_id, name=new_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5c8e244c-dada-4590-9944-749c455b431f')
    def test_update_server_name_length_exceeds_256(self):
        # Update name of server exceed the name length limit

        new_name = 'a' * 256
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_server,
                          self.server_id,
                          name=new_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('1041b4e6-514b-4855-96a5-e974b60870a3')
    def test_delete_non_existent_server(self):
        # Delete a non existent server

        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.delete_server,
                          nonexistent_server)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('75f79124-277c-45e6-a373-a1d6803f4cc4')
    def test_delete_server_pass_negative_id(self):
        # Pass an invalid string parameter to delete server

        self.assertRaises(lib_exc.NotFound, self.client.delete_server, -1)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f4d7279b-5fd2-4bf2-9ba4-ae35df0d18c5')
    def test_delete_server_pass_id_exceeding_length_limit(self):
        # Pass a server ID that exceeds length limit to delete server

        self.assertRaises(lib_exc.NotFound, self.client.delete_server,
                          sys.maxsize + 1)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c5fa6041-80cd-483b-aa6d-4e45f19d093c')
    def test_create_with_nonexistent_security_group(self):
        # Create a server with a nonexistent security group

        security_groups = [{'name': 'does_not_exist'}]
        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          security_groups=security_groups)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('3436b02f-1b1e-4f03-881e-c6a602327439')
    def test_get_non_existent_server(self):
        # Get a non existent server details
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.show_server,
                          nonexistent_server)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a31460a9-49e1-42aa-82ee-06e0bb7c2d03')
    def test_stop_non_existent_server(self):
        # Stop a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.servers_client.stop_server,
                          nonexistent_server)

    @decorators.idempotent_id('6a8dc0c6-6cd4-4c0a-9f32-413881828091')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @decorators.attr(type=['negative'])
    def test_pause_non_existent_server(self):
        # pause a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.pause_server,
                          nonexistent_server)

    @decorators.idempotent_id('705b8e3a-e8a7-477c-a19b-6868fc24ac75')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @decorators.attr(type=['negative'])
    def test_unpause_non_existent_server(self):
        # unpause a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.unpause_server,
                          nonexistent_server)

    @decorators.idempotent_id('c8e639a7-ece8-42dd-a2e0-49615917ba4f')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @decorators.attr(type=['negative'])
    def test_unpause_server_invalid_state(self):
        # unpause an active server.
        self.assertRaises(lib_exc.Conflict,
                          self.client.unpause_server,
                          self.server_id)

    @decorators.idempotent_id('d1f032d5-7b6e-48aa-b252-d5f16dd994ca')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @decorators.attr(type=['negative'])
    def test_suspend_non_existent_server(self):
        # suspend a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.suspend_server,
                          nonexistent_server)

    @decorators.idempotent_id('7f323206-05a9-4bf8-996b-dd5b2036501b')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @decorators.attr(type=['negative'])
    def test_suspend_server_invalid_state(self):
        # suspend a suspended server.
        self.client.suspend_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id,
                                       'SUSPENDED')
        self.assertRaises(lib_exc.Conflict,
                          self.client.suspend_server,
                          self.server_id)
        self.client.resume_server(self.server_id)

    @decorators.idempotent_id('221cd282-bddb-4837-a683-89c2487389b6')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @decorators.attr(type=['negative'])
    def test_resume_non_existent_server(self):
        # resume a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.resume_server,
                          nonexistent_server)

    @decorators.idempotent_id('ccb6294d-c4c9-498f-8a43-554c098bfadb')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @decorators.attr(type=['negative'])
    def test_resume_server_invalid_state(self):
        # resume an active server.
        self.assertRaises(lib_exc.Conflict,
                          self.client.resume_server,
                          self.server_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7dd919e7-413f-4198-bebb-35e2a01b13e9')
    def test_get_console_output_of_non_existent_server(self):
        # get the console output for a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.client.get_console_output,
                          nonexistent_server, length=10)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('6f47992b-5144-4250-9f8b-f00aa33950f3')
    def test_force_delete_nonexistent_server_id(self):
        # force-delete a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.client.force_delete_server,
                          nonexistent_server)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9c6d38cc-fcfb-437a-85b9-7b788af8bf01')
    def test_restore_nonexistent_server_id(self):
        # restore-delete a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.client.restore_soft_deleted_server,
                          nonexistent_server)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7fcadfab-bd6a-4753-8db7-4a51e51aade9')
    def test_restore_server_invalid_state(self):
        # we can only restore-delete a server in 'soft-delete' state
        self.assertRaises(lib_exc.Conflict,
                          self.client.restore_soft_deleted_server,
                          self.server_id)

    @decorators.idempotent_id('abca56e2-a892-48ea-b5e5-e07e69774816')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @decorators.attr(type=['negative'])
    def test_shelve_non_existent_server(self):
        # shelve a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.shelve_server,
                          nonexistent_server)

    @decorators.idempotent_id('443e4f9b-e6bf-4389-b601-3a710f15fddd')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @decorators.attr(type=['negative'])
    def test_shelve_shelved_server(self):
        # shelve a shelved server.
        compute.shelve_server(self.client, self.server_id)

        def _unshelve_server():
            server_info = self.client.show_server(self.server_id)['server']
            if 'SHELVED' in server_info['status']:
                self.client.unshelve_server(self.server_id)
        self.addOnException(_unshelve_server)

        server = self.client.show_server(self.server_id)['server']
        image_name = server['name'] + '-shelved'
        params = {'name': image_name}
        images = self.compute_images_client.list_images(**params)['images']
        self.assertEqual(1, len(images))
        self.assertEqual(image_name, images[0]['name'])

        self.assertRaises(lib_exc.Conflict,
                          self.client.shelve_server,
                          self.server_id)

        self.client.unshelve_server(self.server_id)

    @decorators.idempotent_id('23d23b37-afaf-40d7-aa5d-5726f82d8821')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @decorators.attr(type=['negative'])
    def test_unshelve_non_existent_server(self):
        # unshelve a non existent server
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.unshelve_server,
                          nonexistent_server)

    @decorators.idempotent_id('8f198ded-1cca-4228-9e65-c6b449c54880')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @decorators.attr(type=['negative'])
    def test_unshelve_server_invalid_state(self):
        # unshelve an active server.
        self.assertRaises(lib_exc.Conflict,
                          self.client.unshelve_server,
                          self.server_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('74085be3-a370-4ca2-bc51-2d0e10e0f573')
    @utils.services('volume', 'image')
    def test_create_server_from_non_bootable_volume(self):
        # Create a volume
        volume = self.create_volume()

        # Update volume bootable status to false
        self.volumes_client.set_bootable_volume(volume['id'],
                                                bootable=False)

        # Verify bootable flag was updated
        nonbootable_vol = self.volumes_client.show_volume(
            volume['id'])['volume']
        self.assertEqual('false', nonbootable_vol['bootable'])

        # Block device mapping
        bd_map = [{'boot_index': '0',
                   'uuid': volume['id'],
                   'source_type': 'volume',
                   'destination_type': 'volume',
                   'delete_on_termination': False}]

        # Try creating a server from non-bootable volume
        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          image_id='',
                          wait_until='ACTIVE',
                          block_device_mapping_v2=bd_map)


class ServersNegativeTestMultiTenantJSON(base.BaseV2ComputeTest):

    credentials = ['primary', 'alt']

    def setUp(self):
        super(ServersNegativeTestMultiTenantJSON, self).setUp()
        try:
            waiters.wait_for_server_status(self.servers_client, self.server_id,
                                           'ACTIVE')
        except Exception:
            self.__class__.server_id = self.recreate_server(self.server_id)

    @classmethod
    def setup_clients(cls):
        super(ServersNegativeTestMultiTenantJSON, cls).setup_clients()
        cls.alt_client = cls.os_alt.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServersNegativeTestMultiTenantJSON, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('543d84c1-dd2e-4c6d-8cb2-b9da0efaa384')
    def test_update_server_of_another_tenant(self):
        # Update name of a server that belongs to another tenant

        new_name = self.server_id + '_new'
        self.assertRaises(lib_exc.NotFound,
                          self.alt_client.update_server, self.server_id,
                          name=new_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5c75009d-3eea-423e-bea3-61b09fd25f9c')
    def test_delete_a_server_of_another_tenant(self):
        # Delete a server that belongs to another tenant
        self.assertRaises(lib_exc.NotFound,
                          self.alt_client.delete_server,
                          self.server_id)
