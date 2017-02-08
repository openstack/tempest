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


radvd_template = '''
interface {iface}
{{
   AdvSendAdvert on;
   MinRtrAdvInterval 3;
   MaxRtrAdvInterval 10;
   prefix {prefix}
   {{
        AdvOnLink on;
        AdvAutonomous on;
   }};
}};
'''


def radvd_create_config(iface, prefix):
    import tempfile

    abs_file_name = tempfile.mktemp('_radvd.conf')
    with open(abs_file_name, 'w') as f:
        f.write(radvd_template.format(iface=iface, prefix=prefix))
    return abs_file_name


def radvd_start_on(iface, prefix):
    from tempest.common import commands
    conf_abs_path = radvd_create_config(iface=iface, prefix=prefix)
    commands.sudo_cmd_call('radvd -C {conf} -p {pid}'.format(
        conf=conf_abs_path, pid=conf_abs_path.replace('.conf', '.pid')))
