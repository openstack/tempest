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

from oslo_log import log as logging
from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib import exceptions
from tempest.lib.services.identity.v3 import token_client

import six

class K2KTokenClient(rest_client.RestClient):
    def __init__(self, auth_url, password,
                 disable_ssl_certificate_validation=None,
                 ca_certs=None, trace_requests=None):
	self.token_client = token_client.V3TokenClient(auth_url)

	r, b = self.get_credentials(password)
	self.sp_id = b['token']['service_providers'][0]['id']
        self.ecp_url = str(b['token']['service_providers'][0]['sp_url'])
        self.sp_auth_url = str(b['token']['service_providers'][0]['auth_url'])
	#self.sp_ip contains the port number 5000
    	self.sp_ip = str(b['token']['service_providers'][0]['sp_url'].split('/')[2])

    
    def get_token(self, **kwargs):
        return self.token_client.get_token(**kwargs)

    
    def auth(self, **kwargs):
        return self.token_client.auth(**kwargs)


    def _get_ecp_assertion(self, token=None):
	"""Obtains a token from the authentication service
        :param sp_id: registered Service Provider id in Identity Provider
        :param token: a token to perform K2K Federation.
        Accepts one combinations of credentials.
        - token, sp_id
        Validation is left to the Service Provider side.
        """
        body = {
            "auth": {
                "identity": {
                    "methods": [
                        "token"
                    ],
                    "token": {
                        "id": token
                    }
                },
                "scope": {
                    "service_provider": {
                        "id": self.sp_id
                    }
                }
            }
        }
	
	self.body = body
	url = 'http://localhost:5000/v3/auth/OS-FEDERATION/saml2/ecp'
	endpoint_filter = {'version': (3, 0),
                           'interface': 'public'}

        headers = {'Accept': 'application/json'}

        resp, body = self.token_client.post(url=url,
                               body=json.dumps(body, sort_keys=True),
                               headers=headers, saml='saml2')

        self.expected_success(200, resp.status)
        return six.text_type(body)


    def get_unscoped_token(self, assertion):
        """Send assertion to a Keystone SP and get an unscoped token"""
	
        r, b = self.token_client.post(
            url=self.ecp_url,
            headers={'Content-Type': 'application/vnd.paos+xml'},
            body=assertion, saml='saml2')
	
	cookie = r['set-cookie'].split(';')[0]
        headers={'Content-Type': 'application/vnd.paos+xml',
                 'Cookie': cookie}
        resp, body = self.token_client.get(url=self.sp_auth_url, headers=headers)
        fed_token_id = resp['x-subject-token']
        return fed_token_id


    def get_scoped_token(self, _token):
	"""Send an unscoped token and get a scoped token"""
	
	headers = {'x-auth-token': _token,
                   'Content-Type': 'application/json'}

	sp_auth_url = 'http://'+ self.sp_ip  +'/v3/auth/tokens'
	#this is very ugly, needs to change. 
	self.token_client.auth_url = sp_auth_url	
	r = self.auth(token=_token)
        scoped_token_id = str(r['token']['user']['OS-FEDERATION']['groups'][0]['id'])
	return scoped_token_id


    def get_credentials(self, password):
        """ Get a token with default scope containing the service
	    provider's credentials""" 
	body = {
            "auth": {
              "identity": {
                "methods": ["password"
                 ],
                 "password": {
                   "user": {
                     "name": "admin",
                     "domain": { "id": "default"
                      },
                     "password": password
                  }
                }
              }
            }
          }

        headers = {"Content-Type": "application/json"}
        url = 'http://localhost:5000/v3/auth/tokens'
        r, b = self.token_client.post(url=url, headers=headers, body=json.dumps(body))
	return r, b

