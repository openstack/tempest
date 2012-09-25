from tempest.common.rest_client import RestClient
import json


class KeyPairsClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(KeyPairsClientJSON, self).__init__(config, username, password,
                                                 auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def list_keypairs(self):
        resp, body = self.get("os-keypairs")
        body = json.loads(body)
        #Each returned keypair is embedded within an unnecessary 'keypair'
        #element which is a deviation from other resources like floating-ips,
        #servers, etc. A bug?
        #For now we shall adhere to the spec, but the spec for keypairs
        #is yet to be found
        return resp, body['keypairs']

    def get_keypair(self, key_name):
        resp, body = self.get("os-keypairs/%s" % str(key_name))
        body = json.loads(body)
        return resp, body['keypair']

    def create_keypair(self, name, pub_key=None):
        post_body = {'keypair': {'name': name}}
        if pub_key:
            post_body['keypair']['public_key'] = pub_key
        post_body = json.dumps(post_body)
        resp, body = self.post("os-keypairs",
                               headers=self.headers, body=post_body)
        body = json.loads(body)
        return resp, body['keypair']

    def delete_keypair(self, key_name):
        return self.delete("os-keypairs/%s" % str(key_name))
