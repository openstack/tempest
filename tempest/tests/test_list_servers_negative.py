import re
import sys
import unittest2 as unittest
from tempest import exceptions
from base_compute_test import BaseComputeTest
from tempest import openstack
from tempest.common.utils.data_utils import rand_name


class ServerDetailsNegativeTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        cls.client = cls.servers_client
        cls.servers = []

        # Verify the alternate user is configured and not the same as the first
        cls.user1 = cls.config.compute.username
        cls.user2 = cls.config.compute.alt_username
        cls.user2_password = cls.config.compute.alt_password
        cls.user2_tenant_name = cls.config.compute.alt_tenant_name
        cls.multi_user = False

        if (not None in (cls.user2, cls.user2_password, cls.user2_tenant_name)
            and cls.user1 != cls.user2):

            try:
                cls.alt_manager = openstack.AltManager()
                cls.alt_client = cls.alt_manager.servers_client
            except exceptions.AuthenticationFailure:
                # multi_user is already set to false, just fall through
                pass
            else:
                cls.multi_user = True

    @classmethod
    def tearDownClass(cls):
        """Terminate all running instances in nova"""
        try:
            resp, body = cls.client.list_servers()
            for server in body['servers']:
                resp, body = cls.client.delete_server(server)
        except exceptions.NotFound:
            pass

    def tearDown(self):
        """Terminate instances created by tests"""
        try:
            for server in self.servers:
                resp, body = self.client.delete_server(server)
                if resp['status'] == '204':
                    self.client.wait_for_server_termination(server)
        except exceptions.NotFound:
            pass

    def get_active_servers(self, server_count):
        """Returns active test instances to calling test methods"""
        resp, body = self.client.list_servers_with_detail()
        servers = body['servers']
        active_servers = [server for server in servers if server['status'] ==
                        'ACTIVE']
        num_of_active_servers = len(active_servers)

        # Check if we already have enough active servers
        if active_servers and num_of_active_servers >= server_count:
            return active_servers[0:server_count]

        # Otherwise create the remaining shortfall of servers
        servers_needed = server_count - num_of_active_servers

        for i in range(0, servers_needed):
            srv = self.create_server()
            active_servers.append(srv)

        return active_servers

    def test_list_servers_when_no_servers_running(self):
        """Return an empty list when there are no active servers"""
        # Delete Active servers
        try:
            resp, body = self.client.list_servers()
            for server in body['servers']:
                resp, body = self.client.delete_server(server['id'])
                self.client.wait_for_server_termination(server['id'])
        except exceptions.NotFound:
            pass
        # Verify empty list
        resp, body = self.client.list_servers()
        servers = body['servers']
        self.assertEqual('200', resp['status'])
        self.assertEqual([], servers)

    def test_list_servers_with_a_deleted_server(self):
        """Create and delete a server and verify empty list"""
        server = self.get_active_servers(1)[0]

        # Delete the server
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

        # List servers and verify server not returned
        resp, body = self.client.list_servers()
        servers = body['servers']
        actual = [srv for srv in servers if srv['id'] == server['id']]
        self.assertEqual('200', resp['status'])
        self.assertEqual([], actual)

    def test_list_servers_by_existing_image(self):
        """Server list is returned for a specific image and snapshot images"""
        try:
            base_server = self.get_active_servers(1)[0]

            # Create a snapshot of the server
            snapshot_name = "%s_snapshot" % base_server['id']
            resp, body = self.client.create_image(base_server['id'],
                                                 snapshot_name)
            snapshot_url = resp['location']
            match = re.search('/images/(?P<image_id>.+)', snapshot_url)
            self.assertIsNotNone(match)
            snapshot_id = match.groupdict()['image_id']

            self.images_client.wait_for_image_status(snapshot_id, 'ACTIVE')

            # Create a server from the snapshot
            snap_server = self.create_server(image_id=snapshot_id)
            self.servers.append(snap_server['id'])

            # List base servers by image
            resp, body = self.client.list_servers({'image': self.image_ref})
            servers = body['servers']
            self.assertEqual('200', resp['status'])
            self.assertIn(base_server['id'], [server['id'] for server in
                          servers])
            self.assertTrue(len(body['servers']) > 0)

            # List snapshotted server by image
            resp, body = self.client.list_servers({'image': snapshot_id})
            servers = body['servers']
            self.assertEqual('200', resp['status'])
            self.assertIn(snap_server['id'], [server['id'] for server in
                         servers])
            self.assertEqual(1, len(body['servers']))

        finally:
            self.images_client.delete_image(snapshot_id)

    @unittest.skip("Until Bug 1002911 is fixed")
    def test_list_servers_by_non_existing_image(self):
        """Listing servers for a non existing image raises error"""
        self.assertRaises(exceptions.NotFound, self.client.list_servers,
                         {'image': '1234abcd-zzz0-aaa9-ppp3-0987654abcde'})

    @unittest.skip("Until Bug 1002911 is fixed")
    def test_list_servers_by_image_pass_overlimit_image(self):
        """Return an error while listing server with too large image id"""
        self.assertRaises(exceptions.OverLimit, self.client.list_servers,
                         {'image': sys.maxint + 1})

    @unittest.skip("Until Bug 1002911 is fixed")
    def test_list_servers_by_image_pass_negative_id(self):
        """Return an error while listing server with negative image id"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                         {'image': -1})

    def test_list_servers_by_existing_flavor(self):
        """List servers by flavor"""
        self.get_active_servers(1)

        resp, body = self.client.list_servers({'flavor': self.flavor_ref})
        self.assertEqual('200', resp['status'])
        self.assertTrue(len(body['servers']) > 0)

    @unittest.skip("Until Bug 1002918 is fixed")
    def test_list_servers_by_non_existing_flavor(self):
        """Return an error while listing server by non existing flavor"""
        self.assertRaises(exceptions.NotFound, self.client.list_servers,
                        {'flavor': 1234})

    @unittest.skip("Until Bug 1002918 is fixed")
    def test_list_servers_by_flavor_pass_overlimit_flavor(self):
        """Return an error while listing server with too large flavor value"""
        self.assertRaises(exceptions.OverLimit, self.client.list_servers,
                        {'flavor': sys.maxint + 1})

    @unittest.skip("Until Bug 1002918 is fixed")
    def test_list_servers_by_flavor_pass_negative_value(self):
        """Return an error while listing server with negative flavor value"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                         {'flavor': -1})

    def test_list_servers_by_server_name(self):
        """Returns a list of servers containing an existing server name"""
        server_name = rand_name('test-vm-')
        resp, server = self.client.create_server(server_name, self.image_ref,
                                                self.flavor_ref)
        self.servers.append(server['id'])

        resp, body = self.client.list_servers({'name': server_name})
        self.assertEqual('200', resp['status'])
        self.assertEqual(server_name, body['servers'][0]['name'])

    @unittest.skip("Until Bug 1002892 is fixed")
    def test_list_servers_by_non_existing_server_name(self):
        """Return an error while listing for a non existent server"""
        resp, body = self.client.list_servers({'name': 'junk_serv_100'})
        self.assertRaises(exceptions.NotFound, self.client.list_servers,
                          {'name': 'junk_serv_100'})

    @unittest.skip("Until Bug 1002892 is fixed")
    def test_list_servers_by_server_name_empty(self):
        """Return an error when an empty server name is passed"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                        {'name': ''})

    @unittest.skip("Until Bug 1002892 is fixed")
    def test_list_servers_by_server_name_too_large(self):
        """Return an error for a very large value for server name listing"""
        self.assertRaises(exceptions.OverLimit, self.client.list_servers,
                        {'name': 'a' * 65})

    @unittest.skip("Until Bug 1002892 is fixed")
    def test_list_servers_by_name_pass_numeric_name(self):
        """Return an error for a numeric server name listing"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                        {'name': 99})

    def test_list_servers_by_active_status(self):
        """Return a listing of servers by active status"""
        self.create_server()
        resp, body = self.client.list_servers({'status': 'ACTIVE'})
        self.assertEqual('200', resp['status'])
        self.assertTrue(len(body['servers']) > 0)

    def test_list_servers_by_building_status(self):
        """Return a listing of servers in build state"""
        server_name = rand_name('test-vm-')
        resp, server = self.client.create_server(server_name, self.image_ref,
                                                self.flavor_ref)
        self.servers.append(server['id'])
        resp, body = self.client.list_servers({'status': 'BUILD'})
        self.assertEqual('200', resp['status'])
        self.assertEqual(1, len(body['servers']))
        self.assertEqual(server['id'], body['servers'][0]['id'])

        self.client.wait_for_server_status(server['id'], 'ACTIVE')

    def test_list_servers_status_is_invalid(self):
        """Return an error when invalid status is specified"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                          {'status': 'DEAD'})

    def test_list_servers_pass_numeric_status(self):
        """Return an error when a numeric value for status is specified"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                         {'status': 1})

    def test_list_servers_by_limits(self):
        """List servers by specifying limits"""
        self.get_active_servers(2)
        resp, body = self.client.list_servers({'limit': 1})
        self.assertEqual('200', resp['status'])
        self.assertEqual(1, len(body['servers']))

    def test_list_servers_by_limits_greater_than_actual_count(self):
        """List servers by specifying a greater value for limit"""
        self.get_active_servers(2)
        resp, body = self.client.list_servers({'limit': 100})
        self.assertEqual('200', resp['status'])
        self.assertTrue(len(body['servers']) >= 2)

    def test_list_servers_by_limits_pass_string(self):
        """Return an error if a string value is passed for limit"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                         {'limit': 'testing'})

    def test_list_servers_by_limits_pass_negative_value(self):
        """Return an error if a negative value for limit is passed"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                         {'limit': -1})

    @unittest.skip("Until Bug 1002924 is fixed")
    def test_list_servers_by_limits_pass_overlimit_value(self):
        """Return an error if too large value for limit is passed"""
        self.assertRaises(exceptions.OverLimit, self.client.list_servers,
                         {'limit': sys.maxint + 1})

    def test_list_servers_by_changes_since(self):
        """Servers are listed by specifying changes-since date"""
        self.get_active_servers(2)
        resp, body = self.client.list_servers(
                         {'changes-since': '2011-01-01T12:34:00Z'})
        self.assertEqual('200', resp['status'])
        self.assertTrue(len(body['servers']) >= 2)

    def test_list_servers_by_changes_since_invalid_date(self):
        """Return an error when invalid date format is passed"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                          {'changes-since': '2011/01/01'})

    @unittest.skip("Until Bug 1002926 is fixed")
    def test_list_servers_by_changes_since_future_date(self):
        """Return an error when a date in the future is passed"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                          {'changes-since': '2051-01-01T12:34:00Z'})

    @unittest.skip("Until Bug 1002935 is fixed")
    def test_list_servers_list_another_tenant_servers(self):
        """Return an error when a user lists servers in another tenant"""
        # Create a server by a user in it's tenant
        server_name = rand_name('test-vm-')
        resp, server = self.client.create_server(server_name, self.image_ref,
                                                 self.flavor_ref)
        self.servers.append(server['id'])

        # List the servers by alternate user in the base user's tenant
        self.assertRaises(exceptions.NotFound, self.alt_client.list_servers,
                         {'name': server_name})

    def test_list_servers_detail_when_no_servers_running(self):
        """Return an empty list for servers detail when no active servers"""
        # Delete active servers
        try:
            resp, body = self.client.list_servers()
            for server in body['servers']:
                resp, body = self.client.delete_server(server['id'])
                self.client.wait_for_server_termination(server['id'])
        except exceptions.NotFound:
            pass
        # Verify empty list
        resp, body = self.client.list_servers_with_detail()
        self.assertEqual('200', resp['status'])
        servers = body['servers']
        actual = [srv for srv in servers if srv['status'] == 'ACTIVE']
        self.assertEqual([], actual)

    def test_list_servers_detail_server_is_building(self):
        """Server in Build state is listed"""
        server_name = rand_name('test-vm-')
        resp, server = self.client.create_server(server_name, self.image_ref,
                                                 self.flavor_ref)

        self.servers.append(server['id'])
        resp, body = self.client.list_servers_with_detail()
        self.assertEqual('200', resp['status'])
        self.assertEqual('BUILD', body['servers'][0]['status'])

    def test_list_servers_detail_server_is_deleted(self):
        """Server details are not listed for a deleted server"""
        server = self.get_active_servers(1)[0]

        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])
        resp, body = self.client.list_servers_with_detail()
        servers = body['servers']
        actual = [srv for srv in servers if srv['id'] == server['id']]
        self.assertEqual('200', resp['status'])
        self.assertEqual([], actual)

    def test_get_server_details_non_existent_id(self):
        """Return an error during get server details using non-existent id"""
        self.assertRaises(exceptions.NotFound, self.client.get_server,
                         'junk-123ab-45cd')

    def test_get_server_details_another_tenant_server(self):
        """Return an error when querying details of server in another tenant"""
        server_name = rand_name('test-vm-')
        resp, server = self.client.create_server(server_name, self.image_ref,
                                                 self.flavor_ref)
        self.servers.append(server['id'])
        self.assertRaises(exceptions.NotFound, self.alt_client.get_server,
                          server['id'])

    def test_get_server_details_pass_string_uuid(self):
        """Return an error when a string value is passed for uuid"""
        try:
            self.assertRaises(exceptions.NotFound, self.client.get_server,
                             'junk-server-uuid')
        except Exception as e:
            self.fail("Incorrect Exception raised: %s" % e)

    @unittest.skip("Until Bug 1002901 is fixed")
    def test_get_server_details_pass_negative_uuid(self):
        """Return an error when a negative value is passed for uuid"""
        try:
            self.assertRaises(exceptions.BadRequest, self.client.get_server,
                             -1)
        except Exception as e:
            self.fail("Incorrect Exception raised: %s" % e)

    @unittest.skip("Until Bug 1002901 is fixed")
    def test_get_server_details_pass_overlimit_length_uuid(self):
        """Return an error when a very large value is passed for uuid"""
        try:
            self.assertRaises(exceptions.OverLimit, self.client.get_server,
                              'a' * 37)
        except Exception as e:
            self.fail("Incorrect Exception raised: %s" % e)
