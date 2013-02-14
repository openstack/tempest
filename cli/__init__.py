# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

from tempest.openstack.common import cfg

LOG = logging.getLogger(__name__)

cli_opts = [
    cfg.BoolOpt('enabled',
                default=True,
                help="enable cli tests"),
    cfg.StrOpt('cli_dir',
               default='/usr/local/bin/',
               help="directory where python client binaries are located"),
]

CONF = cfg.CONF
cli_group = cfg.OptGroup(name='cli', title="cli Configuration Options")
CONF.register_group(cli_group)
CONF.register_opts(cli_opts, group=cli_group)
