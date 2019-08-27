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

from tempest.api.volume import base
from tempest.lib import decorators


class VolumeHostsAdminTestsJSON(base.BaseVolumeAdminTest):

    @decorators.idempotent_id('d5f3efa2-6684-4190-9ced-1c2f526352ad')
    def test_list_hosts(self):
        hosts = self.admin_hosts_client.list_hosts()['hosts']
        self.assertGreaterEqual(len(hosts), 2,
                                "The count of volume hosts is < 2, "
                                "response of list hosts is: %s" % hosts)

    @decorators.idempotent_id('21168d57-b373-4b71-a3ac-f2c88f0c5d31')
    def test_show_host(self):
        hosts = self.admin_hosts_client.list_hosts()['hosts']
        self.assertGreaterEqual(len(hosts), 2,
                                "The count of volume hosts is < 2, "
                                "response of list hosts is: %s" % hosts)

        # Note(jeremyZ): The show host API is to show volume usage info on the
        # specified cinder-volume host. If the host does not run cinder-volume
        # service, or the cinder-volume service is disabled on the host, the
        # show host API should fail (return code: 404). The cinder-volume host
        # is presented in format: <host-name>@driver-name.
        c_vol_hosts = [host['host_name'] for host in hosts
                       if (host['service'] == 'cinder-volume' and
                           host['service-state'] == 'enabled')]
        self.assertNotEmpty(c_vol_hosts,
                            "No available cinder-volume host is found, "
                            "all hosts that found are: %s" % hosts)

        # Check each cinder-volume host.
        for host in c_vol_hosts:
            host_details = self.admin_hosts_client.show_host(host)['host']
            self.assertNotEmpty(host_details)
