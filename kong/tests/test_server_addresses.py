
import json
import os

from kong import exceptions
from kong import openstack
from kong import tests


class ServerAddressesTest(tests.FunctionalTest):

    @classmethod
    def setUpClass(self):
        super(ServerAddressesTest, self).setUp()
        self.os = openstack.Manager(self.nova)
        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref

    def setUp(self):
        server = {
            'name' : 'testserver',
            'imageRef' : self.image_ref,
            'flavorRef' : self.flavor_ref,
        }

        created_server = self.os.nova.create_server(server)
        self.server_id = created_server['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

    def tearDown(self):
        self.os.nova.delete_server(self.server_id)

    def test_server_addresses(self):
        """Retrieve server addresses information"""
        url = '/servers/%s' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response.status, 200)
        body = json.loads(body)
        self.assertTrue('addresses' in body['server'].keys())
        server_addresses = body['server']['addresses']

        url = '/servers/%s/ips' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response.status, 200)
        body = json.loads(body)
        self.assertEqual(body.keys(), ['addresses'])
        ips_addresses = body['addresses']

        self.assertEqual(server_addresses, ips_addresses)

        # Now validate entities within addresses containers if available
        for (network, network_data) in ips_addresses.items():
            # Ensure we can query for each particular network
            url = '/servers/%s/ips/%s' % (self.server_id, network)
            response, body = self.os.nova.request('GET', url)
            self.assertEqual(response.status, 200)
            body = json.loads(body)
            self.assertEqual(body.keys(), [network])
            self.assertEqual(body[network], network_data)

            for ip_data in network_data:
                self.assertEqual(set(ip_data.keys()),
                                 set(['addr', 'version']))
