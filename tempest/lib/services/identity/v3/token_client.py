# Copyright 2015 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib import exceptions


class V3TokenClient(rest_client.RestClient):

    def __init__(self, auth_url, disable_ssl_certificate_validation=None,
                 ca_certs=None, trace_requests=None, **kwargs):
        """Initialises the Token client

        :param auth_url: URL to which the token request is sent
        :param disable_ssl_certificate_validation: pass-through to rest client
        :param ca_certs: pass-through to rest client
        :param trace_requests: pass-through to rest client
        :param kwargs: any extra parameter to pass through the rest client.
               Three kwargs are forbidden: region, service and auth_provider
               as they are not meaningful for token client
        """
        dscv = disable_ssl_certificate_validation
        for unwanted_kwargs in ['region', 'service', 'auth_provider']:
            kwargs.pop(unwanted_kwargs, None)
        super(V3TokenClient, self).__init__(
            None, None, None, disable_ssl_certificate_validation=dscv,
            ca_certs=ca_certs, trace_requests=trace_requests, **kwargs)

        if auth_url is None:
            raise exceptions.IdentityError("Couldn't determine auth_url")

        if 'auth/tokens' not in auth_url:
            auth_url = auth_url.rstrip('/') + '/auth/tokens'

        self.auth_url = auth_url

    def auth(self, user_id=None, username=None, password=None, project_id=None,
             project_name=None, user_domain_id=None, user_domain_name=None,
             project_domain_id=None, project_domain_name=None, domain_id=None,
             domain_name=None, system=None, token=None, app_cred_id=None,
             app_cred_secret=None):
        """Obtains a token from the authentication service

        :param user_id: user id
        :param username: user name
        :param user_domain_id: the user domain id
        :param user_domain_name: the user domain name
        :param project_domain_id: the project domain id
        :param project_domain_name: the project domain name
        :param domain_id: a domain id to scope to
        :param domain_name: a domain name to scope to
        :param project_id: a project id to scope to
        :param project_name: a project name to scope to
        :param system: whether the token should be scoped to the system
        :param token: a token to re-scope.

        Accepts different combinations of credentials.
        Sample sample valid combinations:
        - token
        - token, project_name, project_domain_id
        - user_id, password
        - username, password, user_domain_id
        - username, password, project_name, user_domain_id, project_domain_id
        - username, password, user_domain_id, system
        Validation is left to the server side.
        """
        creds = {
            'auth': {
                'identity': {
                    'methods': [],
                }
            }
        }
        id_obj = creds['auth']['identity']
        if token:
            id_obj['methods'].append('token')
            id_obj['token'] = {
                'id': token
            }

        if (user_id or username) and password:
            id_obj['methods'].append('password')
            id_obj['password'] = {
                'user': {
                    'password': password,
                }
            }
            if user_id:
                id_obj['password']['user']['id'] = user_id
            else:
                id_obj['password']['user']['name'] = username

            _domain = None
            if user_domain_id is not None:
                _domain = dict(id=user_domain_id)
            elif user_domain_name is not None:
                _domain = dict(name=user_domain_name)
            if _domain:
                id_obj['password']['user']['domain'] = _domain

        if app_cred_id and app_cred_secret:
            id_obj['methods'].append('application_credential')
            id_obj['application_credential'] = {
                'id': app_cred_id,
                'secret': app_cred_secret,
            }

        if (project_id or project_name):
            _project = dict()

            if project_id:
                _project['id'] = project_id
            elif project_name:
                _project['name'] = project_name

            if project_domain_id is not None:
                _project['domain'] = {'id': project_domain_id}
            elif project_domain_name is not None:
                _project['domain'] = {'name': project_domain_name}

            creds['auth']['scope'] = dict(project=_project)
        elif domain_id:
            creds['auth']['scope'] = dict(domain={'id': domain_id})
        elif domain_name:
            creds['auth']['scope'] = dict(domain={'name': domain_name})
        elif system:
            creds['auth']['scope'] = dict(system={system: True})

        body = json.dumps(creds, sort_keys=True)
        resp, body = self.post(self.auth_url, body=body)
        self.expected_success(201, resp.status)
        return rest_client.ResponseBody(resp, body)

    def request(self, method, url, extra_headers=False, headers=None,
                body=None, chunked=False):
        """A simple HTTP request interface.

        Note: this overloads the `request` method from the parent class and
        thus must implement the same method signature.
        """
        if headers is None:
            # Always accept 'json', for xml token client too.
            # Because XML response is not easily
            # converted to the corresponding JSON one
            headers = self.get_headers(accept_type="json")
        elif extra_headers:
            try:
                headers.update(self.get_headers(accept_type="json"))
            except (ValueError, TypeError):
                headers = self.get_headers(accept_type="json")

        resp, resp_body = self.raw_request(url, method,
                                           headers=headers, body=body,
                                           log_req_body='<omitted>')
        if resp.status in [401, 403]:
            resp_body = json.loads(resp_body)
            raise exceptions.Unauthorized(resp_body['error']['message'])
        elif resp.status not in [200, 201, 204]:
            raise exceptions.IdentityError(
                'Unexpected status code {0}'.format(resp.status))

        return resp, json.loads(resp_body)

    def get_token(self, **kwargs):
        """Returns (token id, token data) for supplied credentials"""

        auth_data = kwargs.pop('auth_data', False)

        if not (kwargs.get('user_domain_id') or
                kwargs.get('user_domain_name')):
            kwargs['user_domain_name'] = 'Default'

        if not (kwargs.get('project_domain_id') or
                kwargs.get('project_domain_name')):
            kwargs['project_domain_name'] = 'Default'

        body = self.auth(**kwargs)

        token = body.response.get('x-subject-token')
        if auth_data:
            return token, body['token']
        else:
            return token
