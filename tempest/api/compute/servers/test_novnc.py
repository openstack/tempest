# Copyright 2016-2017 OpenStack Foundation
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

import struct

import six
import six.moves.urllib.parse as urlparse
import urllib3

from tempest.api.compute import base
from tempest.common import compute
from tempest import config
from tempest.lib import decorators

CONF = config.CONF

if six.PY2:
    ord_func = ord
else:
    ord_func = int


class NoVNCConsoleTestJSON(base.BaseV2ComputeTest):
    """Test novnc console"""

    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(NoVNCConsoleTestJSON, cls).skip_checks()
        if not CONF.compute_feature_enabled.vnc_console:
            raise cls.skipException('VNC Console feature is disabled.')

    def setUp(self):
        super(NoVNCConsoleTestJSON, self).setUp()
        self._websocket = None

    def tearDown(self):
        super(NoVNCConsoleTestJSON, self).tearDown()
        if self._websocket is not None:
            self._websocket.close()
        # NOTE(zhufl): Because server_check_teardown will raise Exception
        # which will prevent other cleanup steps from being executed, so
        # server_check_teardown should be called after super's tearDown.
        self.server_check_teardown()

    @classmethod
    def setup_clients(cls):
        super(NoVNCConsoleTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(NoVNCConsoleTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until="ACTIVE")
        cls.use_get_remote_console = False
        if not cls.is_requested_microversion_compatible('2.5'):
            cls.use_get_remote_console = True

    def _validate_novnc_html(self, vnc_url):
        """Verify we can connect to novnc and get back the javascript."""
        resp = urllib3.PoolManager().request('GET', vnc_url)
        # Make sure that the GET request was accepted by the novncproxy
        self.assertEqual(resp.status, 200, 'Got a Bad HTTP Response on the '
                         'initial call: ' + six.text_type(resp.status))
        # Do some basic validation to make sure it is an expected HTML document
        resp_data = resp.data.decode()
        # This is needed in the case of example: <html lang="en">
        self.assertRegex(resp_data, '<html.*>',
                         'Not a valid html document in the response.')
        self.assertIn('</html>', resp_data,
                      'Not a valid html document in the response.')
        # Just try to make sure we got JavaScript back for noVNC, since we
        # won't actually use it since not inside of a browser
        self.assertIn('noVNC', resp_data,
                      'Not a valid noVNC javascript html document.')
        self.assertIn('<script', resp_data,
                      'Not a valid noVNC javascript html document.')

    def _validate_rfb_negotiation(self):
        """Verify we can connect to novnc and do the websocket connection."""
        # Turn the Socket into a WebSocket to do the communication
        data = self._websocket.receive_frame()
        self.assertFalse(data is None or not data,
                         'Token must be invalid because the connection '
                         'closed.')
        # Parse the RFB version from the data to make sure it is valid
        # and belong to the known supported RFB versions.
        version = float("%d.%d" % (int(data[4:7], base=10),
                                   int(data[8:11], base=10)))
        # Add the max RFB versions supported
        supported_versions = [3.3, 3.8]
        self.assertIn(version, supported_versions,
                      'Bad RFB Version: ' + str(version))
        # Send our RFB version to the server
        self._websocket.send_frame(data)
        # Get the sever authentication type and make sure None is supported
        data = self._websocket.receive_frame()
        self.assertIsNotNone(data, 'Expected authentication type None.')
        data_length = len(data)
        if version == 3.3:
            # For RFB 3.3: in the security handshake, rather than a two-way
            # negotiation, the server decides the security type and sends a
            # single word(4 bytes).
            self.assertEqual(
                data_length, 4, 'Expected authentication type None.')
            self.assertIn(1, [ord_func(data[i]) for i in (0, 3)],
                          'Expected authentication type None.')
        else:
            self.assertGreaterEqual(
                len(data), 2, 'Expected authentication type None.')
            self.assertIn(
                1,
                [ord_func(data[i + 1]) for i in range(ord_func(data[0]))],
                'Expected authentication type None.')
            # Send to the server that we only support authentication
            # type None
            self._websocket.send_frame(six.int2byte(1))

            # The server should send 4 bytes of 0's if security
            # handshake succeeded
            data = self._websocket.receive_frame()
            self.assertEqual(
                len(data), 4,
                'Server did not think security was successful.')
            self.assertEqual(
                [ord_func(i) for i in data], [0, 0, 0, 0],
                'Server did not think security was successful.')

        # Say to leave the desktop as shared as part of client initialization
        self._websocket.send_frame(six.int2byte(1))
        # Get the server initialization packet back and make sure it is the
        # right structure where bytes 20-24 is the name length and
        # 24-N is the name
        data = self._websocket.receive_frame()
        data_length = len(data) if data is not None else 0
        self.assertFalse(data_length <= 24 or
                         data_length != (struct.unpack(">L",
                                                       data[20:24])[0] + 24),
                         'Server initialization was not the right format.')
        # Since the rest of the data on the screen is arbitrary, we will
        # close the socket and end our validation of the data at this point
        # Assert that the latest check was false, meaning that the server
        # initialization was the right format
        self.assertFalse(data_length <= 24 or
                         data_length != (struct.unpack(">L",
                                                       data[20:24])[0] + 24))

    def _validate_websocket_upgrade(self):
        """Verify that the websocket upgrade was successful.

        Parses response and ensures that required response
        fields are present and accurate.
        (https://tools.ietf.org/html/rfc7231#section-6.2.2)
        """

        self.assertTrue(
            self._websocket.response.startswith(b'HTTP/1.1 101 Switching '
                                                b'Protocols'),
            'Incorrect HTTP return status code: {}'.format(
                six.text_type(self._websocket.response)
            )
        )
        _required_header = 'upgrade: websocket'
        _response = six.text_type(self._websocket.response).lower()
        self.assertIn(
            _required_header,
            _response,
            'Did not get the expected WebSocket HTTP Response.'
        )

    @decorators.idempotent_id('c640fdff-8ab4-45a4-a5d8-7e6146cbd0dc')
    def test_novnc(self):
        """Test accessing novnc console of server"""
        if self.use_get_remote_console:
            body = self.client.get_remote_console(
                self.server['id'], console_type='novnc',
                protocol='vnc')['remote_console']
        else:
            body = self.client.get_vnc_console(self.server['id'],
                                               type='novnc')['console']
        self.assertEqual('novnc', body['type'])
        # Do the initial HTTP Request to novncproxy to get the NoVNC JavaScript
        self._validate_novnc_html(body['url'])
        # Do the WebSockify HTTP Request to novncproxy to do the RFB connection
        self._websocket = compute.create_websocket(body['url'])
        # Validate that we successfully connected and upgraded to Web Sockets
        self._validate_websocket_upgrade()
        # Validate the RFB Negotiation to determine if a valid VNC session
        self._validate_rfb_negotiation()

    @decorators.idempotent_id('f9c79937-addc-4aaa-9e0e-841eef02aeb7')
    def test_novnc_bad_token(self):
        """Test accessing novnc console with bad token

        Do the WebSockify HTTP Request to novnc proxy with a bad token,
        the novnc proxy should reject the connection and closed it.
        """
        if self.use_get_remote_console:
            body = self.client.get_remote_console(
                self.server['id'], console_type='novnc',
                protocol='vnc')['remote_console']
        else:
            body = self.client.get_vnc_console(self.server['id'],
                                               type='novnc')['console']
        self.assertEqual('novnc', body['type'])
        # Do the WebSockify HTTP Request to novncproxy with a bad token
        parts = urlparse.urlparse(body['url'])
        qparams = urlparse.parse_qs(parts.query)
        if 'path' in qparams:
            qparams['path'] = urlparse.unquote(qparams['path'][0]).replace(
                'token=', 'token=bad')
        elif 'token' in qparams:
            qparams['token'] = 'bad' + qparams['token'][0]
        new_query = urlparse.urlencode(qparams)
        new_parts = urlparse.ParseResult(parts.scheme, parts.netloc,
                                         parts.path, parts.params, new_query,
                                         parts.fragment)
        url = urlparse.urlunparse(new_parts)
        self._websocket = compute.create_websocket(url)
        # Make sure the novncproxy rejected the connection and closed it
        data = self._websocket.receive_frame()
        self.assertTrue(data is None or not data,
                        "The novnc proxy actually sent us some data, but we "
                        "expected it to close the connection.")
