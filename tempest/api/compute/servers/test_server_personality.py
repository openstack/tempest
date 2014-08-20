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
from tempest import exceptions
from tempest import test


class ServerPersonalityTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setUpClass(cls):
        super(ServerPersonalityTestJSON, cls).setUpClass()
        cls.client = cls.servers_client
        cls.user_client = cls.limits_client

    @test.attr(type='gate')
    def test_personality_files_exceed_limit(self):
        # Server creation should fail if greater than the maximum allowed
        # number of files are injected into the server.
        file_contents = 'This is a test file.'
        personality = []
        max_file_limit = \
            self.user_client.get_specific_absolute_limit("maxPersonality")
        for i in range(0, int(max_file_limit) + 1):
            path = 'etc/test' + str(i) + '.txt'
            personality.append({'path': path,
                                'contents': base64.b64encode(file_contents)})
        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised when out of quota
        self.assertRaises((exceptions.Unauthorized, exceptions.OverLimit),
                          self.create_test_server, personality=personality)

    @test.attr(type='gate')
    def test_can_create_server_with_max_number_personality_files(self):
        # Server should be created successfully if maximum allowed number of
        # files is injected into the server during creation.
        file_contents = 'This is a test file.'
        max_file_limit = \
            self.user_client.get_specific_absolute_limit("maxPersonality")
        person = []
        for i in range(0, int(max_file_limit)):
            path = 'etc/test' + str(i) + '.txt'
            person.append({
                'path': path,
                'contents': base64.b64encode(file_contents),
            })
        resp, server = self.create_test_server(personality=person)
        self.assertEqual('202', resp['status'])

    @test.attr(type='gate')
    def test_can_create_server_with_a_personality_file(self):
        # The file 'test.txt' should be established when the server created
        file_contents = 'This is a test file.'
        person = []
        path = 'etc/test.txt'
        person.append({
            'path': path,
            'contents': base64.b64encode(file_contents),
        })
        resp, server = self.create_test_server(personality=person,
                                               wait_until='ACTIVE',
                                               min_count=1,
                                               max_count=1)
        self.assertEqual('202', resp['status'])

class ServerPersonalityTestXML(ServerPersonalityTestJSON):
    _interface = "xml"
