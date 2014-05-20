#
# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaremetalBasicOps(manager.BaremetalScenarioTest):
    """
    This smoke test tests the pxe_ssh Ironic driver.  It follows this basic
    set of operations:
        * Creates a keypair
        * Boots an instance using the keypair
        * Monitors the associated Ironic node for power and
          expected state transitions
        * Validates Ironic node's port data has been properly updated
        * Verifies SSH connectivity using created keypair via fixed IP
        * Associates a floating ip
        * Verifies SSH connectivity using created keypair via floating IP
        * Verifies instance rebuild with ephemeral partition preservation
        * Deletes instance
        * Monitors the associated Ironic node for power and
          expected state transitions
    """
    def rebuild_instance(self, preserve_ephemeral=False):
        self.rebuild_server(self.instance,
                            preserve_ephemeral=preserve_ephemeral,
                            wait=False)

        node = self.get_node(instance_id=self.instance.id)
        self.instance = self.compute_client.servers.get(self.instance.id)

        self.addCleanup_with_wait(self.compute_client.servers,
                                  self.instance.id,
                                  cleanup_callable=self.delete_wrapper,
                                  cleanup_args=[self.instance])

        # We should remain on the same node
        self.assertEqual(self.node.uuid, node.uuid)
        self.node = node

        self.status_timeout(self.compute_client.servers, self.instance.id,
                            'REBUILD')
        self.status_timeout(self.compute_client.servers, self.instance.id,
                            'ACTIVE')

    def create_remote_file(self, client, filename):
        """Create a file on the remote client connection.

        After creating the file, force a filesystem sync. Otherwise,
        if we issue a rebuild too quickly, the file may not exist.
        """
        client.exec_command('sudo touch ' + filename)
        client.exec_command('sync')

    def verify_partition(self, client, label, mount, gib_size):
        """Verify a labeled partition's mount point and size."""
        LOG.info("Looking for partition %s mounted on %s" % (label, mount))

        # Validate we have a device with the given partition label
        cmd = "/sbin/blkid | grep '%s' | cut -d':' -f1" % label
        device = client.exec_command(cmd).rstrip('\n')
        LOG.debug("Partition device is %s" % device)
        self.assertNotEqual('', device)

        # Validate the mount point for the device
        cmd = "mount | grep '%s' | cut -d' ' -f3" % device
        actual_mount = client.exec_command(cmd).rstrip('\n')
        LOG.debug("Partition mount point is %s" % actual_mount)
        self.assertEqual(actual_mount, mount)

        # Validate the partition size matches what we expect
        numbers = '0123456789'
        devnum = device.replace('/dev/', '')
        cmd = "cat /sys/block/%s/%s/size" % (devnum.rstrip(numbers), devnum)
        num_bytes = client.exec_command(cmd).rstrip('\n')
        num_bytes = int(num_bytes) * 512
        actual_gib_size = num_bytes / (1024 * 1024 * 1024)
        LOG.debug("Partition size is %d GiB" % actual_gib_size)
        self.assertEqual(actual_gib_size, gib_size)

    def get_flavor_ephemeral_size(self):
        """Returns size of the ephemeral partition in GiB."""
        f_id = self.instance.flavor['id']
        ephemeral = self.compute_client.flavors.get(f_id).ephemeral
        if ephemeral != 'N/A':
            return int(ephemeral)
        return None

    def add_floating_ip(self):
        floating_ip = self.compute_client.floating_ips.create()
        self.instance.add_floating_ip(floating_ip)
        return floating_ip.ip

    def validate_ports(self):
        for port in self.get_ports(self.node.uuid):
            n_port_id = port.extra['vif_port_id']
            n_port = self.network_client.show_port(n_port_id)['port']
            self.assertEqual(n_port['device_id'], self.instance.id)
            self.assertEqual(n_port['mac_address'], port.address)

    @test.services('baremetal', 'compute', 'image', 'network')
    def test_baremetal_server_ops(self):
        test_filename = '/mnt/rebuild_test.txt'
        self.add_keypair()
        self.boot_instance()
        self.validate_ports()
        self.verify_connectivity()
        floating_ip = self.add_floating_ip()
        self.verify_connectivity(ip=floating_ip)

        vm_client = self.get_remote_client(self.instance)

        # We expect the ephemeral partition to be mounted on /mnt and to have
        # the same size as our flavor definition.
        eph_size = self.get_flavor_ephemeral_size()
        self.assertIsNotNone(eph_size)
        self.verify_partition(vm_client, 'ephemeral0', '/mnt', eph_size)

        # Create the test file
        self.create_remote_file(vm_client, test_filename)

        # Rebuild and preserve the ephemeral partition
        self.rebuild_instance(True)
        self.verify_connectivity()

        # Check that we maintained our data
        vm_client = self.get_remote_client(self.instance)
        self.verify_partition(vm_client, 'ephemeral0', '/mnt', eph_size)
        vm_client.exec_command('ls ' + test_filename)

        self.terminate_instance()
