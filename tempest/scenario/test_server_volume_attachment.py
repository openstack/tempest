# Copyright 2023 Red Hat
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

from unittest import mock

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions
from tempest.scenario import manager

CONF = config.CONF


class BaseAttachmentTest(manager.ScenarioTest):
    @classmethod
    def setup_clients(cls):
        super().setup_clients()
        cls.attachments_client = cls.os_primary.attachments_client_latest
        cls.admin_volume_client = cls.os_admin.volumes_client_latest

    def _call_with_fake_service_token(self, valid_token,
                                      client, method_name, *args, **kwargs):
        """Call client method with non-service service token

        Add a service token header that can be a valid normal user token (which
        won't have the service role) or an invalid token altogether.
        """
        original_raw_request = client.raw_request

        def raw_request(url, method, headers=None, body=None, chunked=False,
                        log_req_body=None):
            token = headers['X-Auth-Token']
            if not valid_token:
                token = token[:-1] + ('a' if token[-1] != 'a' else 'b')
            headers['X-Service-Token'] = token
            return original_raw_request(url, method, headers=headers,
                                        body=body, chunked=chunked,
                                        log_req_body=log_req_body)

        client_method = getattr(client, method_name)
        with mock.patch.object(client, 'raw_request', raw_request):
            return client_method(*args, **kwargs)


class TestServerVolumeAttachmentScenario(BaseAttachmentTest):

    """Test server attachment behaviors

    This tests that volume attachments to servers may not be removed directly
    and are only allowed through the compute service (bug #2004555).
    """

    @decorators.attr(type='slow')
    @decorators.idempotent_id('be615530-f105-437a-8afe-ce998c9535d9')
    @utils.services('compute', 'volume', 'image', 'network')
    def test_server_detach_rules(self):
        """Test that various methods of detaching a volume honors the rules"""
        server = self.create_server(wait_until='SSHABLE')
        servers = self.servers_client.list_servers()['servers']
        self.assertIn(server['id'], [x['id'] for x in servers])

        volume = self.create_volume()

        volume = self.nova_volume_attach(server, volume)
        self.addCleanup(self.nova_volume_detach, server, volume)
        att_id = volume['attachments'][0]['attachment_id']

        # Test user call to detach volume is rejected
        self.assertRaises((exceptions.Forbidden, exceptions.Conflict),
                          self.volumes_client.detach_volume, volume['id'])

        # Test user call to terminate connection is rejected
        self.assertRaises((exceptions.Forbidden, exceptions.Conflict),
                          self.volumes_client.terminate_connection,
                          volume['id'], connector={})

        # Test faking of service token on call to detach, force detach,
        # terminate_connection
        for valid_token in (True, False):
            valid_exceptions = [exceptions.Forbidden, exceptions.Conflict]
            if not valid_token:
                valid_exceptions.append(exceptions.Unauthorized)
            self.assertRaises(
                tuple(valid_exceptions),
                self._call_with_fake_service_token,
                valid_token,
                self.volumes_client,
                'detach_volume',
                volume['id'])
            self.assertRaises(
                tuple(valid_exceptions),
                self._call_with_fake_service_token,
                valid_token,
                self.volumes_client,
                'terminate_connection',
                volume['id'], connector={})

        # Reset volume's status to error
        self.admin_volume_client.reset_volume_status(volume['id'],
                                                     status='error')
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'error')

        # For the cleanup, we need to reset the volume status to in-use before
        # the other cleanup steps try to detach it.
        self.addCleanup(waiters.wait_for_volume_resource_status,
                        self.volumes_client, volume['id'], 'in-use')
        self.addCleanup(self.admin_volume_client.reset_volume_status,
                        volume['id'], status='in-use')

        # Test user call to force detach volume is rejected
        self.assertRaises(
            (exceptions.Forbidden, exceptions.Conflict),
            self.admin_volume_client.force_detach_volume,
            volume['id'], connector=None,
            attachment_id=att_id)

        # Test trying to override detach with force and service token
        for valid_token in (True, False):
            valid_exceptions = [exceptions.Forbidden, exceptions.Conflict]
            if not valid_token:
                valid_exceptions.append(exceptions.Unauthorized)
            self.assertRaises(
                tuple(valid_exceptions),
                self._call_with_fake_service_token,
                valid_token,
                self.admin_volume_client,
                'force_detach_volume',
                volume['id'], connector=None, attachment_id=att_id)

        # Test user call to detach with mismatch is rejected
        volume2 = self.create_volume()
        volume2 = self.nova_volume_attach(server, volume2)
        att_id2 = volume2['attachments'][0]['attachment_id']
        self.assertRaises(
            (exceptions.Forbidden, exceptions.BadRequest),
            self.volumes_client.detach_volume,
            volume['id'], attachment_id=att_id2)


class TestServerVolumeAttachScenarioOldVersion(BaseAttachmentTest):
    volume_min_microversion = '3.27'
    volume_max_microversion = 'latest'

    @decorators.attr(type='slow')
    @decorators.idempotent_id('6f4d2144-99f4-495c-8b0b-c6a537971418')
    @utils.services('compute', 'volume', 'image', 'network')
    def test_old_versions_reject(self):
        server = self.create_server(wait_until='SSHABLE')
        servers = self.servers_client.list_servers()['servers']
        self.assertIn(server['id'], [x['id'] for x in servers])

        volume = self.create_volume()

        volume = self.nova_volume_attach(server, volume)
        self.addCleanup(self.nova_volume_detach, server, volume)
        att_id = volume['attachments'][0]['attachment_id']

        for valid_token in (True, False):
            valid_exceptions = [exceptions.Forbidden,
                                exceptions.Conflict]
            if not valid_token:
                valid_exceptions.append(exceptions.Unauthorized)
            self.assertRaises(
                tuple(valid_exceptions),
                self._call_with_fake_service_token,
                valid_token,
                self.attachments_client,
                'delete_attachment',
                att_id)

        self.assertRaises(
            (exceptions.Forbidden, exceptions.Conflict),
            self.attachments_client.delete_attachment,
            att_id)
