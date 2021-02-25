# Copyright 2013 IBM Corp.
# All Rights Reserved.
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

from oslo_log import log

from tempest.api.compute import base
from tempest.common import compute
from tempest.common import utils
from tempest.common.utils import net_utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils.linux import remote_client
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF

LOG = log.getLogger(__name__)


class AttachInterfacesTestBase(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(AttachInterfacesTestBase, cls).skip_checks()
        if not CONF.service_available.neutron:
            raise cls.skipException("Neutron is required")
        if not CONF.compute_feature_enabled.interface_attach:
            raise cls.skipException("Interface attachment is not available.")
        if not CONF.validation.run_validation:
            raise cls.skipException('Validation should be enabled to ensure '
                                    'guest OS is running and capable of '
                                    'processing ACPI events.')

    @classmethod
    def setup_credentials(cls):
        # This test class requires network and subnet
        cls.set_network_resources(network=True, subnet=True, router=True,
                                  dhcp=True)
        super(AttachInterfacesTestBase, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(AttachInterfacesTestBase, cls).setup_clients()
        cls.subnets_client = cls.os_primary.subnets_client
        cls.ports_client = cls.os_primary.ports_client

    def _wait_for_validation(self, server, validation_resources):
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(server, validation_resources),
            self.image_ssh_user,
            self.image_ssh_password,
            validation_resources['keypair']['private_key'],
            server=server,
            servers_client=self.servers_client)
        linux_client.validate_authentication()

    def _create_server_get_interfaces(self):
        validation_resources = self.get_test_validation_resources(
            self.os_primary)
        server = self.create_test_server(
            validatable=True,
            validation_resources=validation_resources,
            wait_until='ACTIVE')
        # NOTE(mgoddard): Get detailed server to ensure addresses are present
        # in fixed IP case.
        server = self.servers_client.show_server(server['id'])['server']
        # NOTE(artom) self.create_test_server adds cleanups, but this is
        # apparently not enough? Add cleanup here.
        self.addCleanup(self.delete_server, server['id'])
        self._wait_for_validation(server, validation_resources)
        try:
            fip = set([validation_resources['floating_ip']['ip']])
        except KeyError:
            fip = ()
        ifs = (self.interfaces_client.list_interfaces(server['id'])
               ['interfaceAttachments'])
        body = waiters.wait_for_interface_status(
            self.interfaces_client, server['id'], ifs[0]['port_id'], 'ACTIVE')
        ifs[0]['port_state'] = body['port_state']
        return server, ifs, fip


class AttachInterfacesTestJSON(AttachInterfacesTestBase):
    """Test attaching interfaces"""

    def wait_for_port_detach(self, port_id):
        """Waits for the port's device_id to be unset.

        :param port_id: The id of the port being detached.
        :returns: The final port dict from the show_port response.
        """
        port = self.ports_client.show_port(port_id)['port']
        device_id = port['device_id']
        start = int(time.time())

        # NOTE(mriedem): Nova updates the port's device_id to '' rather than
        # None, but it's not contractual so handle Falsey either way.
        while device_id:
            time.sleep(self.build_interval)
            port = self.ports_client.show_port(port_id)['port']
            device_id = port['device_id']

            timed_out = int(time.time()) - start >= self.build_timeout

            if device_id and timed_out:
                message = ('Port %s failed to detach (device_id %s) within '
                           'the required time (%s s).' %
                           (port_id, device_id, self.build_timeout))
                raise lib_exc.TimeoutException(message)

        return port

    def _check_interface(self, iface, server_id=None, port_id=None,
                         network_id=None, fixed_ip=None, mac_addr=None):
        if server_id:
            iface = waiters.wait_for_interface_status(
                self.interfaces_client, server_id, iface['port_id'], 'ACTIVE')
        if port_id:
            self.assertEqual(iface['port_id'], port_id)
        if network_id:
            self.assertEqual(iface['net_id'], network_id)
        if fixed_ip:
            self.assertEqual(iface['fixed_ips'][0]['ip_address'], fixed_ip)
        if mac_addr:
            self.assertEqual(iface['mac_addr'], mac_addr)

    def _test_create_interface(self, server):
        iface = (self.interfaces_client.create_interface(server['id'])
                 ['interfaceAttachment'])
        iface = waiters.wait_for_interface_status(
            self.interfaces_client, server['id'], iface['port_id'], 'ACTIVE')
        return iface

    def _test_create_interface_by_network_id(self, server, ifs):
        network_id = ifs[0]['net_id']
        iface = self.interfaces_client.create_interface(
            server['id'], net_id=network_id)['interfaceAttachment']
        self._check_interface(iface, server_id=server['id'],
                              network_id=network_id)
        return iface

    def _test_create_interface_by_port_id(self, server, ifs):
        network_id = ifs[0]['net_id']
        port = self.ports_client.create_port(
            network_id=network_id,
            name=data_utils.rand_name(self.__class__.__name__))
        port_id = port['port']['id']
        self.addCleanup(self.ports_client.delete_port, port_id)
        iface = self.interfaces_client.create_interface(
            server['id'], port_id=port_id)['interfaceAttachment']
        self._check_interface(iface, server_id=server['id'], port_id=port_id,
                              network_id=network_id)
        return iface

    def _test_create_interface_by_fixed_ips(self, server, ifs):
        network_id = ifs[0]['net_id']
        subnet_id = ifs[0]['fixed_ips'][0]['subnet_id']
        ip_list = net_utils.get_unused_ip_addresses(self.ports_client,
                                                    self.subnets_client,
                                                    network_id,
                                                    subnet_id,
                                                    1)

        fixed_ips = [{'ip_address': ip_list[0]}]
        iface = self.interfaces_client.create_interface(
            server['id'], net_id=network_id,
            fixed_ips=fixed_ips)['interfaceAttachment']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.ports_client.delete_port,
                        iface['port_id'])
        self._check_interface(iface, server_id=server['id'],
                              fixed_ip=ip_list[0])
        return iface

    def _test_show_interface(self, server, ifs):
        iface = ifs[0]
        _iface = self.interfaces_client.show_interface(
            server['id'], iface['port_id'])['interfaceAttachment']
        self._check_interface(iface, port_id=_iface['port_id'],
                              network_id=_iface['net_id'],
                              fixed_ip=_iface['fixed_ips'][0]['ip_address'],
                              mac_addr=_iface['mac_addr'])

    def _test_delete_interface(self, server, ifs):
        # NOTE(danms): delete not the first or last, but one in the middle
        iface = ifs[1]
        self.interfaces_client.delete_interface(server['id'], iface['port_id'])
        _ifs = (self.interfaces_client.list_interfaces(server['id'])
                ['interfaceAttachments'])
        start = int(time.time())

        while len(ifs) == len(_ifs):
            time.sleep(self.build_interval)
            _ifs = (self.interfaces_client.list_interfaces(server['id'])
                    ['interfaceAttachments'])
            timed_out = int(time.time()) - start >= self.build_timeout
            if len(ifs) == len(_ifs) and timed_out:
                message = ('Failed to delete interface within '
                           'the required time: %s sec.' % self.build_timeout)
                raise lib_exc.TimeoutException(message)

        self.assertNotIn(iface['port_id'], [i['port_id'] for i in _ifs])
        return _ifs

    def _compare_iface_list(self, list1, list2):
        # NOTE(danms): port_state will likely have changed, so just
        # confirm the port_ids are the same at least
        list1 = [x['port_id'] for x in list1]
        list2 = [x['port_id'] for x in list2]

        self.assertEqual(sorted(list1), sorted(list2))

    @decorators.idempotent_id('73fe8f02-590d-4bf1-b184-e9ca81065051')
    @utils.services('network')
    def test_create_list_show_delete_interfaces_by_network_port(self):
        """Test create/list/show/delete interfaces by network port"""
        server, ifs, _ = self._create_server_get_interfaces()
        interface_count = len(ifs)
        self.assertGreater(interface_count, 0)

        try:
            iface = self._test_create_interface(server)
        except lib_exc.BadRequest as e:
            msg = ('Multiple possible networks found, use a Network ID to be '
                   'more specific.')
            if not CONF.compute.fixed_network_name and str(e) == msg:
                raise
        else:
            ifs.append(iface)

        iface = self._test_create_interface_by_network_id(server, ifs)
        ifs.append(iface)

        iface = self._test_create_interface_by_port_id(server, ifs)
        ifs.append(iface)

        _ifs = (self.interfaces_client.list_interfaces(server['id'])
                ['interfaceAttachments'])
        self._compare_iface_list(ifs, _ifs)

        self._test_show_interface(server, ifs)

        _ifs = self._test_delete_interface(server, ifs)
        self.assertEqual(len(ifs) - 1, len(_ifs))

    @decorators.idempotent_id('d290c06c-f5b3-11e7-8ec8-002293781009')
    @utils.services('network')
    def test_create_list_show_delete_interfaces_by_fixed_ip(self):
        """Test create/list/show/delete interfaces by fixed ip"""
        # NOTE(zhufl) By default only project that is admin or network owner
        # or project with role advsvc is authorised to create interfaces with
        # fixed-ip, so if we don't create network for each project, do not
        # test _test_create_interface_by_fixed_ips.
        if not (CONF.auth.use_dynamic_credentials and
                CONF.auth.create_isolated_networks and
                not CONF.network.shared_physical_network):
            raise self.skipException("Only owner network supports "
                                     "creating interface by fixed ip.")

        server, ifs, _ = self._create_server_get_interfaces()
        interface_count = len(ifs)
        self.assertGreater(interface_count, 0)

        iface = self._test_create_interface_by_fixed_ips(server, ifs)
        ifs.append(iface)

        _ifs = (self.interfaces_client.list_interfaces(server['id'])
                ['interfaceAttachments'])
        self._compare_iface_list(ifs, _ifs)

        self._test_show_interface(server, ifs)

        _ifs = self._test_delete_interface(server, ifs)
        self.assertEqual(len(ifs) - 1, len(_ifs))

    @decorators.idempotent_id('2f3a0127-95c7-4977-92d2-bc5aec602fb4')
    def test_reassign_port_between_servers(self):
        """Tests reassigning port between servers

        1. Create a port in Neutron.
        2. Create two servers in Nova.
        3. Attach the port to the first server.
        4. Detach the port from the first server.
        5. Attach the port to the second server.
        6. Detach the port from the second server.
        """
        network = self.get_tenant_network()
        network_id = network['id']
        port = self.ports_client.create_port(
            network_id=network_id,
            name=data_utils.rand_name(self.__class__.__name__))
        port_id = port['port']['id']
        self.addCleanup(self.ports_client.delete_port, port_id)

        # NOTE(artom) We create two servers one at a time because
        # create_test_server doesn't support multiple validatable servers.
        validation_resources = self.get_test_validation_resources(
            self.os_primary)

        def _create_validatable_server():
            _, servers = compute.create_test_server(
                self.os_primary, tenant_network=network,
                wait_until='ACTIVE', validatable=True,
                validation_resources=validation_resources)
            return servers[0]

        servers = [_create_validatable_server(), _create_validatable_server()]

        # add our cleanups for the servers since we bypassed the base class
        for server in servers:
            self.addCleanup(self.delete_server, server['id'])

        for server in servers:
            # NOTE(mgoddard): Get detailed server to ensure addresses are
            # present in fixed IP case.
            server = self.servers_client.show_server(server['id'])['server']
            self._wait_for_validation(server, validation_resources)
            # attach the port to the server
            iface = self.interfaces_client.create_interface(
                server['id'], port_id=port_id)['interfaceAttachment']
            self._check_interface(iface, server_id=server['id'],
                                  port_id=port_id)

            # detach the port from the server; this is a cast in the compute
            # API so we have to poll the port until the device_id is unset.
            self.interfaces_client.delete_interface(server['id'], port_id)
            self.wait_for_port_detach(port_id)


class AttachInterfacesUnderV243Test(AttachInterfacesTestBase):
    """Test attaching interfaces with compute microversion less than 2.44"""

    max_microversion = '2.43'

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('c7e0e60b-ee45-43d0-abeb-8596fd42a2f9')
    @utils.services('network')
    def test_add_remove_fixed_ip(self):
        """Test adding and removing fixed ip from server"""
        # NOTE(zhufl) By default only project that is admin or network owner
        # or project with role advsvc is authorised to add interfaces with
        # fixed-ip, so if we don't create network for each project, do not
        # test
        if not (CONF.auth.use_dynamic_credentials and
                CONF.auth.create_isolated_networks and
                not CONF.network.shared_physical_network):
            raise self.skipException("Only owner network supports "
                                     "creating interface by fixed ip.")
        # Add and Remove the fixed IP to server.
        server, ifs, fip = self._create_server_get_interfaces()
        original_interface_count = len(ifs)  # This is the number of ports.
        self.assertGreater(original_interface_count, 0)
        # Get the starting list of IPs on the server.
        addresses = self.os_primary.servers_client.list_addresses(
            server['id'])['addresses']
        # There should be one entry for the single network mapped to a list of
        # addresses, which at this point should have at least one entry.
        # Note that we could start with two addresses depending on how tempest
        # is configured for using floating IPs.
        self.assertEqual(1, len(addresses), addresses)  # number of networks
        # Keep track of the original addresses so we can know which IP is new.
        original_ips = [addr['addr'] for addr in list(addresses.values())[0]]
        # Make sure the floating IP possibly assigned during
        # server creation is always present in the set of original ips.
        original_ips = set(original_ips).union(fip)
        original_ip_count = len(original_ips)
        self.assertGreater(original_ip_count, 0, addresses)  # at least 1
        network_id = ifs[0]['net_id']
        # Add another fixed IP to the server. This should result in another
        # fixed IP on the same network (and same port since we only have one
        # port).
        self.servers_client.add_fixed_ip(server['id'], networkId=network_id)

        def _wait_for_ip_change(expected_count):
            _addresses = self.os_primary.servers_client.list_addresses(
                server['id'])['addresses']
            _ips = set([addr['addr'] for addr in list(_addresses.values())[0]])
            # Make sure possible floating ip is always present in the set.
            _ips = _ips.union(fip)
            LOG.debug("Wait for change of IPs. All IPs still associated to "
                      "the server %(id)s: %(ips)s",
                      {'id': server['id'], 'ips': _ips})
            return len(_ips) == expected_count

        # Wait for the ips count to increase by one.
        if not test_utils.call_until_true(
                _wait_for_ip_change, CONF.compute.build_timeout,
                CONF.compute.build_interval, original_ip_count + 1):
            raise lib_exc.TimeoutException(
                'Timed out while waiting for IP count to increase.')

        # Remove the fixed IP that we just added.
        server_detail = self.os_primary.servers_client.show_server(
            server['id'])['server']
        # Get the Fixed IP from server.
        fixed_ip = None
        for ip_set in server_detail['addresses']:
            for ip in server_detail['addresses'][ip_set]:
                if (ip['OS-EXT-IPS:type'] == 'fixed' and
                        ip['addr'] not in original_ips):
                    fixed_ip = ip['addr']
                    break
            if fixed_ip is not None:
                break
        self.servers_client.remove_fixed_ip(server['id'], address=fixed_ip)
        # Wait for the interface count to decrease by one.
        if not test_utils.call_until_true(
                _wait_for_ip_change, CONF.compute.build_timeout,
                CONF.compute.build_interval, original_ip_count):
            raise lib_exc.TimeoutException(
                'Timed out while waiting for IP count to decrease.')


class AttachInterfacesV270Test(AttachInterfacesTestBase):
    """Test interface API with microversion greater than 2.69"""
    min_microversion = '2.70'

    @decorators.idempotent_id('2853f095-8277-4067-92bd-9f10bd4f8e0c')
    @utils.services('network')
    def test_create_get_list_interfaces(self):
        """Test interface API with microversion greater than 2.69

        Checking create, get, list interface APIs response schema.
        """
        server = self.create_test_server(wait_until='ACTIVE')
        try:
            iface = self.interfaces_client.create_interface(server['id'])[
                'interfaceAttachment']
            iface = waiters.wait_for_interface_status(
                self.interfaces_client, server['id'], iface['port_id'],
                'ACTIVE')
        except lib_exc.BadRequest as e:
            msg = ('Multiple possible networks found, use a Network ID to be '
                   'more specific.')
            if not CONF.compute.fixed_network_name and str(e) == msg:
                raise
        else:
            # just to check the response schema
            self.interfaces_client.show_interface(
                server['id'], iface['port_id'])
            self.interfaces_client.list_interfaces(server['id'])
