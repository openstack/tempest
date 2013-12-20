# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 IBM Corp.
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
#

import sys

import tempest.config
from tempest.openstack.common.config import generator

# NOTE(mtreinish): This hack is needed because of how oslo config is used in
# tempest. Tempest is run from inside a test runner and so we can't rely on the
# global CONF object being fully populated when we run a test. (test runners
# don't init every file for running a test) So to get around that we manually
# load the config file in tempest for each test class to ensure that every
# config option is set. However, the tool expects the CONF object to be fully
# populated when it inits all the files in the project. This just works around
# the issue by manually loading the config file (which may or may not exist)
# which will populate all the options before running the generator.


if __name__ == "__main__":
    CONF = tempest.config.TempestConfig()
    generator.generate(sys.argv[1:])
