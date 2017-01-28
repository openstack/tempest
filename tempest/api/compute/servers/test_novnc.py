# Copyright 2016 OpenStack Foundation
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

import socket
import struct

import six
from six.moves.urllib import parse as urlparse
import urllib3

from tempest.api.compute import base
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class NoVNCConsoleTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(NoVNCConsoleTestJSON, cls).skip_checks()
        if not CONF.compute_feature_enabled.vnc_console:
            raise cls.skipException('VNC Console feature is disabled.')

    def setUp(self):
        super(NoVNCConsoleTestJSON, self).setUp()
        self._websocket = None

    def tearDown(self):
        self.server_check_teardown()
        super(NoVNCConsoleTestJSON, self).tearDown()
        if self._websocket is not None:
            self._websocket.close()

    @classmethod
    def setup_clients(cls):
        super(NoVNCConsoleTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(NoVNCConsoleTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until="ACTIVE")

    def _validate_novnc_html(self, vnc_url):
        """Verify we can connect to novnc and get back the javascript."""
        resp = urllib3.PoolManager().request('GET', vnc_url)
        # Make sure that the GET request was accepted by the novncproxy
        self.assertEqual(resp.status, 200, 'Got a Bad HTTP Response on the '
                         'initial call: ' + str(resp.status))
        # Do some basic validation to make sure it is an expected HTML document
        self.assertTrue('<html>' in resp.data and '</html>' in resp.data,
                        'Not a valid html document in the response.')
        # Just try to make sure we got JavaScript back for noVNC, since we
        # won't actually use it since not inside of a browser
        self.assertTrue('noVNC' in resp.data and '<script' in resp.data,
                        'Not a valid noVNC javascript html document.')

    def _validate_rfb_negotiation(self):
        """Verify we can connect to novnc and do the websocket connection."""
        # Turn the Socket into a WebSocket to do the communication
        data = self._websocket.receive_frame()
        self.assertFalse(data is None or len(data) == 0,
                         'Token must be invalid because the connection '
                         'closed.')
        # Parse the RFB version from the data to make sure it is valid
        # and greater than or equal to 3.3
        version = float("%d.%d" % (int(data[4:7], base=10),
                                   int(data[8:11], base=10)))
        self.assertTrue(version >= 3.3, 'Bad RFB Version: ' + str(version))
        # Send our RFB version to the server, which we will just go with 3.3
        self._websocket.send_frame(str(data))
        # Get the sever authentication type and make sure None is supported
        data = self._websocket.receive_frame()
        self.assertIsNotNone(data, 'Expected authentication type None.')
        self.assertGreaterEqual(
            len(data), 2, 'Expected authentication type None.')
        self.assertIn(
            1, [ord(data[i + 1]) for i in range(ord(data[0]))],
            'Expected authentication type None.')
        # Send to the server that we only support authentication type None
        self._websocket.send_frame(six.int2byte(1))
        # The server should send 4 bytes of 0's if security handshake succeeded
        data = self._websocket.receive_frame()
        self.assertEqual(
            len(data), 4, 'Server did not think security was successful.')
        self.assertEqual(
            [ord(i) for i in data], [0, 0, 0, 0],
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
        self.assertTrue(
            self._websocket.response.startswith('HTTP/1.1 101 Switching '
                                                'Protocols\r\n'),
            'Did not get the expected 101 on the websockify call: '
            + str(len(self._websocket.response)))
        self.assertTrue(
            self._websocket.response.find('Server: WebSockify') > 0,
            'Did not get the expected WebSocket HTTP Response.')

    def _create_websocket(self, url):
        url = urlparse.urlparse(url)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((url.hostname, url.port))
        # Turn the Socket into a WebSocket to do the communication
        return _WebSocket(client_socket, url)

    @decorators.idempotent_id('c640fdff-8ab4-45a4-a5d8-7e6146cbd0dc')
    def test_novnc(self):
        body = self.client.get_vnc_console(self.server['id'],
                                           type='novnc')['console']
        self.assertEqual('novnc', body['type'])
        # Do the initial HTTP Request to novncproxy to get the NoVNC JavaScript
        self._validate_novnc_html(body['url'])
        # Do the WebSockify HTTP Request to novncproxy to do the RFB connection
        self._websocket = self._create_websocket(body['url'])
        # Validate that we succesfully connected and upgraded to Web Sockets
        self._validate_websocket_upgrade()
        # Validate the RFB Negotiation to determine if a valid VNC session
        self._validate_rfb_negotiation()

    @decorators.idempotent_id('f9c79937-addc-4aaa-9e0e-841eef02aeb7')
    def test_novnc_bad_token(self):
        body = self.client.get_vnc_console(self.server['id'],
                                           type='novnc')['console']
        self.assertEqual('novnc', body['type'])
        # Do the WebSockify HTTP Request to novncproxy with a bad token
        url = body['url'].replace('token=', 'token=bad')
        self._websocket = self._create_websocket(url)
        # Make sure the novncproxy rejected the connection and closed it
        data = self._websocket.receive_frame()
        self.assertTrue(data is None or len(data) == 0,
                        "The novnc proxy actually sent us some data, but we "
                        "expected it to close the connection.")


class _WebSocket(object):
    def __init__(self, client_socket, url):
        """Contructor for the WebSocket wrapper to the socket."""
        self._socket = client_socket
        # Upgrade the HTTP connection to a WebSocket
        self._upgrade(url)

    def receive_frame(self):
        """Wrapper for receiving data to parse the WebSocket frame format"""
        # We need to loop until we either get some bytes back in the frame
        # or no data was received (meaning the socket was closed).  This is
        # done to handle the case where we get back some empty frames
        while True:
            header = self._socket.recv(2)
            # If we didn't receive any data, just return None
            if len(header) == 0:
                return None
            # We will make the assumption that we are only dealing with
            # frames less than 125 bytes here (for the negotiation) and
            # that only the 2nd byte contains the length, and since the
            # server doesn't do masking, we can just read the data length
            if ord(header[1]) & 127 > 0:
                return self._socket.recv(ord(header[1]) & 127)

    def send_frame(self, data):
        """Wrapper for sending data to add in the WebSocket frame format."""
        frame_bytes = list()
        # For the first byte, want to say we are sending binary data (130)
        frame_bytes.append(130)
        # Only sending negotiation data so don't need to worry about > 125
        # We do need to add the bit that says we are masking the data
        frame_bytes.append(len(data) | 128)
        # We don't really care about providing a random mask for security
        # So we will just hard-code a value since a test program
        mask = [7, 2, 1, 9]
        for i in range(len(mask)):
            frame_bytes.append(mask[i])
        # Mask each of the actual data bytes that we are going to send
        for i in range(len(data)):
            frame_bytes.append(ord(data[i]) ^ mask[i % 4])
        # Convert our integer list to a binary array of bytes
        frame_bytes = struct.pack('!%iB' % len(frame_bytes), * frame_bytes)
        self._socket.sendall(frame_bytes)

    def close(self):
        """Helper method to close the connection."""
        # Close down the real socket connection and exit the test program
        if self._socket is not None:
            self._socket.shutdown(1)
            self._socket.close()
            self._socket = None

    def _upgrade(self, url):
        """Upgrade the HTTP connection to a WebSocket and verify."""
        # The real request goes to the /websockify URI always
        reqdata = 'GET /websockify HTTP/1.1\r\n'
        reqdata += 'Host: %s:%s\r\n' % (url.hostname, url.port)
        # Tell the HTTP Server to Upgrade the connection to a WebSocket
        reqdata += 'Upgrade: websocket\r\nConnection: Upgrade\r\n'
        # The token=xxx is sent as a Cookie not in the URI
        reqdata += 'Cookie: %s\r\n' % url.query
        # Use a hard-coded WebSocket key since a test program
        reqdata += 'Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==\r\n'
        reqdata += 'Sec-WebSocket-Version: 13\r\n'
        # We are choosing to use binary even though browser may do Base64
        reqdata += 'Sec-WebSocket-Protocol: binary\r\n\r\n'
        # Send the HTTP GET request and get the response back
        self._socket.sendall(reqdata)
        self.response = data = self._socket.recv(4096)
        # Loop through & concatenate all of the data in the response body
        while len(data) > 0 and self.response.find('\r\n\r\n') < 0:
            data = self._socket.recv(4096)
            self.response += data
