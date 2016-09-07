# Copyright 2012 OpenStack Foundation
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
from oslo_log import log as logging

from tempest.lib.common.utils import test_utils

LOG = logging.getLogger(__name__)


def singleton(cls):
    """Simple wrapper for classes that should only have a single instance."""
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance


def find_test_caller(*args, **kwargs):
    LOG.warning("tempest.lib.common.utils.misc.find_test_caller is deprecated "
                "in favor of tempest.lib.common.utils.test_utils."
                "find_test_caller")
    test_utils.find_test_caller(*args, **kwargs)
