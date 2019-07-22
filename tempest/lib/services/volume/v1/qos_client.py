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

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc


class QosSpecsClient(rest_client.RestClient):
    """Volume V1 QoS client.

       Client class to send CRUD QoS API requests
    """

    api_version = "v1"

    def is_resource_deleted(self, qos_id):
        try:
            self.show_qos(qos_id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'qos'

    def create_qos(self, **kwargs):
        """Create a QoS Specification.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#create-qos-specification
        """
        post_body = json.dumps({'qos_specs': kwargs})
        resp, body = self.post('qos-specs', post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_qos(self, qos_id, force=False):
        """Delete the specified QoS specification."""
        resp, body = self.delete(
            "qos-specs/%s?force=%s" % (qos_id, force))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_qos(self):
        """List all the QoS specifications created."""
        url = 'qos-specs'
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_qos(self, qos_id):
        """Get the specified QoS specification."""
        url = "qos-specs/%s" % qos_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def set_qos_key(self, qos_id, **kwargs):
        """Set the specified keys/values of QoS specification.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#set-keys-in-qos-specification
        """
        put_body = json.dumps({"qos_specs": kwargs})
        resp, body = self.put('qos-specs/%s' % qos_id, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def unset_qos_key(self, qos_id, keys):
        """Unset the specified keys of QoS specification.

        :param keys: keys to delete from the QoS specification.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#unset-keys-in-qos-specification
        """
        put_body = json.dumps({'keys': keys})
        resp, body = self.put('qos-specs/%s/delete_keys' % qos_id, put_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def associate_qos(self, qos_id, vol_type_id):
        """Associate the specified QoS with specified volume-type."""
        url = "qos-specs/%s/associate" % qos_id
        url += "?vol_type_id=%s" % vol_type_id
        resp, body = self.get(url)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_association_qos(self, qos_id):
        """Get the association of the specified QoS specification."""
        url = "qos-specs/%s/associations" % qos_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def disassociate_qos(self, qos_id, vol_type_id):
        """Disassociate the specified QoS with specified volume-type."""
        url = "qos-specs/%s/disassociate" % qos_id
        url += "?vol_type_id=%s" % vol_type_id
        resp, body = self.get(url)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def disassociate_all_qos(self, qos_id):
        """Disassociate the specified QoS with all associations."""
        url = "qos-specs/%s/disassociate_all" % qos_id
        resp, body = self.get(url)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)
