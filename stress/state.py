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
"""A class to store the state of various persistent objects in the Nova
cluster, e.g. instances, volumes.  Use methods to query to state which than
can be compared to the current state of the objects in Nova"""


class State(object):

    def __init__(self, **kwargs):
        self._max_vms = kwargs.get('max_vms', 32)
        self._instances = {}
        self._volumes = {}

    # machine state methods
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
