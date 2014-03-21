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


# power/provision states as of icehouse
class PowerStates(object):
    """Possible power states of an Ironic node."""
    POWER_ON = 'power on'
    POWER_OFF = 'power off'
    REBOOT = 'rebooting'
    SUSPEND = 'suspended'


class ProvisionStates(object):
    """Possible provision states of an Ironic node."""
    NOSTATE = None
    INIT = 'initializing'
    ACTIVE = 'active'
    BUILDING = 'building'
    DEPLOYWAIT = 'wait call-back'
    DEPLOYING = 'deploying'
    DEPLOYFAIL = 'deploy failed'
    DEPLOYDONE = 'deploy complete'
    DELETING = 'deleting'
    DELETED = 'deleted'
    ERROR = 'error'


class BaremetalBasicOptsPXESSH(manager.BaremetalScenarioTest):
    """
    This smoke test tests the pxe_ssh Ironic driver.  It follows this basic
    set of operations:
        * Creates a keypair
        * Boots an instance using the keypair
        * Monitors the associated Ironic node for power and
          expected state transitions
        * Validates Ironic node's driver_info has been properly
          updated
        * Validates Ironic node's port data has been properly updated
        * Verifies SSH connectivity using created keypair via fixed IP
        * Associates a floating ip
        * Verifies SSH connectivity using created keypair via floating IP
        * Deletes instance
        * Monitors the associated Ironic node for power and
          expected state transitions
    """
    def add_keypair(self):
        self.keypair = self.create_keypair()

    def add_floating_ip(self):
        floating_ip = self.compute_client.floating_ips.create()
        self.instance.add_floating_ip(floating_ip)
        return floating_ip.ip

    def verify_connectivity(self, ip=None):
        if ip:
            dest = self.get_remote_client(ip)
        else:
            dest = self.get_remote_client(self.instance)
        dest.validate_authentication()

    def validate_driver_info(self):
        f_id = self.instance.flavor['id']
        flavor_extra = self.compute_client.flavors.get(f_id).get_keys()
        driver_info = self.node.driver_info
        self.assertEqual(driver_info['pxe_deploy_kernel'],
                         flavor_extra['baremetal:deploy_kernel_id'])
        self.assertEqual(driver_info['pxe_deploy_ramdisk'],
                         flavor_extra['baremetal:deploy_ramdisk_id'])
        self.assertEqual(driver_info['pxe_image_source'],
                         self.instance.image['id'])

    def validate_ports(self):
        for port in self.get_ports(self.node.uuid):
            n_port_id = port.extra['vif_port_id']
            n_port = self.network_client.show_port(n_port_id)['port']
            self.assertEqual(n_port['device_id'], self.instance.id)
            self.assertEqual(n_port['mac_address'], port.address)

    def boot_instance(self):
        create_kwargs = {
            'key_name': self.keypair.id
        }
        self.instance = self.create_server(
            wait=False, create_kwargs=create_kwargs)

        self.set_resource('instance', self.instance)

        self.wait_node(self.instance.id)
        self.node = self.get_node(instance_id=self.instance.id)

        self.wait_power_state(self.node.uuid, PowerStates.POWER_ON)

        self.wait_provisioning_state(
            self.node.uuid,
            [ProvisionStates.DEPLOYWAIT, ProvisionStates.ACTIVE],
            timeout=15)

        self.wait_provisioning_state(self.node.uuid, ProvisionStates.ACTIVE,
                                     timeout=CONF.baremetal.active_timeout)

        self.status_timeout(
            self.compute_client.servers, self.instance.id, 'ACTIVE')

        self.node = self.get_node(instance_id=self.instance.id)
        self.instance = self.compute_client.servers.get(self.instance.id)

    def terminate_instance(self):
        self.instance.delete()
        self.remove_resource('instance')
        self.wait_power_state(self.node.uuid, PowerStates.POWER_OFF)
        self.wait_provisioning_state(
            self.node.uuid,
            ProvisionStates.NOSTATE,
            timeout=CONF.baremetal.unprovision_timeout)

    @test.services('baremetal', 'compute', 'image', 'network')
    def test_baremetal_server_ops(self):
        self.add_keypair()
        self.boot_instance()
        self.validate_driver_info()
        self.validate_ports()
        self.verify_connectivity()
        floating_ip = self.add_floating_ip()
        self.verify_connectivity(ip=floating_ip)
        self.terminate_instance()
