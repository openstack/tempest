# Copyright 2016 Rackspace
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import subprocess
import tempfile

from tempest.cmd import subunit_describe_calls
from tempest.tests import base


class TestSubunitDescribeCalls(base.TestCase):
    def test_return_code(self):
        subunit_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'sample_streams/calls.subunit')
        p = subprocess.Popen([
            'subunit-describe-calls', '-s', subunit_file,
            '-o', tempfile.mkstemp()[1]], stdin=subprocess.PIPE)
        p.communicate()
        self.assertEqual(0, p.returncode)

    def test_verbose(self):
        subunit_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'sample_streams/calls.subunit')
        p = subprocess.Popen([
            'subunit-describe-calls', '-s', subunit_file,
            '-v'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout = p.communicate()
        self.assertEqual(0, p.returncode)
        self.assertIn(b'- request headers:', stdout[0])
        self.assertIn(b'- request body:', stdout[0])
        self.assertIn(b'- response headers:', stdout[0])
        self.assertIn(b'- response body:', stdout[0])

    def test_return_code_no_output(self):
        subunit_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'sample_streams/calls.subunit')
        p = subprocess.Popen([
            'subunit-describe-calls', '-s', subunit_file],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout = p.communicate()
        self.assertEqual(0, p.returncode)
        self.assertIn(b'foo', stdout[0])
        self.assertIn(b'- 200 POST request for Nova to v2.1/<id>/',
                      stdout[0])
        self.assertIn(b'- 200 DELETE request for Nova to v2.1/<id>/',
                      stdout[0])
        self.assertIn(b'- 200 GET request for Nova to v2.1/<id>/',
                      stdout[0])
        self.assertIn(b'- 404 DELETE request for Nova to v2.1/<id>/',
                      stdout[0])
        self.assertNotIn(b'- request headers:', stdout[0])
        self.assertNotIn(b'- request body:', stdout[0])
        self.assertNotIn(b'- response headers:', stdout[0])
        self.assertNotIn(b'- response body:', stdout[0])

    def test_parse(self):
        subunit_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'sample_streams/calls.subunit')
        parser = subunit_describe_calls.parse(
            open(subunit_file), "pythonlogging", None)
        expected_result = {
            'bar': [{
                'name': 'AgentsAdminTestJSON:setUp',
                'request_body': '{"agent": {"url": "xxx://xxxx/xxx/xxx", '
                '"hypervisor": "common", "md5hash": '
                '"add6bb58e139be103324d04d82d8f545", "version": "7.0", '
                '"architecture": "tempest-x86_64-424013832", "os": "linux"}}',
                'request_headers': "{'Content-Type': 'application/json', "
                "'Accept': 'application/json', 'X-Auth-Token': '<omitted>'}",
                'response_body': '{"agent": {"url": "xxx://xxxx/xxx/xxx", '
                '"hypervisor": "common", "md5hash": '
                '"add6bb58e139be103324d04d82d8f545", "version": "7.0", '
                '"architecture": "tempest-x86_64-424013832", "os": "linux", '
                '"agent_id": 1}}',
                'response_headers': "{'status': '200', 'content-length': "
                "'203', 'x-compute-request-id': "
                "'req-25ddaae2-0ef1-40d1-8228-59bd64a7e75b', 'vary': "
                "'X-OpenStack-Nova-API-Version', 'connection': 'close', "
                "'x-openstack-nova-api-version': '2.1', 'date': "
                "'Tue, 02 Feb 2016 03:27:00 GMT', 'content-type': "
                "'application/json'}",
                'service': 'Nova',
                'status_code': '200',
                'url': 'v2.1/<id>/os-agents',
                'verb': 'POST'}, {
                'name': 'AgentsAdminTestJSON:test_create_agent',
                'request_body': '{"agent": {"url": "xxx://xxxx/xxx/xxx", '
                '"hypervisor": "kvm", "md5hash": '
                '"add6bb58e139be103324d04d82d8f545", "version": "7.0", '
                '"architecture": "tempest-x86-252246646", "os": "win"}}',
                'request_headers': "{'Content-Type': 'application/json', "
                "'Accept': 'application/json', 'X-Auth-Token': '<omitted>'}",
                'response_body': '{"agent": {"url": "xxx://xxxx/xxx/xxx", '
                '"hypervisor": "kvm", "md5hash": '
                '"add6bb58e139be103324d04d82d8f545", "version": "7.0", '
                '"architecture": "tempest-x86-252246646", "os": "win", '
                '"agent_id": 2}}',
                'response_headers': "{'status': '200', 'content-length': "
                "'195', 'x-compute-request-id': "
                "'req-b4136f06-c015-4e7e-995f-c43831e3ecce', 'vary': "
                "'X-OpenStack-Nova-API-Version', 'connection': 'close', "
                "'x-openstack-nova-api-version': '2.1', 'date': "
                "'Tue, 02 Feb 2016 03:27:00 GMT', 'content-type': "
                "'application/json'}",
                'service': 'Nova',
                'status_code': '200',
                'url': 'v2.1/<id>/os-agents',
                'verb': 'POST'}, {
                'name': 'AgentsAdminTestJSON:tearDown',
                'request_body': 'None',
                'request_headers': "{'Content-Type': 'application/json', "
                "'Accept': 'application/json', 'X-Auth-Token': '<omitted>'}",
                'response_body': '',
                'response_headers': "{'status': '200', 'content-length': "
                "'0', 'x-compute-request-id': "
                "'req-ee905fd6-a5b5-4da4-8c37-5363cb25bd9d', 'vary': "
                "'X-OpenStack-Nova-API-Version', 'connection': 'close', "
                "'x-openstack-nova-api-version': '2.1', 'date': "
                "'Tue, 02 Feb 2016 03:27:00 GMT', 'content-type': "
                "'application/json'}",
                'service': 'Nova',
                'status_code': '200',
                'url': 'v2.1/<id>/os-agents/1',
                'verb': 'DELETE'}, {
                'name': 'AgentsAdminTestJSON:_run_cleanups',
                'request_body': 'None',
                'request_headers': "{'Content-Type': 'application/json', "
                "'Accept': 'application/json', 'X-Auth-Token': '<omitted>'}",
                'response_headers': "{'status': '200', 'content-length': "
                "'0', 'x-compute-request-id': "
                "'req-e912cac0-63e0-4679-a68a-b6d18ddca074', 'vary': "
                "'X-OpenStack-Nova-API-Version', 'connection': 'close', "
                "'x-openstack-nova-api-version': '2.1', 'date': "
                "'Tue, 02 Feb 2016 03:27:00 GMT', 'content-type': "
                "'application/json'}",
                'service': 'Nova',
                'status_code': '200',
                'url': 'v2.1/<id>/os-agents/2',
                'verb': 'DELETE'}],
            'foo': [{
                'name': 'AgentsAdminTestJSON:setUp',
                'request_body': '{"agent": {"url": "xxx://xxxx/xxx/xxx", '
                '"hypervisor": "common", "md5hash": '
                '"add6bb58e139be103324d04d82d8f545", "version": "7.0", '
                '"architecture": "tempest-x86_64-948635295", "os": "linux"}}',
                'request_headers': "{'Content-Type': 'application/json', "
                "'Accept': 'application/json', 'X-Auth-Token': '<omitted>'}",
                'response_body': '{"agent": {"url": "xxx://xxxx/xxx/xxx", '
                '"hypervisor": "common", "md5hash": '
                '"add6bb58e139be103324d04d82d8f545", "version": "7.0", '
                '"architecture": "tempest-x86_64-948635295", "os": "linux", '
                '"agent_id": 3}}',
                'response_headers': "{'status': '200', 'content-length': "
                "'203', 'x-compute-request-id': "
                "'req-ccd2116d-04b1-4ffe-ae32-fb623f68bf1c', 'vary': "
                "'X-OpenStack-Nova-API-Version', 'connection': 'close', "
                "'x-openstack-nova-api-version': '2.1', 'date': "
                "'Tue, 02 Feb 2016 03:27:01 GMT', 'content-type': "
                "'application/json'}",
                'service': 'Nova',
                'status_code': '200',
                'url': 'v2.1/<id>/os-agents',
                'verb': 'POST'}, {
                'name': 'AgentsAdminTestJSON:test_delete_agent',
                'request_body': 'None',
                'request_headers': "{'Content-Type': 'application/json', "
                "'Accept': 'application/json', 'X-Auth-Token': '<omitted>'}",
                'response_body': '',
                'response_headers': "{'status': '200', 'content-length': "
                "'0', 'x-compute-request-id': "
                "'req-6e7fa28f-ae61-4388-9a78-947c58bc0588', 'vary': "
                "'X-OpenStack-Nova-API-Version', 'connection': 'close', "
                "'x-openstack-nova-api-version': '2.1', 'date': "
                "'Tue, 02 Feb 2016 03:27:01 GMT', 'content-type': "
                "'application/json'}",
                'service': 'Nova',
                'status_code': '200',
                'url': 'v2.1/<id>/os-agents/3',
                'verb': 'DELETE'}, {
                'name': 'AgentsAdminTestJSON:test_delete_agent',
                'request_body': 'None',
                'request_headers': "{'Content-Type': 'application/json', "
                "'Accept': 'application/json', 'X-Auth-Token': '<omitted>'}",
                'response_body': '{"agents": []}',
                'response_headers': "{'status': '200', 'content-length': "
                "'14', 'content-location': "
                "'http://23.253.76.97:8774/v2.1/"
                "cf6b1933fe5b476fbbabb876f6d1b924/os-agents', "
                "'x-compute-request-id': "
                "'req-e41aa9b4-41a6-4138-ae04-220b768eb644', 'vary': "
                "'X-OpenStack-Nova-API-Version', 'connection': 'close', "
                "'x-openstack-nova-api-version': '2.1', 'date': "
                "'Tue, 02 Feb 2016 03:27:01 GMT', 'content-type': "
                "'application/json'}",
                'service': 'Nova',
                'status_code': '200',
                'url': 'v2.1/<id>/os-agents',
                'verb': 'GET'}, {
                'name': 'AgentsAdminTestJSON:tearDown',
                'request_body': 'None',
                'request_headers': "{'Content-Type': 'application/json', "
                "'Accept': 'application/json', 'X-Auth-Token': '<omitted>'}",
                'response_headers': "{'status': '404', 'content-length': "
                "'82', 'x-compute-request-id': "
                "'req-e297aeea-91cf-4f26-b49c-8f46b1b7a926', 'vary': "
                "'X-OpenStack-Nova-API-Version', 'connection': 'close', "
                "'x-openstack-nova-api-version': '2.1', 'date': "
                "'Tue, 02 Feb 2016 03:27:02 GMT', 'content-type': "
                "'application/json; charset=UTF-8'}",
                'service': 'Nova',
                'status_code': '404',
                'url': 'v2.1/<id>/os-agents/3',
                'verb': 'DELETE'}]}

        self.assertEqual(expected_result, parser.test_logs)
