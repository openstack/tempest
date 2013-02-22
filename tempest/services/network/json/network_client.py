import json
from tempest.common.rest_client import RestClient


class NetworkClient(RestClient):

    """
    Tempest REST client for Quantum. Uses v2 of the Quantum API, since the
    V1 API has been removed from the code base.

    Implements the following operations for each one of the basic Quantum
    abstractions (networks, sub-networks and ports):

    create
    delete
    list
    show
    """

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(NetworkClient, self).__init__(config, username, password,
                                            auth_url, tenant_name)
        self.service = self.config.network.catalog_type
        self.version = '2.0'
        self.uri_prefix = "v%s" % (self.version)

    def list_networks(self):
        uri = '%s/networks' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_network(self, name):
        post_body = {
            'network': {
                'name': name,
            }
        }
        body = json.dumps(post_body)
        uri = '%s/networks' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def show_network(self, uuid):
        uri = '%s/networks/%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def delete_network(self, uuid):
        uri = '%s/networks/%s' % (self.uri_prefix, uuid)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def create_subnet(self, net_uuid, cidr):
        post_body = dict(
            subnet=dict(
                ip_version=4,
                network_id=net_uuid,
                cidr=cidr),)
        body = json.dumps(post_body)
        uri = '%s/subnets' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def delete_subnet(self, uuid):
        uri = '%s/subnets/%s' % (self.uri_prefix, uuid)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def list_subnets(self):
        uri = '%s/subnets' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def show_subnet(self, uuid):
        uri = '%s/subnets/%s' % (self.uri_prefix, uuid)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def create_port(self, network_id, state=None):
        if not state:
            state = True
        post_body = {
            'port': {
                'network_id': network_id,
                'admin_state_up': state,
            }
        }
        body = json.dumps(post_body)
        uri = '%s/ports' % (self.uri_prefix)
        resp, body = self.post(uri, headers=self.headers, body=body)
        body = json.loads(body)
        return resp, body

    def delete_port(self, port_id):
        uri = '%s/ports/%s' % (self.uri_prefix, port_id)
        resp, body = self.delete(uri, self.headers)
        return resp, body

    def list_ports(self):
        uri = '%s/ports' % (self.uri_prefix)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body

    def show_port(self, port_id):
        uri = '%s/ports/%s' % (self.uri_prefix, port_id)
        resp, body = self.get(uri, self.headers)
        body = json.loads(body)
        return resp, body
