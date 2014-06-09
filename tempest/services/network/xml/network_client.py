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

from tempest.common import rest_client
from tempest.common import xml_utils as common
from tempest.services.network import network_client_base as client_base


class NetworkClientXML(client_base.NetworkClientBase):
    TYPE = "xml"

    # list of plurals used for xml serialization
    PLURALS = ['dns_nameservers', 'host_routes', 'allocation_pools',
               'fixed_ips', 'extensions', 'extra_dhcp_opts', 'pools',
               'health_monitors', 'vips', 'members', 'allowed_address_pairs']

    def get_rest_client(self, auth_provider):
        rc = rest_client.RestClient(auth_provider)
        rc.TYPE = self.TYPE
        return rc

    def deserialize_list(self, body):
        return common.parse_array(etree.fromstring(body), self.PLURALS)

    def deserialize_single(self, body):
        return _root_tag_fetcher_and_xml_to_json_parse(body)

    def serialize(self, body):
        # TODO(enikanorov): implement better json to xml conversion
        # expecting the dict with single key
        root = body.keys()[0]
        post_body = common.Element(root)
        post_body.add_attr('xmlns:xsi',
                           'http://www.w3.org/2001/XMLSchema-instance')
        elements = set()
        for name, attr in body[root].items():
            elt = self._get_element(name, attr)
            post_body.append(elt)
            if ":" in name:
                elements.add(name.split(":")[0])
        if elements:
            self._add_namespaces(post_body, elements)
        return str(common.Document(post_body))

    def serialize_list(self, body, root_name=None, item_name=None):
        # expecting dict in form
        # body = {'resources': [res_dict1, res_dict2, ...]
        post_body = common.Element(root_name)
        post_body.add_attr('xmlns:xsi',
                           'http://www.w3.org/2001/XMLSchema-instance')
        for item in body[body.keys()[0]]:
            elt = common.Element(item_name)
            for name, attr in item.items():
                elt_content = self._get_element(name, attr)
                elt.append(elt_content)
            post_body.append(elt)
        return str(common.Document(post_body))

    def _get_element(self, name, value):
        if value is None:
            xml_elem = common.Element(name)
            xml_elem.add_attr("xsi:nil", "true")
            return xml_elem
        elif isinstance(value, dict):
            dict_element = common.Element(name)
            for key, value in value.iteritems():
                elem = self._get_element(key, value)
                dict_element.append(elem)
            return dict_element
        elif isinstance(value, list):
            list_element = common.Element(name)
            for element in value:
                elem = self._get_element(name[:-1], element)
                list_element.append(elem)
            return list_element
        else:
            return common.Element(name, value)

    def _add_namespaces(self, root, elements):
        for element in elements:
            root.add_attr('xmlns:%s' % element,
                          common.NEUTRON_NAMESPACES[element])

    def associate_health_monitor_with_pool(self, health_monitor_id,
                                           pool_id):
        uri = '%s/lb/pools/%s/health_monitors' % (self.uri_prefix,
                                                  pool_id)
        post_body = common.Element("health_monitor")
        p1 = common.Element("id", health_monitor_id,)
        post_body.append(p1)
        resp, body = self.post(uri, str(common.Document(post_body)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def disassociate_health_monitor_with_pool(self, health_monitor_id,
                                              pool_id):
        uri = '%s/lb/pools/%s/health_monitors/%s' % (self.uri_prefix, pool_id,
                                                     health_monitor_id)
        return self.delete(uri)

    def show_extension_details(self, ext_alias):
        uri = '%s/extensions/%s' % (self.uri_prefix, str(ext_alias))
        resp, body = self.get(uri)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def create_router(self, name, **kwargs):
        uri = '%s/routers' % (self.uri_prefix)
        router = common.Element("router")
        router.append(common.Element("name", name))
        common.deep_dict_to_xml(router, kwargs)
        resp, body = self.post(uri, str(common.Document(router)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def update_router(self, router_id, **kwargs):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        router = common.Element("router")
        for element, content in kwargs.iteritems():
            router.append(common.Element(element, content))
        resp, body = self.put(uri, str(common.Document(router)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def add_router_interface_with_subnet_id(self, router_id, subnet_id):
        uri = '%s/routers/%s/add_router_interface' % (self.uri_prefix,
              router_id)
        subnet = common.Element("subnet_id", subnet_id)
        resp, body = self.put(uri, str(common.Document(subnet)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def add_router_interface_with_port_id(self, router_id, port_id):
        uri = '%s/routers/%s/add_router_interface' % (self.uri_prefix,
              router_id)
        port = common.Element("port_id", port_id)
        resp, body = self.put(uri, str(common.Document(port)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def remove_router_interface_with_subnet_id(self, router_id, subnet_id):
        uri = '%s/routers/%s/remove_router_interface' % (self.uri_prefix,
              router_id)
        subnet = common.Element("subnet_id", subnet_id)
        resp, body = self.put(uri, str(common.Document(subnet)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def remove_router_interface_with_port_id(self, router_id, port_id):
        uri = '%s/routers/%s/remove_router_interface' % (self.uri_prefix,
              router_id)
        port = common.Element("port_id", port_id)
        resp, body = self.put(uri, str(common.Document(port)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_router_interfaces(self, uuid):
        uri = '%s/ports?device_id=%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri)
        ports = common.parse_array(etree.fromstring(body), self.PLURALS)
        ports = {"ports": ports}
        return resp, ports

    def update_agent(self, agent_id, agent_info):
        uri = '%s/agents/%s' % (self.uri_prefix, agent_id)
        agent = common.Element('agent')
        for (key, value) in agent_info.items():
            p = common.Element(key, value)
            agent.append(p)
        resp, body = self.put(uri, str(common.Document(agent)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_pools_hosted_by_one_lbaas_agent(self, agent_id):
        uri = '%s/agents/%s/loadbalancer-pools' % (self.uri_prefix, agent_id)
        resp, body = self.get(uri)
        pools = common.parse_array(etree.fromstring(body))
        body = {'pools': pools}
        return resp, body

    def show_lbaas_agent_hosting_pool(self, pool_id):
        uri = ('%s/lb/pools/%s/loadbalancer-agent' %
               (self.uri_prefix, pool_id))
        resp, body = self.get(uri)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def list_routers_on_l3_agent(self, agent_id):
        uri = '%s/agents/%s/l3-routers' % (self.uri_prefix, agent_id)
        resp, body = self.get(uri)
        routers = common.parse_array(etree.fromstring(body))
        body = {'routers': routers}
        return resp, body

    def list_l3_agents_hosting_router(self, router_id):
        uri = '%s/routers/%s/l3-agents' % (self.uri_prefix, router_id)
        resp, body = self.get(uri)
        agents = common.parse_array(etree.fromstring(body))
        body = {'agents': agents}
        return resp, body

    def add_router_to_l3_agent(self, agent_id, router_id):
        uri = '%s/agents/%s/l3-routers' % (self.uri_prefix, agent_id)
        router = (common.Element("router_id", router_id))
        resp, body = self.post(uri, str(common.Document(router)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def remove_router_from_l3_agent(self, agent_id, router_id):
        uri = '%s/agents/%s/l3-routers/%s' % (
            self.uri_prefix, agent_id, router_id)
        resp, body = self.delete(uri)
        return resp, body

    def list_dhcp_agent_hosting_network(self, network_id):
        uri = '%s/networks/%s/dhcp-agents' % (self.uri_prefix, network_id)
        resp, body = self.get(uri)
        agents = common.parse_array(etree.fromstring(body))
        body = {'agents': agents}
        return resp, body

    def list_networks_hosted_by_one_dhcp_agent(self, agent_id):
        uri = '%s/agents/%s/dhcp-networks' % (self.uri_prefix, agent_id)
        resp, body = self.get(uri)
        networks = common.parse_array(etree.fromstring(body))
        body = {'networks': networks}
        return resp, body

    def remove_network_from_dhcp_agent(self, agent_id, network_id):
        uri = '%s/agents/%s/dhcp-networks/%s' % (self.uri_prefix, agent_id,
                                                 network_id)
        resp, body = self.delete(uri)
        return resp, body

    def list_lb_pool_stats(self, pool_id):
        uri = '%s/lb/pools/%s/stats' % (self.uri_prefix, pool_id)
        resp, body = self.get(uri)
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body

    def add_dhcp_agent_to_network(self, agent_id, network_id):
        uri = '%s/agents/%s/dhcp-networks' % (self.uri_prefix, agent_id)
        network = common.Element("network_id", network_id)
        resp, body = self.post(uri, str(common.Document(network)))
        body = _root_tag_fetcher_and_xml_to_json_parse(body)
        return resp, body


def _root_tag_fetcher_and_xml_to_json_parse(xml_returned_body):
    body = ET.fromstring(xml_returned_body)
    root_tag = body.tag
    if root_tag.startswith("{"):
        ns, root_tag = root_tag.split("}", 1)
    body = common.xml_to_json(etree.fromstring(xml_returned_body),
                              NetworkClientXML.PLURALS)
    nil = '{http://www.w3.org/2001/XMLSchema-instance}nil'
    for key, val in body.iteritems():
        if isinstance(val, dict):
            if (nil in val and val[nil] == 'true'):
                body[key] = None
    body = {root_tag: body}
    return body
