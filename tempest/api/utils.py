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

"""Common utilities used in testing."""

from tempest import test


class skip_unless_attr(object):
    """Decorator that skips a test if a specified attr exists and is True."""
    def __init__(self, attr, msg=None):
        self.attr = attr
        self.message = msg or ("Test case attribute %s not found "
                               "or False") % attr

    def __call__(self, func):
        def _skipper(*args, **kw):
            """Wrapped skipper function."""
            testobj = args[0]
            if not getattr(testobj, self.attr, False):
                raise test.BaseTestCase.skipException(self.message)
            func(*args, **kw)
        _skipper.__name__ = func.__name__
        _skipper.__doc__ = func.__doc__
        return _skipper
