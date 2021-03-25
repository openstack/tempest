# Copyright (c) 2019 Ericsson
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

import testtools

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.scenario import manager


CONF = config.CONF


class MinBwAllocationPlacementTest(manager.NetworkScenarioTest):
    credentials = ['primary', 'admin']
    required_extensions = ['port-resource-request',
                           'qos',
                           'qos-bw-minimum-ingress']
    # The feature QoS minimum bandwidth allocation in Placement API depends on
    # Granular resource requests to GET /allocation_candidates and Support
    # allocation candidates with nested resource providers features in
    # Placement (see: https://specs.openstack.org/openstack/nova-specs/specs/
    # stein/approved/bandwidth-resource-provider.html#rest-api-impact) and this
    # means that the minimum placement microversion is 1.29
    placement_min_microversion = '1.29'
    placement_max_microversion = 'latest'

    # Nova rejects to boot VM with port which has resource_request field, below
    # microversion 2.72
    compute_min_microversion = '2.72'
    compute_max_microversion = 'latest'

    INGRESS_RESOURCE_CLASS = "NET_BW_IGR_KILOBIT_PER_SEC"
    INGRESS_DIRECTION = 'ingress'

    SMALLEST_POSSIBLE_BW = 1
    # For any realistic inventory value (that is inventory != MAX_INT) an
    # allocation candidate request of MAX_INT is expected to be rejected, see:
    # https://github.com/openstack/placement/blob/master/placement/
    # db/constants.py#L16
    PLACEMENT_MAX_INT = 0x7FFFFFFF
    BANDWIDTH_1 = 1000
    BANDWIDTH_2 = 2000

    @classmethod
    def setup_clients(cls):
        super(MinBwAllocationPlacementTest, cls).setup_clients()
        cls.placement_client = cls.os_admin.placement_client
        cls.networks_client = cls.os_admin.networks_client
        cls.subnets_client = cls.os_admin.subnets_client
        cls.ports_client = cls.os_primary.ports_client
        cls.routers_client = cls.os_adm.routers_client
        cls.qos_client = cls.os_admin.qos_client
        cls.qos_min_bw_client = cls.os_admin.qos_min_bw_client
        cls.flavors_client = cls.os_adm.flavors_client
        cls.servers_client = cls.os_adm.servers_client

    @classmethod
    def skip_checks(cls):
        super(MinBwAllocationPlacementTest, cls).skip_checks()
        if not CONF.network_feature_enabled.qos_placement_physnet:
            msg = "Skipped as no physnet is available in config for " \
                  "placement based QoS allocation."
            raise cls.skipException(msg)

    def setUp(self):
        super(MinBwAllocationPlacementTest, self).setUp()
        self._check_if_allocation_is_possible()

    def _create_policy_and_min_bw_rule(self, name_prefix, min_kbps):
        policy = self.qos_client.create_qos_policy(
            name=data_utils.rand_name(name_prefix),
            shared=True)['policy']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.qos_client.delete_qos_policy, policy['id'])
        rule = self.qos_min_bw_client.create_minimum_bandwidth_rule(
            policy['id'],
            **{
                'min_kbps': min_kbps,
                'direction': self.INGRESS_DIRECTION
            })['minimum_bandwidth_rule']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.qos_min_bw_client.delete_minimum_bandwidth_rule, policy['id'],
            rule['id'])

        return policy

    def _create_qos_basic_policies(self):
        self.qos_policy_valid = self._create_policy_and_min_bw_rule(
            name_prefix='test_policy_valid',
            min_kbps=self.SMALLEST_POSSIBLE_BW)
        self.qos_policy_not_valid = self._create_policy_and_min_bw_rule(
            name_prefix='test_policy_not_valid',
            min_kbps=self.PLACEMENT_MAX_INT)

    def _create_qos_policies_from_life(self):
        # For tempest-slow the max bandwidth configured is 1000000,
        # https://opendev.org/openstack/tempest/src/branch/master/
        # .zuul.yaml#L416-L420
        self.qos_policy_1 = self._create_policy_and_min_bw_rule(
            name_prefix='test_policy_1',
            min_kbps=self.BANDWIDTH_1
        )
        self.qos_policy_2 = self._create_policy_and_min_bw_rule(
            name_prefix='test_policy_2',
            min_kbps=self.BANDWIDTH_2
        )

    def _create_network_and_qos_policies(self, policy_method):
        physnet_name = CONF.network_feature_enabled.qos_placement_physnet
        base_segm = \
            CONF.network_feature_enabled.provider_net_base_segmentation_id

        self.prov_network, _, _ = self.setup_network_subnet_with_router(
            networks_client=self.networks_client,
            routers_client=self.routers_client,
            subnets_client=self.subnets_client,
            **{
                'shared': True,
                'provider:network_type': 'vlan',
                'provider:physical_network': physnet_name,
                'provider:segmentation_id': base_segm
            })

        policy_method()

    def _check_if_allocation_is_possible(self):
        alloc_candidates = self.placement_client.list_allocation_candidates(
            resources1='%s:%s' % (self.INGRESS_RESOURCE_CLASS,
                                  self.SMALLEST_POSSIBLE_BW))
        if len(alloc_candidates['provider_summaries']) == 0:
            # Skip if the backend does not support QoS minimum bandwidth
            # allocation in Placement API
            raise self.skipException(
                'No allocation candidates are available for %s:%s' %
                (self.INGRESS_RESOURCE_CLASS, self.SMALLEST_POSSIBLE_BW))

        # Just to be sure check with impossible high (placement max_int),
        # allocation
        alloc_candidates = self.placement_client.list_allocation_candidates(
            resources1='%s:%s' % (self.INGRESS_RESOURCE_CLASS,
                                  self.PLACEMENT_MAX_INT))
        if len(alloc_candidates['provider_summaries']) != 0:
            self.fail('For %s:%s there should be no available candidate!' %
                      (self.INGRESS_RESOURCE_CLASS, self.PLACEMENT_MAX_INT))

    def _boot_vm_with_min_bw(self, qos_policy_id, status='ACTIVE'):
        wait_until = (None if status == 'ERROR' else status)
        port = self.create_port(
            self.prov_network['id'], qos_policy_id=qos_policy_id)

        server = self.create_server(networks=[{'port': port['id']}],
                                    wait_until=wait_until)
        waiters.wait_for_server_status(
            client=self.os_primary.servers_client, server_id=server['id'],
            status=status, ready_wait=False, raise_on_error=False)
        return server, port

    def _assert_allocation_is_as_expected(self, consumer, port_ids,
                                          min_kbps=SMALLEST_POSSIBLE_BW):
        allocations = self.placement_client.list_allocations(
            consumer)['allocations']
        self.assertGreater(len(allocations), 0)
        bw_resource_in_alloc = False
        for rp, resources in allocations.items():
            if self.INGRESS_RESOURCE_CLASS in resources['resources']:
                self.assertEqual(
                    min_kbps,
                    resources['resources'][self.INGRESS_RESOURCE_CLASS])
                bw_resource_in_alloc = True
                allocation_rp = rp
        if min_kbps:
            self.assertTrue(bw_resource_in_alloc)

            # Check binding_profile of the port is not empty and equals with
            # the rp uuid
            for port_id in port_ids:
                port = self.os_admin.ports_client.show_port(port_id)
                self.assertEqual(
                    allocation_rp,
                    port['port']['binding:profile']['allocation'])

    @decorators.idempotent_id('78625d92-212c-400e-8695-dd51706858b8')
    @utils.services('compute', 'network')
    def test_qos_min_bw_allocation_basic(self):
        """"Basic scenario with QoS min bw allocation in placement.

        Steps:
        * Create prerequisites:
        ** VLAN type provider network with subnet.
        ** valid QoS policy with minimum bandwidth rule with min_kbps=1
        (This is a simplification to skip the checks in placement for
        detecting the resource provider tree and inventories, as if
        bandwidth resource is available 1 kbs will be available).
        ** invalid QoS policy with minimum bandwidth rule with
        min_kbs=max integer from placement (this is a simplification again
        to avoid detection of RP tress and inventories, as placement will
        reject such big allocation).
        * Create port with valid QoS policy, and boot VM with that, it should
        pass.
        * Create port with invalid QoS policy, and try to boot VM with that,
        it should fail.
        """
        self._create_network_and_qos_policies(self._create_qos_basic_policies)
        server1, valid_port = self._boot_vm_with_min_bw(
            qos_policy_id=self.qos_policy_valid['id'])
        self._assert_allocation_is_as_expected(server1['id'],
                                               [valid_port['id']])

        server2, not_valid_port = self._boot_vm_with_min_bw(
            self.qos_policy_not_valid['id'], status='ERROR')
        allocations = self.placement_client.list_allocations(server2['id'])

        self.assertEqual(0, len(allocations['allocations']))
        server2 = self.servers_client.show_server(server2['id'])
        self.assertIn('fault', server2['server'])
        self.assertIn('No valid host', server2['server']['fault']['message'])
        # Check that binding_profile of the port is empty
        port = self.os_admin.ports_client.show_port(not_valid_port['id'])
        self.assertEqual(0, len(port['port']['binding:profile']))

    @decorators.idempotent_id('8a98150c-a506-49a5-96c6-73a5e7b04ada')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration is not available.')
    @testtools.skipUnless(CONF.compute.min_compute_nodes > 1,
                          'Less than 2 compute nodes, skipping multinode '
                          'tests.')
    @utils.services('compute', 'network')
    def test_migrate_with_qos_min_bw_allocation(self):
        """Scenario to migrate VM with QoS min bw allocation in placement

        Boot a VM like in test_qos_min_bw_allocation_basic, do the same
        checks, and
        * migrate the server
        * confirm the resize, if the VM state is VERIFY_RESIZE
        * If the VM goes to ACTIVE state check that allocations are as
        expected.
        """
        self._create_network_and_qos_policies(self._create_qos_basic_policies)
        server, valid_port = self._boot_vm_with_min_bw(
            qos_policy_id=self.qos_policy_valid['id'])
        self._assert_allocation_is_as_expected(server['id'],
                                               [valid_port['id']])

        self.servers_client.migrate_server(server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.os_primary.servers_client, server_id=server['id'],
            status='VERIFY_RESIZE', ready_wait=False, raise_on_error=False)

        # TODO(lajoskatona): Check that the allocations are ok for the
        #  migration?
        self._assert_allocation_is_as_expected(server['id'],
                                               [valid_port['id']])

        self.servers_client.confirm_resize_server(server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.os_primary.servers_client, server_id=server['id'],
            status='ACTIVE', ready_wait=False, raise_on_error=True)
        self._assert_allocation_is_as_expected(server['id'],
                                               [valid_port['id']])

    @decorators.idempotent_id('c29e7fd3-035d-4993-880f-70819847683f')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @utils.services('compute', 'network')
    def test_resize_with_qos_min_bw_allocation(self):
        """Scenario to resize VM with QoS min bw allocation in placement.

        Boot a VM like in test_qos_min_bw_allocation_basic, do the same
        checks, and
        * resize the server with new flavor
        * confirm the resize, if the VM state is VERIFY_RESIZE
        * If the VM goes to ACTIVE state check that allocations are as
        expected.
        """
        self._create_network_and_qos_policies(self._create_qos_basic_policies)
        server, valid_port = self._boot_vm_with_min_bw(
            qos_policy_id=self.qos_policy_valid['id'])
        self._assert_allocation_is_as_expected(server['id'],
                                               [valid_port['id']])

        old_flavor = self.flavors_client.show_flavor(
            CONF.compute.flavor_ref)['flavor']
        new_flavor = self.flavors_client.create_flavor(**{
            'ram': old_flavor['ram'],
            'vcpus': old_flavor['vcpus'],
            'name': old_flavor['name'] + 'extra',
            'disk': old_flavor['disk'] + 1
        })['flavor']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.flavors_client.delete_flavor, new_flavor['id'])

        self.servers_client.resize_server(
            server_id=server['id'], flavor_ref=new_flavor['id'])
        waiters.wait_for_server_status(
            client=self.os_primary.servers_client, server_id=server['id'],
            status='VERIFY_RESIZE', ready_wait=False, raise_on_error=False)

        # TODO(lajoskatona): Check that the allocations are ok for the
        #  migration?
        self._assert_allocation_is_as_expected(server['id'],
                                               [valid_port['id']])

        self.servers_client.confirm_resize_server(server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.os_primary.servers_client, server_id=server['id'],
            status='ACTIVE', ready_wait=False, raise_on_error=True)
        self._assert_allocation_is_as_expected(server['id'],
                                               [valid_port['id']])

    @decorators.idempotent_id('79fdaa1c-df62-4738-a0f0-1cff9dc415f6')
    @utils.services('compute', 'network')
    def test_qos_min_bw_allocation_update_policy(self):
        """Test the update of QoS policy on bound port

        Related RFE in neutron: #1882804
        The scenario is the following:
        * Have a port with QoS policy and minimum bandwidth rule.
        * Boot a VM with the port.
        * Update the port with a new policy with different minimum bandwidth
        values.
        * The allocation on placement side should be according to the new
        rules.
        """
        if not utils.is_network_feature_enabled('update_port_qos'):
            raise self.skipException("update_port_qos feature is not enabled")

        self._create_network_and_qos_policies(
            self._create_qos_policies_from_life)

        port = self.create_port(
            self.prov_network['id'], qos_policy_id=self.qos_policy_1['id'])

        server1 = self.create_server(
            networks=[{'port': port['id']}])

        self._assert_allocation_is_as_expected(server1['id'], [port['id']],
                                               self.BANDWIDTH_1)

        self.ports_client.update_port(
            port['id'],
            **{'qos_policy_id': self.qos_policy_2['id']})
        self._assert_allocation_is_as_expected(server1['id'], [port['id']],
                                               self.BANDWIDTH_2)

        # I changed my mind
        self.ports_client.update_port(
            port['id'],
            **{'qos_policy_id': self.qos_policy_1['id']})
        self._assert_allocation_is_as_expected(server1['id'], [port['id']],
                                               self.BANDWIDTH_1)

        # bad request....
        self.qos_policy_not_valid = self._create_policy_and_min_bw_rule(
            name_prefix='test_policy_not_valid',
            min_kbps=self.PLACEMENT_MAX_INT)
        port_orig = self.ports_client.show_port(port['id'])['port']
        self.assertRaises(
            lib_exc.Conflict,
            self.ports_client.update_port,
            port['id'], **{'qos_policy_id': self.qos_policy_not_valid['id']})
        self._assert_allocation_is_as_expected(server1['id'], [port['id']],
                                               self.BANDWIDTH_1)

        port_upd = self.ports_client.show_port(port['id'])['port']
        self.assertEqual(port_orig['qos_policy_id'],
                         port_upd['qos_policy_id'])
        self.assertEqual(self.qos_policy_1['id'], port_upd['qos_policy_id'])

    @decorators.idempotent_id('9cfc3bb8-f433-4c91-87b6-747cadc8958a')
    @utils.services('compute', 'network')
    def test_qos_min_bw_allocation_update_policy_from_zero(self):
        """Test port without QoS policy to have QoS policy

        This scenario checks if updating a port without QoS policy to
        have QoS policy with minimum_bandwidth rule succeeds only on
        controlplane, but placement allocation remains 0.
        """
        if not utils.is_network_feature_enabled('update_port_qos'):
            raise self.skipException("update_port_qos feature is not enabled")

        self._create_network_and_qos_policies(
            self._create_qos_policies_from_life)

        port = self.create_port(self.prov_network['id'])

        server1 = self.create_server(
            networks=[{'port': port['id']}])

        self._assert_allocation_is_as_expected(server1['id'], [port['id']], 0)

        self.ports_client.update_port(
            port['id'], **{'qos_policy_id': self.qos_policy_2['id']})
        self._assert_allocation_is_as_expected(server1['id'], [port['id']], 0)

    @decorators.idempotent_id('a9725a70-1d28-4e3b-ae0e-450abc235962')
    @utils.services('compute', 'network')
    def test_qos_min_bw_allocation_update_policy_to_zero(self):
        """Test port with QoS policy to remove QoS policy

        In this scenario port with QoS minimum_bandwidth rule update to
        remove QoS policy results in 0 placement allocation.
        """
        if not utils.is_network_feature_enabled('update_port_qos'):
            raise self.skipException("update_port_qos feature is not enabled")

        self._create_network_and_qos_policies(
            self._create_qos_policies_from_life)

        port = self.create_port(
            self.prov_network['id'], qos_policy_id=self.qos_policy_1['id'])

        server1 = self.create_server(
            networks=[{'port': port['id']}])
        self._assert_allocation_is_as_expected(server1['id'], [port['id']],
                                               self.BANDWIDTH_1)

        self.ports_client.update_port(
            port['id'],
            **{'qos_policy_id': None})
        self._assert_allocation_is_as_expected(server1['id'], [port['id']], 0)

    @decorators.idempotent_id('756ced7f-6f1a-43e7-a851-2fcfc16f3dd7')
    @utils.services('compute', 'network')
    def test_qos_min_bw_allocation_update_with_multiple_ports(self):
        if not utils.is_network_feature_enabled('update_port_qos'):
            raise self.skipException("update_port_qos feature is not enabled")

        self._create_network_and_qos_policies(
            self._create_qos_policies_from_life)

        port1 = self.create_port(
            self.prov_network['id'], qos_policy_id=self.qos_policy_1['id'])
        port2 = self.create_port(
            self.prov_network['id'], qos_policy_id=self.qos_policy_2['id'])

        server1 = self.create_server(
            networks=[{'port': port1['id']}, {'port': port2['id']}])
        self._assert_allocation_is_as_expected(
            server1['id'], [port1['id'], port2['id']],
            self.BANDWIDTH_1 + self.BANDWIDTH_2)

        self.ports_client.update_port(
            port1['id'],
            **{'qos_policy_id': self.qos_policy_2['id']})
        self._assert_allocation_is_as_expected(
            server1['id'], [port1['id'], port2['id']],
            2 * self.BANDWIDTH_2)

    @decorators.idempotent_id('0805779e-e03c-44fb-900f-ce97a790653b')
    @utils.services('compute', 'network')
    def test_empty_update(self):
        if not utils.is_network_feature_enabled('update_port_qos'):
            raise self.skipException("update_port_qos feature is not enabled")

        self._create_network_and_qos_policies(
            self._create_qos_policies_from_life)

        port = self.create_port(
            self.prov_network['id'], qos_policy_id=self.qos_policy_1['id'])

        server1 = self.create_server(
            networks=[{'port': port['id']}])
        self._assert_allocation_is_as_expected(server1['id'], [port['id']],
                                               self.BANDWIDTH_1)
        self.ports_client.update_port(
            port['id'],
            **{'description': 'foo'})
        self._assert_allocation_is_as_expected(server1['id'], [port['id']],
                                               self.BANDWIDTH_1)
