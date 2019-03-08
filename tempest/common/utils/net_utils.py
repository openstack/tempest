# Copyright 2016 Hewlett Packard Enterprise Development Company
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import netaddr

from tempest.lib import exceptions as lib_exc


def get_unused_ip_addresses(ports_client, subnets_client,
                            network_id, subnet_id, count):
    """Return a list with the specified number of unused IP addresses

    This method uses the given ports_client to find the specified number of
    unused IP addresses on the given subnet using the supplied subnets_client
    """

    ports = ports_client.list_ports(network_id=network_id)['ports']
    subnet = subnets_client.show_subnet(subnet_id)
    ip_net = netaddr.IPNetwork(subnet['subnet']['cidr'])
    subnet_set = netaddr.IPSet(ip_net.iter_hosts())
    alloc_set = netaddr.IPSet()

    # prune out any addresses already allocated to existing ports
    for port in ports:
        for fixed_ip in port.get('fixed_ips'):
            alloc_set.add(fixed_ip['ip_address'])

    # exclude gateway_ip of subnet
    gateway_ip = subnet['subnet']['gateway_ip']
    if gateway_ip:
        alloc_set.add(gateway_ip)

    av_set = subnet_set - alloc_set
    addrs = []
    for cidr in reversed(av_set.iter_cidrs()):
        for ip in reversed(cidr):
            addrs.append(str(ip))
            if len(addrs) == count:
                return addrs
    msg = "Insufficient IP addresses available"
    raise lib_exc.BadRequest(message=msg)


def get_ping_payload_size(mtu, ip_version):
    """Return the maximum size of ping payload that will fit into MTU."""
    if not mtu:
        return None
    if ip_version == 4:
        ip_header = 20
        icmp_header = 8
    else:
        ip_header = 40
        icmp_header = 4
    res = mtu - ip_header - icmp_header
    if res < 0:
        raise lib_exc.BadRequest(
            message='MTU = %(mtu)d is too low for IPv%(ip_version)d' % {
                'mtu': mtu,
                'ip_version': ip_version,
            })
    return res
