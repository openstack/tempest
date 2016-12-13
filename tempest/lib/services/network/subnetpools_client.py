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

from tempest.lib.services.network import base


class SubnetpoolsClient(base.BaseNetworkClient):

    def list_subnetpools(self, **filters):
        """Lists subnet pools to which the tenant has access.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#listSubnetPools
        """
        uri = '/subnetpools'
        return self.list_resources(uri, **filters)

    def create_subnetpool(self, **kwargs):
        """Creates a subnet pool.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#createSubnetPool
        """
        uri = '/subnetpools'
        post_data = {'subnetpool': kwargs}
        return self.create_resource(uri, post_data)

    def show_subnetpool(self, subnetpool_id, **fields):
        """Shows information for a subnet pool.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#showSubnetPool
        """
        uri = '/subnetpools/%s' % subnetpool_id
        return self.show_resource(uri, **fields)

    def update_subnetpool(self, subnetpool_id, **kwargs):
        """Updates a subnet pool.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#updateSubnetPool
        """
        uri = '/subnetpools/%s' % subnetpool_id
        post_data = {'subnetpool': kwargs}
        return self.update_resource(uri, post_data)

    def delete_subnetpool(self, subnetpool_id):
        uri = '/subnetpools/%s' % subnetpool_id
        return self.delete_resource(uri)
