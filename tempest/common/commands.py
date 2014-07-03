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

import shlex
import subprocess

from tempest.openstack.common import log as logging

LOG = logging.getLogger(__name__)

# NOTE(afazekas):
# These commands assumes the tempest node is the same as
# the only one service node. all-in-one installation.


def sudo_cmd_call(cmd):
    args = shlex.split(cmd)
    subprocess_args = {'stdout': subprocess.PIPE,
                       'stderr': subprocess.STDOUT}
    proc = subprocess.Popen(['/usr/bin/sudo', '-n'] + args,
                            **subprocess_args)
    stdout = proc.communicate()[0]
    if proc.returncode != 0:
        LOG.error(("Command {0} returned with exit status {1},"
                   "output {2}").format(cmd, proc.returncode, stdout))
    return stdout


def ip_addr_raw():
    return sudo_cmd_call("ip a")


def ip_route_raw():
    return sudo_cmd_call("ip r")


def ip_ns_raw():
    return sudo_cmd_call("ip netns list")


def iptables_raw(table):
    return sudo_cmd_call("iptables --line-numbers -L -nv -t " + table)


def ip_ns_list():
    return ip_ns_raw().split()


def ip_ns_exec(ns, cmd):
    return sudo_cmd_call(" ".join(("ip netns exec", ns, cmd)))


def ip_ns_addr(ns):
    return ip_ns_exec(ns, "ip a")


def ip_ns_route(ns):
    return ip_ns_exec(ns, "ip r")


def iptables_ns(ns, table):
    return ip_ns_exec(ns, "iptables -v -S -t " + table)


def ovs_db_dump():
    return sudo_cmd_call("ovsdb-client dump")


def copy_file_to_host(file_from, dest, host, username, pkey):
    dest = "%s@%s:%s" % (username, host, dest)
    cmd = "scp -v -o UserKnownHostsFile=/dev/null " \
          "-o StrictHostKeyChecking=no " \
          "-i %(pkey)s %(file1)s %(dest)s" % {'pkey': pkey,
                                              'file1': file_from,
                                              'dest': dest}
    args = shlex.split(cmd)
    subprocess_args = {'stdout': subprocess.PIPE,
                       'stderr': subprocess.STDOUT}
    proc = subprocess.Popen(args, **subprocess_args)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        LOG.error(("Command {0} returned with exit status {1},"
                  "output {2}, error {3}").format(cmd, proc.returncode,
                                                  stdout, stderr))
    return stdout
