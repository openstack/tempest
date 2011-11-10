
import base64
import datetime
import json
import os

from kong import openstack
from kong import exceptions
from kong import tests
from kong.common import ssh
from kong.common import utils


class ServersTest(tests.FunctionalTest):
    def setUp(self):
        super(ServersTest, self).setUp()
        self.os = openstack.Manager(self.nova)
        self.image_ref = self.glance['image_id']
        self.flavor_ref = self.nova['flavor_ref']
        self.ssh_timeout = self.nova['ssh_timeout']
        self.build_timeout = self.nova['build_timeout']

    def tearDown(self):
        if getattr(self, 'server_id', False):
            self.os.nova.delete_server(self.server_id)

    def _assert_created_server_entity(self, created_server):
        actual_keys = set(created_server.keys())
        expected_keys = set((
            'id',
            'adminPass',
            'links',
        ))
        print actual_keys
        print expected_keys
        self.assertTrue(expected_keys <= actual_keys)
        self._assert_server_links(created_server)

    def _assert_server_entity(self, server):
        actual_keys = set(server.keys())
        expected_keys = set((
            'accessIPv4',
            'accessIPv6',
            'addresses',
            'created',
            'flavor',
            'hostId',
            'id',
            'image',
            'links',
            'metadata',
            'name',
            'progress',
            'status',
            'updated',
        ))
        self.assertTrue(expected_keys <= actual_keys)
        self._assert_server_links(server)

    def _assert_server_links(self, server):
        server_id = str(server['id'])
        host = self.nova['host']
        port = self.nova['port']
        api_url = '%s:%s' % (host, port)
        base_url = os.path.join(api_url, self.nova['apiver'])

        self_link = 'http://' + os.path.join(base_url,
                                             self.os.nova.project_id,
                                             'servers', server_id)
        bookmark_link = 'http://' + os.path.join(api_url,
                                            self.os.nova.project_id,
                                            'servers', server_id)

        expected_links = [
            {
                'rel': 'self',
                'href': self_link,
            },
            {
                'rel': 'bookmark',
                'href': bookmark_link,
            },
        ]

        self.assertEqual(server['links'], expected_links)

    def test_build_update_delete(self):
        """Build and delete a server"""

        server_password = 'testpwd'

        expected_server = {
            'name': 'testserver',
            'imageRef': self.image_ref,
            'flavorRef': self.flavor_ref,
            'metadata': {'testEntry': 'testValue'},
        }

        post_body = json.dumps({'server': expected_server})
        response, body = self.os.nova.request('POST',
                                              '/servers',
                                              body=post_body)

        # Ensure attributes were returned
        self.assertEqual(response.status, 202)
        _body = json.loads(body)
        self.assertEqual(_body.keys(), ['server'])
        created_server = _body['server']
        admin_pass = created_server['adminPass']
        self._assert_created_server_entity(created_server)
        self.server_id = created_server['id']

        # Get server again and ensure attributes stuck
        server = self.os.nova.get_server(self.server_id)
        self._assert_server_entity(server)
        self.assertEqual(server['name'], expected_server['name'])
        self.assertEqual(server['accessIPv4'], '')
        self.assertEqual(server['accessIPv6'], '')
        self.assertEqual(server['metadata'], {'testEntry': 'testValue'})

        # Parse last-updated time
        update_time = utils.load_isotime(server['created'])

        # Ensure server not returned with future changes-since
        future_time = utils.dump_isotime(update_time + datetime.timedelta(100))
        params = 'changes-since=%s' % future_time
        response, body = self.os.nova.request('GET', '/servers?%s' % params)
        servers = json.loads(body)['servers']
        self.assertTrue(len(servers) == 0)

        # Ensure server is returned with past changes-since
        future_time = utils.dump_isotime(update_time - datetime.timedelta(1))
        params = 'changes-since=%s' % future_time
        response, body = self.os.nova.request('GET', '/servers?%s' % params)
        servers = json.loads(body)['servers']
        server_ids = map(lambda x: x['id'], servers)
        self.assertTrue(self.server_id in server_ids)

        # Update name
        new_name = 'testserver2'
        new_server = {'name': new_name}
        put_body = json.dumps({'server': new_server})
        url = '/servers/%s' % self.server_id
        resp, body = self.os.nova.request('PUT', url, body=put_body)

        # Output from update should be a full server
        self.assertEqual(resp.status, 200)
        data = json.loads(body)
        self.assertEqual(data.keys(), ['server'])
        self._assert_server_entity(data['server'])
        self.assertEqual(new_name, data['server']['name'])

        # Check that name was changed
        updated_server = self.os.nova.get_server(self.server_id)
        self._assert_server_entity(updated_server)
        self.assertEqual(new_name, updated_server['name'])

        # Update accessIPv4
        new_server = {'accessIPv4': '192.168.0.200'}
        put_body = json.dumps({'server': new_server})
        url = '/servers/%s' % self.server_id
        resp, body = self.os.nova.request('PUT', url, body=put_body)

        # Output from update should be a full server
        self.assertEqual(resp.status, 200)
        data = json.loads(body)
        self.assertEqual(data.keys(), ['server'])
        self._assert_server_entity(data['server'])
        self.assertEqual('192.168.0.200', data['server']['accessIPv4'])

        # Check that accessIPv4 was changed
        updated_server = self.os.nova.get_server(self.server_id)
        self._assert_server_entity(updated_server)
        self.assertEqual('192.168.0.200', updated_server['accessIPv4'])

        # Update accessIPv6
        new_server = {'accessIPv6': 'feed::beef'}
        put_body = json.dumps({'server': new_server})
        url = '/servers/%s' % self.server_id
        resp, body = self.os.nova.request('PUT', url, body=put_body)

	# Output from update should be a full server
        self.assertEqual(resp.status, 200)
        data = json.loads(body)
        self.assertEqual(data.keys(), ['server'])
        self._assert_server_entity(data['server'])
        self.assertEqual('feed::beef', data['server']['accessIPv6'])

        # Check that accessIPv6 was changed
        updated_server = self.os.nova.get_server(self.server_id)
        self._assert_server_entity(updated_server)
        self.assertEqual('feed::beef', updated_server['accessIPv6'])

        # Check metadata subresource
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)

        result = json.loads(body)
        expected = {'metadata': {'testEntry': 'testValue'}}
        self.assertEqual(expected, result)

        # Ensure metadata container can be modified
        expected = {
            'metadata': {
                'new_meta1': 'new_value1',
                'new_meta2': 'new_value2',
            },
        }
        post_body = json.dumps(expected)
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        expected['metadata']['testEntry'] = 'testValue'
        self.assertEqual(expected, result)

        # Ensure values stick
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertEqual(expected, result)

	# Ensure metadata container can be overwritten
        expected = {
            'metadata': {
                'new_meta3': 'new_value3',
                'new_meta4': 'new_value4',
            },
        }
        url = '/servers/%s/metadata' % self.server_id
        post_body = json.dumps(expected)
        response, body = self.os.nova.request('PUT', url, body=post_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertEqual(expected, result)

        # Ensure values stick
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertEqual(expected, result)

        # Set specific key
        expected_meta = {'meta': {'new_meta5': 'new_value5'}}
        put_body = json.dumps(expected_meta)
        url = '/servers/%s/metadata/new_meta5' % self.server_id
        response, body = self.os.nova.request('PUT', url, body=put_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertDictEqual(expected_meta, result)

        # Ensure value sticks
        expected_metadata = {
            'metadata': {
                'new_meta3': 'new_value3',
                'new_meta4': 'new_value4',
                'new_meta5': 'new_value5',
            },
        }
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        result = json.loads(body)
        self.assertDictEqual(expected_metadata, result)

        # Update existing key
        expected_meta = {'meta': {'new_meta4': 'new_value6'}}
        put_body = json.dumps(expected_meta)
        url = '/servers/%s/metadata/new_meta4' % self.server_id
        response, body = self.os.nova.request('PUT', url, body=put_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertEqual(expected_meta, result)

         # Ensure value sticks
        expected_metadata = {
            'metadata': {
                'new_meta3': 'new_value3',
                'new_meta4': 'new_value6',
                'new_meta5': 'new_value5',
            },
        }
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        result = json.loads(body)
        self.assertDictEqual(expected_metadata, result)

        # Delete a certain key
        url = '/servers/%s/metadata/new_meta3' % self.server_id
        response, body = self.os.nova.request('DELETE', url)
        self.assertEquals(204, response.status)

        # Make sure the key is gone
        url = '/servers/%s/metadata/new_meta3' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEquals(404, response.status)

        # Delete a nonexistant key
        url = '/servers/%s/metadata/new_meta3' % self.server_id
        response, body = self.os.nova.request('DELETE', url)
        self.assertEquals(404, response.status)

        # Wait for instance to boot
        self.os.nova.wait_for_server_status(self.server_id,
                                            'ACTIVE',
                                            timeout=self.build_timeout)

        # Look for 'addresses' attribute on server
        url = '/servers/%s' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response.status, 200)
        body = json.loads(body)
        self.assertTrue('addresses' in body['server'].keys())
        server_addresses = body['server']['addresses']

        # Addresses should be available from subresource
        url = '/servers/%s/ips' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response.status, 200)
        body = json.loads(body)
        self.assertEqual(body.keys(), ['addresses'])
        ips_addresses = body['addresses']

        # Ensure both resources return identical information
        self.assertEqual(server_addresses, ips_addresses)

        # Validate entities within network containers
        for (network, network_data) in ips_addresses.items():
            url = '/servers/%s/ips/%s' % (self.server_id, network)
            response, body = self.os.nova.request('GET', url)
            self.assertEqual(response.status, 200)
            body = json.loads(body)
            self.assertEqual(body.keys(), [network])
            self.assertEqual(body[network], network_data)

            # Check each IP entity
            for ip_data in network_data:
                self.assertEqual(set(ip_data.keys()), set(['addr', 'version']))

        # Find IP of server
        try:
            (_, network) = server_addresses.items()[0]
            ip = network[0]['addr']
        except KeyError:
            self.fail("Failed to retrieve IP address from server entity")

        # Assert password works
        if int(self.nova['ssh_timeout']) > 0:
            client = ssh.Client(ip, 'root', admin_pass, self.ssh_timeout)
            self.assertTrue(client.test_connection_auth())

        self.os.nova.delete_server(self.server_id)

        # Poll server until deleted
        try:
            url = '/servers/%s' % self.server_id
            self.os.nova.poll_request_status('GET', url, 404)
        except exceptions.TimeoutException:
            self.fail("Server deletion timed out")
    test_build_update_delete.tags = ['nova']

    def test_build_with_password_and_file(self):
        """Build a server with a custom password and an injected file"""

        file_contents = 'testing'

        expected_server = {
            'name': 'testserver',
            'metadata': {
                'key1': 'value1',
                'key2': 'value2',
            },
            'personality': [
                {
                    'path': '/etc/test.txt',
                    'contents': base64.b64encode(file_contents),
                },
            ],
            'imageRef': self.image_ref,
            'flavorRef': self.flavor_ref,
            'adminPass': 'secrete',
        }

        post_body = json.dumps({'server': expected_server})
        response, body = self.os.nova.request('POST',
                                              '/servers',
                                              body=post_body)

        self.assertEqual(response.status, 202)

        _body = json.loads(body)
        self.assertEqual(_body.keys(), ['server'])
        created_server = _body['server']
        self.server_id = _body['server']['id']

        admin_pass = created_server['adminPass']
        self.assertEqual(expected_server['adminPass'], admin_pass)
        self._assert_created_server_entity(created_server)
        self.assertEqual(expected_server['metadata'], {
            'key1': 'value1',
            'key2': 'value2',
        })

        self.os.nova.wait_for_server_status(created_server['id'],
                                            'ACTIVE',
                                            timeout=self.build_timeout)

        server = self.os.nova.get_server(created_server['id'])

        # Find IP of server
        try:
            (_, network) = server['addresses'].popitem()
            ip = network[0]['addr']
        except KeyError:
            self.fail("Failed to retrieve IP address from server entity")

        # Assert injected file is on instance, also verifying password works
        if int(self.nova['ssh_timeout']) > 0:
            client = ssh.Client(ip, 'root', admin_pass, self.ssh_timeout)
            injected_file = client.exec_command('cat /etc/test.txt')
            self.assertEqual(injected_file, file_contents)
    test_build_with_password_and_file.tags = ['nova']

    def test_delete_while_building(self):
        """Delete a server while building"""

        # Make create server request
        server = {
            'name' : 'testserver',
            'imageRef' : self.image_ref,
            'flavorRef' : self.flavor_ref,
        }
        created_server = self.os.nova.create_server(server)

        # Server should immediately be accessible, but in have building status
        server = self.os.nova.get_server(created_server['id'])
        self.assertEqual(server['status'], 'BUILD')

        self.os.nova.delete_server(created_server['id'])

        # Poll server until deleted
        try:
            url = '/servers/%s' % created_server['id']
            self.os.nova.poll_request_status('GET', url, 404)
        except exceptions.TimeoutException:
            self.fail("Server deletion timed out")
    test_delete_while_building.tags = ['nova']

    def test_create_with_invalid_image(self):
        """Create a server with an unknown image"""

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : -1,
                'flavorRef' : self.flavor_ref,
            }
        })

        resp, body = self.os.nova.request('POST', '/servers', body=post_body)

        self.assertEqual(400, resp.status)

        fault = json.loads(body)
        expected_fault = {
            "badRequest": {
                "message": "Cannot find requested image",
                "code": 400,
            },
        }
        # KNOWN-ISSUE - The error message is confusing and should be improved
        #self.assertEqual(fault, expected_fault)
    test_create_with_invalid_image.tags = ['nova']

    def test_create_with_invalid_flavor(self):
        """Create a server with an unknown flavor"""

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : -1,
            }
        })

        resp, body = self.os.nova.request('POST', '/servers', body=post_body)

        self.assertEqual(400, resp.status)

        fault = json.loads(body)
        expected_fault = {
            "badRequest": {
                "message": "Cannot find requested flavor",
                "code": 400,
            },
        }
        # KNOWN-ISSUE lp804084
        #self.assertEqual(fault, expected_fault)
    test_create_with_invalid_flavor.tags = ['nova']
