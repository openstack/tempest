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

from oslo_log import log

from tempest import config
from tempest.lib import exceptions as lib_exc

CONF = config.CONF
LOG = log.getLogger(__name__)


def delete_containers(containers, container_client, object_client):
    """Remove containers and all objects in them.

    The containers should be visible from the container_client given.
    Will not throw any error if the containers don't exist.

    :param containers: List of containers(or string of a container)
                       to be deleted
    :param container_client: Client to be used to delete containers
    :param object_client: Client to be used to delete objects
    """
    if isinstance(containers, str):
        containers = [containers]

    for cont in containers:
        try:
            delete_objects(cont, container_client, object_client)
            container_client.delete_container(cont)
            container_client.wait_for_resource_deletion(cont)
        except lib_exc.NotFound:
            LOG.warning(f"Container {cont} wasn't deleted as it wasn't found.")


def delete_objects(container, container_client, object_client):
    """Remove all objects from container.

    Will not throw any error if the objects do not exist

    :param container: Name of the container that contains the objects to be
                      deleted
    :param container_client: Client to be used to list objects in
                             the container
    :param object_client: Client to be used to delete objects
    """
    params = {'limit': 9999, 'format': 'json'}
    _, objlist = container_client.list_container_objects(container, params)

    for obj in objlist:
        try:
            object_client.delete_object(container, obj['name'])
            object_client.wait_for_resource_deletion(obj['name'], container)
        except lib_exc.NotFound:
            LOG.warning(f"Object {obj} wasn't deleted as it wasn't found.")
