# Copyright 2014 IBM Corp.
# All Rights Reserved.
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

import json

import httplib2

FAKE_AUTH_URL = 'http://fake_uri.com/auth'

TOKEN = "fake_token"
ALT_TOKEN = "alt_fake_token"

# Fake Identity v2 constants
COMPUTE_ENDPOINTS_V2 = {
    "endpoints": [
        {
            "adminURL": "http://fake_url/v2/first_endpoint/admin",
            "region": "NoMatchRegion",
            "internalURL": "http://fake_url/v2/first_endpoint/internal",
            "publicURL": "http://fake_url/v2/first_endpoint/public"
        },
        {
            "adminURL": "http://fake_url/v2/second_endpoint/admin",
            "region": "FakeRegion",
            "internalURL": "http://fake_url/v2/second_endpoint/internal",
            "publicURL": "http://fake_url/v2/second_endpoint/public"
        },
    ],
    "type": "compute",
    "name": "nova"
}

CATALOG_V2 = [COMPUTE_ENDPOINTS_V2, ]

ALT_IDENTITY_V2_RESPONSE = {
    "access": {
        "token": {
            "expires": "2020-01-01T00:00:10Z",
            "id": ALT_TOKEN,
            "tenant": {
                "id": "fake_tenant_id"
            },
        },
        "user": {
            "id": "fake_user_id",
        },
        "serviceCatalog": CATALOG_V2,
    },
}

IDENTITY_V2_RESPONSE = {
    "access": {
        "token": {
            "expires": "2020-01-01T00:00:10Z",
            "id": TOKEN,
            "tenant": {
                "id": "fake_tenant_id"
            },
        },
        "user": {
            "id": "fake_user_id",
        },
        "serviceCatalog": CATALOG_V2,
    },
}

# Fake Identity V3 constants
COMPUTE_ENDPOINTS_V3 = {
    "endpoints": [
        {
            "id": "first_compute_fake_service",
            "interface": "public",
            "region": "NoMatchRegion",
            "url": "http://fake_url/v3/first_endpoint/api"
        },
        {
            "id": "second_fake_service",
            "interface": "public",
            "region": "FakeRegion",
            "url": "http://fake_url/v3/second_endpoint/api"
        },
        {
            "id": "third_fake_service",
            "interface": "admin",
            "region": "MiddleEarthRegion",
            "url": "http://fake_url/v3/third_endpoint/api"
        }

    ],
    "type": "compute",
    "id": "fake_compute_endpoint"
}

CATALOG_V3 = [COMPUTE_ENDPOINTS_V3, ]

IDENTITY_V3_RESPONSE = {
    "token": {
        "methods": [
            "token",
            "password"
        ],
        "expires_at": "2020-01-01T00:00:10.000123Z",
        "project": {
            "domain": {
                "id": "fake_domain_id",
                "name": "fake"
            },
            "id": "project_id",
            "name": "project_name"
        },
        "user": {
            "domain": {
                "id": "fake_domain_id",
                "name": "domain_name"
            },
            "id": "fake_user_id",
            "name": "username"
        },
        "issued_at": "2013-05-29T16:55:21.468960Z",
        "catalog": CATALOG_V3
    }
}

ALT_IDENTITY_V3 = IDENTITY_V3_RESPONSE


def _fake_v3_response(self, uri, method="GET", body=None, headers=None,
                      redirections=5, connection_type=None):
    fake_headers = {
        "status": "201",
        "x-subject-token": TOKEN
    }
    return (httplib2.Response(fake_headers),
            json.dumps(IDENTITY_V3_RESPONSE))


def _fake_v2_response(self, uri, method="GET", body=None, headers=None,
                      redirections=5, connection_type=None):
    return (httplib2.Response({"status": "200"}),
            json.dumps(IDENTITY_V2_RESPONSE))


def _fake_auth_failure_response():
    # the response body isn't really used in this case, but lets send it anyway
    # to have a safe check in some future change on the rest client.
    body = {
        "unauthorized": {
            "message": "Unauthorized",
            "code": "401"
        }
    }
    return httplib2.Response({"status": "401"}), json.dumps(body)
