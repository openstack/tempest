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

from tempest.common import commands
from tempest import config
from tempest.openstack.common import log as logging

CONF = config.CONF
LOG = logging.getLogger(__name__)

TABLES = ['filter', 'nat', 'mangle']


def log_ip_ns():
    if not CONF.debug.enable:
        return
    LOG.info("Host Addr:\n" + commands.ip_addr_raw())
    LOG.info("Host Route:\n" + commands.ip_route_raw())
    for table in TABLES:
        LOG.info('Host %s table:\n%s', table, commands.iptables_raw(table))
    ns_list = commands.ip_ns_list()
    LOG.info("Host ns list" + str(ns_list))
    for ns in ns_list:
        LOG.info("ns(%s) Addr:\n%s", ns, commands.ip_ns_addr(ns))
        LOG.info("ns(%s) Route:\n%s", ns, commands.ip_ns_route(ns))
        for table in TABLES:
            LOG.info('ns(%s) table(%s):\n%s', ns, table,
                     commands.iptables_ns(ns, table))


def log_ovs_db():
    if not CONF.debug.enable or not CONF.service_available.neutron:
        return
    db_dump = commands.ovs_db_dump()
    LOG.info("OVS DB:\n" + db_dump)


def log_net_debug():
    log_ip_ns()
    log_ovs_db()
