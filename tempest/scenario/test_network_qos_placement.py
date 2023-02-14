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


class NetworkQoSPlacementTestBase(manager.NetworkScenarioTest):
    """Base class for Network QoS testing

    Base class for testing Network QoS scenarios involving placement
    resource allocations.
    """
    credentials = ['primary', 'admin']
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

    INGRESS_DIRECTION = 'ingress'
    EGRESS_DIRECTION = 'egress'
    ANY_DIRECTION = 'any'
    INGRESS_RESOURCE_CLASS = "NET_BW_IGR_KILOBIT_PER_SEC"
    EGRESS_RESOURCE_CLASS = "NET_BW_EGR_KILOBIT_PER_SEC"

    # For any realistic inventory value (that is inventory != MAX_INT) an
    # allocation candidate request of MAX_INT is expected to be rejected, see:
    # https://github.com/openstack/placement/blob/master/placement/
    # db/constants.py#L16
    PLACEMENT_MAX_INT = 0x7FFFFFFF

    @classmethod
    def setup_clients(cls):
        super().setup_clients()
        cls.placement_client = cls.os_admin.placement_client
        cls.networks_client = cls.os_admin.networks_client
        cls.subnets_client = cls.os_admin.subnets_client
        cls.ports_client = cls.os_primary.ports_client
        cls.routers_client = cls.os_adm.routers_client
        cls.qos_client = cls.os_admin.qos_client
        cls.qos_min_bw_client = cls.os_admin.qos_min_bw_client
        cls.flavors_client = cls.os_adm.flavors_client
        cls.servers_client = cls.os_primary.servers_client

    def _create_flavor_to_resize_to(self):
        old_flavor = self.flavors_client.show_flavor(
            CONF.compute.flavor_ref)['flavor']
        new_flavor = self.flavors_client.create_flavor(**{
            'ram': old_flavor['ram'],
            'vcpus': old_flavor['vcpus'],
            'name': old_flavor['name'] + 'extra-%s' % data_utils.rand_int_id(),
            'disk': old_flavor['disk'] + 1
        })['flavor']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.flavors_client.delete_flavor, new_flavor['id'])
        return new_flavor


class MinBwAllocationPlacementTest(NetworkQoSPlacementTestBase):

    required_extensions = ['port-resource-request',
                           'qos',
                           'qos-bw-minimum-ingress']

    SMALLEST_POSSIBLE_BW = 1
    BANDWIDTH_1 = 1000
    BANDWIDTH_2 = 2000

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

    def _create_policy_and_min_bw_rule(
        self, name_prefix, min_kbps, direction="ingress"
    ):
        policy = self.qos_client.create_qos_policy(
            name=data_utils.rand_name(name_prefix),
            shared=True)['policy']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.qos_client.delete_qos_policy, policy['id'])
        rule = self.qos_min_bw_client.create_minimum_bandwidth_rule(
            policy['id'],
            **{
                'min_kbps': min_kbps,
                'direction': direction,
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
            self.fail('No allocation candidates are available for %s:%s' %
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
            client=self.servers_client, server_id=server['id'],
            status=status, ready_wait=False, raise_on_error=False)
        return server, port

    def _assert_allocation_is_as_expected(
        self, consumer, port_ids, min_kbps=SMALLEST_POSSIBLE_BW,
        expected_rc=NetworkQoSPlacementTestBase.INGRESS_RESOURCE_CLASS,
    ):
        allocations = self.placement_client.list_allocations(
            consumer)['allocations']
        self.assertGreater(len(allocations), 0)
        bw_resource_in_alloc = False
        allocation_rp = None
        for rp, resources in allocations.items():
            if expected_rc in resources['resources']:
                self.assertEqual(
                    min_kbps,
                    resources['resources'][expected_rc])
                bw_resource_in_alloc = True
                allocation_rp = rp
        if min_kbps:
            self.assertTrue(
                bw_resource_in_alloc,
                f"expected {min_kbps} bandwidth allocation from {expected_rc} "
                f"but instance has allocation {allocations} instead."
            )

            # Check binding_profile of the port is not empty and equals with
            # the rp uuid
            for port_id in port_ids:
                port = self.os_admin.ports_client.show_port(port_id)
                port_binding_alloc = port['port']['binding:profile'][
                    'allocation']
                # NOTE(gibi): the format of the allocation key depends on the
                # existence of port-resource-request-groups API extension.
                # TODO(gibi): drop the else branch once tempest does not need
                # to support Xena release any more.
                if utils.is_extension_enabled(
                        'port-resource-request-groups', 'network'):
                    self.assertEqual(
                        {allocation_rp},
                        set(port_binding_alloc.values()))
                else:
                    self.assertEqual(allocation_rp, port_binding_alloc)

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

    @decorators.attr(type='multinode')
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

        self.os_adm.servers_client.migrate_server(server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
            status='VERIFY_RESIZE', ready_wait=False, raise_on_error=False)

        # TODO(lajoskatona): Check that the allocations are ok for the
        #  migration?
        self._assert_allocation_is_as_expected(server['id'],
                                               [valid_port['id']])

        self.os_adm.servers_client.confirm_resize_server(
            server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
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

        new_flavor = self._create_flavor_to_resize_to()

        self.servers_client.resize_server(
            server_id=server['id'], flavor_ref=new_flavor['id'])
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
            status='VERIFY_RESIZE', ready_wait=False, raise_on_error=False)

        # TODO(lajoskatona): Check that the allocations are ok for the
        #  migration?
        self._assert_allocation_is_as_expected(server['id'],
                                               [valid_port['id']])

        self.servers_client.confirm_resize_server(server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
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

    @decorators.idempotent_id('372b2728-cfed-469a-b5f6-b75779e1ccbe')
    @utils.services('compute', 'network')
    def test_qos_min_bw_allocation_update_policy_direction_change(self):
        """Test QoS min bw direction change on a bound port

        Related RFE in neutron: #1882804
        The scenario is the following:
        * Have a port with QoS policy and minimum bandwidth rule with ingress
        direction
        * Boot a VM with the port.
        * Update the port with a new policy to egress direction in
        minimum bandwidth rule.
        * The allocation on placement side should be according to the new
        rules.
        """
        if not utils.is_network_feature_enabled('update_port_qos'):
            raise self.skipException("update_port_qos feature is not enabled")

        def create_policies():
            self.qos_policy_ingress = self._create_policy_and_min_bw_rule(
                name_prefix='test_policy_ingress',
                min_kbps=self.BANDWIDTH_1,
                direction=self.INGRESS_DIRECTION,
            )
            self.qos_policy_egress = self._create_policy_and_min_bw_rule(
                name_prefix='test_policy_egress',
                min_kbps=self.BANDWIDTH_1,
                direction=self.EGRESS_DIRECTION,
            )

        self._create_network_and_qos_policies(create_policies)

        port = self.create_port(
            self.prov_network['id'],
            qos_policy_id=self.qos_policy_ingress['id'])

        server1 = self.create_server(
            networks=[{'port': port['id']}])

        self._assert_allocation_is_as_expected(
            server1['id'], [port['id']], self.BANDWIDTH_1,
            expected_rc=self.INGRESS_RESOURCE_CLASS)

        self.ports_client.update_port(
            port['id'],
            qos_policy_id=self.qos_policy_egress['id'])

        self._assert_allocation_is_as_expected(
            server1['id'], [port['id']], self.BANDWIDTH_1,
            expected_rc=self.EGRESS_RESOURCE_CLASS)
        self._assert_allocation_is_as_expected(
            server1['id'], [port['id']], 0,
            expected_rc=self.INGRESS_RESOURCE_CLASS)


class QoSBandwidthAndPacketRateTests(NetworkQoSPlacementTestBase):

    PPS_RESOURCE_CLASS = "NET_PACKET_RATE_KILOPACKET_PER_SEC"

    @classmethod
    def skip_checks(cls):
        super().skip_checks()
        if not CONF.network_feature_enabled.qos_min_bw_and_pps:
            msg = (
                "Skipped as no resource inventories are configured for QoS "
                "minimum bandwidth and packet rate testing.")
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super().setup_clients()
        cls.qos_min_pps_client = cls.os_admin.qos_min_pps_client

    def setUp(self):
        super().setUp()
        self.network = self._create_network()

    def _create_qos_policy_with_bw_and_pps_rules(self, min_kbps, min_kpps):
        policy = self.qos_client.create_qos_policy(
            name=data_utils.rand_name(),
            shared=True
        )['policy']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.qos_client.delete_qos_policy,
            policy['id']
        )

        if min_kbps > 0:
            bw_rule = self.qos_min_bw_client.create_minimum_bandwidth_rule(
                policy['id'],
                min_kbps=min_kbps,
                direction=self.INGRESS_DIRECTION
            )['minimum_bandwidth_rule']
            self.addCleanup(
                test_utils.call_and_ignore_notfound_exc,
                self.qos_min_bw_client.delete_minimum_bandwidth_rule,
                policy['id'],
                bw_rule['id']
            )

        if min_kpps > 0:
            pps_rule = self.qos_min_pps_client.create_minimum_packet_rate_rule(
                policy['id'],
                min_kpps=min_kpps,
                direction=self.ANY_DIRECTION
            )['minimum_packet_rate_rule']
            self.addCleanup(
                test_utils.call_and_ignore_notfound_exc,
                self.qos_min_pps_client.delete_minimum_packet_rate_rule,
                policy['id'],
                pps_rule['id']
            )

        return policy

    def _create_network(self):
        physnet_name = CONF.network_feature_enabled.qos_placement_physnet
        base_segm = (
            CONF.network_feature_enabled.provider_net_base_segmentation_id)

        # setup_network_subnet_with_router will add the necessary cleanup calls
        network, _, _ = self.setup_network_subnet_with_router(
            networks_client=self.networks_client,
            routers_client=self.routers_client,
            subnets_client=self.subnets_client,
            shared=True,
            **{
                'provider:network_type': 'vlan',
                'provider:physical_network': physnet_name,
                # +1 to be different from the segmentation_id used in
                # MinBwAllocationPlacementTest
                'provider:segmentation_id': int(base_segm) + 1,
            }
        )
        return network

    def _create_port_with_qos_policy(self, policy):
        port = self.ports_client.create_port(
            name=data_utils.rand_name(self.__class__.__name__),
            network_id=self.network['id'],
            qos_policy_id=policy['id'] if policy else None,
        )['port']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.ports_client.delete_port, port['id']
        )
        return port

    def assert_allocations(
            self, server, port, expected_min_kbps, expected_min_kpps
    ):
        allocations = self.placement_client.list_allocations(
            server['id'])['allocations']

        # one allocation for the flavor related resources on the compute RP
        expected_allocation = 1
        # one allocation due to bw rule
        if expected_min_kbps > 0:
            expected_allocation += 1
        # one allocation due to pps rule
        if expected_min_kpps > 0:
            expected_allocation += 1
        self.assertEqual(expected_allocation, len(allocations), allocations)

        expected_rp_uuids_in_binding_allocation = set()

        if expected_min_kbps > 0:
            bw_rp_allocs = {
                rp: alloc['resources'][self.INGRESS_RESOURCE_CLASS]
                for rp, alloc in allocations.items()
                if self.INGRESS_RESOURCE_CLASS in alloc['resources']
            }
            self.assertEqual(1, len(bw_rp_allocs))
            bw_rp, bw_alloc = list(bw_rp_allocs.items())[0]
            self.assertEqual(expected_min_kbps, bw_alloc)
            expected_rp_uuids_in_binding_allocation.add(bw_rp)

        if expected_min_kpps > 0:
            pps_rp_allocs = {
                rp: alloc['resources'][self.PPS_RESOURCE_CLASS]
                for rp, alloc in allocations.items()
                if self.PPS_RESOURCE_CLASS in alloc['resources']
            }
            self.assertEqual(1, len(pps_rp_allocs))
            pps_rp, pps_alloc = list(pps_rp_allocs.items())[0]
            self.assertEqual(expected_min_kpps, pps_alloc)
            expected_rp_uuids_in_binding_allocation.add(pps_rp)

        # Let's check port.binding:profile.allocation points to the two
        # provider resource allocated from
        port = self.os_admin.ports_client.show_port(port['id'])
        port_binding_alloc = port[
            'port']['binding:profile'].get('allocation', {})
        self.assertEqual(
            expected_rp_uuids_in_binding_allocation,
            set(port_binding_alloc.values())
        )

    def assert_no_allocation(self, server, port):
        # check that there are no allocations
        allocations = self.placement_client.list_allocations(
            server['id'])['allocations']
        self.assertEqual(0, len(allocations))

        # check that binding_profile of the port is empty
        port = self.os_admin.ports_client.show_port(port['id'])
        self.assertEqual(0, len(port['port']['binding:profile']))

    @decorators.idempotent_id('93d1a88d-235e-4b7b-b44d-2a17dcf4e213')
    @utils.services('compute', 'network')
    def test_server_create_delete(self):
        min_kbps = 1000
        min_kpps = 100
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)
        port = self._create_port_with_qos_policy(policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, min_kbps, min_kpps)

        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])

        self.assert_no_allocation(server, port)

    def _test_create_server_negative(self, min_kbps=1000, min_kpps=100):
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)
        port = self._create_port_with_qos_policy(policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until=None)
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
            status='ERROR', ready_wait=False, raise_on_error=False)

        # check that the creation failed with No valid host
        server = self.servers_client.show_server(server['id'])['server']
        self.assertIn('fault', server)
        self.assertIn('No valid host', server['fault']['message'])

        self.assert_no_allocation(server, port)

    @decorators.idempotent_id('915dd2ce-4890-40c8-9db6-f3e04080c6c1')
    @utils.services('compute', 'network')
    def test_server_create_no_valid_host_due_to_bandwidth(self):
        self._test_create_server_negative(min_kbps=self.PLACEMENT_MAX_INT)

    @decorators.idempotent_id('2d4a755e-10b9-4ac0-bef2-3f89de1f150b')
    @utils.services('compute', 'network')
    def test_server_create_no_valid_host_due_to_packet_rate(self):
        self._test_create_server_negative(min_kpps=self.PLACEMENT_MAX_INT)

    @decorators.idempotent_id('69d93e4f-0dfc-4d17-8d84-cc5c3c842cd5')
    @testtools.skipUnless(
        CONF.compute_feature_enabled.resize, 'Resize not available.')
    @utils.services('compute', 'network')
    def test_server_resize(self):
        min_kbps = 1000
        min_kpps = 100
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)
        port = self._create_port_with_qos_policy(policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, min_kbps, min_kpps)

        new_flavor = self._create_flavor_to_resize_to()

        self.servers_client.resize_server(
            server_id=server['id'], flavor_ref=new_flavor['id']
        )
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
            status='VERIFY_RESIZE', ready_wait=False, raise_on_error=False)

        self.assert_allocations(server, port, min_kbps, min_kpps)

        self.servers_client.confirm_resize_server(server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
            status='ACTIVE', ready_wait=False, raise_on_error=True)

        self.assert_allocations(server, port, min_kbps, min_kpps)

    @decorators.idempotent_id('d01d4aee-ca06-4e4e-add7-8a47fe0daf96')
    @testtools.skipUnless(
        CONF.compute_feature_enabled.resize, 'Resize not available.')
    @utils.services('compute', 'network')
    def test_server_resize_revert(self):
        min_kbps = 1000
        min_kpps = 100
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)
        port = self._create_port_with_qos_policy(policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, min_kbps, min_kpps)

        new_flavor = self._create_flavor_to_resize_to()

        self.servers_client.resize_server(
            server_id=server['id'], flavor_ref=new_flavor['id']
        )
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
            status='VERIFY_RESIZE', ready_wait=False, raise_on_error=False)

        self.assert_allocations(server, port, min_kbps, min_kpps)

        self.servers_client.revert_resize_server(server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
            status='ACTIVE', ready_wait=False, raise_on_error=True)

        self.assert_allocations(server, port, min_kbps, min_kpps)

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('bdd0b31c-c8b0-4b7b-b80a-545a46b32abe')
    @testtools.skipUnless(
        CONF.compute_feature_enabled.cold_migration,
        'Cold migration is not available.')
    @testtools.skipUnless(
        CONF.compute.min_compute_nodes > 1,
        'Less than 2 compute nodes, skipping multinode tests.')
    @utils.services('compute', 'network')
    def test_server_migrate(self):
        min_kbps = 1000
        min_kpps = 100
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)
        port = self._create_port_with_qos_policy(policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, min_kbps, min_kpps)

        self.os_adm.servers_client.migrate_server(server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
            status='VERIFY_RESIZE', ready_wait=False, raise_on_error=False)

        self.assert_allocations(server, port, min_kbps, min_kpps)

        self.os_adm.servers_client.confirm_resize_server(
            server_id=server['id'])
        waiters.wait_for_server_status(
            client=self.servers_client, server_id=server['id'],
            status='ACTIVE', ready_wait=False, raise_on_error=True)

        self.assert_allocations(server, port, min_kbps, min_kpps)

    @decorators.idempotent_id('fdb260e3-caa5-482d-ac7c-8c22adf3d750')
    @utils.services('compute', 'network')
    def test_qos_policy_update_on_bound_port(self):
        min_kbps = 1000
        min_kpps = 100
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)

        min_kbps2 = 2000
        min_kpps2 = 50
        policy2 = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps2, min_kpps2)

        port = self._create_port_with_qos_policy(policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, min_kbps, min_kpps)

        self.ports_client.update_port(
            port['id'],
            qos_policy_id=policy2['id'])

        self.assert_allocations(server, port, min_kbps2, min_kpps2)

    @decorators.idempotent_id('e6a20125-a02e-49f5-bcf6-894305ee3715')
    @utils.services('compute', 'network')
    def test_qos_policy_update_on_bound_port_from_null_policy(self):
        min_kbps = 1000
        min_kpps = 100
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)

        port = self._create_port_with_qos_policy(policy=None)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, 0, 0)

        self.ports_client.update_port(
            port['id'],
            qos_policy_id=policy['id'])

        # NOTE(gibi): This is unintuitive but it is the expected behavior.
        # If there was no policy attached to the port when the server was
        # created then neutron still allows adding a policy to the port later
        # as this operation was support before placement enforcement was added
        # for the qos minimum bandwidth rule. However neutron cannot create
        # the placement resource allocation for this port.
        self.assert_allocations(server, port, 0, 0)

    @decorators.idempotent_id('f5864761-966c-4e49-b430-ac0044b7d658')
    @utils.services('compute', 'network')
    def test_qos_policy_update_on_bound_port_additional_rule(self):
        min_kbps = 1000
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, 0)

        min_kbps2 = 2000
        min_kpps2 = 50
        policy2 = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps2, min_kpps2)

        port = self._create_port_with_qos_policy(policy=policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, min_kbps, 0)

        self.ports_client.update_port(
            port['id'],
            qos_policy_id=policy2['id'])

        # FIXME(gibi): Agree in the spec: do we ignore the pps request or we
        # reject the update? It seems current implementation goes with
        # ignoring the additional pps rule.
        self.assert_allocations(server, port, min_kbps2, 0)

    @decorators.idempotent_id('fbbb9c81-ed21-48c3-bdba-ce2361e93aad')
    @utils.services('compute', 'network')
    def test_qos_policy_update_on_bound_port_to_null_policy(self):
        min_kbps = 1000
        min_kpps = 100
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)

        port = self._create_port_with_qos_policy(policy=policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, min_kbps, min_kpps)

        self.ports_client.update_port(
            port['id'],
            qos_policy_id=None)

        self.assert_allocations(server, port, 0, 0)

    @decorators.idempotent_id('0393d038-03ad-4844-a0e4-83010f69dabb')
    @utils.services('compute', 'network')
    def test_interface_attach_detach(self):
        min_kbps = 1000
        min_kpps = 100
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)

        port = self._create_port_with_qos_policy(policy=None)

        port2 = self._create_port_with_qos_policy(policy=policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, 0, 0)

        self.interface_client.create_interface(
            server_id=server['id'],
            port_id=port2['id'])
        waiters.wait_for_interface_status(
            self.interface_client, server['id'], port2['id'], 'ACTIVE')

        self.assert_allocations(server, port2, min_kbps, min_kpps)

        req_id = self.interface_client.delete_interface(
            server_id=server['id'],
            port_id=port2['id']).response['x-openstack-request-id']
        waiters.wait_for_interface_detach(
            self.servers_client, server['id'], port2['id'], req_id)

        self.assert_allocations(server, port2, 0, 0)

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('36ffdb85-6cc2-4cc9-a426-cad5bac8626b')
    @testtools.skipUnless(
        CONF.compute.min_compute_nodes > 1,
        'Less than 2 compute nodes, skipping multinode tests.')
    @testtools.skipUnless(
        CONF.compute_feature_enabled.live_migration,
        'Live migration not available')
    @utils.services('compute', 'network')
    def test_server_live_migrate(self):
        min_kbps = 1000
        min_kpps = 100
        policy = self._create_qos_policy_with_bw_and_pps_rules(
            min_kbps, min_kpps)

        port = self._create_port_with_qos_policy(policy=policy)

        server = self.create_server(
            networks=[{'port': port['id']}],
            wait_until='ACTIVE'
        )

        self.assert_allocations(server, port, min_kbps, min_kpps)

        server_details = self.os_adm.servers_client.show_server(server['id'])
        source_host = server_details['server']['OS-EXT-SRV-ATTR:host']

        self.os_adm.servers_client.live_migrate_server(
            server['id'], block_migration=True, host=None)
        waiters.wait_for_server_status(
            self.servers_client, server['id'], 'ACTIVE')

        server_details = self.os_adm.servers_client.show_server(server['id'])
        new_host = server_details['server']['OS-EXT-SRV-ATTR:host']

        self.assertNotEqual(source_host, new_host, "Live migration failed")

        self.assert_allocations(server, port, min_kbps, min_kpps)
