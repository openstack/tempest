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

import functools

from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions as exc
from tempest import test

CONF = config.CONF


def creates(resource):
    """Decorator that adds resources to the appropriate cleanup list."""

    def decorator(f):
        @functools.wraps(f)
        def wrapper(cls, *args, **kwargs):
            result = f(cls, *args, **kwargs)
            body = result[resource]

            if 'uuid' in body:
                cls.created_objects[resource].add(body['uuid'])

            return result
        return wrapper
    return decorator


class BaseBaremetalTest(test.BaseTestCase):
    """Base class for Baremetal API tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseBaremetalTest, cls).setUpClass()

        if not CONF.service_available.ironic:
            skip_msg = ('%s skipped as Ironic is not available' % cls.__name__)
            raise cls.skipException(skip_msg)

        mgr = clients.AdminManager()
        cls.client = mgr.baremetal_client

        cls.created_objects = {'chassis': set(),
                               'port': set(),
                               'node': set()}

    @classmethod
    def tearDownClass(cls):
        """Ensure that all created objects get destroyed."""

        try:
            for resource, uuids in cls.created_objects.iteritems():
                delete_method = getattr(cls.client, 'delete_%s' % resource)
                for u in uuids:
                    delete_method(u, ignore_errors=exc.NotFound)
        finally:
            super(BaseBaremetalTest, cls).tearDownClass()

    @classmethod
    @creates('chassis')
    def create_chassis(cls, description=None, expect_errors=False):
        """
        Wrapper utility for creating test chassis.

        :param description: A description of the chassis. if not supplied,
            a random value will be generated.
        :return: Created chassis.

        """
        description = description or data_utils.rand_name('test-chassis-')
        resp, body = cls.client.create_chassis(description=description)

        return {'chassis': body, 'response': resp}

    @classmethod
    @creates('node')
    def create_node(cls, chassis_id, cpu_arch='x86', cpu_num=8, storage=1024,
                    memory=4096, driver='fake'):
        """
        Wrapper utility for creating test baremetal nodes.

        :param cpu_arch: CPU architecture of the node. Default: x86.
        :param cpu_num: Number of CPUs. Default: 8.
        :param storage: Disk size. Default: 1024.
        :param memory: Available RAM. Default: 4096.
        :return: Created node.

        """
        resp, body = cls.client.create_node(chassis_id, cpu_arch=cpu_arch,
                                            cpu_num=cpu_num, storage=storage,
                                            memory=memory, driver=driver)

        return {'node': body, 'response': resp}

    @classmethod
    @creates('port')
    def create_port(cls, node_id, address, extra=None, uuid=None):
        """
        Wrapper utility for creating test ports.

        :param address: MAC address of the port.
        :param extra: Meta data of the port. If not supplied, an empty
            dictionary will be created.
        :param uuid: UUID of the port.
        :return: Created port.

        """
        extra = extra or {}
        resp, body = cls.client.create_port(address=address, node_id=node_id,
                                            extra=extra, uuid=uuid)

        return {'port': body, 'response': resp}

    @classmethod
    def delete_chassis(cls, chassis_id):
        """
        Deletes a chassis having the specified UUID.

        :param uuid: The unique identifier of the chassis.
        :return: Server response.

        """

        resp, body = cls.client.delete_chassis(chassis_id)

        if chassis_id in cls.created_objects['chassis']:
            cls.created_objects['chassis'].remove(chassis_id)

        return resp

    @classmethod
    def delete_node(cls, node_id):
        """
        Deletes a node having the specified UUID.

        :param uuid: The unique identifier of the node.
        :return: Server response.

        """

        resp, body = cls.client.delete_node(node_id)

        if node_id in cls.created_objects['node']:
            cls.created_objects['node'].remove(node_id)

        return resp

    @classmethod
    def delete_port(cls, port_id):
        """
        Deletes a port having the specified UUID.

        :param uuid: The unique identifier of the port.
        :return: Server response.

        """

        resp, body = cls.client.delete_port(port_id)

        if port_id in cls.created_objects['port']:
            cls.created_objects['port'].remove(port_id)

        return resp

    def validate_self_link(self, resource, uuid, link):
        """Check whether the given self link formatted correctly."""
        expected_link = "{base}/{pref}/{res}/{uuid}".format(
                        base=self.client.base_url,
                        pref=self.client.uri_prefix,
                        res=resource,
                        uuid=uuid)
        self.assertEqual(expected_link, link)
