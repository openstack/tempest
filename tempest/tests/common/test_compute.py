# Copyright 2017 Citrix Systems
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

from urllib import parse as urlparse

from tempest.common import compute
from tempest import exceptions
from tempest.lib import exceptions as lib_exc
from tempest.tests import base


class TestCompute(base.TestCase):
    def setUp(self):
        super(TestCompute, self).setUp()
        self.client_sock = mock.Mock()
        self.url = urlparse.urlparse("http://www.fake.com:80")

    @mock.patch('tempest.common.compute.' 'config.CONF.validation')
    def test_get_server_ip_connect_method_floating(self, mock_conf):
        fake_server = {'id': 'fake-uuid'}
        fake_vr = {'floating_ip': {'ip': '10.10.10.1'}}
        mock_conf.connect_method = 'floating'

        fake_server_ip = compute.get_server_ip(fake_server, fake_vr)
        self.assertEqual(fake_server_ip, '10.10.10.1')

        # assert that InvalidParam is raised when validadation
        # resources are not set
        self.assertRaises(lib_exc.InvalidParam,
                          compute.get_server_ip,
                          fake_server)

    @mock.patch('tempest.common.compute.' 'config.CONF.validation')
    def test_get_server_ip_connect_method_fixed(self, mock_conf):
        fake_server = {'id': 'fake-uuid',
                       'addresses': {
                           'private': [
                               {'addr': '192.168.0.3',
                                'version': 4}]}}
        mock_conf.connect_method = 'fixed'
        mock_conf.network_for_ssh = 'private'
        mock_conf.ip_version_for_ssh = 4

        fake_server_ip = compute.get_server_ip(fake_server)
        self.assertEqual(fake_server_ip, '192.168.0.3')

        fake_server_v6 = {'id': 'fake-uuid',
                          'addresses': {
                              'private': [
                                  {'addr': '2345:0425:2CA1::0567:5673:23b5',
                                   'version': 6}]}}
        # assert when server is unreachable
        self.assertRaises(exceptions.ServerUnreachable,
                          compute.get_server_ip,
                          fake_server_v6)

    @mock.patch('tempest.common.compute.' 'config.CONF.validation')
    def test_get_server_ip_invalid_config(self, mock_conf):
        fake_server = {'id': 'fake-uuid',
                       'addresses': {
                           'private': [
                               {'addr': '192.168.0.3',
                                'version': 4}]}}
        mock_conf.connect_method = 'fake-method'
        # assert when the connection method is not correctly set
        self.assertRaises(lib_exc.InvalidConfiguration,
                          compute.get_server_ip,
                          fake_server)

    def test_rfp_frame_not_cached(self):
        # rfp negotiation frame arrived separately after upgrade
        # response, so it's not cached.
        RFP_VERSION = b'RFB.003.003\x0a'
        rfp_frame_header = b'\x82\x0c'

        self.client_sock.recv.side_effect = [
            b'fake response start\r\n',
            b'fake response end\r\n\r\n',
            rfp_frame_header,
            RFP_VERSION]
        expect_response = b'fake response start\r\nfake response end\r\n\r\n'

        webSocket = compute._WebSocket(self.client_sock, self.url)

        self.assertEqual(webSocket.response, expect_response)
        # no cache
        self.assertEqual(webSocket.cached_stream, b'')
        self.client_sock.recv.assert_has_calls([mock.call(4096),
                                                mock.call(4096)])

        self.client_sock.recv.reset_mock()
        recv_version = webSocket.receive_frame()

        self.assertEqual(recv_version, RFP_VERSION)
        self.client_sock.recv.assert_has_calls([mock.call(2),
                                                mock.call(12)])

    def test_rfp_frame_fully_cached(self):
        RFP_VERSION = b'RFB.003.003\x0a'
        rfp_version_frame = b'\x82\x0c%s' % RFP_VERSION

        self.client_sock.recv.side_effect = [
            b'fake response start\r\n',
            b'fake response end\r\n\r\n%s' % rfp_version_frame]
        expect_response = b'fake response start\r\nfake response end\r\n\r\n'
        webSocket = compute._WebSocket(self.client_sock, self.url)

        self.client_sock.recv.assert_has_calls([mock.call(4096),
                                                mock.call(4096)])
        self.assertEqual(webSocket.response, expect_response)
        self.assertEqual(webSocket.cached_stream, rfp_version_frame)

        self.client_sock.recv.reset_mock()
        recv_version = webSocket.receive_frame()

        self.client_sock.recv.assert_not_called()
        self.assertEqual(recv_version, RFP_VERSION)
        # cached_stream should be empty in the end.
        self.assertEqual(webSocket.cached_stream, b'')

    def test_rfp_frame_partially_cached(self):
        RFP_VERSION = b'RFB.003.003\x0a'
        rfp_version_frame = b'\x82\x0c%s' % RFP_VERSION
        frame_part1 = rfp_version_frame[:6]
        frame_part2 = rfp_version_frame[6:]

        self.client_sock.recv.side_effect = [
            b'fake response start\r\n',
            b'fake response end\r\n\r\n%s' % frame_part1,
            frame_part2]
        expect_response = b'fake response start\r\nfake response end\r\n\r\n'
        webSocket = compute._WebSocket(self.client_sock, self.url)

        self.client_sock.recv.assert_has_calls([mock.call(4096),
                                                mock.call(4096)])
        self.assertEqual(webSocket.response, expect_response)
        self.assertEqual(webSocket.cached_stream, frame_part1)

        self.client_sock.recv.reset_mock()

        recv_version = webSocket.receive_frame()

        self.client_sock.recv.assert_called_once_with(len(frame_part2))
        self.assertEqual(recv_version, RFP_VERSION)
        # cached_stream should be empty in the end.
        self.assertEqual(webSocket.cached_stream, b'')
