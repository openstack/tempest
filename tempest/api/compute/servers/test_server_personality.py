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

import base64

from tempest.api.compute import base
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF


class ServerPersonalityTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServerPersonalityTestJSON, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        cls.set_validation_resources()
        super(ServerPersonalityTestJSON, cls).resource_setup()

    @classmethod
    def skip_checks(cls):
        super(ServerPersonalityTestJSON, cls).skip_checks()
        if not CONF.compute_feature_enabled.personality:
            raise cls.skipException("Nova personality feature disabled")

    @classmethod
    def setup_clients(cls):
        super(ServerPersonalityTestJSON, cls).setup_clients()
        cls.client = cls.servers_client
        cls.user_client = cls.limits_client

    @test.idempotent_id('3cfe87fd-115b-4a02-b942-7dc36a337fdf')
    def test_create_server_with_personality(self):
        file_contents = 'This is a test file.'
        file_path = '/test.txt'
        personality = [{'path': file_path,
                        'contents': base64.b64encode(file_contents)}]
        password = data_utils.rand_password()
        created_server = self.create_test_server(personality=personality,
                                                 adminPass=password,
                                                 wait_until='ACTIVE',
                                                 validatable=True)
        server = self.client.show_server(created_server['id'])['server']
        if CONF.validation.run_validation:
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server),
                self.ssh_user, password,
                self.validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.client)
            self.assertEqual(file_contents,
                             linux_client.exec_command(
                                 'sudo cat %s' % file_path))

    @test.idempotent_id('128966d8-71fc-443c-8cab-08e24114ecc9')
    def test_rebuild_server_with_personality(self):
        server = self.create_test_server(wait_until='ACTIVE', validatable=True)
        server_id = server['id']
        file_contents = 'Test server rebuild.'
        personality = [{'path': 'rebuild.txt',
                        'contents': base64.b64encode(file_contents)}]
        rebuilt_server = self.client.rebuild_server(server_id,
                                                    self.image_ref_alt,
                                                    personality=personality)
        waiters.wait_for_server_status(self.client, server_id, 'ACTIVE')
        self.assertEqual(self.image_ref_alt,
                         rebuilt_server['server']['image']['id'])

    @test.idempotent_id('176cd8c9-b9e8-48ee-a480-180beab292bf')
    def test_personality_files_exceed_limit(self):
        # Server creation should fail if greater than the maximum allowed
        # number of files are injected into the server.
        file_contents = 'This is a test file.'
        personality = []
        limits = self.user_client.show_limits()['limits']
        max_file_limit = limits['absolute']['maxPersonality']
        if max_file_limit == -1:
            raise self.skipException("No limit for personality files")
        for i in range(0, int(max_file_limit) + 1):
            path = 'etc/test' + str(i) + '.txt'
            personality.append({'path': path,
                                'contents': base64.b64encode(file_contents)})
        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised when out of quota
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.create_test_server, personality=personality)

    @test.idempotent_id('52f12ee8-5180-40cc-b417-31572ea3d555')
    def test_can_create_server_with_max_number_personality_files(self):
        # Server should be created successfully if maximum allowed number of
        # files is injected into the server during creation.
        file_contents = 'This is a test file.'
        limits = self.user_client.show_limits()['limits']
        max_file_limit = limits['absolute']['maxPersonality']
        if max_file_limit == -1:
            raise self.skipException("No limit for personality files")
        person = []
        for i in range(0, int(max_file_limit)):
            path = '/etc/test' + str(i) + '.txt'
            person.append({
                'path': path,
                'contents': base64.b64encode(file_contents),
            })
        password = data_utils.rand_password()
        created_server = self.create_test_server(personality=person,
                                                 adminPass=password,
                                                 wait_until='ACTIVE',
                                                 validatable=True)
        server = self.client.show_server(created_server['id'])['server']
        if CONF.validation.run_validation:
            linux_client = remote_client.RemoteClient(
                self.get_server_ip(server),
                self.ssh_user, password,
                self.validation_resources['keypair']['private_key'],
                server=server,
                servers_client=self.client)
            for i in person:
                self.assertEqual(base64.b64decode(i['contents']),
                                 linux_client.exec_command(
                                     'sudo cat %s' % i['path']))
