from tempest.common import rest_client
import json


class KeyPairsClient(object):

    def __init__(self, config, username, key, auth_url, tenant_name=None):
        self.config = config
        catalog_type = self.config.nova.catalog_type
        self.client = rest_client.RestClient(config, username, key,
                                             auth_url, catalog_type,
                                             tenant_name)
        self.headers = {'Content-Type': 'application/json',
                        'Accept': 'application/json'}

    def list_keypairs(self):
        resp, body = self.client.get("os-keypairs")
        body = json.loads(body)
        #Each returned keypair is embedded within an unnecessary 'keypair'
        #element which is a deviation from other resources like floating-ips,
        #servers, etc. A bug?
        #For now we shall adhere to the spec, but the spec for keypairs
        #is yet to be found
        return resp, body['keypairs']

    def get_keypair(self, key_name):
        resp, body = self.client.get("os-keypairs/%s" % str(key_name))
        body = json.loads(body)
        return resp, body['keypair']

    def create_keypair(self, name, pub_key=None):
        post_body = {'keypair': {'name': name}}
        if pub_key:
            post_body['keypair']['public_key'] = pub_key
        post_body = json.dumps(post_body)
        resp, body = self.client.post("os-keypairs",
                                headers=self.headers, body=post_body)
        body = json.loads(body)
        return resp, body['keypair']

    def delete_keypair(self, key_name):
        return self.client.delete("os-keypairs/%s" % str(key_name))
