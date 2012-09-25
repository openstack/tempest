import json
from tempest.common.rest_client import RestClient


class NetworkClient(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(NetworkClient, self).__init__(config, username, password,
                                            auth_url, tenant_name)
        self.service = self.config.network.catalog_type

    def list_networks(self):
        resp, body = self.get('networks')
        body = json.loads(body)
        return resp, body

    def create_network(self, name, key="network"):
        post_body = {
            key: {
              'name': name
             }
        }
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(post_body)
        resp, body = self.post('networks', headers=headers, body=body)
        body = json.loads(body)
        return resp, body

    def list_networks_details(self):
        resp, body = self.get('networks/detail')
        body = json.loads(body)
        return resp, body

    def get_network(self, uuid):
        resp, body = self.get('networks/%s' % uuid)
        body = json.loads(body)
        return resp, body

    def get_network_details(self, uuid):
        resp, body = self.get('networks/%s/detail' % uuid)
        body = json.loads(body)
        return resp, body

    def delete_network(self, uuid):
        resp, body = self.delete('networks/%s' % uuid)
        return resp, body

    def create_port(self, network_id, zone, state=None, key='port'):
        if not state:
            state = 'ACTIVE'
        post_body = {
            key: {
                'state': state,
                'nova_id': zone
            }
        }
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(post_body)
        resp, body = self.post('networks/%s/ports.json' % network_id,
                               headers=headers, body=body)
        body = json.loads(body)
        return resp, body

    def delete_port(self, network_id, port_id):
        resp, body = self.delete('networks/%s/ports/%s.json' %
                                 (network_id, port_id))
        return resp, body

    def list_ports(self, network_id):
        resp, body = self.get('networks/%s/ports.json' % network_id)
        body = json.loads(body)
        return resp, body

    def list_port_details(self, network_id):
        url = 'networks/%s/ports/detail.json' % network_id
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body

    def attach_port(self, network_id, port_id, interface_id):
        post_body = {
            'attachment': {
                'id': interface_id
            }
        }
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(post_body)
        url = 'networks/%s/ports/%s/attachment.json' % (network_id, port_id)
        resp, body = self.put(url, headers=headers, body=body)
        return resp, body

    def detach_port(self, network_id, port_id):
        url = 'networks/%s/ports/%s/attachment.json' % (network_id, port_id)
        resp, body = self.delete(url)
        return resp, body

    def list_port_attachment(self, network_id, port_id):
        url = 'networks/%s/ports/%s/attachment.json' % (network_id, port_id)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body
