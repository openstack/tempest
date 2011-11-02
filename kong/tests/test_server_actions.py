
import json
import time

from kong import exceptions
from kong import openstack
from kong import tests
from kong.common import ssh

import unittest2 as unittest


class ServerActionsTest(tests.FunctionalTest):

    def setUp(self):
        super(ServerActionsTest, self).setUp()
        self.os = openstack.Manager(self.nova)

        self.multi_node = self.nova['multi_node'] == 'yes'
        self.image_ref = self.glance['image_id']
        self.image_ref_alt = self.glance['image_id_alt']
        self.flavor_ref = self.nova['flavor_ref']
        self.flavor_ref_alt = self.nova['flavor_ref_alt']
        self.ssh_timeout = int(self.nova['ssh_timeout'])
        self.build_timeout = int(self.nova['build_timeout'])

        self.server_password = 'testpwd'
        self.server_name = 'stacktester1'

        expected_server = {
            'name': self.server_name,
            'imageRef': self.image_ref,
            'flavorRef': self.flavor_ref,
            'adminPass': self.server_password,
        }

        created_server = self.os.nova.create_server(expected_server)

        self.server_id = created_server['id']
        self._wait_for_server_status(self.server_id, 'ACTIVE')

        server = self.os.nova.get_server(self.server_id)
        self.access_ip = server['addresses']['public'][0]['addr']

        # Ensure server came up
        if self.ssh_timeout:
            self._assert_ssh_password()

    def tearDown(self):
        self.os.nova.delete_server(self.server_id)

    def _get_ssh_client(self, password):
        return ssh.Client(self.access_ip, 'root', password, self.ssh_timeout)

    def _assert_ssh_password(self, password=None):
        _password = password or self.server_password
        client = self._get_ssh_client(_password)
        self.assertTrue(client.test_connection_auth())

    def _wait_for_server_status(self, server_id, status):
        try:
            self.os.nova.wait_for_server_status(server_id, status,
                                                timeout=self.build_timeout)
        except exceptions.TimeoutException:
            self.fail("Server failed to change status to %s" % status)

    def _get_boot_time(self):
        """Return the time the server was started"""
        output = self._read_file("/proc/uptime")
        uptime = float(output.split().pop(0))
        return time.time() - uptime

    def _write_file(self, filename, contents, password=None):
        command = "echo -n %s > %s" % (contents, filename)
        return self._exec_command(command, password)

    def _read_file(self, filename, password=None):
        command = "cat %s" % filename
        return self._exec_command(command, password)

    def _exec_command(self, command, password=None):
        if password is None:
            password = self.server_password
        client = self._get_ssh_client(password)
        return client.exec_command(command)

    def test_reboot_server(self):
        """Reboot a server SOFT and HARD"""
        # SSH and get the uptime
        if self.ssh_timeout:
            initial_time_started = self._get_boot_time()
        else:
            intitial_time_started = 0

        # Make reboot request
        post_body = json.dumps({'reboot': {'type': 'SOFT'}})
        url = "/servers/%s/action" % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(response['status'], '202')

        # Assert status transition
        self._wait_for_server_status(self.server_id, 'REBOOT')
        self._wait_for_server_status(self.server_id, 'ACTIVE')

        # SSH and verify uptime is less than before
        if self.ssh_timeout:
            post_reboot_time_started = self._get_boot_time()
            self.assertTrue(initial_time_started < post_reboot_time_started)

            # SSH and get the uptime for the next reboot
            initial_time_started = post_reboot_time_started

        # Make reboot request
        post_body = json.dumps({'reboot': {'type': 'HARD'}})
        url = "/servers/%s/action" % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(response['status'], '202')

        # Assert status transition
        # KNOWN-ISSUE 884906
        #self._wait_for_server_status(self.server_id, 'HARD_REBOOT')
        self._wait_for_server_status(self.server_id, 'REBOOT')
        self._wait_for_server_status(self.server_id, 'ACTIVE')

        # SSH and verify uptime is less than before
        if self.ssh_timeout:
            post_reboot_time_started = self._get_boot_time()
            self.assertTrue(initial_time_started < post_reboot_time_started)
    test_reboot_server.tags = ['nova']

    def test_change_password(self):
        """Change root password of a server"""
        # Change server password
        post_body = json.dumps({'changePassword': {'adminPass': 'test123'}})
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Assert status transition
        self.assertEqual('202', response['status'])
        self._wait_for_server_status(self.server_id, 'PASSWORD')
        self._wait_for_server_status(self.server_id, 'ACTIVE')

        # SSH into server using new password
        if self.ssh_timeout:
            self._assert_ssh_password('test123')
    test_change_password.tags = ['nova']

    def test_rebuild(self):
        """Rebuild a server"""

        FILENAME = '/tmp/testfile'
        CONTENTS = 'WORDS'

        # write file to server
        if self.ssh_timeout:
            self._write_file(FILENAME, CONTENTS)
            self.assertEqual(self._read_file(FILENAME), CONTENTS)

        # Make rebuild request
        post_body = json.dumps({'rebuild': {'imageRef': self.image_ref_alt}})
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # check output
        self.assertEqual('202', response['status'])
        rebuilt_server = json.loads(body)['server']
        generated_password = rebuilt_server['adminPass']

        # Ensure correct status transition
        self._wait_for_server_status(self.server_id, 'REBUILD')
        self._wait_for_server_status(self.server_id, 'ACTIVE')

        # Treats an issue where we ssh'd in too soon after rebuild
        #TODO(bcwaldon): fix the Xen driver so we don't have to sleep here
        time.sleep(30)

        # Check that the instance's imageRef matches the new imageRef
        server = self.os.nova.get_server(self.server_id)
        ref_match = self.image_ref_alt == server['image']['links'][0]['href']
        id_match = self.image_ref_alt == server['image']['id']
        self.assertTrue(ref_match or id_match)

        # SSH into the server to ensure it came back up
        if self.ssh_timeout:
            self._assert_ssh_password(generated_password)

            # make sure file is gone
            self.assertEqual(self._read_file(FILENAME, generated_password), '')

            # test again with a specified password
            self._write_file(FILENAME, CONTENTS, generated_password)
            _contents = self._read_file(FILENAME, generated_password)
            self.assertEqual(_contents, CONTENTS)

        specified_password = 'some_password'

        # Make rebuild request
        post_body = json.dumps({
            'rebuild': {
                'imageRef': self.image_ref,
                'adminPass': specified_password,
            }
        })
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # check output
        self.assertEqual('202', response['status'])
        rebuilt_server = json.loads(body)['server']
        self.assertEqual(rebuilt_server['adminPass'], specified_password)

        # Ensure correct status transition
        self._wait_for_server_status(self.server_id, 'REBUILD')
        self._wait_for_server_status(self.server_id, 'ACTIVE')

        # Treats an issue where we ssh'd in too soon after rebuild
        time.sleep(30)

        # Check that the instance's imageRef matches the new imageRef
        server = self.os.nova.get_server(self.server_id)
        ref_match = self.image_ref == server['image']['links'][0]['href']
        id_match = self.image_ref == server['image']['id']
        self.assertTrue(ref_match or id_match)

        # make sure file is gone
        if self.ssh_timeout:
            self.assertEqual(self._read_file(FILENAME, specified_password), '')
    test_rebuild.tags = ['nova']

    def test_resize(self):
        """Resize a server"""

        # Make resize request
        post_body = json.dumps({'resize': {'flavorRef': self.flavor_ref_alt}})
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Wait for status transition
        self.assertEqual('202', response['status'])
        self._wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        # Ensure API reports new flavor
        server = self.os.nova.get_server(self.server_id)
        self.assertEqual(self.flavor_ref_alt, server['flavor']['id'])

        #SSH into the server to ensure it came back up
        if self.ssh_timeout:
            self._assert_ssh_password()

        # Make confirmResize request
        post_body = json.dumps({'confirmResize': 'null'})
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Wait for status transition
        self.assertEqual('204', response['status'])
        self._wait_for_server_status(self.server_id, 'ACTIVE')

        # Ensure API still reports new flavor
        server = self.os.nova.get_server(self.server_id)
        self.assertEqual(self.flavor_ref_alt, server['flavor']['id'])
    test_resize.tags = ['nova']

    def test_resize_revert(self):
        """Resize a server, then revert"""
        # Make resize request
        post_body = json.dumps({'resize': {'flavorRef': self.flavor_ref_alt}})
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Wait for status transition
        self.assertEqual('202', response['status'])
        self._wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        # SSH into the server to ensure it came back up
        if self.ssh_timeout:
            self._assert_ssh_password()

        # Ensure API reports new flavor
        server = self.os.nova.get_server(self.server_id)
        self.assertEqual(self.flavor_ref_alt, server['flavor']['id'])

        # Make revertResize request
        post_body = json.dumps({'revertResize': 'null'})
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Assert status transition
        self.assertEqual('202', response['status'])
        self._wait_for_server_status(self.server_id, 'ACTIVE')

        # Ensure flavor ref was reverted to original
        server = self.os.nova.get_server(self.server_id)
        self.assertEqual(self.flavor_ref, server['flavor']['id'])
    test_resize_revert.tags = ['nova']


class SnapshotTests(tests.FunctionalTest):

    def setUp(self):
        super(SnapshotTests, self).setUp()
        self.os = openstack.Manager(self.nova)

        self.image_ref = self.glance['image_id']
        self.flavor_ref = self.nova['flavor_ref']
        self.ssh_timeout = int(self.nova['ssh_timeout'])
        self.build_timeout = int(self.nova['build_timeout'])

        self.server_name = 'stacktester1'

        expected_server = {
            'name': self.server_name,
            'imageRef': self.image_ref,
            'flavorRef': self.flavor_ref,
        }

        created_server = self.os.nova.create_server(expected_server)
        self.server_id = created_server['id']

    def tearDown(self):
        self.os.nova.delete_server(self.server_id)

    def _wait_for_server_status(self, server_id, status):
        try:
            self.os.nova.wait_for_server_status(server_id, status,
                                                timeout=self.build_timeout)
        except exceptions.TimeoutException:
            self.fail("Server failed to change status to %s" % status)

    def test_snapshot(self):
        """Create image from an existing server"""

        # Wait for server to come up before running this test
        self._wait_for_server_status(self.server_id, 'ACTIVE')

        # Create snapshot
        image_data = {'name': 'testserver_snapshot'}
        req_body = json.dumps({'createImage': image_data})
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=req_body)
        self.assertEqual(response['status'], '202')
        image_ref = response['location']
        snapshot_id = image_ref.rsplit('/', 1)[1]

        # Get snapshot and check its attributes
        resp, body = self.os.nova.request('GET', '/images/%s' % snapshot_id)
        snapshot = json.loads(body)['image']
        self.assertEqual(snapshot['name'], image_data['name'])
        server_ref = snapshot['server']['links'][0]['href']
        self.assertTrue(server_ref.endswith('/%s' % self.server_id))

        # Wait for first snapshot to start saving before making second snapshot
        self.os.nova.wait_for_image_status(snapshot['id'], 'SAVING')

        # Create second snapshot
        image_data = {'name': 'testserver_snapshot2'}
        req_body = json.dumps({'createImage': image_data})
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=req_body)
        self.assertEqual(response['status'], '409')

        # Ensure both snapshots succeed
        self.os.nova.wait_for_image_status(snapshot['id'], 'ACTIVE')

        # Cleaning up
        self.os.nova.request('DELETE', '/images/%s' % snapshot_id)
    test_snapshot.tags = ['nova']

    def test_snapshot_while_building(self):
        """Ensure inability to snapshot server in BUILD state"""

        # Ensure server is in BUILD state
        url = '/servers/%s' % self.server_id
        response, body = self.os.nova.request('GET', url)
        server = json.loads(body)['server']
        self.assertEqual(server['status'], 'BUILD', 'Server built too quickly')

        # Create snapshot
        req_body = json.dumps({'createImage': {'name': 'testserver_snapshot'}})
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=req_body)

        # KNOWN-ISSUE 885232
        self.assertEqual(response['status'], '409')
    test_snapshot_while_building.tags = ['nova']
