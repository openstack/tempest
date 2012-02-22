from nose.plugins.attrib import attr
import unittest2 as unittest
from tempest import openstack
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions


class ServerAddressesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.servers_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref

        cls.name = rand_name('server')
        resp, cls.server = cls.client.create_server(cls.name,
                                                 cls.image_ref,
                                                 cls.flavor_ref)
        cls.client.wait_for_server_status(cls.server['id'], 'ACTIVE')

    @classmethod
    def tearDownClass(cls):
        cls.client.delete_server(cls.server['id'])

    @attr(type='negative', category='server-addresses')
    def test_list_server_addresses_invalid_server_id(self):
        """List addresses request should fail if server id not in system"""

        try:
            self.client.list_addresses('999')
        except exceptions.NotFound:
            pass
        else:
            self.fail('The server rebuild for a non existing server should not'
                      ' be allowed')

    @attr(type='negative', category='server-addresses')
    def test_list_server_addresses_by_network_neg(self):
        """List addresses by network should fail if network name not valid"""

        try:
            self.client.list_addresses_by_network(self.server['id'], 'invalid')
        except exceptions.NotFound:
            pass
        else:
            self.fail('The server rebuild for a non existing server should not'
                      ' be allowed')

    @attr(type='smoke', category='server-addresses')
    def test_list_server_addresses(self):
        """All public and private addresses for
        a server should be returned"""

        resp, addresses = self.client.list_addresses(self.server['id'])
        self.assertEqual('200', resp['status'])

        # We do not know the exact network configuration, but an instance
        # should at least have a single public or private address
        self.assertTrue('public' in addresses and len(addresses['public']) > 0
                        or 'private' in addresses
                        and len(addresses['private']) > 0)

    @attr(type='smoke', category='server-addresses')
    def test_list_server_addresses_by_network(self):
        """Providing a network type should filter
        the addresses return by that type"""

        resp, addresses = self.client.list_addresses(self.server['id'])

        # Once again we don't know the environment's exact network config,
        # but the response for each individual network should be the same
        # as the partial result of the full address list
        id = self.server['id']
        for addr_type in addresses:
            resp, addr = self.client.list_addresses_by_network(id, addr_type)
            self.assertEqual('200', resp['status'])

            addr = addr[addr_type]
            for address in addresses[addr_type]:
                self.assertTrue(any([a for a in addr if a == address]))
