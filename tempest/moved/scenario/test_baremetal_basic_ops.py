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

from oslo_log import log as logging

from tempest import config
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaremetalBasicOps(manager.BaremetalScenarioTest):
    """This smoke test tests the pxe_ssh Ironic driver.

    It follows this basic set of operations:
        * Creates a keypair
        * Boots an instance using the keypair
        * Monitors the associated Ironic node for power and
          expected state transitions
        * Validates Ironic node's port data has been properly updated
        * Verifies SSH connectivity using created keypair via fixed IP
        * Associates a floating ip
        * Verifies SSH connectivity using created keypair via floating IP
        * Deletes instance
        * Monitors the associated Ironic node for power and
          expected state transitions
    """
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
        f_id = self.instance['flavor']['id']
        flavor = self.flavors_client.show_flavor(f_id)['flavor']
        ephemeral = flavor.get('OS-FLV-EXT-DATA:ephemeral')
        if not ephemeral or ephemeral == 'N/A':
            return None
        return int(ephemeral)

    def validate_ports(self):
        for port in self.get_ports(self.node['uuid']):
            n_port_id = port['extra']['vif_port_id']
            body = self.ports_client.show_port(n_port_id)
            n_port = body['port']
            self.assertEqual(n_port['device_id'], self.instance['id'])
            self.assertEqual(n_port['mac_address'], port['address'])

    @test.idempotent_id('549173a5-38ec-42bb-b0e2-c8b9f4a08943')
    @test.services('baremetal', 'compute', 'image', 'network')
    def test_baremetal_server_ops(self):
        self.add_keypair()
        self.boot_instance()
        self.validate_ports()
        ip_address = self.get_server_ip(self.instance)
        self.get_remote_client(ip_address).validate_authentication()
        vm_client = self.get_remote_client(ip_address)

        # We expect the ephemeral partition to be mounted on /mnt and to have
        # the same size as our flavor definition.
        eph_size = self.get_flavor_ephemeral_size()
        if eph_size:
            self.verify_partition(vm_client, 'ephemeral0', '/mnt', eph_size)
            # Create the test file
            self.create_timestamp(
                ip_address, private_key=self.keypair['private_key'])

        self.terminate_instance()
