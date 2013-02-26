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


class StressConfig(object):
    """Provides configuration information for whitebox stress tests."""

    def __init__(self, conf):
        self.conf = conf

    @property
    def host_private_key_path(self):
        """Path to ssh key for logging into compute nodes."""
        return self.conf.compute.path_to_private_key

    @property
    def host_admin_user(self):
        """Username for logging into compute nodes."""
        return self.conf.compute.ssh_user

    @property
    def nova_logdir(self):
        """Directory containing log files on the compute nodes."""
        return self.conf.stress.nova_logdir

    @property
    def controller(self):
        """Controller host."""
        return self.conf.stress.controller

    @property
    def max_instances(self):
        """Maximum number of instances to create during test."""
        return self.conf.stress.max_instances
