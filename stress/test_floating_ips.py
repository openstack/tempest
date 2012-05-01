# Copyright 2011 Quanta Research Cambridge, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


# system imports
import random
import time
import telnetlib
import logging

# local imports
import test_case
import pending_action


class TestChangeFloatingIp(test_case.StressTestCase):
    """Add or remove a floating ip from a vm."""

    def __init__(self):
        super(TestChangeFloatingIp, self).__init__()
        self.server_ids = None

    def run(self, manager, state, *pargs, **kwargs):
        if self.server_ids == None:
            vms = state.get_instances()
            self.server_ids = [k for k, v in vms.iteritems()]
        floating_ip = random.choice(state.get_floating_ips())
        if floating_ip.change_pending:
            return None
        floating_ip.change_pending = True
        timeout = int(kwargs.get('timeout', 60))
        if floating_ip.server_id == None:
            server = random.choice(self.server_ids)
            address = floating_ip.address
            self._logger.info('Adding %s to server %s' % (address, server))
            resp, body =\
            manager.floating_ips_client.associate_floating_ip_to_server(
                                                        address,
                                                        server)
            if resp.status != 202:
                raise Exception("response: %s body: %s" % (resp, body))
            floating_ip.server_id = server
            return VerifyChangeFloatingIp(manager, floating_ip,
                                          timeout, add=True)
        else:
            server = floating_ip.server_id
            address = floating_ip.address
            self._logger.info('Removing %s from server %s' % (address, server))
            resp, body =\
            manager.floating_ips_client.disassociate_floating_ip_from_server(
                                                           address, server)
            if resp.status != 202:
                raise Exception("response: %s body: %s" % (resp, body))
            return VerifyChangeFloatingIp(manager, floating_ip,
                                          timeout, add=False)


class VerifyChangeFloatingIp(pending_action.PendingAction):
    """Verify that floating ip was changed"""
    def __init__(self, manager, floating_ip, timeout, add=None):
        super(VerifyChangeFloatingIp, self).__init__(manager, timeout=timeout)
        self.floating_ip = floating_ip
        self.add = add

    def retry(self):
        """
        Check to see that we can contact the server at its new address.
        """
        try:
            conn = telnetlib.Telnet(self.floating_ip.address, 22, timeout=0.5)
            conn.close()
            if self.add:
                self._logger.info('%s added [%.1f secs elapsed]' %
                          (self.floating_ip.address, self.elapsed()))
                self.floating_ip.change_pending = False
                return True
        except:
            if not self.add:
                self._logger.info('%s removed [%.1f secs elapsed]' %
                          (self.floating_ip.address, self.elapsed()))
                self.floating_ip.change_pending = False
                self.floating_ip.server_id = None
                return True
        return False
