import json

import kong.common.http
from kong import exceptions


class API(kong.common.http.Client):
    """Barebones Nova HTTP API client."""

    def __init__(self, host, port, base_url, user, api_key, project_id=''):
        """Initialize Nova HTTP API client.

        :param host: Hostname/IP of the Nova API to test.
        :param port: Port of the Nova API to test.
        :param base_url: Version identifier (normally /v1.0 or /v1.1)
        :param user: The username to use for tests.
        :param api_key: The API key of the user.
        :returns: None

        """
        super(API, self).__init__(host, port, base_url)
        self.user = user
        self.api_key = api_key
        self.project_id = project_id
        # Default to same as base_url, but will be changed for auth
        self.management_url = self.base_url

    def authenticate(self, user, api_key, project_id):
        """Request and return an authentication token from Nova.

        :param user: The username we're authenticating.
        :param api_key: The API key for the user we're authenticating.
        :returns: Authentication token (string)
        :raises: KeyError if authentication fails.

        """
        headers = {
            'X-Auth-User': user,
            'X-Auth-Key': api_key,
            'X-Auth-Project-Id': project_id,
        }
        resp, body = super(API, self).request('GET', '', headers=headers,
                                              base_url=self.base_url)

        try:
            self.management_url = resp['x-server-management-url']
            return resp['x-auth-token']
        except KeyError:
            print "Failed to authenticate user"
            raise

    def _wait_for_entity_status(self, url, entity_name, status, **kwargs):
        """Poll the provided url until expected entity status is returned"""

        def check_response(resp, body):
            try:
                data = json.loads(body)
                return data[entity_name]['status'] == status
            except (ValueError, KeyError):
                return False

        try:
            self.poll_request('GET', url, check_response, **kwargs)
        except exceptions.TimeoutException:
            msg = "%s failed to reach status %s" % (entity_name, status)
            raise AssertionError(msg)

    def wait_for_server_status(self, server_id, status='ACTIVE', **kwargs):
        """Wait for the server status to be equal to the status passed in.

        :param server_id: Server ID to query.
        :param status: The status string to look for.
        :returns: None
        :raises: AssertionError if request times out

        """
        url = '/servers/%s' % server_id
        return self._wait_for_entity_status(url, 'server', status, **kwargs)

    def wait_for_image_status(self, image_id, status='ACTIVE', **kwargs):
        """Wait for the image status to be equal to the status passed in.

        :param image_id: Image ID to query.
        :param status: The status string to look for.
        :returns: None
        :raises: AssertionError if request times out

        """
        url = '/images/%s' % image_id
        return self._wait_for_entity_status(url, 'image', status, **kwargs)

    def request(self, method, url, **kwargs):
        """Generic HTTP request on the Nova API.

        :param method: Request verb to use (GET, PUT, POST, etc.)
        :param url: The API resource to request.
        :param kwargs: Additional keyword arguments to pass to the request.
        :returns: HTTP response object.

        """
        headers = kwargs.get('headers', {})
        project_id = kwargs.get('project_id', self.project_id)

        headers['X-Auth-Token'] = self.authenticate(self.user, self.api_key,
                                                    project_id)
        kwargs['headers'] = headers
        return super(API, self).request(method, url, **kwargs)

    def get_server(self, server_id):
        """Fetch a server by id

        :param server_id: dict of server attributes
        :returns: dict of server attributes
        :raises: ServerNotFound if server does not exist

        """
        resp, body = self.request('GET', '/servers/%s' % server_id)
        try:
            assert resp['status'] == '200'
            data = json.loads(body)
            return data['server']
        except (AssertionError, ValueError, TypeError, KeyError):
            raise exceptions.ServerNotFound(server_id)

    def create_server(self, entity):
        """Attempt to create a new server.

        :param entity: dict of server attributes
        :returns: dict of server attributes after creation
        :raises: AssertionError if server creation fails

        """
        post_body = json.dumps({
            'server': entity,
        })

        resp, body = self.request('POST', '/servers', body=post_body)
        try:
            assert resp['status'] == '202'
            data = json.loads(body)
            return data['server']
        except (AssertionError, ValueError, TypeError, KeyError):
            raise AssertionError("Failed to create server")

    def delete_server(self, server_id):
        """Attempt to delete a server.

        :param server_id: server identifier
        :returns: None

        """
        url = '/servers/%s' % server_id
        response, body = self.request('DELETE', url)
