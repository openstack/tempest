# Copyright 2016 IBM Corp.
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

from tempest.lib import exceptions
from tempest.lib.services.object_storage import object_client
from tempest.tests import base
from tempest.tests.lib import fake_auth_provider


class TestObjectClient(base.TestCase):

    def setUp(self):
        super(TestObjectClient, self).setUp()
        self.fake_auth = fake_auth_provider.FakeAuthProvider()
        self.url = self.fake_auth.base_url(None)
        self.object_client = object_client.ObjectClient(self.fake_auth,
                                                        'swift', 'region1')

    @mock.patch.object(object_client, '_create_connection')
    def test_create_object_continue_no_data(self, mock_poc):
        self._validate_create_object_continue(None, mock_poc)

    @mock.patch.object(object_client, '_create_connection')
    def test_create_object_continue_with_data(self, mock_poc):
        self._validate_create_object_continue('hello', mock_poc)

    @mock.patch.object(object_client, '_create_connection')
    def test_create_continue_with_no_continue_received(self, mock_poc):
        self._validate_create_object_continue('hello', mock_poc,
                                              initial_status=201)

    def _validate_create_object_continue(self, req_data,
                                         mock_poc, initial_status=100):

        expected_hdrs = {
            'X-Auth-Token': self.fake_auth.get_token(),
            'content-length': 0 if req_data is None else len(req_data),
            'Expect': '100-continue'}

        # Setup the Mocks prior to invoking the object creation
        mock_resp_cls = mock.Mock()
        mock_resp_cls._read_status.return_value = ("1", initial_status, "OK")

        mock_poc.return_value.response_class.return_value = mock_resp_cls

        # This is the final expected return value
        mock_poc.return_value.getresponse.return_value.status = 201
        mock_poc.return_value.getresponse.return_value.reason = 'OK'

        # Call method to PUT object using expect:100-continue
        cnt = "container1"
        obj = "object1"
        path = "/%s/%s" % (cnt, obj)

        # If the expected initial status is not 100, then an exception
        # should be thrown and the connection closed
        if initial_status == 100:
            status, reason = \
                self.object_client.create_object_continue(cnt, obj, req_data)
        else:
            self.assertRaises(exceptions.UnexpectedResponseCode,
                              self.object_client.create_object_continue, cnt,
                              obj, req_data)
            mock_poc.return_value.close.assert_called_once_with()

        # Verify that putrequest is called 1 time with the appropriate values
        mock_poc.return_value.putrequest.assert_called_once_with('PUT', path)

        # Verify that headers were written, including "Expect:100-continue"
        calls = []

        for header, value in expected_hdrs.items():
            calls.append(mock.call(header, value))

        mock_poc.return_value.putheader.assert_has_calls(calls, False)
        mock_poc.return_value.endheaders.assert_called_once_with()

        # The following steps are only taken if the initial status is 100
        if initial_status == 100:
            # Verify that the method returned what it was supposed to
            self.assertEqual(status, 201)

            # Verify that _safe_read was called once to remove the CRLF
            # after the 100 response
            mock_rc = mock_poc.return_value.response_class.return_value
            mock_rc._safe_read.assert_called_once_with(2)

            # Verify the actual data was written via send
            mock_poc.return_value.send.assert_called_once_with(req_data)

            # Verify that the getresponse method was called to receive
            # the final
            mock_poc.return_value.getresponse.assert_called_once_with()
