from tempest import exceptions
from tempest.common import rest_client
import json
import time


class VolumesClient(object):

    def __init__(self, config, username, key, auth_url, tenant_name=None):
        self.config = config
        catalog_type = self.config.nova.catalog_type
        self.client = rest_client.RestClient(config, username, key, auth_url,
                                             catalog_type, tenant_name)
        self.build_interval = self.config.nova.build_interval
        self.build_timeout = self.config.nova.build_timeout
        self.headers = {'Content-Type': 'application/json',
                        'Accept': 'application/json'}

    def list_volumes(self, params=None):
        """List all the volumes created"""
        url = 'os-volumes'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url += '?' + ' '.join(param_list)

        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body['volumes']

    def list_volumes_with_detail(self, params=None):
        """List all the details of volumes"""
        url = 'os-volumes/detail'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url = '?' + ' '.join(param_list)

        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body['volumes']

    def get_volume(self, volume_id):
        """Returns the details of a single volume"""
        url = "os-volumes/%s" % str(volume_id)
        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body['volume']

    def create_volume(self, size, **kwargs):
        """
        Creates a new Volume.
        size(Required): Size of volume in GB.
        Following optional keyword arguments are accepted:
        display_name: Optional Volume Name.
        metadata: A dictionary of values to be used as metadata.
        """
        post_body = {
            'size': size,
            'display_name': kwargs.get('display_name'),
            'metadata': kwargs.get('metadata'),
            }

        post_body = json.dumps({'volume': post_body})
        resp, body = self.client.post('os-volumes', post_body, self.headers)
        body = json.loads(body)
        return resp, body['volume']

    def delete_volume(self, volume_id):
        """Deletes the Specified Volume"""
        return self.client.delete("os-volumes/%s" % str(volume_id))

    def wait_for_volume_status(self, volume_id, status):
        """Waits for a Volume to reach a given status"""
        resp, body = self.get_volume(volume_id)
        volume_name = body['displayName']
        volume_status = body['status']
        start = int(time.time())

        while volume_status != status:
            time.sleep(self.build_interval)
            resp, body = self.get_volume(volume_id)
            volume_status = body['status']
            if volume_status == 'error':
                raise exceptions.BuildErrorException(volume_id=volume_id)

            if int(time.time()) - start >= self.build_timeout:
                message = 'Volume %s failed to reach %s status within '\
                'the required time (%s s).' % (volume_name, status,
                                              self.build_timeout)
                raise exceptions.TimeoutException(message)
