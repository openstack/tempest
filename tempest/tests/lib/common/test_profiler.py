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

import testtools

from tempest.lib.common import profiler


class TestProfiler(testtools.TestCase):

    def test_serialize(self):
        key = 'SECRET_KEY'
        pm = {'key': key, 'uuid': 'ID'}

        with mock.patch('tempest.lib.common.profiler._profiler', pm):
            with mock.patch('json.dumps') as jdm:
                jdm.return_value = '{"base_id": "ID", "parent_id": "ID"}'

                expected = {
                    'X-Trace-HMAC':
                        '887292df9f13b8b5ecd6bbbd2e16bfaaa4d914b0',
                    'X-Trace-Info':
                        b'eyJiYXNlX2lkIjogIklEIiwgInBhcmVudF9pZCI6ICJJRCJ9'
                }

                self.assertEqual(expected,
                                 profiler.serialize_as_http_headers())

    def test_profiler_lifecycle(self):
        key = 'SECRET_KEY'
        uuid = 'ID'

        self.assertEqual({}, profiler._profiler)

        profiler.enable(key, uuid)
        self.assertEqual({'key': key, 'uuid': uuid}, profiler._profiler)

        profiler.disable()
        self.assertEqual({}, profiler._profiler)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    def test_profiler_lifecycle_generate_trace_id(self, generate_uuid_mock):
        key = 'SECRET_KEY'
        uuid = 'ID'
        generate_uuid_mock.return_value = uuid

        self.assertEqual({}, profiler._profiler)

        profiler.enable(key)
        self.assertEqual({'key': key, 'uuid': uuid}, profiler._profiler)

        profiler.disable()
        self.assertEqual({}, profiler._profiler)
