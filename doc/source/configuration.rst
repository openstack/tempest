.. _tempest-configuration:

Tempest Configuration Guide
===========================

This guide is a starting point for configuring Tempest. It aims to elaborate
on and explain some of the mandatory and common configuration settings and how
they are used in conjunction. The source of truth on each option is the sample
config file which explains the purpose of each individual option. You can see
the sample config file here: :ref:`tempest-sampleconf`

.. _tempest_cred_provider_conf:

Test Credentials
----------------

Tempest allows for configuring a set of admin credentials in the ``auth``
section, via the following parameters:

#. ``admin_username``
#. ``admin_password``
#. ``admin_project_name``
#. ``admin_domain_name``

Admin credentials are not mandatory to run Tempest, but when provided they
can be used to:

- Run tests for admin APIs
- Generate test credentials on the fly (see `Dynamic Credentials`_)

When Keystone uses a policy that requires domain scoped tokens for admin
actions, the flag ``admin_domain_scope`` must be set to ``True``.
The admin user configured, if any, must have a role assigned to the domain to
be usable.

Tempest allows for configuring pre-provisioned test credentials as well.
This can be done using the accounts.yaml file (see
`Pre-Provisioned Credentials`_). This file is used to specify an arbitrary
number of users available to run tests with.
You can specify the location of the file in the ``auth`` section in the
tempest.conf file. To see the specific format used in the file please refer to
the ``accounts.yaml.sample`` file included in Tempest.

Keystone Connection Info
^^^^^^^^^^^^^^^^^^^^^^^^
In order for Tempest to be able to talk to your OpenStack deployment you need
to provide it with information about how it communicates with keystone.
This involves configuring the following options in the ``identity`` section:

- ``auth_version``
- ``uri``
- ``uri_v3``

The ``auth_version`` option is used to tell Tempest whether it should be using
Keystone's v2 or v3 api for communicating with Keystone. The two uri options are
used to tell Tempest the url of the keystone endpoint. The ``uri`` option is
used for Keystone v2 request and ``uri_v3`` is used for Keystone v3. You want to
ensure that which ever version you set for ``auth_version`` has its uri option
defined.

Credential Provider Mechanisms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Tempest currently has two different internal methods for providing authentication
to tests: dynamic credentials and pre-provisioned credentials.
Depending on which one is in use the configuration of Tempest is slightly different.

Dynamic Credentials
"""""""""""""""""""
Dynamic Credentials (formerly known as Tenant isolation) was originally created
to enable running Tempest in parallel.  For each test class it creates a unique
set of user credentials to use for the tests in the class. It can create up to
three sets of username, password, and project names for a primary user,
an admin user, and an alternate user. To enable and use dynamic credentials you
only need to configure two things:

#. A set of admin credentials with permissions to create users and
   projects. This is specified in the ``auth`` section with the
   ``admin_username``, ``admin_project_name``, ``admin_domain_name`` and
   ``admin_password`` options
#. To enable dynamic credentials in the ``auth`` section with the
   ``use_dynamic_credentials`` option.

This is also currently the default credential provider enabled by Tempest, due
to its common use and ease of configuration.

It is worth pointing out that depending on your cloud configuration you might
need to assign a role to each of the users created by Tempest's dynamic
credentials.  This can be set using the ``tempest_roles`` option. It takes in a
list of role names each of which will be assigned to each of the users created
by dynamic credentials. This option will not have any effect when Tempest is not
configured to use dynamic credentials.

When the ``admin_domain_scope`` option is set to ``True``, provisioned admin
accounts will be assigned a role on domain configured in
``default_credentials_domain_name``. This will make the accounts provisioned
usable in a cloud where domain scoped tokens are required by Keystone for
admin operations. Note that the initial pre-provision admin accounts,
configured in tempest.conf, must have a role on the same domain as well, for
Dynamic Credentials to work.


Pre-Provisioned Credentials
"""""""""""""""""""""""""""

For a long time using dynamic credentials was the only method available if you
wanted to enable parallel execution of Tempest tests. However, this was
insufficient for certain use cases because of the admin credentials requirement
to create the credential sets on demand. To get around that the accounts.yaml
file was introduced and with that a new internal credential provider to enable
using the list of credentials instead of creating them on demand. With locking
test accounts each test class will reserve a set of credentials from the
accounts.yaml before executing any of its tests so that each class is isolated
like with dynamic credentials.

To enable and use locking test accounts you need do a few things:

#. Create an accounts.yaml file which contains the set of pre-existing
   credentials to use for testing. To make sure you don't have a credentials
   starvation issue when running in parallel make sure you have at least two
   times the number of worker processes you are using to execute Tempest
   available in the file. (If running serially the worker count is 1.)

   You can check the accounts.yaml.sample file packaged in Tempest for the yaml
   format.
#. Provide Tempest with the location of your accounts.yaml file with the
   ``test_accounts_file`` option in the ``auth`` section

   *NOTE: Be sure to use a full path for the file; otherwise Tempest will
   likely not find it.*

#. Set ``use_dynamic_credentials = False`` in the ``auth`` group

It is worth pointing out that each set of credentials in the accounts.yaml
should have a unique project. This is required to provide proper isolation
to the tests using the credentials, and failure to do this will likely cause
unexpected failures in some tests. Also, ensure that these projects and users
used do not have any pre-existing resources created. Tempest assumes all
tenants it's using are empty and may sporadically fail if there are unexpected
resources present.

When the Keystone in the target cloud requires domain scoped tokens to
perform admin actions, all pre-provisioned admin users must have a role
assigned on the domain where test accounts a provisioned.
The option ``admin_domain_scope`` is used to tell Tempest that domain scoped
tokens shall be used. ``default_credentials_domain_name`` is the domain where
test accounts are expected to be provisioned if no domain is specified.

Note that if credentials are pre-provisioned via ``tempest account-generator``
the role on the domain will be assigned automatically for you, as long as
``admin_domain_scope`` as ``default_credentials_domain_name`` are configured
properly in tempest.conf.

Pre-Provisioned Credentials are also known as accounts.yaml or accounts file.

Compute
-------

Flavors
^^^^^^^
For Tempest to be able to create servers you need to specify flavors that it
can use to boot the servers with. There are two options in the Tempest config
for doing this:

#. ``flavor_ref``
#. ``flavor_ref_alt``

Both of these options are in the ``compute`` section of the config file and take
in the flavor id (not the name) from Nova. The ``flavor_ref`` option is what
will be used for booting almost all of the guests; ``flavor_ref_alt`` is only
used in tests where two different-sized servers are required (for example, a
resize test).

Using a smaller flavor is generally recommended. When larger flavors are used,
the extra time required to bring up servers will likely affect total run time
and probably require tweaking timeout values to ensure tests have ample time to
finish.

Images
^^^^^^
Just like with flavors, Tempest needs to know which images to use for booting
servers. There are two options in the compute section just like with flavors:

#. ``image_ref``
#. ``image_ref_alt``

Both options are expecting an image id (not name) from Nova. The ``image_ref``
option is what will be used for booting the majority of servers in Tempest.
``image_ref_alt`` is used for tests that require two images such as rebuild. If
two images are not available you can set both options to the same image id and
those tests will be skipped.

There are also options in the ``scenario`` section for images:

#. ``img_file``
#. ``img_dir``
#. ``aki_img_file``
#. ``ari_img_file``
#. ``ami_img_file``
#. ``img_container_format``
#. ``img_disk_format``

However, unlike the other image options, these are used for a very small subset
of scenario tests which are uploading an image. These options are used to tell
Tempest where an image file is located and describe its metadata for when it is
uploaded.

The behavior of these options is a bit convoluted (which will likely be fixed in
future versions). You first need to specify ``img_dir``, which is the directory
in which Tempest will look for the image files. First it will check if the
filename set for ``img_file`` could be found in ``img_dir``. If it is found then
the ``img_container_format`` and ``img_disk_format`` options are used to upload
that image to glance. However, if it is not found, Tempest will look for the
three uec image file name options as a fallback. If neither is found, the tests
requiring an image to upload will fail.

It is worth pointing out that using `cirros`_ is a very good choice for running
Tempest. It's what is used for upstream testing, they boot quickly and have a
small footprint.

.. _cirros: https://launchpad.net/cirros

Networking
----------
OpenStack has a myriad of different networking configurations possible and
depending on which of the two network backends, nova-network or Neutron, you are
using things can vary drastically. Due to this complexity Tempest has to provide
a certain level of flexibility in its configuration to ensure it will work
against any cloud. This ends up causing a large number of permutations in
Tempest's config around network configuration.


Enabling Remote Access to Created Servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _tempest_conf_network_allocation:

Network Creation/Usage for Servers
""""""""""""""""""""""""""""""""""
When Tempest creates servers for testing, some tests require being able to
connect those servers. Depending on the configuration of the cloud, the methods
for doing this can be different. In certain configurations it is required to
specify a single network with server create calls. Accordingly, Tempest provides
a few different methods for providing this information in configuration to try
and ensure that regardless of the cloud's configuration it'll still be able to
run. This section covers the different methods of configuring Tempest to provide
a network when creating servers.

Fixed Network Name
''''''''''''''''''
This is the simplest method of specifying how networks should be used. You can
just specify a single network name/label to use for all server creations. The
limitation with this is that all projects and users must be able to see
that network name/label if they are to perform a network list and be able to use
it.

If no network name is assigned in the config file and none of the below
alternatives are used, then Tempest will not specify a network on server
creations, which depending on the cloud configuration might prevent them from
booting.

To set a fixed network name simply:

#. Set the ``fixed_network_name`` option in the ``compute`` group

In the case that the configured fixed network name can not be found by a user
network list call, it will be treated like one was not provided except that a
warning will be logged stating that it couldn't be found.


Accounts File
'''''''''''''
If you are using an accounts file to provide credentials for running Tempest
then you can leverage it to also specify which network should be used with
server creations on a per project and user pair basis. This provides
the necessary flexibility to work with more intricate networking configurations
by enabling the user to specify exactly which network to use for which
projects. You can refer to the accounts.yaml.sample file included in
the Tempest repo for the syntax around specifying networks in the file.

However, specifying a network is not required when using an accounts file. If
one is not specified you can use a fixed network name to specify the network to
use when creating servers just as without an accounts file. However, any network
specified in the accounts file will take precedence over the fixed network name
provided. If no network is provided in the accounts file and a fixed network
name is not set then no network will be included in create server requests.

If a fixed network is provided and the accounts.yaml file also contains networks
this has the benefit of enabling a couple more tests which require a static
network to perform operations like server lists with a network filter. If a
fixed network name is not provided these tests are skipped. Additionally, if a
fixed network name is provided it will serve as a fallback in case of a
misconfiguration or a missing network in the accounts file.


With Dynamic Credentials
''''''''''''''''''''''''
With dynamic credentials enabled and using nova-network, your only option for
configuration is to either set a fixed network name or not. However, in most
cases it shouldn't matter because nova-network should have no problem booting a
server with multiple networks. If this is not the case for your cloud then using
an accounts file is recommended because it provides the necessary flexibility to
describe your configuration. Dynamic credentials is not able to dynamically
allocate things as necessary if Neutron is not enabled.

With Neutron and dynamic credentials enabled there should not be any additional
configuration necessary to enable Tempest to create servers with working
networking, assuming you have properly configured the ``network`` section to
work for your cloud. Tempest will dynamically create the Neutron resources
necessary to enable using servers with that network. Also, just as with the
accounts file, if you specify a fixed network name while using Neutron and
dynamic credentials it will enable running tests which require a static network
and it will additionally be used as a fallback for server creation. However,
unlike accounts.yaml this should never be triggered.

However, there is an option ``create_isolated_networks`` to disable dynamic
credentials's automatic provisioning of network resources. If this option is set
to ``False`` you will have to either rely on there only being a single/default
network available for the server creation, or use ``fixed_network_name`` to
inform Tempest which network to use.

SSH Connection Configuration
""""""""""""""""""""""""""""
There are also several different ways to actually establish a connection and
authenticate/login on the server. After a server is booted with a provided
network there are still details needed to know how to actually connect to
the server. The ``validation`` group gathers all the options regarding
connecting to and remotely accessing the created servers.

To enable remote access to servers, there are 3 options at a minimum that are used:

#. ``run_validation``
#. ``connect_method``
#. ``auth_method``

The ``run_validation`` is used to enable or disable ssh connectivity for
all tests (with the exception of scenario tests which do not have a flag for
enabling or disabling ssh) To enable ssh connectivity this needs be set to ``True``.

The ``connect_method`` option is used to tell Tempest what kind of IP to use for
establishing a connection to the server. Two methods are available: ``fixed``
and ``floating``, the later being set by default. If this is set to floating
Tempest will create a floating ip for the server before attempted to connect
to it. The IP for the floating ip is what is used for the connection.

For the ``auth_method`` option there is currently, only one valid option,
``keypair``. With this set to ``keypair`` Tempest will create an ssh keypair
and use that for authenticating against the created server.

Configuring Available Services
------------------------------
OpenStack is really a constellation of several different projects which
are running together to create a cloud. However which projects you're running
is not set in stone, and which services are running is up to the deployer.
Tempest however needs to know which services are available so it can figure
out which tests it is able to run and certain setup steps which differ based
on the available services.

The ``service_available`` section of the config file is used to set which
services are available. It contains a boolean option for each service (except
for Keystone which is a hard requirement) set it to ``True`` if the service is
available or ``False`` if it is not.

Service Catalog
^^^^^^^^^^^^^^^
Each project which has its own REST API contains an entry in the service
catalog. Like most things in OpenStack this is also completely configurable.
However, for Tempest to be able to figure out which endpoints should get REST
API calls for each service, it needs to know how that project is defined in the
service catalog. There are three options for each service section to accomplish
this:

#. ``catalog_type``
#. ``endpoint_type``
#. ``region``

Setting ``catalog_type`` and ``endpoint_type`` should normally give Tempest
enough information to determine which endpoint it should pull from the service
catalog to use for talking to that particular service. However, if your cloud
has multiple regions available and you need to specify a particular one to use a
service you can set the ``region`` option in that service's section.

It should also be noted that the default values for these options are set
to what DevStack uses (which is a de facto standard for service catalog
entries). So often nothing actually needs to be set on these options to enable
communication to a particular service. It is only if you are either not using
the same ``catalog_type`` as DevStack or you want Tempest to talk to a different
endpoint type instead of ``publicURL`` for a service that these need to be
changed.

.. note::

    Tempest does not serve all kinds of fancy URLs in the service catalog.  The
    service catalog should be in a standard format (which is going to be
    standardized at the Keystone level).
    Tempest expects URLs in the Service catalog in the following format:

    * ``http://example.com:1234/<version-info>``

    Examples:

    * Good - ``http://example.com:1234/v2.0``
    * Wouldn't work -  ``http://example.com:1234/xyz/v2.0/``
      (adding prefix/suffix around version etc)

Service Feature Configuration
-----------------------------

OpenStack provides its deployers a myriad of different configuration options to
enable anyone deploying it to create a cloud tailor-made for any individual use
case. It provides options for several different backend types, databases,
message queues, etc. However, the downside to this configurability is that
certain operations and features aren't supported depending on the configuration.
These features may or may not be discoverable from the API so the burden is
often on the user to figure out what is supported by the cloud they're talking
to.  Besides the obvious interoperability issues with this it also leaves
Tempest in an interesting situation trying to figure out which tests are
expected to work. However, Tempest tests do not rely on dynamic API discovery
for a feature (assuming one exists). Instead Tempest has to be explicitly
configured as to which optional features are enabled. This is in order to
prevent bugs in the discovery mechanisms from masking failures.

The service ``feature-enabled`` config sections are how Tempest addresses the
optional feature question. Each service that has tests for optional features
contains one of these sections. The only options in it are boolean options
with the name of a feature which is used. If it is set to false any test which
depends on that functionality will be skipped. For a complete list of all these
options refer to the sample config file.


API Extensions
^^^^^^^^^^^^^^
The service feature-enabled sections often contain an ``api-extensions`` option
(or in the case of Swift a ``discoverable_apis`` option). This is used to tell
Tempest which api extensions (or configurable middleware) is used in your
deployment. It has two valid config states: either it contains a single value
``all`` (which is the default) which means that every api extension is assumed
to be enabled, or it is set to a list of each individual extension that is
enabled for that service.
