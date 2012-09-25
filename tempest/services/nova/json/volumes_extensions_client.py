from tempest import exceptions
from tempest.common.rest_client import RestClient
import json
import time


class VolumesExtensionsClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(VolumesExtensionsClientJSON, self).__init__(config, username,
                                                          password, auth_url,
                                                          tenant_name)
        self.service = self.config.compute.catalog_type
        self.build_interval = self.config.volume.build_interval
        self.build_timeout = self.config.volume.build_timeout

    def list_volumes(self, params=None):
        """List all the volumes created"""
        url = 'os-volumes'
        if params is not None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url += '?' + ' '.join(param_list)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['volumes']

    def list_volumes_with_detail(self, params=None):
        """List all the details of volumes"""
        url = 'os-volumes/detail'
        if params is not None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url = '?' + ' '.join(param_list)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['volumes']

    def get_volume(self, volume_id):
        """Returns the details of a single volume"""
        url = "os-volumes/%s" % str(volume_id)
        resp, body = self.get(url)
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
        resp, body = self.post('os-volumes', post_body, self.headers)
        body = json.loads(body)
        return resp, body['volume']

    def delete_volume(self, volume_id):
        """Deletes the Specified Volume"""
        return self.delete("os-volumes/%s" % str(volume_id))

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
                raise exceptions.VolumeBuildErrorException(volume_id=volume_id)

            if int(time.time()) - start >= self.build_timeout:
                message = ('Volume %s failed to reach %s status within '
                           'the required time (%s s).' %
                           (volume_name, status, self.build_timeout))
                raise exceptions.TimeoutException(message)

    def is_resource_deleted(self, id):
        try:
            self.get_volume(id)
        except exceptions.NotFound:
            return True
        return False
