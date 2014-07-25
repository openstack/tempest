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

import mock
import testtools

from tempest.common import waiters
from tempest import exceptions
from tempest.tests import base


class TestImageWaiters(base.TestCase):
    def setUp(self):
        super(TestImageWaiters, self).setUp()
        self.client = mock.MagicMock()
        self.client.build_timeout = 1
        self.client.build_interval = 1

    def test_wait_for_image_status(self):
        self.client.get_image.return_value = (None, {'status': 'active'})
        start_time = int(time.time())
        waiters.wait_for_image_status(self.client, 'fake_image_id', 'active')
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout
        self.assertTrue((end_time - start_time) < 10)

    def test_wait_for_image_status_timeout(self):
        self.client.get_image.return_value = (None, {'status': 'saving'})
        self.assertRaises(exceptions.TimeoutException,
                          waiters.wait_for_image_status,
                          self.client, 'fake_image_id', 'active')

    def test_wait_for_image_status_error_on_image_create(self):
        self.client.get_image.return_value = (None, {'status': 'ERROR'})
        self.assertRaises(exceptions.AddImageException,
                          waiters.wait_for_image_status,
                          self.client, 'fake_image_id', 'active')


class TestServerWaiters(base.TestCase):
    def setUp(self):
        super(TestServerWaiters, self).setUp()
        self.client = mock.MagicMock()
        self.client.build_timeout = 1
        self.client.build_interval = 1

    def test_wait_for_server_status(self):
        self.client.get_server.return_value = (None, {'status':
                                                      'active'}
                                               )
        start_time = int(time.time())
        waiters.wait_for_server_status(self.client, 'fake_svr_id',
                                       'active'
                                       )
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout
        self.assertTrue((end_time - start_time) < 2)

    def test_wait_for_server_status_BUILD_from_not_UNKNOWN(self):
        self.client.get_server.return_value = (None, {'status': 'active'})
        start_time = int(time.time())
        waiters.wait_for_server_status(self.client, 'fake_svr_id',
                                       'BUILD')
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout
        self.assertTrue((end_time - start_time) < 2)

    def test_wait_for_server_status_ready_wait_with_BUILD(self):
        self.client.get_server.return_value = (None, {'status': 'BUILD'})
        start_time = int(time.time())
        waiters.wait_for_server_status(self.client, 'fake_svr_id',
                                       'BUILD', True)
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout
        self.assertTrue((end_time - start_time) < 2)

    def test_wait_for_server_status_ready_wait(self):
        self.client.get_server.return_value = (None, {'status':
                                                      'ERROR',
                                                      'OS-EXT-STS:task_state':
                                                      'n/a'
                                                      }
                                               )
        self.client.get_console_output.return_value = (None,
                          {'output': 'Server fake_svr_id failed to reach '
                           'active status and task state n/a within the '
                           'required time (1 s).\nCurrent status: SUSPENDED.'
                           '\nCurrent task state: None.'}
        )
        self.assertRaises(exceptions.BuildErrorException,
                          waiters.wait_for_server_status,
                          self.client, 'fake_svr_id', 'active',
                          ready_wait=True, extra_timeout=0,
                          raise_on_error=True
                          )

    def test_wait_for_server_status_no_ready_wait(self):
        self.client.get_server.return_value = (None, {'status':
                                                      'ERROR',
                                                      'OS-EXT-STS:task_state':
                                                      'n/a'
                                                      }
                                               )
        start_time = int(time.time())
        waiters.wait_for_server_status(self.client, 'fake_svr_id',
                                       'ERROR', ready_wait=False,
                                       extra_timeout=10, raise_on_error=True
                                       )
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout + extra_timeout
        self.assertTrue((end_time - start_time) < 12)

    def test_wait_for_server_status_timeout(self):
        self.client.get_server.return_value = (None, {'status': 'SUSPENDED'})
        self.client.get_console_output.return_value = (None,
                          {'output': 'Server fake_svr_id failed to reach '
                           'active status and task state n/a within the '
                           'required time (1 s).\nCurrent status: SUSPENDED.'
                           '\nCurrent task state: None.'}
        )
        self.assertRaises(exceptions.TimeoutException,
                          waiters.wait_for_server_status,
                         self.client, 'fake_svr_id', 'active')

    def test_wait_for_server_status_extra_timeout(self):
        self.client.get_server.return_value = (None, {'status': 'SUSPENDED'})
        start_time = int(time.time())
        self.client.get_console_output.return_value = (None,
                          {'output': 'Server fake_svr_id failed to reach '
                           'active status and task state n/a within the '
                           'required time (10 s). \nCurrent status: SUSPENDED.'
                           '\nCurrent task state: None.'}
        )
        self.assertRaises(exceptions.TimeoutException,
                          waiters.wait_for_server_status,
                          self.client, 'fake_svr_id',
                          'active', ready_wait=True,
                          extra_timeout=10, raise_on_error=True
                          )
        end_time = int(time.time())
        # Ensure waiter returns after build_timeout but
        #   before build_timeout+extra timeout
        self.assertTrue(10 < (end_time - start_time) < 12)

    def test_wait_for_server_status_error_on_server_create(self):
        self.client.get_server.return_value = (None, {'status': 'ERROR'})
        self.client.get_console_output.return_value = (None,
                          {'output': 'Server fake_svr_id failed to reach '
                           'activestatus and task state n/a within the '
                           'required time (1 s).\nCurrent status: ERROR.'
                           '\nCurrent task state: None.'}
        )
        self.assertRaises(exceptions.BuildErrorException,
                          waiters.wait_for_server_status,
                          self.client, 'fake_svr_id', 'active')

    def test_wait_for_server_status_no_raise_on_error(self):
        self.client.get_server.return_value = (None, {'status': 'ERROR'})
        self.client.get_console_output.return_value = (None,
                          {'output': 'Server fake_svr_id failed to reach '
                           'activestatus and task state n/a within the '
                           'required time (1 s).\nCurrent status: ERROR.'
                           '\nCurrent task state: None.'}
        )
        self.assertRaises(exceptions.TimeoutException,
                          waiters.wait_for_server_status,
                          self.client, 'fake_svr_id', 'active',
                          ready_wait=True, extra_timeout=0,
                          raise_on_error=False
                          )

    def test_wait_for_server_status_no_ready_wait_timeout(self):
        self.client.get_server.return_value = (None, {'status': 'ERROR'})
        self.client.get_console_output.return_value = (None,
                          {'output': 'Server fake_svr_id failed to reach '
                           'active status and task state n/a within the '
                           'required time (11 s).\nCurrent status: ERROR.'
                           '\nCurrent task state: None.'}
        )
        expected_msg = '''Request timed out
Details: (TestServerWaiters:test_wait_for_server_status_no_ready_wait_timeout)\
 Server fake_svr_id failed to reach active status and task state "n/a" within\
 the required time (11 s). Current status: ERROR. Current task state: None.\
'''
        with testtools.ExpectedException(exceptions.TimeoutException,
                                         testtools.matchers.AfterPreprocessing(
                str,
                testtools.matchers.Equals(expected_msg)
                )
            ):
            waiters.wait_for_server_status(self.client, 'fake_svr_id',
                                           'active', ready_wait=False,
                                           extra_timeout=10,
                                           raise_on_error=False
                                           )

    def test_wait_for_server_status_ready_wait_timeout(self):
        self.client.get_server.return_value = (None, {'status': 'ERROR'})
        self.client.get_console_output.return_value = (None,
                          {'output': 'Server fake_svr_id failed to reach '
                           'activestatus and task state n/a within the '
                           'required time (11 s).\nCurrent status: ERROR.'
                           '\nCurrent task state: None.'}
        )
        expected_msg = '''Request timed out
Details: (TestServerWaiters:test_wait_for_server_status_ready_wait_timeout)\
 Server fake_svr_id failed to reach active status and task state "None" within\
 the required time (11 s). Current status: ERROR. Current task state: None.\
'''
        with testtools.ExpectedException(exceptions.TimeoutException,
                                         testtools.matchers.AfterPreprocessing(
                str,
                testtools.matchers.Equals(expected_msg)
                )
            ):
            waiters.wait_for_server_status(self.client, 'fake_svr_id',
                                           'active', ready_wait=True,
                                           extra_timeout=10,
                                           raise_on_error=False
                                           )

    def test_wait_for_changing_server_status(self):
        self.client.get_server.side_effect = [(None, {'status': 'BUILD'}),
                                              (None, {'status': 'active'})]
        start_time = int(time.time())
        waiters.wait_for_server_status(self.client, 'fake_svr_id',
                                       'active', ready_wait=True,
                                       extra_timeout=10,
                                       raise_on_error=True
                                       )
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout + extra_timeout
        self.assertTrue((end_time - start_time) < 12)

    def test_wait_for_changing_server_task_status(self):
        self.client.get_server.side_effect = [(None, {'status': 'BUILD',
                                                      'OS-EXT-STS:task_state':
                                                      'n/a'
                                                      }
                                               ),
                                              (None, {'status': 'active',
                                                      'OS-EXT-STS:task_state':
                                                      'None'
                                                      }
                                               )
                                              ]
        start_time = int(time.time())
        waiters.wait_for_server_status(self.client, 'fake_svr_id',
                                       'active', ready_wait=True,
                                       extra_timeout=10,
                                       raise_on_error=True
                                       )
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout + extra_timeout
        self.assertTrue((end_time - start_time) < 12)
