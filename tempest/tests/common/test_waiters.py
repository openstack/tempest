# Copyright 2014 IBM Corp.
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

import time
from unittest import mock

from oslo_utils.fixture import uuidsentinel as uuids

from tempest.common import waiters
from tempest import exceptions
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.volume.v2 import volumes_client
from tempest.tests import base
import tempest.tests.utils as utils


class TestImageWaiters(base.TestCase):
    def setUp(self):
        super(TestImageWaiters, self).setUp()
        self.client = mock.MagicMock()
        self.client.build_timeout = 1
        self.client.build_interval = 1

    def test_wait_for_image_status(self):
        self.client.show_image.return_value = ({'status': 'active'})
        start_time = int(time.time())
        waiters.wait_for_image_status(self.client, 'fake_image_id', 'active')
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout
        self.assertLess((end_time - start_time), 10)

    def test_wait_for_image_status_timeout(self):
        time_mock = self.patch('time.time')
        time_mock.side_effect = utils.generate_timeout_series(1)

        self.client.show_image.return_value = ({'status': 'saving'})
        self.assertRaises(lib_exc.TimeoutException,
                          waiters.wait_for_image_status,
                          self.client, 'fake_image_id', 'active')

    def test_wait_for_image_status_error_on_image_create(self):
        self.client.show_image.return_value = ({'status': 'ERROR'})
        self.assertRaises(exceptions.AddImageException,
                          waiters.wait_for_image_status,
                          self.client, 'fake_image_id', 'active')


class TestInterfaceWaiters(base.TestCase):

    build_timeout = 1.
    build_interval = 1
    port_down = {'interfaceAttachment': {'port_state': 'DOWN'}}
    port_active = {'interfaceAttachment': {'port_state': 'ACTIVE'}}

    def mock_client(self, **kwargs):
        return mock.MagicMock(
            build_timeout=self.build_timeout,
            build_interval=self.build_interval,
            **kwargs)

    def test_wait_for_interface_status(self):
        show_interface = mock.Mock(
            side_effect=[self.port_down, self.port_active])
        client = self.mock_client(show_interface=show_interface)
        self.patch('time.time', return_value=0.)
        sleep = self.patch('time.sleep')

        result = waiters.wait_for_interface_status(
            client, 'server_id', 'port_id', 'ACTIVE')

        self.assertIs(self.port_active['interfaceAttachment'], result)
        show_interface.assert_has_calls([mock.call('server_id', 'port_id'),
                                         mock.call('server_id', 'port_id')])
        sleep.assert_called_once_with(client.build_interval)

    def test_wait_for_interface_status_timeout(self):
        show_interface = mock.MagicMock(return_value=self.port_down)
        client = self.mock_client(show_interface=show_interface)
        self.patch('time.time', side_effect=[0., client.build_timeout + 1.])
        sleep = self.patch('time.sleep')

        self.assertRaises(lib_exc.TimeoutException,
                          waiters.wait_for_interface_status,
                          client, 'server_id', 'port_id', 'ACTIVE')

        show_interface.assert_has_calls([mock.call('server_id', 'port_id'),
                                         mock.call('server_id', 'port_id')])
        sleep.assert_called_once_with(client.build_interval)

    one_interface = {'interfaceAttachments': [{'port_id': 'port_one'}]}
    two_interfaces = {'interfaceAttachments': [{'port_id': 'port_one'},
                                               {'port_id': 'port_two'}]}

    def test_wait_for_interface_detach(self):
        list_interfaces = mock.MagicMock(
            side_effect=[self.two_interfaces, self.one_interface])
        client = self.mock_client(list_interfaces=list_interfaces)
        self.patch('time.time', return_value=0.)
        sleep = self.patch('time.sleep')

        result = waiters.wait_for_interface_detach(
            client, 'server_id', 'port_two')

        self.assertIs(self.one_interface['interfaceAttachments'], result)
        list_interfaces.assert_has_calls([mock.call('server_id'),
                                          mock.call('server_id')])
        sleep.assert_called_once_with(client.build_interval)

    def test_wait_for_interface_detach_timeout(self):
        list_interfaces = mock.MagicMock(return_value=self.one_interface)
        client = self.mock_client(list_interfaces=list_interfaces)
        self.patch('time.time', side_effect=[0., client.build_timeout + 1.])
        sleep = self.patch('time.sleep')

        self.assertRaises(lib_exc.TimeoutException,
                          waiters.wait_for_interface_detach,
                          client, 'server_id', 'port_one')

        list_interfaces.assert_has_calls([mock.call('server_id'),
                                          mock.call('server_id')])
        sleep.assert_called_once_with(client.build_interval)


class TestVolumeWaiters(base.TestCase):
    vol_migrating_src_host = {
        'volume': {'migration_status': 'migrating',
                   'os-vol-host-attr:host': 'src_host@backend#type'}}
    vol_migrating_dst_host = {
        'volume': {'migration_status': 'migrating',
                   'os-vol-host-attr:host': 'dst_host@backend#type'}}
    vol_migration_success = {
        'volume': {'migration_status': 'success',
                   'os-vol-host-attr:host': 'dst_host@backend#type'}}
    vol_migration_error = {
        'volume': {'migration_status': 'error',
                   'os-vol-host-attr:host': 'src_host@backend#type'}}

    def test_wait_for_volume_migration_timeout(self):
        show_volume = mock.MagicMock(return_value=self.vol_migrating_src_host)
        client = mock.Mock(spec=volumes_client.VolumesClient,
                           resource_type="volume",
                           build_interval=1,
                           build_timeout=1,
                           show_volume=show_volume)
        self.patch('time.time', side_effect=[0., client.build_timeout + 1.])
        self.patch('time.sleep')
        self.assertRaises(lib_exc.TimeoutException,
                          waiters.wait_for_volume_migration,
                          client, mock.sentinel.volume_id, 'dst_host')

    def test_wait_for_volume_migration_error(self):
        show_volume = mock.MagicMock(side_effect=[
            self.vol_migrating_src_host,
            self.vol_migrating_src_host,
            self.vol_migration_error])
        client = mock.Mock(spec=volumes_client.VolumesClient,
                           resource_type="volume",
                           build_interval=1,
                           build_timeout=1,
                           show_volume=show_volume)
        self.patch('time.time', return_value=0.)
        self.patch('time.sleep')
        self.assertRaises(lib_exc.TempestException,
                          waiters.wait_for_volume_migration,
                          client, mock.sentinel.volume_id, 'dst_host')

    def test_wait_for_volume_migration_success_and_dst(self):
        show_volume = mock.MagicMock(side_effect=[
            self.vol_migrating_src_host,
            self.vol_migrating_dst_host,
            self.vol_migration_success])
        client = mock.Mock(spec=volumes_client.VolumesClient,
                           resource_type="volume",
                           build_interval=1,
                           build_timeout=1,
                           show_volume=show_volume)
        self.patch('time.time', return_value=0.)
        self.patch('time.sleep')
        waiters.wait_for_volume_migration(
            client, mock.sentinel.volume_id, 'dst_host')

        # Assert that we wait until migration_status is success and dst_host is
        # part of the returned os-vol-host-attr:host.
        show_volume.assert_has_calls([mock.call(mock.sentinel.volume_id),
                                      mock.call(mock.sentinel.volume_id),
                                      mock.call(mock.sentinel.volume_id)])

    @mock.patch.object(time, 'sleep')
    def test_wait_for_volume_status_error_restoring(self, mock_sleep):
        # Tests that the wait method raises VolumeRestoreErrorException if
        # the volume status is 'error_restoring'.
        client = mock.Mock(spec=volumes_client.VolumesClient,
                           resource_type="volume",
                           build_interval=1)
        volume1 = {'volume': {'status': 'restoring-backup'}}
        volume2 = {'volume': {'status': 'error_restoring'}}
        mock_show = mock.Mock(side_effect=(volume1, volume2))
        client.show_volume = mock_show
        volume_id = '7532b91e-aa0a-4e06-b3e5-20c0c5ee1caa'
        self.assertRaises(exceptions.VolumeRestoreErrorException,
                          waiters.wait_for_volume_resource_status,
                          client, volume_id, 'available')
        mock_show.assert_has_calls([mock.call(volume_id),
                                    mock.call(volume_id)])
        mock_sleep.assert_called_once_with(1)

    @mock.patch.object(time, 'sleep')
    def test_wait_for_volume_status_error_extending(self, mock_sleep):
        # Tests that the wait method raises VolumeExtendErrorException if
        # the volume status is 'error_extending'.
        client = mock.Mock(spec=volumes_client.VolumesClient,
                           resource_type="volume",
                           build_interval=1)
        volume1 = {'volume': {'status': 'extending'}}
        volume2 = {'volume': {'status': 'error_extending'}}
        mock_show = mock.Mock(side_effect=(volume1, volume2))
        client.show_volume = mock_show
        volume_id = '7532b91e-aa0a-4e06-b3e5-20c0c5ee1caa'
        self.assertRaises(exceptions.VolumeExtendErrorException,
                          waiters.wait_for_volume_resource_status,
                          client, volume_id, 'available')
        mock_show.assert_has_calls([mock.call(volume_id),
                                    mock.call(volume_id)])
        mock_sleep.assert_called_once_with(1)

    def test_wait_for_volume_attachment_create(self):
        vol_detached = {'volume': {'attachments': []}}
        vol_attached = {'volume': {'attachments': [
                       {'id': uuids.volume_id,
                        'attachment_id': uuids.attachment_id,
                        'server_id': uuids.server_id,
                        'volume_id': uuids.volume_id}]}}
        show_volume = mock.MagicMock(side_effect=[
            vol_detached, vol_detached, vol_attached])
        client = mock.Mock(spec=volumes_client.VolumesClient,
                           build_interval=1,
                           build_timeout=5,
                           show_volume=show_volume)
        self.patch('time.time')
        self.patch('time.sleep')
        att = waiters.wait_for_volume_attachment_create(
            client, uuids.volume_id, uuids.server_id)
        assert att == vol_attached['volume']['attachments'][0]
        # Assert that show volume is called until the attachment is removed.
        show_volume.assert_has_calls([mock.call(uuids.volume_id),
                                      mock.call(uuids.volume_id),
                                      mock.call(uuids.volume_id)])

    def test_wait_for_volume_attachment(self):
        vol_detached = {'volume': {'attachments': []}}
        vol_attached = {'volume': {'attachments': [
                       {'attachment_id': uuids.attachment_id}]}}
        show_volume = mock.MagicMock(side_effect=[
            vol_attached, vol_attached, vol_detached])
        client = mock.Mock(spec=volumes_client.VolumesClient,
                           build_interval=1,
                           build_timeout=5,
                           show_volume=show_volume)
        self.patch('time.time')
        self.patch('time.sleep')
        waiters.wait_for_volume_attachment_remove(client, uuids.volume_id,
                                                  uuids.attachment_id)
        # Assert that show volume is called until the attachment is removed.
        show_volume.assert_has_calls([mock.call(uuids.volume_id),
                                      mock.call(uuids.volume_id),
                                      mock.call(uuids.volume_id)])

    def test_wait_for_volume_attachment_timeout(self):
        show_volume = mock.MagicMock(return_value={
            'volume': {'attachments': [
                {'attachment_id': uuids.attachment_id}]}})
        client = mock.Mock(spec=volumes_client.VolumesClient,
                           build_interval=1,
                           build_timeout=1,
                           show_volume=show_volume)
        self.patch('time.time', side_effect=[0., client.build_timeout + 1.])
        self.patch('time.sleep')
        # Assert that a timeout is raised if the attachment remains.
        self.assertRaises(lib_exc.TimeoutException,
                          waiters.wait_for_volume_attachment_remove,
                          client, uuids.volume_id, uuids.attachment_id)

    def test_wait_for_volume_attachment_not_present(self):
        show_volume = mock.MagicMock(return_value={
            'volume': {'attachments': []}})
        client = mock.Mock(spec=volumes_client.VolumesClient,
                           build_interval=1,
                           build_timeout=1,
                           show_volume=show_volume)
        self.patch('time.time', side_effect=[0., client.build_timeout + 1.])
        self.patch('time.sleep')
        waiters.wait_for_volume_attachment_remove(client, uuids.volume_id,
                                                  uuids.attachment_id)
        # Assert that show volume is only called once before we return
        show_volume.assert_called_once_with(uuids.volume_id)
