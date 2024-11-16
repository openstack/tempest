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

PASSED = 'PASSED'
FAILED = 'FAILED'
METADATA_SCRIPT_PATH = '/tmp/metadata_meter_script.sh'
METADATA_RESULTS_PATH = '/tmp/metadata_meter.log'
METADATA_PID_PATH = '/tmp/metadata_meter.pid'
# /proc/uptime is used because it include two decimals in cirros, while
# `date +%s.%N` does not work in cirros (min granularity is seconds)
METADATA_SCRIPT = """#!/bin/sh
echo $$ > %(metadata_meter_pidfile)s
old_time=$(cut -d" " -f1 /proc/uptime)
while true; do
    curl http://169.254.169.254/latest/meta-data/hostname 2>/dev/null | \
grep -q `hostname`
    result=$?
    new_time=$(cut -d" " -f1 /proc/uptime)
    runtime=$(awk -v new=$new_time -v old=$old_time "BEGIN {print new-old}")
    old_time=$new_time
    if [ $result -eq 0 ]; then
        echo "PASSED $runtime"
    else
        echo "FAILED $runtime"
    fi
    sleep %(interval)s
done
"""


class NetDowntimeMeter(fixtures.Fixture):
    def __init__(self, dest_ip, interval=0.2):
        self.dest_ip = dest_ip
        # Note: for intervals lower than 0.2 ping requires root privileges
        self.interval = float(interval)
        self.ping_process = None

    def _setUp(self):
        self.start_background_pinger()

    def start_background_pinger(self):
        cmd = ['ping', '-q', '-s1']
        cmd.append('-i%g' % self.interval)
        cmd.append(self.dest_ip)
        LOG.debug("Starting background pinger to '%s' with interval %g",
                  self.dest_ip, self.interval)
        self.ping_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        if self.ping_process and self.ping_process.poll() is None:
            LOG.debug('Terminating background pinger with pid %d',
                      self.ping_process.pid)
            self.ping_process.terminate()
        self.ping_process = None

    def get_downtime(self):
        self.ping_process.send_signal(signal.SIGQUIT)
        # Example of the expected output:
        # 264/274 packets, 3% loss
        output = self.ping_process.stderr.readline().strip().decode('utf-8')
        if output and len(output.split()[0].split('/')) == 2:
            succ, total = output.split()[0].split('/')
            return (int(total) - int(succ)) * self.interval
        else:
            LOG.warning('Unexpected output obtained from the pinger: %s',
                        output)


class MetadataDowntimeMeter(fixtures.Fixture):
    def __init__(self, ssh_client,
                 interval='0.2', script_path=METADATA_SCRIPT_PATH,
                 output_path=METADATA_RESULTS_PATH,
                 pidfile_path=METADATA_PID_PATH):
        self.ssh_client = ssh_client
        self.interval = interval
        self.script_path = script_path
        self.output_path = output_path
        self.pidfile_path = pidfile_path
        self.pid = None

    def _setUp(self):
        self.addCleanup(self.cleanup)
        self.upload_metadata_script()
        self.run_metadata_script()

    def upload_metadata_script(self):
        metadata_script = METADATA_SCRIPT % {
            'metadata_meter_pidfile': self.pidfile_path,
            'interval': self.interval}
        echo_cmd = "echo '{}' > {}".format(
            metadata_script, self.script_path)
        chmod_cmd = 'chmod +x {}'.format(self.script_path)
        self.ssh_client.exec_command(';'.join((echo_cmd, chmod_cmd)))
        LOG.debug('script created: %s', self.script_path)
        output = self.ssh_client.exec_command(
            'cat {}'.format(self.script_path))
        LOG.debug('script content: %s', output)

    def run_metadata_script(self):
        self.ssh_client.exec_command('{} > {} &'.format(self.script_path,
                                                        self.output_path))
        self.pid = self.ssh_client.exec_command(
            'cat {}'.format(self.pidfile_path)).strip()
        LOG.debug('running metadata downtime meter script in background with '
                  'PID = %s', self.pid)

    def get_results(self):
        output = self.ssh_client.exec_command(
            'cat {}'.format(self.output_path))
        results = {}
        results['successes'] = output.count(PASSED)
        results['failures'] = output.count(FAILED)
        downtime = {PASSED: 0.0, FAILED: 0.0}
        for line in output.splitlines():
            key, value = line.strip().split()
            downtime[key] += float(value)

        results['downtime'] = downtime
        LOG.debug('metadata downtime meter results: %r', results)
        return results

    def cleanup(self):
        if self.pid:
            self.ssh_client.exec_command('kill {}'.format(self.pid))
            LOG.debug('killed metadata downtime script with PID %s', self.pid)
        else:
            LOG.debug('No metadata downtime script found')
