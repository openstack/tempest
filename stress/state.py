# Copyright 2011 Quanta Research Cambridge, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


class ClusterState(object):
    """A class to store the state of various persistent objects in the Nova
    cluster, e.g. instances, volumes.  Use methods to query to state which than
    can be compared to the current state of the objects in Nova"""

    def __init__(self, **kwargs):
        self._max_vms = kwargs.get('max_vms', 32)
        self._instances = {}
        self._floating_ips = []
        self._keypairs = []
        self._volumes = []

    # instance state methods
    def get_instances(self):
        """return the instances dictionary that we believe are in cluster."""
        return self._instances

    def get_max_instances(self):
        """return the maximum number of instances we can create."""
        return self._max_vms

    def set_instance_state(self, key, val):
        """Store `val` in the dictionary indexed at `key`."""
        self._instances[key] = val

    def delete_instance_state(self, key):
        """Delete state indexed at `key`."""
        del self._instances[key]

    #floating_ip state methods
    def get_floating_ips(self):
        """return the floating ips list for the cluster."""
        return self._floating_ips

    def add_floating_ip(self, floating_ip_state):
        """Add floating ip."""
        self._floating_ips.append(floating_ip_state)

    def remove_floating_ip(self, floating_ip_state):
        """Remove floating ip."""
        self._floating_ips.remove(floating_ip_state)

    # keypair methods
    def get_keypairs(self):
        """return the keypairs list for the cluster."""
        return self._keypairs

    def add_keypair(self, keypair_state):
        """Add keypair."""
        self._keypairs.append(keypair_state)

    def remove_keypair(self, keypair_state):
        """Remove keypair."""
        self._keypairs.remove(keypair_state)

    # volume methods
    def get_volumes(self):
        """return the volumes list for the cluster."""
        return self._volumes

    def add_volume(self, volume_state):
        """Add volume."""
        self._volumes.append(volume_state)

    def remove_volume(self, volume_state):
        """Remove volume."""
        self._volumes.remove(volume_state)


class ServerAssociatedState(object):
    """Class that tracks resources that are associated with a particular server
    such as a volume or floating ip"""

    def __init__(self, resource_id):
        # The id of the server.
        self.server_id = None
        # The id of the resource that is attached to the server.
        self.resource_id = resource_id
        # True if in the process of attaching/detaching the resource.
        self.change_pending = False


class FloatingIpState(ServerAssociatedState):

    def __init__(self, ip_desc):
        super(FloatingIpState, self).__init__(ip_desc['id'])
        self.address = ip_desc['ip']


class VolumeState(ServerAssociatedState):

    def __init__(self, volume_desc):
        super(VolumeState, self).__init__(volume_desc['id'])


class KeyPairState(object):

    def __init__(self, keypair_spec):
        self.name = keypair_spec['name']
        self.private_key = keypair_spec['private_key']
