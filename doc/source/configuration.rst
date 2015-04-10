.. _tempest-configuration:

Tempest Configuration Guide
===========================

This guide is a starting point for configuring tempest. It aims to elaborate
on and explain some of the mandatory and common configuration settings and how
they are used in conjunction. The source of truth on each option is the sample
config file which explains the purpose of each individual option.

Lock Path
---------

There are some tests and operations inside of tempest that need to be
externally locked when running in parallel to prevent them from running at
the same time. This is a mandatory step for configuring tempest and is still
needed even when running serially. All that is needed to do this is:

 #. Set the lock_path option in the oslo_concurrency group

Auth/Credentials
----------------

Tempest currently has 2 different ways in configuration to provide credentials
to use when running tempest. One is a traditional set of configuration options
in the tempest.conf file. These options are in the identity section and let you
specify a regular user, a global admin user, and a alternate user set of
credentials. (which consist of a username, password, and project/tenant name)
These options should be clearly labelled in the sample config file in the
identity section.

The other method to provide credentials is using the accounts.yaml file. This
file is used to specify an arbitrary number of users available to run tests
with. You can specify the location of the file in the
auth section in the tempest.conf file. To see the specific format used in
the file please refer to the accounts.yaml.sample file included in tempest.
Currently users that are specified in the accounts.yaml file are assumed to
have the same set of roles which can be used for executing all the tests you
are running. This will be addressed in the future, but is a current limitation.
Eventually the config options for providing credentials to tempest will be
deprecated and removed in favor of the accounts.yaml file.

Credential Provider Mechanisms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Tempest currently also has 3 different internal methods for providing
authentication to tests. Tenant isolation, locking test accounts, and
non-locking test accounts. Depending on which one is in use the configuration
of tempest is slightly different.

Tenant Isolation
""""""""""""""""
Tenant isolation was originally create to enable running tempest in parallel.
For each test class it creates a unique set of user credentials to use for the
tests in the class. It can create up to 3 sets of username, password, and
tenant/project names for a primary user, an admin user, and an alternate user.
To enable and use tenant isolation you only need to configure 2 things:

 #. A set of admin credentials with permissions to create users and
    tenants/projects. This is specified in the identity section with the
    admin_username, admin_tenant_name, and admin_password options
 #. To enable tenant_isolation in the auth section with the
    allow_tenant_isolation option.

This is also the currently the default credential provider enabled by tempest,
due to it's common use and ease of configuration.

Locking Test Accounts
"""""""""""""""""""""
For a long time using tenant isolation was the only method available if you
wanted to enable parallel execution of tempest tests. However this was
insufficient for certain use cases because of the admin credentials requirement
to create the credential sets on demand. To get around that the accounts.yaml
file was introduced and with that a new internal credential provider to enable
using the list of credentials instead of creating them on demand. With locking
test accounts each test class will reserve a set of credentials from the
accounts.yaml before executing any of its tests so that each class is isolated
like in tenant isolation.

Currently, this mechanism has some limitations, mostly around networking. The
locking test accounts provider will only work with a single flat network as
the default for each tenant/project. If another network configuration is used
in your cloud you might face unexpected failures.

To enable and use locking test accounts you need do a few things:

 #. Create a accounts.yaml file which contains the set of pre-existing
    credentials to use for testing. To make sure you don't have a credentials
    starvation issue when running in parallel make sure you have at least 2
    times the number of worker processes you are using to execute tempest
    available in the file. (if running serially the worker count is 1)

    You can check the sample file packaged in tempest for the yaml format
 #. Provide tempest with the location of you accounts.yaml file with the
    test_accounts_file option in the auth section


Non-locking test accounts
"""""""""""""""""""""""""
When tempest was refactored to allow for locking test accounts, the original
non-tenant isolated case was converted to support the new accounts.yaml file.
This mechanism is the non-locking test accounts provider. It only makes sense
to use it if parallel execution isn't needed. If the role restrictions were too
limiting with the locking accounts provider and tenant isolation is not wanted
then you can use the non-locking test accounts credential provider without the
accounts.yaml file.

To use the non-locking test accounts provider you have 2 ways to configure it.
First you can specify the sets of credentials in the configuration file like
detailed above with following 9 options in the identity section:

 #. username
 #. password
 #. tenant_name
 #. admin_username
 #. admin_password
 #. admin_tenant_name
 #. alt_username
 #. alt_password
 #. alt_tenant_name

The only restriction with using the traditional config options for credentials
is that if a test requires specific roles on accounts these tests can not be
run. This is because the config options do not give sufficient flexibility to
describe the roles assigned to a user for running the tests.

Networking
----------
OpenStack has a myriad of different networking configurations possible and
depending on which of the 2 network backends, nova-network or neutron, you are
using things can vary drastically. Due to this complexity Tempest has to provide
a certain level of flexibility in it's configuration to ensure it will work
against any cloud. This ends up causing a large number of permutations in
Tempest's config around network configuration.


Enabling Remote Access to Created Servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When Tempest creates servers for testing, some tests require being able to
connect those servers. Depending on the configuration of the cloud, the methods
for doing this can be different. In certain configurations it is required to
specify a single network with server create calls. Accordingly, Tempest provides
a few different methods for providing this information in configuration to try
and ensure that regardless of the clouds configuration it'll still be able to
run. This section covers the different methods of configuring Tempest to provide
a network when creating servers.

Fixed Network Name
""""""""""""""""""
This is the simplest method of specifying how networks should be used. You can
just specify a single network name/label to use for all server creations. The
limitation with this is that all tenants/projects and users must be able to see
that network name/label if they were to perform a network list and be able to
use it.

If no network name is assigned in the config file and none of the below
alternatives are used, then Tempest will not specify a network on server
creations, which depending on the cloud configuration might prevent them from
booting.

To set a fixed network name simply do:

 #. Set the fixed_network_name option in the compute group

In the case that the configured fixed network name can not be found by a user
network list call, it will be treated like one was not provided except that a
warning will be logged stating that it couldn't be found.


Accounts File
"""""""""""""
If you are using an accounts file to provide credentials for running Tempest
then you can leverage it to also specify which network should be used with
server creations on a per tenant/project and user pair basis. This provides
the necessary flexibility to work with more intricate networking configurations
by enabling the user to specify exactly which network to use for which
tenants/projects. You can refer to the accounts.yaml sample file included in
the tempest repo for the syntax around specifying networks in the file.

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


With Tenant Isolation
"""""""""""""""""""""
With tenant isolation enabled and using nova-network then nothing changes. Your
only option for configuration is to either set a fixed network name or not.
However, in most cases it shouldn't matter because nova-network should have no
problem booting a server with multiple networks. If this is not the case for
your cloud then using an accounts file is recommended because it provides the
necessary flexibility to describe your configuration. Tenant isolation is not
able to dynamically allocate things as necessary if neutron is not enabled.

With neutron and tenant isolation enabled there should not be any additional
configuration necessary to enable Tempest to create servers with working
networking, assuming you have properly configured the network section to work
for your cloud. Tempest will dynamically create the neutron resources necessary
to enable using servers with that network. Also, just as with the accounts
file, if you specify a fixed network name while using neutron and tenant
isolation it will enable running tests which require a static network and it
will additionally be used as a fallback for server creation. However, unlike
accounts.yaml this should never be triggered.
