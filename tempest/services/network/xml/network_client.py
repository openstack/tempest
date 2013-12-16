# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

from lxml import etree
import xml.etree.ElementTree as ET

from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import deep_dict_to_xml
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import xml_to_json


class NetworkClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(NetworkClientXML, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.network.catalog_type
        self.version = '2.0'
        self.uri_prefix = "v%s" % (self.version)

    def list_networks(self):
        uri = '%s/networks' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        networks = self._parse_array(etree.fromstring(body))
        networks = {"networks": networks}
        return resp, networks

    def create_network(self, name):
        uri = '%s/networks' % (self.uri_prefix)
        post_body = Element("network")
        p2 = Element("name", name)
        post_body.append(p2)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def create_bulk_network(self, count, names):
        uri = '%s/networks' % (self.uri_prefix)
        post_body = Element("networks")
        for i in range(count):
                p1 = Element("network")
                p2 = Element("name", names[i])
                p1.append(p2)
                post_body.append(p1)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        networks = self._parse_array(etree.fromstring(body))
        networks = {"networks": networks}
        return resp, networks

    def delete_network(self, uuid):
        uri = '%s/networks/%s' % (self.uri_prefix, str(uuid))
        return self.delete(uri, self.headers)

    def show_network(self, uuid):
        uri = '%s/networks/%s' % (self.uri_prefix, str(uuid))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def create_subnet(self, net_uuid, cidr):
        uri = '%s/subnets' % (self.uri_prefix)
        subnet = Element("subnet")
        p2 = Element("network_id", net_uuid)
        p3 = Element("cidr", cidr)
        p4 = Element("ip_version", 4)
        subnet.append(p2)
        subnet.append(p3)
        subnet.append(p4)
        resp, body = self.post(uri, str(Document(subnet)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def delete_subnet(self, subnet_id):
        uri = '%s/subnets/%s' % (self.uri_prefix, str(subnet_id))
        return self.delete(uri, self.headers)

    def list_subnets(self):
        uri = '%s/subnets' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        subnets = self._parse_array(etree.fromstring(body))
        subnets = {"subnets": subnets}
        return resp, subnets

    def show_subnet(self, uuid):
        uri = '%s/subnets/%s' % (self.uri_prefix, str(uuid))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def create_port(self, net_uuid, **kwargs):
        uri = '%s/ports' % (self.uri_prefix)
        port = Element("port")
        p1 = Element('network_id', net_uuid)
        port.append(p1)
        for key, val in kwargs.items():
            key = Element(key, val)
            port.append(key)
        resp, body = self.post(uri, str(Document(port)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def delete_port(self, port_id):
        uri = '%s/ports/%s' % (self.uri_prefix, str(port_id))
        return self.delete(uri, self.headers)

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            array.append(xml_to_json(child))
        return array

    def list_ports(self):
        url = '%s/ports' % (self.uri_prefix)
        resp, body = self.get(url, self.headers)
        ports = self._parse_array(etree.fromstring(body))
        ports = {"ports": ports}
        return resp, ports

    def show_port(self, port_id):
        uri = '%s/ports/%s' % (self.uri_prefix, str(port_id))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_port(self, port_id, name):
        uri = '%s/ports/%s' % (self.uri_prefix, str(port_id))
        port = Element("port")
        p2 = Element("name", name)
        port.append(p2)
        resp, body = self.put(uri, str(Document(port)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_subnet(self, subnet_id, name):
        uri = '%s/subnets/%s' % (self.uri_prefix, str(subnet_id))
        subnet = Element("subnet")
        p2 = Element("name", name)
        subnet.append(p2)
        resp, body = self.put(uri, str(Document(subnet)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_network(self, net_id, name):
        uri = '%s/networks/%s' % (self.uri_prefix, str(net_id))
        network = Element("network")
        p2 = Element("name", name)
        network.append(p2)
        resp, body = self.put(uri, str(Document(network)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def create_security_group(self, name):
        uri = '%s/security-groups' % (self.uri_prefix)
        post_body = Element("security_group")
        p2 = Element("name", name)
        post_body.append(p2)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_security_groups(self):
        url = '%s/security-groups' % (self.uri_prefix)
        resp, body = self.get(url, self.headers)
        secgroups = self._parse_array(etree.fromstring(body))
        secgroups = {"security_groups": secgroups}
        return resp, secgroups

    def delete_security_group(self, secgroup_id):
        uri = '%s/security-groups/%s' % (self.uri_prefix, str(secgroup_id))
        return self.delete(uri, self.headers)

    def show_security_group(self, secgroup_id):
        uri = '%s/security-groups/%s' % (self.uri_prefix, str(secgroup_id))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_security_group_rules(self):
        url = '%s/security-group-rules' % (self.uri_prefix)
        resp, body = self.get(url, self.headers)
        rules = self._parse_array(etree.fromstring(body))
        rules = {"security_group_rules": rules}
        return resp, rules

    def create_security_group_rule(self, secgroup_id,
                                   direction='ingress', **kwargs):
        uri = '%s/security-group-rules' % (self.uri_prefix)
        rule = Element("security_group_rule")
        p1 = Element('security_group_id', secgroup_id)
        p2 = Element('direction', direction)
        rule.append(p1)
        rule.append(p2)
        for key, val in kwargs.items():
            key = Element(key, val)
            rule.append(key)
        resp, body = self.post(uri, str(Document(rule)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def delete_security_group_rule(self, rule_id):
        uri = '%s/security-group-rules/%s' % (self.uri_prefix, str(rule_id))
        return self.delete(uri, self.headers)

    def show_security_group_rule(self, rule_id):
        uri = '%s/security-group-rules/%s' % (self.uri_prefix, str(rule_id))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def create_bulk_subnet(self, subnet_list):
        uri = '%s/subnets' % (self.uri_prefix)
        post_body = Element("subnets")
        for i in range(len(subnet_list)):
            v = subnet_list[i]
            p1 = Element("subnet")
            for k, kv in v.iteritems():
                p2 = Element(k, kv)
                p1.append(p2)
            post_body.append(p1)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        subnets = self._parse_array(etree.fromstring(body))
        subnets = {"subnets": subnets}
        return resp, subnets

    def create_bulk_port(self, port_list):
        uri = '%s/ports' % (self.uri_prefix)
        post_body = Element("ports")
        for i in range(len(port_list)):
            v = port_list[i]
            p1 = Element("port")
            for k, kv in v.iteritems():
                p2 = Element(k, kv)
                p1.append(p2)
            post_body.append(p1)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        ports = self._parse_array(etree.fromstring(body))
        ports = {"ports": ports}
        return resp, ports

    def list_vips(self):
        url = '%s/lb/vips' % (self.uri_prefix)
        resp, body = self.get(url, self.headers)
        vips = self._parse_array(etree.fromstring(body))
        vips = {"vips": vips}
        return resp, vips

    def create_vip(self, name, protocol, protocol_port, subnet_id, pool_id):
        uri = '%s/lb/vips' % (self.uri_prefix)
        post_body = Element("vip")
        p1 = Element("name", name)
        p2 = Element("protocol", protocol)
        p3 = Element("protocol_port", protocol_port)
        p4 = Element("subnet_id", subnet_id)
        p5 = Element("pool_id", pool_id)
        post_body.append(p1)
        post_body.append(p2)
        post_body.append(p3)
        post_body.append(p4)
        post_body.append(p5)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def delete_vip(self, vip_id):
        uri = '%s/lb/vips/%s' % (self.uri_prefix, str(vip_id))
        return self.delete(uri, self.headers)

    def show_vip(self, vip_id):
        uri = '%s/lb/vips/%s' % (self.uri_prefix, str(vip_id))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_vip(self, vip_id, new_name):
        uri = '%s/lb/vips/%s' % (self.uri_prefix, str(vip_id))
        put_body = Element("vip")
        p2 = Element("name", new_name)
        put_body.append(p2)
        resp, body = self.put(uri, str(Document(put_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_pools(self):
        url = '%s/lb/pools' % (self.uri_prefix)
        resp, body = self.get(url, self.headers)
        pools = self._parse_array(etree.fromstring(body))
        pools = {"pools": pools}
        return resp, pools

    def create_pool(self, name, lb_method, protocol, subnet_id):
        uri = '%s/lb/pools' % (self.uri_prefix)
        post_body = Element("pool")
        p1 = Element("lb_method", lb_method)
        p2 = Element("protocol", protocol)
        p3 = Element("subnet_id", subnet_id)
        post_body.append(p1)
        post_body.append(p2)
        post_body.append(p3)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def delete_pool(self, pool_id):
        uri = '%s/lb/pools/%s' % (self.uri_prefix, str(pool_id))
        return self.delete(uri, self.headers)

    def show_pool(self, pool_id):
        uri = '%s/lb/pools/%s' % (self.uri_prefix, str(pool_id))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_pool(self, pool_id, new_name):
        uri = '%s/lb/pools/%s' % (self.uri_prefix, str(pool_id))
        put_body = Element("pool")
        p2 = Element("name", new_name)
        put_body.append(p2)
        resp, body = self.put(uri, str(Document(put_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_members(self):
        url = '%s/lb/members' % (self.uri_prefix)
        resp, body = self.get(url, self.headers)
        members = self._parse_array(etree.fromstring(body))
        members = {"members": members}
        return resp, members

    def create_member(self, address, protocol_port, pool_id):
        uri = '%s/lb/members' % (self.uri_prefix)
        post_body = Element("member")
        p1 = Element("address", address)
        p2 = Element("protocol_port", protocol_port)
        p3 = Element("pool_id", pool_id)
        post_body.append(p1)
        post_body.append(p2)
        post_body.append(p3)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def delete_member(self, member_id):
        uri = '%s/lb/members/%s' % (self.uri_prefix, str(member_id))
        return self.delete(uri, self.headers)

    def show_member(self, member_id):
        uri = '%s/lb/members/%s' % (self.uri_prefix, str(member_id))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_member(self, admin_state_up, member_id):
        uri = '%s/lb/members/%s' % (self.uri_prefix, str(member_id))
        put_body = Element("member")
        p2 = Element("admin_state_up", admin_state_up)
        put_body.append(p2)
        resp, body = self.put(uri, str(Document(put_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_health_monitors(self):
        uri = '%s/lb/health_monitors' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = self._parse_array(etree.fromstring(body))
        body = {"health_monitors": body}
        return resp, body

    def create_health_monitor(self, delay, max_retries, Type, timeout):
        uri = '%s/lb/health_monitors' % (self.uri_prefix)
        post_body = Element("health_monitor")
        p1 = Element("delay", delay)
        p2 = Element("max_retries", max_retries)
        p3 = Element("type", Type)
        p4 = Element("timeout", timeout)
        post_body.append(p1)
        post_body.append(p2)
        post_body.append(p3)
        post_body.append(p4)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def delete_health_monitor(self, uuid):
        uri = '%s/lb/health_monitors/%s' % (self.uri_prefix, str(uuid))
        return self.delete(uri, self.headers)

    def show_health_monitor(self, uuid):
        uri = '%s/lb/health_monitors/%s' % (self.uri_prefix, str(uuid))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_health_monitor(self, admin_state_up, uuid):
        uri = '%s/lb/health_monitors/%s' % (self.uri_prefix, str(uuid))
        put_body = Element("health_monitor")
        p2 = Element("admin_state_up", admin_state_up)
        put_body.append(p2)
        resp, body = self.put(uri, str(Document(put_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def associate_health_monitor_with_pool(self, health_monitor_id,
                                           pool_id):
        uri = '%s/lb/pools/%s/health_monitors' % (self.uri_prefix,
                                                  pool_id)
        post_body = Element("health_monitor")
        p1 = Element("id", health_monitor_id,)
        post_body.append(p1)
        resp, body = self.post(uri, str(Document(post_body)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def disassociate_health_monitor_with_pool(self, health_monitor_id,
                                              pool_id):
        uri = '%s/lb/pools/%s/health_monitors/%s' % (self.uri_prefix, pool_id,
                                                     health_monitor_id)
        return self.delete(uri, self.headers)

    def list_extensions(self):
        url = '%s/extensions' % (self.uri_prefix)
        resp, body = self.get(url, self.headers)
        extensions = self._parse_array(etree.fromstring(body))
        extensions = {"extensions": extensions}
        return resp, extensions

    def show_extension_details(self, ext_alias):
        uri = '%s/extensions/%s' % (self.uri_prefix, str(ext_alias))
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def create_router(self, name, **kwargs):
        uri = '%s/routers' % (self.uri_prefix)
        router = Element("router")
        router.append(Element("name", name))
        deep_dict_to_xml(router, kwargs)
        resp, body = self.post(uri, str(Document(router)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def delete_router(self, router_id):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def show_router(self, router_id):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_router(self, router_id, **kwargs):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        router = Element("router")
        for element, content in kwargs.iteritems():
            router.append(Element(element, content))
        resp, body = self.put(uri, str(Document(router)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def add_router_interface_with_subnet_id(self, router_id, subnet_id):
        uri = '%s/routers/%s/add_router_interface' % (self.uri_prefix,
              router_id)
        subnet = Element("subnet_id", subnet_id)
        resp, body = self.put(uri, str(Document(subnet)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def add_router_interface_with_port_id(self, router_id, port_id):
        uri = '%s/routers/%s/add_router_interface' % (self.uri_prefix,
              router_id)
        port = Element("port_id", port_id)
        resp, body = self.put(uri, str(Document(port)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def remove_router_interface_with_subnet_id(self, router_id, subnet_id):
        uri = '%s/routers/%s/remove_router_interface' % (self.uri_prefix,
              router_id)
        subnet = Element("subnet_id", subnet_id)
        resp, body = self.put(uri, str(Document(subnet)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def remove_router_interface_with_port_id(self, router_id, port_id):
        uri = '%s/routers/%s/remove_router_interface' % (self.uri_prefix,
              router_id)
        port = Element("port_id", port_id)
        resp, body = self.put(uri, str(Document(port)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def create_floating_ip(self, ext_network_id, **kwargs):
        uri = '%s/floatingips' % (self.uri_prefix)
        floatingip = Element('floatingip')
        floatingip.append(Element("floating_network_id", ext_network_id))
        for element, content in kwargs.iteritems():
            floatingip.append(Element(element, content))
        resp, body = self.post(uri, str(Document(floatingip)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def show_floating_ip(self, floating_ip_id):
        uri = '%s/floatingips/%s' % (self.uri_prefix, floating_ip_id)
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_floating_ips(self):
        uri = '%s/floatingips' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        floatingips = self._parse_array(etree.fromstring(body))
        floatingips = {"floatingips": floatingips}
        return resp, floatingips

    def delete_floating_ip(self, floating_ip_id):
        uri = '%s/floatingips/%s' % (self.uri_prefix, floating_ip_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def update_floating_ip(self, floating_ip_id, **kwargs):
        uri = '%s/floatingips/%s' % (self.uri_prefix, floating_ip_id)
        floatingip = Element('floatingip')
        floatingip.add_attr('xmlns:xsi',
                            'http://www.w3.org/2001/XMLSchema-instance')
        for element, content in kwargs.iteritems():
            if content is None:
                xml_elem = Element(element)
                xml_elem.add_attr("xsi:nil", "true")
                floatingip.append(xml_elem)
            else:
                floatingip.append(Element(element, content))
        resp, body = self.put(uri, str(Document(floatingip)), self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_router_interfaces(self, uuid):
        uri = '%s/ports?device_id=%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        ports = self._parse_array(etree.fromstring(body))
        ports = {"ports": ports}
        return resp, ports

    def list_agents(self):
        uri = '%s/agents' % self.uri_prefix
        resp, body = self.get(uri, self.headers)
        agents = self._parse_array(etree.fromstring(body))
        agents = {'agents': agents}
        return resp, agents

    def show_agent(self, agent_id):
        uri = '%s/agents/%s' % (self.uri_prefix, agent_id)
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_agent(self, agent_id, agent_info):
        uri = '%s/agents/%s' % (self.uri_prefix, agent_id)
        agent = Element('agent')
        for (key, value) in agent_info.items():
            p = Element(key, value)
            agent.append(p)
        resp, body = self.put(uri, body=str(Document(agent)),
                              headers=self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_routers_on_l3_agent(self, agent_id):
        uri = '%s/agents/%s/l3-routers' % (self.uri_prefix, agent_id)
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_l3_agents_hosting_router(self, router_id):
        uri = '%s/routers/%s/l3-agents' % (self.uri_prefix, router_id)
        resp, body = self.get(uri, self.headers)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_service_providers(self):
        uri = '%s/service-providers' % self.uri_prefix
        resp, body = self.get(uri, self.headers)
        providers = self._parse_array(etree.fromstring(body))
        body = {'service_providers': providers}
        return resp, body

    def list_dhcp_agent_hosting_network(self, network_id):
        uri = '%s/networks/%s/dhcp-agents' % (self.uri_prefix, network_id)
        resp, body = self.get(uri, self.headers)
        agents = self._parse_array(etree.fromstring(body))
        body = {'agents': agents}
        return resp, body

    def list_networks_hosted_by_one_dhcp_agent(self, agent_id):
        uri = '%s/agents/%s/dhcp-networks' % (self.uri_prefix, agent_id)
        resp, body = self.get(uri, self.headers)
        networks = self._parse_array(etree.fromstring(body))
        body = {'networks': networks}
        return resp, body

    def remove_network_from_dhcp_agent(self, agent_id, network_id):
        uri = '%s/agents/%s/dhcp-networks/%s' % (self.uri_prefix, agent_id,
                                                 network_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body


def _root_tag_fetcher_and_xml_to_json_parse(xml_returned_body):
    body = ET.fromstring(xml_returned_body)
    root_tag = body.tag
    if root_tag.startswith("{"):
        ns, root_tag = root_tag.split("}", 1)
    body = xml_to_json(etree.fromstring(xml_returned_body))
    nil = '{http://www.w3.org/2001/XMLSchema-instance}nil'
    for key, val in body.iteritems():
        if isinstance(val, dict):
            if (nil in val and val[nil] == 'true'):
                body[key] = None
    body = {root_tag: body}
    return body
