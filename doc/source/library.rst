.. _library:

Tempest Library Documentation
=============================

Tempest provides a stable library interface that provides external tools or
test suites an interface for reusing pieces of Tempest code. Any public
interface that lives in tempest/lib in the Tempest repo is treated as a stable
public interface and it should be safe to external consume that. Every effort
goes into maintaining backwards compatibility with any change.
The library is self contained and doesn't have any dependency on
other Tempest internals outside of lib (including no usage of Tempest
configuration).

Stability
---------
Any code that lives in tempest/lib will be treated as a stable interface.
This means that any public interface under the tempest/lib directory is
expected to be a stable interface suitable for public consumption. However, for
any interfaces outside of tempest/lib in the tempest tree (unless otherwise
noted) or any private interfaces the same stability guarantees don't apply.

Adding Interfaces
'''''''''''''''''
When adding an interface to tempest/lib we have to make sure there are no
dependencies on any pieces of tempest outside of tempest/lib. This means if
for example there is a dependency on the configuration file we need remove that.
The other aspect when adding an interface is to make sure it's really an
interface ready for external consumption and something we want to commit to
supporting.

Making changes
''''''''''''''
When making changes to tempest/lib you have to be conscious of the effect of
any changes on external consumers. If your proposed change set will change the
default behaviour of any interface, or make something which previously worked
not after your change, then it is not acceptable. Every effort needs to go into
preserving backwards compatibility in changes.

Reviewing
'''''''''
When reviewing a proposed change to tempest/lib code we need to be careful to
ensure that we don't break backward compatibility. For patches that change
existing interfaces, we have to be careful to make sure we don't break any
external consumers. Some common red flags are:

* a change to an existing API requires a change outside the library directory
  where the interface is being consumed
* a unit test has to be significantly changed to make the proposed change pass

Testing
'''''''
When adding a new interface to the library we need to at a minimum have unit
test coverage. A proposed change to add an interface to tempest/lib that
doesn't have unit tests shouldn't be accepted. Ideally, these unit tests will
provide sufficient coverage to ensure a stable interface moving forward.

Current Library APIs
--------------------

.. toctree::
   :maxdepth: 2

   library/cli
   library/decorators
   library/rest_client
   library/utils
   library/api_microversion_testing
   library/auth
   library/clients
   library/credential_providers
   library/validation_resources
