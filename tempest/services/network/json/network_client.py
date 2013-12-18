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

import json

from tempest.common.rest_client import RestClient
from tempest.services.network import network_client_base


class NetworkClientJSON(network_client_base.NetworkClientBase):

    """
    Tempest REST client for Neutron. Uses v2 of the Neutron API, since the
    V1 API has been removed from the code base.

    Implements create, delete, update, list and show for the basic Neutron
    abstractions (networks, sub-networks, routers, ports and floating IP):

    Implements add/remove interface to router using subnet ID / port ID

    It also implements list, show, update and reset for OpenStack Networking
    quotas
    """

    def get_rest_client(self, config, username,
                        password, auth_url, tenant_name=None):
        return RestClient(config, username, password, auth_url, tenant_name)

    def deserialize_single(self, body):
        return json.loads(body)

    def deserialize_list(self, body):
        res = json.loads(body)
        # expecting response in form
        # {'resources': [ res1, res2] }
        return res[res.keys()[0]]

    def serialize(self, data):
        return json.dumps(data)

    def serialize_list(self, data, root=None, item=None):
        return self.serialize(data)

    def update_quotas(self, tenant_id, **kwargs):
        put_body = {'quota': kwargs}
        body = json.dumps(put_body)
        uri = '%s/quotas/%s' % (self.uri_prefix, tenant_id)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body['quota']

    def reset_quotas(self, tenant_id):
        uri = '%s/quotas/%s' % (self.uri_prefix, tenant_id)
        resp, body = self.delete(uri)
        return resp, body

    def create_router(self, name, admin_state_up=True, **kwargs):
        post_body = {'router': kwargs}
        post_body['router']['name'] = name
        post_body['router']['admin_state_up'] = admin_state_up
        body = json.dumps(post_body)
        uri = '%s/routers' % (self.uri_prefix)
        resp, body = self.post(uri, body)
        body = json.loads(body)
        return resp, body

    def _update_router(self, router_id, set_enable_snat, **kwargs):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        resp, body = self.get(uri)
        body = json.loads(body)
        update_body = {}
        update_body['name'] = kwargs.get('name', body['router']['name'])
        update_body['admin_state_up'] = kwargs.get(
            'admin_state_up', body['router']['admin_state_up'])
        cur_gw_info = body['router']['external_gateway_info']
        if cur_gw_info and not set_enable_snat:
            cur_gw_info.pop('enable_snat', None)
        update_body['external_gateway_info'] = kwargs.get(
            'external_gateway_info', body['router']['external_gateway_info'])
        update_body = dict(router=update_body)
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body)
        body = json.loads(body)
        return resp, body

    def update_router(self, router_id, **kwargs):
        """Update a router leaving enable_snat to its default value."""
        # If external_gateway_info contains enable_snat the request will fail
        # with 404 unless executed with admin client, and therefore we instruct
        # _update_router to not set this attribute
        # NOTE(salv-orlando): The above applies as long as Neutron's default
        # policy is to restrict enable_snat usage to admins only.
        return self._update_router(router_id, set_enable_snat=False, **kwargs)

    def update_router_with_snat_gw_info(self, router_id, **kwargs):
        """Update a router passing also the enable_snat attribute.

        This method must be execute with admin credentials, otherwise the API
        call will return a 404 error.
        """
        return self._update_router(router_id, set_enable_snat=True, **kwargs)

    def add_router_interface_with_subnet_id(self, router_id, subnet_id):
        uri = '%s/routers/%s/add_router_interface' % (self.uri_prefix,
              router_id)
        update_body = {"subnet_id": subnet_id}
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body)
        body = json.loads(body)
        return resp, body

    def add_router_interface_with_port_id(self, router_id, port_id):
        uri = '%s/routers/%s/add_router_interface' % (self.uri_prefix,
              router_id)
        update_body = {"port_id": port_id}
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body)
        body = json.loads(body)
        return resp, body

    def remove_router_interface_with_subnet_id(self, router_id, subnet_id):
        uri = '%s/routers/%s/remove_router_interface' % (self.uri_prefix,
              router_id)
        update_body = {"subnet_id": subnet_id}
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body)
        body = json.loads(body)
        return resp, body

    def remove_router_interface_with_port_id(self, router_id, port_id):
        uri = '%s/routers/%s/remove_router_interface' % (self.uri_prefix,
              router_id)
        update_body = {"port_id": port_id}
        update_body = json.dumps(update_body)
        resp, body = self.put(uri, update_body)
        body = json.loads(body)
        return resp, body

    def create_floating_ip(self, ext_network_id, **kwargs):
        post_body = {
            'floatingip': kwargs}
        post_body['floatingip']['floating_network_id'] = ext_network_id
        body = json.dumps(post_body)
        uri = '%s/floatingips' % (self.uri_prefix)
        resp, body = self.post(uri, body=body)
        body = json.loads(body)
        return resp, body

    def create_security_group(self, name, **kwargs):
        post_body = {
            'security_group': {
                'name': name,
            }
        }
        for key, value in kwargs.iteritems():
            post_body['security_group'][str(key)] = value
        body = json.dumps(post_body)
        uri = '%s/security-groups' % (self.uri_prefix)
        resp, body = self.post(uri, body)
        body = json.loads(body)
        return resp, body

    def update_floating_ip(self, floating_ip_id, **kwargs):
        post_body = {
            'floatingip': kwargs}
        body = json.dumps(post_body)
        uri = '%s/floatingips/%s' % (self.uri_prefix, floating_ip_id)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body

    def create_security_group_rule(self, secgroup_id,
                                   direction='ingress', **kwargs):
        post_body = {
            'security_group_rule': {
                'direction': direction,
                'security_group_id': secgroup_id
            }
        }
        for key, value in kwargs.iteritems():
            post_body['security_group_rule'][str(key)] = value
        body = json.dumps(post_body)
        uri = '%s/security-group-rules' % (self.uri_prefix)
        resp, body = self.post(uri, body)
        body = json.loads(body)
        return resp, body

    def create_vip(self, name, protocol, protocol_port, subnet_id, pool_id):
        post_body = {
            "vip": {
                "protocol": protocol,
                "name": name,
                "subnet_id": subnet_id,
                "pool_id": pool_id,
                "protocol_port": protocol_port
            }
        }
        body = json.dumps(post_body)
        uri = '%s/lb/vips' % (self.uri_prefix)
        resp, body = self.post(uri, body)
        body = json.loads(body)
        return resp, body

    def update_vip(self, vip_id, new_name):
        put_body = {
            "vip": {
                "name": new_name,
            }
        }
        body = json.dumps(put_body)
        uri = '%s/lb/vips/%s' % (self.uri_prefix, vip_id)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body

    def create_member(self, address, protocol_port, pool_id):
        post_body = {
            "member": {
                "protocol_port": protocol_port,
                "pool_id": pool_id,
                "address": address
            }
        }
        body = json.dumps(post_body)
        uri = '%s/lb/members' % (self.uri_prefix)
        resp, body = self.post(uri, body)
        body = json.loads(body)
        return resp, body

    def update_member(self, admin_state_up, member_id):
        put_body = {
            "member": {
                "admin_state_up": admin_state_up
            }
        }
        body = json.dumps(put_body)
        uri = '%s/lb/members/%s' % (self.uri_prefix, member_id)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body

    def create_health_monitor(self, delay, max_retries, Type, timeout):
        post_body = {
            "health_monitor": {
                "delay": delay,
                "max_retries": max_retries,
                "type": Type,
                "timeout": timeout
            }
        }
        body = json.dumps(post_body)
        uri = '%s/lb/health_monitors' % (self.uri_prefix)
        resp, body = self.post(uri, body)
        body = json.loads(body)
        return resp, body

    def update_health_monitor(self, admin_state_up, uuid):
        put_body = {
            "health_monitor": {
                "admin_state_up": admin_state_up
            }
        }
        body = json.dumps(put_body)
        uri = '%s/lb/health_monitors/%s' % (self.uri_prefix, uuid)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body

    def associate_health_monitor_with_pool(self, health_monitor_id,
                                           pool_id):
        post_body = {
            "health_monitor": {
                "id": health_monitor_id,
            }
        }
        body = json.dumps(post_body)
        uri = '%s/lb/pools/%s/health_monitors' % (self.uri_prefix,
                                                  pool_id)
        resp, body = self.post(uri, body)
        body = json.loads(body)
        return resp, body

    def disassociate_health_monitor_with_pool(self, health_monitor_id,
                                              pool_id):
        uri = '%s/lb/pools/%s/health_monitors/%s' % (self.uri_prefix, pool_id,
                                                     health_monitor_id)
        resp, body = self.delete(uri)
        return resp, body

    def create_vpnservice(self, subnet_id, router_id, **kwargs):
        post_body = {
            "vpnservice": {
                "subnet_id": subnet_id,
                "router_id": router_id
            }
        }
        for key, val in kwargs.items():
            post_body['vpnservice'][key] = val
        body = json.dumps(post_body)
        uri = '%s/vpn/vpnservices' % (self.uri_prefix)
        resp, body = self.post(uri, body)
        body = json.loads(body)
        return resp, body

    def update_vpnservice(self, uuid, description):
        put_body = {
            "vpnservice": {
                "description": description
            }
        }
        body = json.dumps(put_body)
        uri = '%s/vpn/vpnservices/%s' % (self.uri_prefix, uuid)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body

    def list_router_interfaces(self, uuid):
        uri = '%s/ports?device_id=%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri)
        body = json.loads(body)
        return resp, body

    def update_agent(self, agent_id, agent_info):
        """
        :param agent_info: Agent update information.
        E.g {"admin_state_up": True}
        """
        uri = '%s/agents/%s' % (self.uri_prefix, agent_id)
        agent = {"agent": agent_info}
        body = json.dumps(agent)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body

    def list_routers_on_l3_agent(self, agent_id):
        uri = '%s/agents/%s/l3-routers' % (self.uri_prefix, agent_id)
        resp, body = self.get(uri)
        body = json.loads(body)
        return resp, body

    def list_l3_agents_hosting_router(self, router_id):
        uri = '%s/routers/%s/l3-agents' % (self.uri_prefix, router_id)
        resp, body = self.get(uri)
        body = json.loads(body)
        return resp, body

    def list_dhcp_agent_hosting_network(self, network_id):
        uri = '%s/networks/%s/dhcp-agents' % (self.uri_prefix, network_id)
        resp, body = self.get(uri)
        body = json.loads(body)
        return resp, body

    def list_networks_hosted_by_one_dhcp_agent(self, agent_id):
        uri = '%s/agents/%s/dhcp-networks' % (self.uri_prefix, agent_id)
        resp, body = self.get(uri)
        body = json.loads(body)
        return resp, body

    def remove_network_from_dhcp_agent(self, agent_id, network_id):
        uri = '%s/agents/%s/dhcp-networks/%s' % (self.uri_prefix, agent_id,
                                                 network_id)
        resp, body = self.delete(uri)
        return resp, body

    def create_ikepolicy(self, name, **kwargs):
        post_body = {
            "ikepolicy": {
                "name": name,
            }
        }
        for key, val in kwargs.items():
            post_body['ikepolicy'][key] = val
        body = json.dumps(post_body)
        uri = '%s/vpn/ikepolicies' % (self.uri_prefix)
        resp, body = self.post(uri, body)
        body = json.loads(body)
        return resp, body

    def update_ikepolicy(self, uuid, **kwargs):
        put_body = {'ikepolicy': kwargs}
        body = json.dumps(put_body)
        uri = '%s/vpn/ikepolicies/%s' % (self.uri_prefix, uuid)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body

    def update_extra_routes(self, router_id, nexthop, destination):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        put_body = {
            'router': {
                'routes': [{'nexthop': nexthop,
                            "destination": destination}]
            }
        }
        body = json.dumps(put_body)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body

    def delete_extra_routes(self, router_id):
        uri = '%s/routers/%s' % (self.uri_prefix, router_id)
        null_routes = None
        put_body = {
            'router': {
                'routes': null_routes
            }
        }
        body = json.dumps(put_body)
        resp, body = self.put(uri, body)
        body = json.loads(body)
        return resp, body
