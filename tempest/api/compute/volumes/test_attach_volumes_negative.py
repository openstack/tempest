import testtools
import uuid

from tempest.api.compute import base
from tempest.common.utils.linux import remote_client
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF

class AttachVolumeNegativeTestJSON(base.BaseV2ComputeTest):
    def __init__(self, *args, **kwargs):
        super(AttachVolumeNegativeTestJSON, self).__init__(*args, **kwargs)
        self.server = None
        self.volume = None
        self.attached = False

    @classmethod
    def setUpClass(cls):
        cls.prepare_instance_network()
        super(AttachVolumeNegativeTestJSON, cls).setUpClass()
        cls.device = CONF.compute.volume_device_name
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    def _detach(self, server_id, volume_id):
        if self.attached:
            self.servers_client.detach_volume(server_id, volume_id)
            self.volumes_client.wait_for_volume_status(volume_id, 'available')

    def _delete_volume(self):
        if self.volume:
            self.volumes_client.delete_volume(self.volume['id'])
            self.volume = None

    def _create_sever_and_volume(self):
        # Start a server and wait for it to become ready
        admin_pass = self.image_ssh_password
        _, self.server = self.create_test_server(wait_until='ACTIVE',
                                                 adminPass=admin_pass)

        # Record addresses so that we can ssh later
        _, self.server['addresses'] = \
            self.servers_client.list_addresses(self.server['id'])

        # Create a volume and wait for it to become ready
        _, self.volume = self.volumes_client.create_volume(
            1, display_name='test')
        self.addCleanup(self._delete_volume)
        self.volumes_client.wait_for_volume_status(self.volume['id'],
                                                   'available')


    @testtools.skipUnless(CONF.compute.run_ssh, 'SSH required for this test')
    @test.attr(type=['negative', 'gate'])
    def test_attach_detach_volume_with_empty_volume_id(self):
        self._create_sever_and_volume()
        self.servers_client.stop(self.server['id'])
        self.servers_client.wait_for_server_status(self.server['id'],
                                                   'SHUTOFF')
        self.servers_client.start(self.server['id'])
        self.servers_client.wait_for_server_status(self.server['id'], 'ACTIVE')

        server_id=self.server['id']
        self.assertRaises(exceptions.BadRequest, self.servers_client.attach_volume,
                          server_id, '')

        self.assertRaises(exceptions.NotFound, self.servers_client.detach_volume,
                          server_id, '')


    @testtools.skipUnless(CONF.compute.run_ssh, 'SSH required for this test') 
    @test.attr(type=['negative', 'gate'])
    def test_get_list_volume_attach_with_nonexistent_server_id(self):
	self._create_sever_and_volume()
	server_id='&%&'
	self.assertRaises(exceptions.NotFound, self.servers_client.list_volume_attachment,
			server_id)
	self.assertRaises(exceptions.NotFound, self.servers_client.get_volume_attachment,
			server_id, self.volume['id'])









