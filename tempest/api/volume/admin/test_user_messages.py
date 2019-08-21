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

from tempest.api.volume import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class UserMessagesTest(base.BaseVolumeAdminTest):
    _api_version = 3
    min_microversion = '3.3'
    max_microversion = 'latest'

    def _create_user_message(self):
        """Trigger a 'no valid host' situation to generate a message."""
        bad_protocol = data_utils.rand_name('storage_protocol')
        bad_vendor = data_utils.rand_name('vendor_name')
        extra_specs = {'storage_protocol': bad_protocol,
                       'vendor_name': bad_vendor}
        vol_type_name = data_utils.rand_name(
            self.__class__.__name__ + '-volume-type')
        bogus_type = self.create_volume_type(
            name=vol_type_name, extra_specs=extra_specs)
        params = {'volume_type': bogus_type['id'],
                  'size': CONF.volume.volume_size}
        volume = self.create_volume(wait_until="error", **params)
        messages = self.messages_client.list_messages()['messages']
        message_id = None
        for message in messages:
            if message['resource_uuid'] == volume['id']:
                message_id = message['id']
                break
        self.assertIsNotNone(message_id, 'No user message generated for '
                                         'volume %s' % volume['id'])
        return message_id

    @decorators.idempotent_id('50f29e6e-f363-42e1-8ad1-f67ae7fd4d5a')
    def test_list_show_messages(self):
        message_id = self._create_user_message()
        self.addCleanup(self.messages_client.delete_message, message_id)

        # show message, check response schema
        self.messages_client.show_message(message_id)

        # list messages, check response schema
        self.messages_client.list_messages()

    @decorators.idempotent_id('c6eb6901-cdcc-490f-b735-4fe251842aed')
    def test_delete_message(self):
        message_id = self._create_user_message()
        self.messages_client.delete_message(message_id)
        self.messages_client.wait_for_resource_deletion(message_id)
