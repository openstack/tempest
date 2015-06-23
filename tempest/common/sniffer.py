# Copyright 2014 Cisco Systems, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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

SNIFF_RADVD = 'icmp6'


def sniff_analyzer_radvd(capture):
    import re

    result = {'advertisement': {'count': 0, 'prefixes': [], 'flags': []},
              'solicitation': {'count': 0, 'prefixes': [], 'flags': []}}

    p = re.compile('(advertisement|solicitation)|prefix .+ (.+), '
                   'Flags \[(.+)\]', re.MULTILINE)

    msg_type = None
    index = -1
    for msg, prefix, flags in p.findall(capture):
        if msg:
            result[msg]['count'] += 1
            result[msg]['prefixes'].append(None)
            result[msg]['flags'].append(None)
            msg_type = msg
            index += 1
        if prefix and msg_type in result.keys():
            result[msg_type]['prefixes'][index] = prefix
        if flags and msg_type in result.keys():
            result[msg_type]['flags'][index] = flags
    return result


def sniff_analyzer(what, capture):
    if what == SNIFF_RADVD:
        return sniff_analyzer_radvd(capture=capture)


def sniff(what, interface='any', count=1, timeout=60, is_save=False,
          is_remote=False):
    """Executes tcpdump and collects some info depending on argument 'what'
       For example for SNIFF_RADVD one would expect something like
       {'what': 'icmp6', 'count': 3,
        'advertisement': {'count': 2, 'prefixes': ['feee::/64', None]}
        'solicitation': {'count': 1, 'prefixes': ['feee::/64']}
       }
       If run with is_remote to be True, that just compile string representing
       the commmand to be run by external ssh client.
       In this case, one needs to call sniff_analyzer by hands
    """
    from tempest.common import commands
    import tempfile

    cmd = 'tcpdump -vv -n -t -i {i} -c {c} {what}'.format(i=interface,
                                                          what=what,
                                                          c=count)
    if timeout:
        cmd = 'timeout -s SIGINT {0} '.format(timeout) + cmd
    if is_remote:
        return cmd
    if is_save:
        tmp_file_path = tempfile.mktemp('_out.tcpdump')
        commands.sudo_cmd_call(cmd=cmd + ' -w {0}'.format(tmp_file_path))
        return 'Check ' + tmp_file_path

    result = {'what': what, 'count': int(count)}
    capture = commands.sudo_cmd_call(cmd=cmd)
    result.update(sniff_analyzer(what=what, capture=capture))
    return result


def sniff_in_thread(what, interface='any', count=1, timeout=60):
    import threading

    class SniffThread(threading.Thread):

        def __init__(self):
            self.what = what
            self.interface = interface
            self.count = count
            self.timeout = timeout
            self.result = None
            super(SniffThread, self).__init__()

        def run(self):
            self.result = sniff(what=self.what, interface=self.interface,
                                count=self.count, timeout=self.timeout)

    t = SniffThread()
    t.start()
    return t
