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
