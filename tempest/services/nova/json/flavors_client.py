from tempest.common import rest_client
import json
import time


class FlavorsClient(object):

    def __init__(self, config, username, key, auth_url, tenant_name=None):
        self.config = config
        self.client = rest_client.RestClient(config, username, key,
                                             auth_url, tenant_name)

    def list_flavors(self, params=None):
        url = 'flavors'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url = "flavors?" + "".join(param_list)

        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body

    def list_flavors_with_detail(self, params=None):
        url = 'flavors/detail'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url = "flavors/detail?" + "".join(param_list)

        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body

    def get_flavor_details(self, flavor_id):
        resp, body = self.client.get("flavors/%s" % str(flavor_id))
        body = json.loads(body)
        return resp, body['flavor']
