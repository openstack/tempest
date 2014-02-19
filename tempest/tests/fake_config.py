# Copyright 2013 IBM Corp.
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


class FakeConfig(object):

    class fake_compute(object):
        build_interval = 10
        build_timeout = 10

    class fake_identity(object):
        disable_ssl_certificate_validation = True
        catalog_type = 'identity'
        uri = 'http://fake_uri.com/auth'
        uri_v3 = 'http://fake_uri_v3.com/auth'

    class fake_default_feature_enabled(object):
        api_extensions = ['all']

    class fake_compute_feature_enabled(fake_default_feature_enabled):
        api_v3_extensions = ['all']

    class fake_object_storage_discoverable_apis(object):
        discoverable_apis = ['all']

    class fake_service_available(object):
        nova = True
        glance = True
        cinder = True
        heat = True
        neutron = True
        swift = True
        horizon = True

    compute_feature_enabled = fake_compute_feature_enabled()
    volume_feature_enabled = fake_default_feature_enabled()
    network_feature_enabled = fake_default_feature_enabled()
    object_storage_feature_enabled = fake_object_storage_discoverable_apis()

    service_available = fake_service_available()

    compute = fake_compute()
    identity = fake_identity()
