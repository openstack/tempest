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

from oslo_serialization import base64

from tempest.api.compute import base
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class ServerPersonalityTestJSON(base.BaseV2ComputeTest):
    """Test servers with injected files"""
    max_microversion = '2.56'

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServerPersonalityTestJSON, cls).setup_credentials()

    @classmethod
    def skip_checks(cls):
        super(ServerPersonalityTestJSON, cls).skip_checks()
        if not CONF.compute_feature_enabled.personality:
            raise cls.skipException("Nova personality feature disabled")

    @classmethod
    def setup_clients(cls):
        super(ServerPersonalityTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    # NOTE(mriedem): Marked as slow because personality (file injection) is
    # deprecated in nova so we don't care as much about running this all the
    # time (and it's slow).
    @decorators.attr(type='slow')
    @decorators.idempotent_id('3cfe87fd-115b-4a02-b942-7dc36a337fdf')
    def test_create_server_with_personality(self):
        """Test creating server with file injection"""
        file_contents = 'This is a test file.'
        file_path = '/test.txt'
        personality = [{'path': file_path,
                        'contents': base64.encode_as_text(file_contents)}]
        password = data_utils.rand_password()
        validation_resources = self.get_test_validation_resources(
            self.os_primary)
        created_server = self.create_test_server(
            personality=personality, adminPass=password, wait_until='ACTIVE',
            validatable=True,
            validation_resources=validation_resources)
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, created_server['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.servers_client.delete_server,
                        created_server['id'])
        server = self.client.show_server(created_server['id'])['server']
        if CONF.validation.run_validation:
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server, validation_resources),
                self.ssh_user, password,
                validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.client)
            self.assertEqual(file_contents,
                             linux_client.exec_command(
                                 'sudo cat %s' % file_path))

    # NOTE(mriedem): Marked as slow because personality (file injection) is
    # deprecated in nova so we don't care as much about running this all the
    # time (and it's slow).
    @decorators.attr(type='slow')
    @decorators.idempotent_id('128966d8-71fc-443c-8cab-08e24114ecc9')
    def test_rebuild_server_with_personality(self):
        """Test injecting file when rebuilding server"""
        validation_resources = self.get_test_validation_resources(
            self.os_primary)
        server = self.create_test_server(
            wait_until='ACTIVE', validatable=True,
            validation_resources=validation_resources)
        server_id = server['id']
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, server_id)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.servers_client.delete_server, server_id)
        file_contents = 'Test server rebuild.'
        personality = [{'path': 'rebuild.txt',
                        'contents': base64.encode_as_text(file_contents)}]
        rebuilt_server = self.client.rebuild_server(server_id,
                                                    self.image_ref_alt,
                                                    personality=personality)
        waiters.wait_for_server_status(self.client, server_id, 'ACTIVE')
        self.assertEqual(self.image_ref_alt,
                         rebuilt_server['server']['image']['id'])

    @decorators.idempotent_id('176cd8c9-b9e8-48ee-a480-180beab292bf')
    def test_personality_files_exceed_limit(self):
        """Test creating server with injected files over limitation

        Server creation should fail if greater than the maximum allowed
        number of files are injected into the server.
        """
        file_contents = 'This is a test file.'
        personality = []
        limits = self.limits_client.show_limits()['limits']
        max_file_limit = limits['absolute']['maxPersonality']
        if max_file_limit == -1:
            raise self.skipException("No limit for personality files")
        for i in range(0, max_file_limit + 1):
            path = 'etc/test' + str(i) + '.txt'
            personality.append({'path': path,
                                'contents': base64.encode_as_text(
                                    file_contents)})
        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised when out of quota
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.create_test_server, personality=personality)

    # NOTE(mriedem): Marked as slow because personality (file injection) is
    # deprecated in nova so we don't care as much about running this all the
    # time (and it's slow).
    @decorators.attr(type='slow')
    @decorators.idempotent_id('52f12ee8-5180-40cc-b417-31572ea3d555')
    def test_can_create_server_with_max_number_personality_files(self):
        """Test creating server with maximum allowed number of injected files

        Server should be created successfully if maximum allowed number of
        files is injected into the server during creation.
        """
        file_contents = 'This is a test file.'
        limits = self.limits_client.show_limits()['limits']
        max_file_limit = limits['absolute']['maxPersonality']
        if max_file_limit == -1:
            raise self.skipException("No limit for personality files")
        person = []
        for i in range(0, max_file_limit):
            # NOTE(andreaf) The cirros disk image is blank before boot
            # so we can only inject safely to /
            path = '/test' + str(i) + '.txt'
            person.append({
                'path': path,
                'contents': base64.encode_as_text(file_contents + str(i)),
            })
        password = data_utils.rand_password()
        validation_resources = self.get_test_validation_resources(
            self.os_primary)
        created_server = self.create_test_server(
            personality=person, adminPass=password, wait_until='ACTIVE',
            validatable=True, validation_resources=validation_resources)
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, created_server['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.servers_client.delete_server,
                        created_server['id'])
        server = self.client.show_server(created_server['id'])['server']
        if CONF.validation.run_validation:
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server, validation_resources),
                self.ssh_user, password,
                validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.client)
            for i in person:
                self.assertEqual(base64.decode_as_text(i['contents']),
                                 linux_client.exec_command(
                                     'sudo cat %s' % i['path']))
