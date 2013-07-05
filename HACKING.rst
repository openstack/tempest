Tempest Coding Guide
====================


Test Data/Configuration
-----------------------
- Assume nothing about existing test data
- Tests should be self contained (provide their own data)
- Clean up test data at the completion of each test
- Use configuration files for values that will vary by environment


General
-------
- Put two newlines between top-level code (funcs, classes, etc)
- Put one newline between methods in classes and anywhere else
- Long lines should be wrapped in parentheses
  in preference to using a backslash for line continuation.
- Do not write "except:", use "except Exception:" at the very least
- Include your name with TODOs as in "#TODO(termie)"
- Do not name anything the same name as a built-in or reserved word Example::

    def list():
        return [1, 2, 3]

    mylist = list() # BAD, shadows `list` built-in

    class Foo(object):
        def list(self):
            return [1, 2, 3]

    mylist = Foo().list() # OKAY, does not shadow built-in

Imports
-------
- Do not import objects, only modules (*)
- Do not import more than one module per line (*)
- Do not make relative imports
- Order your imports by the full module path
- Organize your imports according to the following template

Example::

  # vim: tabstop=4 shiftwidth=4 softtabstop=4
  {{stdlib imports in human alphabetical order}}
  \n
  {{third-party lib imports in human alphabetical order}}
  \n
  {{tempest imports in human alphabetical order}}
  \n
  \n
  {{begin your code}}


Human Alphabetical Order Examples
---------------------------------
Example::

  import httplib
  import logging
  import random
  import StringIO
  import testtools
  import time

  import eventlet
  import webob.exc

  import tempest.config
  from tempest.services.compute.json.limits_client import LimitsClientJSON
  from tempest.services.compute.xml.limits_client import LimitsClientXML
  from tempest.services.volume.volumes_client import VolumesClientJSON
  import tempest.test


Docstrings
----------
Example::

  """A one line docstring looks like this and ends in a period."""


  """A multi line docstring has a one-line summary, less than 80 characters.

  Then a new paragraph after a newline that explains in more detail any
  general information about the function, class or method. Example usages
  are also great to have here if it is a complex class for function.

  When writing the docstring for a class, an extra line should be placed
  after the closing quotations. For more in-depth explanations for these
  decisions see http://www.python.org/dev/peps/pep-0257/

  If you are going to describe parameters and return values, use Sphinx, the
  appropriate syntax is as follows.

  :param foo: the foo parameter
  :param bar: the bar parameter
  :returns: return_type -- description of the return value
  :returns: description of the return value
  :raises: AttributeError, KeyError
  """


Dictionaries/Lists
------------------
If a dictionary (dict) or list object is longer than 80 characters, its items
should be split with newlines. Embedded iterables should have their items
indented. Additionally, the last item in the dictionary should have a trailing
comma. This increases readability and simplifies future diffs.

Example::

  my_dictionary = {
      "image": {
          "name": "Just a Snapshot",
          "size": 2749573,
          "properties": {
               "user_id": 12,
               "arch": "x86_64",
          },
          "things": [
              "thing_one",
              "thing_two",
          ],
          "status": "ACTIVE",
      },
  }


Calling Methods
---------------
Calls to methods 80 characters or longer should format each argument with
newlines. This is not a requirement, but a guideline::

    unnecessarily_long_function_name('string one',
                                     'string two',
                                     kwarg1=constants.ACTIVE,
                                     kwarg2=['a', 'b', 'c'])


Rather than constructing parameters inline, it is better to break things up::

    list_of_strings = [
        'what_a_long_string',
        'not as long',
    ]

    dict_of_numbers = {
        'one': 1,
        'two': 2,
        'twenty four': 24,
    }

    object_one.call_a_method('string three',
                             'string four',
                             kwarg1=list_of_strings,
                             kwarg2=dict_of_numbers)


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


Test Skips
----------
If a test is broken because of a bug it is appropriate to skip the test until
bug has been fixed. However, the skip message should be formatted so that
Tempest's skip tracking tool can watch the bug status. The skip message should
contain the string 'Bug' immediately followed by a space. Then the bug number
should be included in the message '#' in front of the number.

Example::

  @testtools.skip("Skipped until the Bug #980688 is resolved")


openstack-common
----------------

A number of modules from openstack-common are imported into the project.

These modules are "incubating" in openstack-common and are kept in sync
with the help of openstack-common's update.py script. See:

  http://wiki.openstack.org/CommonLibrary#Incubation

The copy of the code should never be directly modified here. Please
always update openstack-common first and then run the script to copy
the changes across.


OpenStack Trademark
-------------------

OpenStack is a registered trademark of the OpenStack Foundation, and uses the
following capitalization:

   OpenStack


Commit Messages
---------------
Using a common format for commit messages will help keep our git history
readable. Follow these guidelines:

  First, provide a brief summary (it is recommended to keep the commit title
  under 50 chars).

  The first line of the commit message should provide an accurate
  description of the change, not just a reference to a bug or
  blueprint. It must be followed by a single blank line.

  If the change relates to a specific driver (libvirt, xenapi, qpid, etc...),
  begin the first line of the commit message with the driver name, lowercased,
  followed by a colon.

  Following your brief summary, provide a more detailed description of
  the patch, manually wrapping the text at 72 characters. This
  description should provide enough detail that one does not have to
  refer to external resources to determine its high-level functionality.

  Once you use 'git review', two lines will be appended to the commit
  message: a blank line followed by a 'Change-Id'. This is important
  to correlate this commit with a specific review in Gerrit, and it
  should not be modified.

For further information on constructing high quality commit messages,
and how to split up commits into a series of changes, consult the
project wiki:

   http://wiki.openstack.org/GitCommitMessages
