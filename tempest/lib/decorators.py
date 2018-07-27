# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import functools
import uuid

from oslo_log import log as logging
import six
import testtools

from tempest.lib import exceptions as lib_exc

LOG = logging.getLogger(__name__)

_SUPPORTED_BUG_TYPES = {
    'launchpad': 'https://launchpad.net/bugs/%s',
    'storyboard': 'https://storyboard.openstack.org/#!/story/%s',
}


def _validate_bug_and_bug_type(bug, bug_type):
    """Validates ``bug`` and ``bug_type`` values.

    :param bug: bug number causing the test to skip (launchpad or storyboard)
    :param bug_type: 'launchpad' or 'storyboard', default 'launchpad'
    :raises: InvalidParam if ``bug`` is not a digit or ``bug_type`` is not
        a valid value
    """
    if not bug.isdigit():
        invalid_param = '%s must be a valid %s number' % (bug, bug_type)
        raise lib_exc.InvalidParam(invalid_param=invalid_param)
    if bug_type not in _SUPPORTED_BUG_TYPES:
        invalid_param = 'bug_type "%s" must be one of: %s' % (
            bug_type, ', '.join(_SUPPORTED_BUG_TYPES.keys()))
        raise lib_exc.InvalidParam(invalid_param=invalid_param)


def _get_bug_url(bug, bug_type='launchpad'):
    """Get the bug URL based on the ``bug_type`` and ``bug``

    :param bug: The launchpad/storyboard bug number causing the test
    :param bug_type: 'launchpad' or 'storyboard', default 'launchpad'
    :returns: Bug URL corresponding to ``bug_type`` value
    """
    _validate_bug_and_bug_type(bug, bug_type)
    return _SUPPORTED_BUG_TYPES[bug_type] % bug


def skip_because(*args, **kwargs):
    """A decorator useful to skip tests hitting known bugs

    ``bug`` must be a number and ``condition`` must be true for the test to
    skip.

    :param bug: bug number causing the test to skip (launchpad or storyboard)
    :param bug_type: 'launchpad' or 'storyboard', default 'launchpad'
    :param condition: optional condition to be True for the skip to have place
    :raises: testtools.TestCase.skipException if ``condition`` is True and
        ``bug`` is included
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*func_args, **func_kwargs):
            skip = False
            msg = ''
            if "condition" in kwargs:
                if kwargs["condition"] is True:
                    skip = True
            else:
                skip = True
            if "bug" in kwargs and skip is True:
                bug = kwargs['bug']
                bug_type = kwargs.get('bug_type', 'launchpad')
                bug_url = _get_bug_url(bug, bug_type)
                msg = "Skipped until bug: %s is resolved." % bug_url
                raise testtools.TestCase.skipException(msg)
            return f(*func_args, **func_kwargs)
        return wrapper
    return decorator


def related_bug(bug, status_code=None, bug_type='launchpad'):
    """A decorator useful to know solutions from launchpad/storyboard reports

    :param bug: The launchpad/storyboard bug number causing the test bug
    :param bug_type: 'launchpad' or 'storyboard', default 'launchpad'
    :param status_code: The status code related to the bug report
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*func_args, **func_kwargs):
            try:
                return f(*func_args, **func_kwargs)
            except Exception as exc:
                exc_status_code = getattr(exc, 'status_code', None)
                if status_code is None or status_code == exc_status_code:
                    if bug:
                        LOG.error('Hints: This test was made for the bug_type '
                                  '%s. The failure could be related to '
                                  '%s', bug, _get_bug_url(bug, bug_type))
                raise exc
        return wrapper
    return decorator


def idempotent_id(id):
    """Stub for metadata decorator"""
    if not isinstance(id, six.string_types):
        raise TypeError('Test idempotent_id must be string not %s'
                        '' % type(id).__name__)
    uuid.UUID(id)

    def decorator(f):
        f = testtools.testcase.attr('id-%s' % id)(f)
        if f.__doc__:
            f.__doc__ = 'Test idempotent id: %s\n%s' % (id, f.__doc__)
        else:
            f.__doc__ = 'Test idempotent id: %s' % id
        return f
    return decorator


def attr(**kwargs):
    """A decorator which applies the testtools attr decorator

    This decorator applies the testtools.testcase.attr if it is in the list of
    attributes to testtools we want to apply.
    """

    def decorator(f):
        if 'type' in kwargs and isinstance(kwargs['type'], str):
            f = testtools.testcase.attr(kwargs['type'])(f)
        elif 'type' in kwargs and isinstance(kwargs['type'], list):
            for attr in kwargs['type']:
                f = testtools.testcase.attr(attr)(f)
        return f

    return decorator
