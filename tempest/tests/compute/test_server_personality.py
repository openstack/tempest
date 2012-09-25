# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from nose.plugins.attrib import attr

from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
from tempest.tests.compute import base


class ServerPersonalityTestBase(object):

    def test_personality_files_exceed_limit(self):
        """
        Server creation should fail if greater than the maximum allowed
        number of files are injected into the server.
        """
        name = rand_name('server')
        file_contents = 'This is a test file.'
        personality = []
        _, max_file_limit = self.user_client.get_personality_file_limit()
        for i in range(0, max_file_limit + 1):
            path = 'etc/test' + str(i) + '.txt'
            personality.append({'path': path,
                                'contents': base64.b64encode(file_contents)})
        try:
            self.client.create_server(name, self.image_ref, self.flavor_ref,
                                      personality=personality)
        except exceptions.OverLimit:
            pass
        else:
            self.fail('This request did not fail as expected')

    @attr(type='positive')
    def test_can_create_server_with_max_number_personality_files(self):
        """
        Server should be created successfully if maximum allowed number of
        files is injected into the server during creation.
        """
        try:
            name = rand_name('server')
            file_contents = 'This is a test file.'

            resp, max_file_limit = self.user_client.\
                    get_personality_file_limit()
            self.assertEqual(200, resp.status)

            personality = []
            for i in range(0, max_file_limit):
                path = 'etc/test' + str(i) + '.txt'
                personality.append({
                    'path': path,
                    'contents': base64.b64encode(file_contents),
                })

            resp, server = self.client.create_server(name, self.image_ref,
                                                     self.flavor_ref,
                                                     personality=personality)
            self.assertEqual('202', resp['status'])

        except Exception:
            raise Error(resp['message'])

        #Teardown
        finally:
            self.client.delete_server(server['id'])


class ServerPersonalityTestXML(base.BaseComputeTestXML,
                                ServerPersonalityTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = "xml"
        super(ServerPersonalityTestXML, cls).setUpClass()
        cls.client = cls.servers_client
        cls.user_client = cls.limits_client


class ServerPersonalityTestJSON(base.BaseComputeTestJSON,
                                ServerPersonalityTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = "json"
        super(ServerPersonalityTestJSON, cls).setUpClass()
        cls.client = cls.servers_client
        cls.user_client = cls.limits_client
