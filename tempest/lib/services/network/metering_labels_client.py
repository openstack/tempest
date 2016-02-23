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


class MeteringLabelsClient(base.BaseNetworkClient):

    def create_metering_label(self, **kwargs):
        uri = '/metering/metering-labels'
        post_data = {'metering_label': kwargs}
        return self.create_resource(uri, post_data)

    def show_metering_label(self, metering_label_id, **fields):
        uri = '/metering/metering-labels/%s' % metering_label_id
        return self.show_resource(uri, **fields)

    def delete_metering_label(self, metering_label_id):
        uri = '/metering/metering-labels/%s' % metering_label_id
        return self.delete_resource(uri)

    def list_metering_labels(self, **filters):
        uri = '/metering/metering-labels'
        return self.list_resources(uri, **filters)
