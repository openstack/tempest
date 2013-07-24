Tempest Coding Guide
====================

- Step 1: Read the OpenStack Style Commandments
  https://github.com/openstack-dev/hacking/blob/master/HACKING.rst
- Step 2: Read on

Tempest Specific Commandments
------------------------------

[T101] If a test is broken because of a bug it is appropriate to skip the test until
bug has been fixed. However, the skip message should be formatted so that
Tempest's skip tracking tool can watch the bug status. The skip message should
contain the string 'Bug' immediately followed by a space. Then the bug number
should be included in the message '#' in front of the number.

Example::

  @testtools.skip("Skipped until the Bug #980688 is resolved")

- [T102] Cannot import OpenStack python clients in tempest/api tests
- [T103] tempest/tests is deprecated

Test Data/Configuration
-----------------------
- Assume nothing about existing test data
- Tests should be self contained (provide their own data)
- Clean up test data at the completion of each test
- Use configuration files for values that will vary by environment


Exception Handling
------------------
According to the ``The Zen of Python`` the
``Errors should never pass silently.``
Tempest usually runs in special environment (jenkins gate jobs), in every
error or failure situation we should provide as much error related
information as possible, because we usually do not have the chance to
investigate the situation after the issue happened.

In every test case the abnormal situations must be very verbosely explained,
by the exception and the log.

In most cases the very first issue is the most important information.

Try to avoid using ``try`` blocks in the test cases, both the ``except``
and ``finally`` block could replace the original exception,
when the additional operations leads to another exception.

Just letting an exception to propagate, is not bad idea in a test case,
 at all.

Try to avoid using any exception handling construct which can hide the errors
origin.

If you really need to use a ``try`` block, please ensure the original
exception at least logged.  When the exception is logged you usually need
to ``raise`` the same or a different exception anyway.

Use of ``self.addCleanup`` is often a good way to avoid having to catch
exceptions and still ensure resources are correctly cleaned up if the
test fails part way through.

Use the ``self.assert*`` methods provided by the unit test framework
 the signal failures early.

Avoid using the ``self.fail`` alone, it's stack trace will signal
 the ``self.fail`` line as the origin of the error.

Avoid constructing complex boolean expressions for assertion.
The ``self.assertTrue`` or ``self.assertFalse`` will just tell you the
single boolean, and you will not know anything about the values used in
the formula. Most other assert method can include more information.
For example ``self.assertIn`` can include the whole set.

If the test case fails you can see the related logs and the information
carried by the exception (exception class, backtrack and exception info).
This and the service logs are your only guide to find the root cause of flaky
issue.

Guidelines
----------
- Do not submit changesets with only testcases which are skipped as
  they will not be merged.
- Consistently check the status code of responses in testcases. The
  earlier a problem is detected the easier it is to debug, especially
  where there is complicated setup required.
