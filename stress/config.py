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

import ConfigParser


class StressConfig(object):
    """Provides configuration information for whitebox stress tests."""

    def __init__(self, conf):
        self.conf = conf

    def get(self, item_name, default_value=None):
        try:
            return self.conf.get("stress", item_name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default_value

    @property
    def host_private_key_path(self):
        """Path to ssh key for logging into compute nodes."""
        return self.get("host_private_key_path", None)

    @property
    def host_admin_user(self):
        """Username for logging into compute nodes."""
        return self.get("host_admin_user", None)

    @property
    def nova_logdir(self):
        """Directory containing log files on the compute nodes"""
        return self.get("nova_logdir", None)

    @property
    def controller(self):
        """Controller host"""
        return self.get("controller", None)
