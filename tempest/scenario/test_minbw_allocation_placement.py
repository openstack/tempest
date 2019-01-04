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

from oslo_log import log as logging

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.scenario import manager


LOG = logging.getLogger(__name__)
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

    @classmethod
    def setup_clients(cls):
        super(MinBwAllocationPlacementTest, cls).setup_clients()
        cls.placement_client = cls.os_admin.placement_client
        cls.networks_client = cls.os_admin.networks_client
        cls.subnets_client = cls.os_admin.subnets_client
        cls.routers_client = cls.os_adm.routers_client
        cls.qos_client = cls.os_admin.qos_client
        cls.qos_min_bw_client = cls.os_admin.qos_min_bw_client

    @classmethod
    def skip_checks(cls):
        super(MinBwAllocationPlacementTest, cls).skip_checks()
        if not CONF.network_feature_enabled.qos_placement_physnet:
            msg = "Skipped as no physnet is available in config for " \
                  "placement based QoS allocation."
            raise cls.skipException(msg)

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

    def _create_qos_policies(self):
        self.qos_policy_valid = self._create_policy_and_min_bw_rule(
            name_prefix='test_policy_valid',
            min_kbps=self.SMALLEST_POSSIBLE_BW)
        self.qos_policy_not_valid = self._create_policy_and_min_bw_rule(
            name_prefix='test_policy_not_valid',
            min_kbps=self.PLACEMENT_MAX_INT)

    def _create_network_and_qos_policies(self):
        physnet_name = CONF.network_feature_enabled.qos_placement_physnet
        base_segm = \
            CONF.network_feature_enabled.provider_net_base_segmentation_id

        self.prov_network, _, _ = self.create_networks(
            networks_client=self.networks_client,
            routers_client=self.routers_client,
            subnets_client=self.subnets_client,
            **{
                'shared': True,
                'provider:network_type': 'vlan',
                'provider:physical_network': physnet_name,
                'provider:segmentation_id': base_segm
            })

        self._create_qos_policies()

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

    @decorators.idempotent_id('78625d92-212c-400e-8695-dd51706858b8')
    @decorators.attr(type='slow')
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

        self._check_if_allocation_is_possible()

        self._create_network_and_qos_policies()

        valid_port = self.create_port(
            self.prov_network['id'], qos_policy_id=self.qos_policy_valid['id'])

        server1 = self.create_server(
            networks=[{'port': valid_port['id']}])
        allocations = self.placement_client.list_allocations(server1['id'])

        self.assertGreater(len(allocations['allocations']), 0)
        bw_resource_in_alloc = False
        for rp, resources in allocations['allocations'].items():
            if self.INGRESS_RESOURCE_CLASS in resources['resources']:
                bw_resource_in_alloc = True
        self.assertTrue(bw_resource_in_alloc)

        # boot another vm with max int bandwidth
        not_valid_port = self.create_port(
            self.prov_network['id'],
            qos_policy_id=self.qos_policy_not_valid['id'])
        server2 = self.create_server(
            wait_until=None,
            networks=[{'port': not_valid_port['id']}])
        waiters.wait_for_server_status(
            client=self.os_primary.servers_client, server_id=server2['id'],
            status='ERROR', ready_wait=False, raise_on_error=False)
        allocations = self.placement_client.list_allocations(server2['id'])

        self.assertEqual(0, len(allocations['allocations']))
        server2 = self.servers_client.show_server(server2['id'])
        self.assertIn('fault', server2['server'])
        self.assertIn('No valid host', server2['server']['fault']['message'])
