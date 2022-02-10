# Copyright 2022 OpenStack Foundation
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
import signal
import subprocess

import fixtures

from oslo_log import log


LOG = log.getLogger(__name__)


class NetDowntimeMeter(fixtures.Fixture):
    def __init__(self, dest_ip, interval='0.2'):
        self.dest_ip = dest_ip
        # Note: for intervals lower than 0.2 ping requires root privileges
        self.interval = interval
        self.ping_process = None

    def _setUp(self):
        self.start_background_pinger()

    def start_background_pinger(self):
        cmd = ['ping', '-q', '-s1']
        cmd.append('-i{}'.format(self.interval))
        cmd.append(self.dest_ip)
        LOG.debug("Starting background pinger to '{}' with interval {}".format(
            self.dest_ip, self.interval))
        self.ping_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        if self.ping_process and self.ping_process.poll() is None:
            LOG.debug('Terminating background pinger with pid {}'.format(
                self.ping_process.pid))
            self.ping_process.terminate()
        self.ping_process = None

    def get_downtime(self):
        self.ping_process.send_signal(signal.SIGQUIT)
        # Example of the expected output:
        # 264/274 packets, 3% loss
        output = self.ping_process.stderr.readline().strip().decode('utf-8')
        if output and len(output.split()[0].split('/')) == 2:
            succ, total = output.split()[0].split('/')
            return (int(total) - int(succ)) * float(self.interval)
        else:
            LOG.warning('Unexpected output obtained from the pinger: %s',
                        output)
