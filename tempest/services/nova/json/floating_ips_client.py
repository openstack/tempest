from tempest.common import rest_client
from tempest import exceptions
import json


class FloatingIPsClient(object):
    def __init__(self, config, username, key, auth_url, tenant_name=None):
        self.config = config
        self.client = rest_client.RestClient(config, username, key,
                                             auth_url, 'nova', tenant_name)
        self.headers = {'Content-Type': 'application/json',
                        'Accept': 'application/json'}

    def list_floating_ips(self, params=None):
        """Returns a list of all floating IPs filtered by any parameters"""
        url = 'os-floating-ips'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))
            url += '?' + ' '.join(param_list)
        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body['floating_ips']

    def get_floating_ip_details(self, floating_ip_id):
        """Get the details of a floating IP"""
        url = "os-floating-ips/%s" % str(floating_ip_id)
        resp, body = self.client.get(url)
        body = json.loads(body)
        if resp.status == 404:
            raise exceptions.NotFound(body)
        return resp, body['floating_ip']

    def create_floating_ip(self):
        """Allocate a floating IP to the project"""
        url = 'os-floating-ips'
        resp, body = self.client.post(url, None, None)
        body = json.loads(body)
        return resp, body['floating_ip']

    def delete_floating_ip(self, floating_ip_id):
        """Deletes the provided floating IP from the project"""
        url = "os-floating-ips/%s" % str(floating_ip_id)
        resp, body = self.client.delete(url)
        return resp, body

    def associate_floating_ip_to_server(self, floating_ip, server_id):
        """Associate the provided floating IP to a specific server"""
        url = "servers/%s/action" % str(server_id)
        post_body = {
            'addFloatingIp': {
                'address': floating_ip,
            }
        }

        post_body = json.dumps(post_body)
        resp, body = self.client.post(url, post_body, self.headers)
        return resp, body

    def disassociate_floating_ip_from_server(self, floating_ip, server_id):
        """Disassociate the provided floating IP from a specific server"""
        url = "servers/%s/action" % str(server_id)
        post_body = {
            'removeFloatingIp': {
                'address': floating_ip,
            }
        }

        post_body = json.dumps(post_body)
        resp, body = self.client.post(url, post_body, self.headers)
        return resp, body
