# Copyright 2013 Hewlett-Packard Development Company, L.P.
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


class AttributeDict(dict):

    """
    Provide attribute access (dict.key) to dictionary values.
    """

    def __getattr__(self, name):
        """Allow attribute access for all keys in the dict."""
        if name in self:
            return self[name]
        return super(AttributeDict, self).__getattribute__(name)


class DeletableResource(AttributeDict):

    """
    Support deletion of neutron resources (networks, subnets) via a
    delete() method, as is supported by keystone and nova resources.
    """

    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        super(DeletableResource, self).__init__(*args, **kwargs)

    def __str__(self):
        return '<%s id="%s" name="%s">' % (self.__class__.__name__,
                                           self.id, self.name)

    def delete(self):
        raise NotImplemented()

    def __hash__(self):
        return id(self)


class DeletableNetwork(DeletableResource):

    def delete(self):
        self.client.delete_network(self.id)


class DeletableSubnet(DeletableResource):

    def __init__(self, *args, **kwargs):
        super(DeletableSubnet, self).__init__(*args, **kwargs)
        self._router_ids = set()

    def update(self, *args, **kwargs):
        body = dict(subnet=dict(*args, **kwargs))
        result = self.client.update_subnet(subnet=self.id, body=body)
        super(DeletableSubnet, self).update(**result['subnet'])

    def add_to_router(self, router_id):
        self._router_ids.add(router_id)
        body = dict(subnet_id=self.id)
        self.client.add_interface_router(router_id, body=body)

    def delete(self):
        for router_id in self._router_ids.copy():
            body = dict(subnet_id=self.id)
            self.client.remove_interface_router(router_id, body=body)
            self._router_ids.remove(router_id)
        self.client.delete_subnet(self.id)


class DeletableRouter(DeletableResource):

    def add_gateway(self, network_id):
        body = dict(network_id=network_id)
        self.client.add_gateway_router(self.id, body=body)

    def delete(self):
        self.client.remove_gateway_router(self.id)
        self.client.delete_router(self.id)


class DeletableFloatingIp(DeletableResource):

    def update(self, *args, **kwargs):
        result = self.client.update_floatingip(floatingip=self.id,
                                               body=dict(
                                                   floatingip=dict(*args,
                                                                   **kwargs)
                                               ))
        super(DeletableFloatingIp, self).update(**result['floatingip'])

    def __repr__(self):
        return '<%s addr="%s">' % (self.__class__.__name__,
                                   self.floating_ip_address)

    def __str__(self):
        return '<"FloatingIP" addr="%s" id="%s">' % (self.floating_ip_address,
                                                     self.id)

    def delete(self):
        self.client.delete_floatingip(self.id)


class DeletablePort(DeletableResource):

    def delete(self):
        self.client.delete_port(self.id)


class DeletableSecurityGroup(DeletableResource):

    def delete(self):
        self.client.delete_security_group(self.id)


class DeletableSecurityGroupRule(DeletableResource):

    def __repr__(self):
        return '<%s id="%s">' % (self.__class__.__name__, self.id)

    def delete(self):
        self.client.delete_security_group_rule(self.id)


class DeletablePool(DeletableResource):

    def delete(self):
        self.client.delete_pool(self.id)


class DeletableMember(DeletableResource):

    def delete(self):
        self.client.delete_member(self.id)


class DeletableVip(DeletableResource):

    def delete(self):
        self.client.delete_vip(self.id)
