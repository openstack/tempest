# Copyright 2013 OpenStack Foundation
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

import random

from tempest.api.volume import base
from tempest.lib import decorators


class VolumeHostsAdminTestsJSON(base.BaseVolumeAdminTest):

    @decorators.idempotent_id('d5f3efa2-6684-4190-9ced-1c2f526352ad')
    def test_list_hosts(self):
        hosts = self.admin_hosts_client.list_hosts()['hosts']
        self.assertGreaterEqual(len(hosts), 2,
                                "The count of volume hosts is < 2, "
                                "response of list hosts is: %s" % hosts)

        # Check elements in volume hosts list
        host_list_keys = ['service', 'host_name', 'last-update',
                          'zone', 'service-status', 'service-state']
        for host in hosts:
            for key in host_list_keys:
                self.assertIn(key, host)

    @decorators.idempotent_id('21168d57-b373-4b71-a3ac-f2c88f0c5d31')
    def test_show_host(self):
        hosts = self.admin_hosts_client.list_hosts()['hosts']
        self.assertGreaterEqual(len(hosts), 2,
                                "The count of volume hosts is < 2, "
                                "response of list hosts is: %s" % hosts)

        # Note(jeremyZ): Host in volume is always presented in two formats:
        # <host-name> or <host-name>@<driver-name>. Since Mitaka is EOL,
        # both formats can be chosen for test.
        host_names = [host['host_name'] for host in hosts]
        self.assertNotEmpty(host_names, "No available volume host is found, "
                                        "all hosts that found are: %s" % hosts)

        # Choose a random host to get and check its elements
        host_details = self.admin_hosts_client.show_host(
            random.choice(host_names))['host']
        self.assertNotEmpty(host_details)
        host_detail_keys = ['project', 'volume_count', 'snapshot_count',
                            'host', 'total_volume_gb', 'total_snapshot_gb']
        for detail in host_details:
            self.assertIn('resource', detail)
            for key in host_detail_keys:
                self.assertIn(key, detail['resource'])
