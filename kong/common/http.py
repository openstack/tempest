from kong import exceptions

import httplib2
import os
import time


class Client(object):

    USER_AGENT = 'python-nova_test_client'

    def __init__(self, host='localhost', port=80, base_url=''):
        #TODO: join these more robustly
        self.base_url = "http://%s:%s/%s" % (host, port, base_url)

    def poll_request(self, method, url, check_response, **kwargs):

        timeout = kwargs.pop('timeout', 180)
        interval = kwargs.pop('interval', 2)
        # Start timestamp
        start_ts = int(time.time())

        while True:
            resp, body = self.request(method, url, **kwargs)
            if (check_response(resp, body)):
                break
            if (int(time.time()) - start_ts >= timeout):
                raise exceptions.TimeoutException
            time.sleep(interval)

    def poll_request_status(self, method, url, status=200, **kwargs):

        def check_response(resp, body):
            return resp['status'] == str(status)

        self.poll_request(method, url, check_response, **kwargs)


    def request(self, method, url, **kwargs):
        # Default to management_url, but can be overridden here 
        # (for auth requests)
        base_url = kwargs.get('base_url', self.management_url)

        self.http_obj = httplib2.Http()

        params = {}
        params['headers'] = {'User-Agent': self.USER_AGENT}
        params['headers'].update(kwargs.get('headers', {}))
        if 'Content-Type' not in params.get('headers',{}):
            params['headers']['Content-Type'] = 'application/json'

        if 'body' in kwargs:
            params['body'] = kwargs.get('body')

        req_url = os.path.join(base_url, url.strip('/'))
        resp, body = self.http_obj.request(req_url, method, **params)
        return resp, body
