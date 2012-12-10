# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import shlex
import subprocess

SSH_OPTIONS = (" -q" +
               " -o UserKnownHostsFile=/dev/null" +
               " -o StrictHostKeyChecking=no -i ")


def get_ssh_options(keypath):
    return SSH_OPTIONS + keypath


def scp(keypath, args):
    options = get_ssh_options(keypath)
    return subprocess.check_call(shlex.split("scp" + options + args))


def ssh(keypath, user, node, command, check=True):
    command = 'sudo ' + command
    command = "ssh %s %s@%s %s" % (get_ssh_options(keypath), user,
                                   node, command)
    popenargs = shlex.split(command)
    process = subprocess.Popen(popenargs, stdout=subprocess.PIPE)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode and check:
        raise Exception("%s: ssh failed with retcode: %s" % (node, retcode))
    return output


def execute_on_all(keypath, user, nodes, command):
    for node in nodes:
        ssh(keypath, user, node, command)


def enum(*sequential, **named):
    """Create auto-incremented enumerated types"""
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)
