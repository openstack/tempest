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
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class ServerPersonalityTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(ServerPersonalityTestJSON, cls).setup_clients()
        cls.client = cls.servers_client
        cls.user_client = cls.limits_client

    @test.attr(type='gate')
    @test.idempotent_id('176cd8c9-b9e8-48ee-a480-180beab292bf')
    def test_personality_files_exceed_limit(self):
        # Server creation should fail if greater than the maximum allowed
        # number of files are injected into the server.
        file_contents = 'This is a test file.'
        personality = []
        max_file_limit = \
            self.user_client.get_specific_absolute_limit("maxPersonality")
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

    @test.attr(type='gate')
    @test.idempotent_id('52f12ee8-5180-40cc-b417-31572ea3d555')
    def test_can_create_server_with_max_number_personality_files(self):
        # Server should be created successfully if maximum allowed number of
        # files is injected into the server during creation.
        file_contents = 'This is a test file.'
        max_file_limit = \
            self.user_client.get_specific_absolute_limit("maxPersonality")
        if max_file_limit == -1:
            raise self.skipException("No limit for personality files")
        person = []
        for i in range(0, int(max_file_limit)):
            path = 'etc/test' + str(i) + '.txt'
            person.append({
                'path': path,
                'contents': base64.b64encode(file_contents),
            })
        self.create_test_server(personality=person)
