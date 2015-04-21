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
import time

from tempest_lib import exceptions as lib_exc

from tempest.common import service_client
from tempest import exceptions


class BaseQosSpecsClientJSON(service_client.ServiceClient):
    """Client class to send CRUD QoS API requests"""

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

    def wait_for_qos_operations(self, qos_id, operation, args=None):
        """Waits for a qos operations to be completed.

        NOTE : operation value is required for  wait_for_qos_operations()
        operation = 'qos-key' / 'disassociate' / 'disassociate-all'
        args = keys[] when operation = 'qos-key'
        args = volume-type-id disassociated when operation = 'disassociate'
        args = None when operation = 'disassociate-all'
        """
        start_time = int(time.time())
        while True:
            if operation == 'qos-key-unset':
                body = self.show_qos(qos_id)
                if not any(key in body['specs'] for key in args):
                    return
            elif operation == 'disassociate':
                body = self.show_association_qos(qos_id)
                if not any(args in body[i]['id'] for i in range(0, len(body))):
                    return
            elif operation == 'disassociate-all':
                body = self.show_association_qos(qos_id)
                if not body:
                    return
            else:
                msg = (" operation value is either not defined or incorrect.")
                raise lib_exc.UnprocessableEntity(msg)

            if int(time.time()) - start_time >= self.build_timeout:
                raise exceptions.TimeoutException
            time.sleep(self.build_interval)

    def create_qos(self, name, consumer, **kwargs):
        """Create a QoS Specification.

        name : name of the QoS specifications
        consumer : conumer of Qos ( front-end / back-end / both )
        """
        post_body = {'name': name, 'consumer': consumer}
        post_body.update(kwargs)
        post_body = json.dumps({'qos_specs': post_body})
        resp, body = self.post('qos-specs', post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body['qos_specs'])

    def delete_qos(self, qos_id, force=False):
        """Delete the specified QoS specification."""
        resp, body = self.delete(
            "qos-specs/%s?force=%s" % (str(qos_id), force))
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def list_qos(self):
        """List all the QoS specifications created."""
        url = 'qos-specs'
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBodyList(resp, body['qos_specs'])

    def show_qos(self, qos_id):
        """Get the specified QoS specification."""
        url = "qos-specs/%s" % str(qos_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['qos_specs'])

    def set_qos_key(self, qos_id, **kwargs):
        """Set the specified keys/values of QoS specification.

        kwargs : it is the dictionary of the key=value pairs to set
        """
        put_body = json.dumps({"qos_specs": kwargs})
        resp, body = self.put('qos-specs/%s' % qos_id, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['qos_specs'])

    def unset_qos_key(self, qos_id, keys):
        """Unset the specified keys of QoS specification.

        keys : it is the array of the keys to unset
        """
        put_body = json.dumps({'keys': keys})
        resp, body = self.put('qos-specs/%s/delete_keys' % qos_id, put_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def associate_qos(self, qos_id, vol_type_id):
        """Associate the specified QoS with specified volume-type."""
        url = "qos-specs/%s/associate" % str(qos_id)
        url += "?vol_type_id=%s" % vol_type_id
        resp, body = self.get(url)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def show_association_qos(self, qos_id):
        """Get the association of the specified QoS specification."""
        url = "qos-specs/%s/associations" % str(qos_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBodyList(resp, body['qos_associations'])

    def disassociate_qos(self, qos_id, vol_type_id):
        """Disassociate the specified QoS with specified volume-type."""
        url = "qos-specs/%s/disassociate" % str(qos_id)
        url += "?vol_type_id=%s" % vol_type_id
        resp, body = self.get(url)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def disassociate_all_qos(self, qos_id):
        """Disassociate the specified QoS with all associations."""
        url = "qos-specs/%s/disassociate_all" % str(qos_id)
        resp, body = self.get(url)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)


class QosSpecsClientJSON(BaseQosSpecsClientJSON):
    """Volume V1 QoS client."""
