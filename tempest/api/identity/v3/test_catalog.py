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

from tempest.api.identity import base
from tempest import config
from tempest.lib import decorators


CONF = config.CONF


class IdentityCatalogTest(base.BaseIdentityV3Test):
    """Test service's catalog type values"""

    @decorators.idempotent_id('56b57ced-22b8-4127-9b8a-565dfb0207e2')
    def test_catalog_standardization(self):
        """Test that every service has a standard catalog type value"""
        # https://opendev.org/openstack/service-types-authority
        # /src/branch/master/service-types.yaml
        standard_service_values = [{'name': 'keystone', 'type': 'identity'},
                                   {'name': 'nova', 'type': 'compute'},
                                   {'name': 'glance', 'type': 'image'},
                                   {'name': 'swift', 'type': 'object-store'}]
        # next, we need to GET the catalog using the catalog client
        catalog = self.non_admin_catalog_client.show_catalog()['catalog']
        # get list of the service types present in the catalog
        catalog_services = [service['type'] for service in catalog]
        for service in standard_service_values:
            # if service enabled, check if it has a standard type value
            if service['name'] == 'keystone' or\
                    getattr(CONF.service_available, service['name']):
                self.assertIn(service['type'], catalog_services)
