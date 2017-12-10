.. _cred_providers:

Credential Providers
====================

These library interfaces are used to deal with allocating credentials on demand
either dynamically by calling keystone to allocate new credentials, or from
a list of preprovisioned credentials. These 2 modules are implementations of
the same abstract credential providers class and can be used interchangeably.
However, each implementation has some additional parameters that are used to
influence the behavior of the modules. The API reference at the bottom of this
doc shows the interface definitions for both modules, however that may be a bit
opaque. You can see some examples of how to leverage this interface below.

Initialization Example
----------------------
This example is from Tempest itself (from tempest/common/credentials_factory.py
just modified slightly) and is how it initializes the credential provider based
on config::

  from tempest import config
  from tempest.lib.common import dynamic_creds
  from tempest.lib.common import preprov_creds

  CONF = config.CONF

  def get_credentials_provider(name, network_resources=None,
                               force_tenant_isolation=False,
                               identity_version=None):
      # If a test requires a new account to work, it can have it via forcing
      # dynamic credentials. A new account will be produced only for that test.
      # In case admin credentials are not available for the account creation,
      # the test should be skipped else it would fail.
      identity_version = identity_version or CONF.identity.auth_version
      if CONF.auth.use_dynamic_credentials or force_tenant_isolation:
          admin_creds = get_configured_admin_credentials(
              fill_in=True, identity_version=identity_version)
          return dynamic_creds.DynamicCredentialProvider(
              name=name,
              network_resources=network_resources,
              identity_version=identity_version,
              admin_creds=admin_creds,
              identity_admin_domain_scope=CONF.identity.admin_domain_scope,
              identity_admin_role=CONF.identity.admin_role,
              extra_roles=CONF.auth.tempest_roles,
              neutron_available=CONF.service_available.neutron,
              project_network_cidr=CONF.network.project_network_cidr,
              project_network_mask_bits=CONF.network.project_network_mask_bits,
              public_network_id=CONF.network.public_network_id,
              create_networks=(CONF.auth.create_isolated_networks and not
                               CONF.network.shared_physical_network),
              resource_prefix='tempest',
              credentials_domain=CONF.auth.default_credentials_domain_name,
              admin_role=CONF.identity.admin_role,
              identity_uri=CONF.identity.uri_v3,
              identity_admin_endpoint_type=CONF.identity.v3_endpoint_type)
      else:
          if CONF.auth.test_accounts_file:
              # Most params are not relevant for pre-created accounts
              return preprov_creds.PreProvisionedCredentialProvider(
                  name=name, identity_version=identity_version,
                  accounts_lock_dir=lockutils.get_lock_path(CONF),
                  test_accounts_file=CONF.auth.test_accounts_file,
                  object_storage_operator_role=CONF.object_storage.operator_role,
                  object_storage_reseller_admin_role=reseller_admin_role,
                  credentials_domain=CONF.auth.default_credentials_domain_name,
                  admin_role=CONF.identity.admin_role,
                  identity_uri=CONF.identity.uri_v3,
                  identity_admin_endpoint_type=CONF.identity.v3_endpoint_type)
          else:
              raise exceptions.InvalidConfiguration(
                  'A valid credential provider is needed')

This function just returns an initialized credential provider class based on the
config file. The consumer of this function treats the output as the same
regardless of whether it's a dynamic or preprovisioned provider object.

Dealing with Credentials
------------------------

Once you have a credential provider object created the access patterns for
allocating and removing credentials are the same across both the dynamic
and preprovisioned credentials. These are defined in the abstract
CredentialProvider class. At a high level the credentials provider enables
you to get 3 basic types of credentials at once (per object): a primary, alt,
and admin. You're also able to allocate a credential by role. These credentials
are tracked by the provider object and delete must manually be called otherwise
the created resources will not be deleted (or returned to the pool in the case
of preprovisioned creds)

Examples
''''''''

Continuing from the example above, to allocate credentials by the 3 basic types
you can do the following::

  provider = get_credentials_provider('my_tests')
  primary_creds = provider.get_primary_creds()
  alt_creds = provider.get_alt_creds()
  admin_creds = provider.get_admin_creds()
  # Make sure to delete the credentials when you're finished
  provider.clear_creds()

To create and interact with credentials by role you can do the following::

  provider = get_credentials_provider('my_tests')
  my_role_creds = provider.get_creds_by_role({'roles': ['my_role']})
  # provider.clear_creds() will clear all creds including those allocated by
  # role
  provider.clear_creds()

When multiple roles are specified a set of creds with all the roles assigned
will be allocated::

  provider = get_credentials_provider('my_tests')
  my_role_creds = provider.get_creds_by_role({'roles': ['my_role',
                                                        'my_other_role']})
  # provider.clear_creds() will clear all creds including those allocated by
  # role
  provider.clear_creds()

If you need multiple sets of credentials with the same roles you can also do
this by leveraging the ``force_new`` kwarg::

  provider = get_credentials_provider('my_tests')
  my_role_creds = provider.get_creds_by_role({'roles': ['my_role']})
  my_role_other_creds = provider.get_creds_by_role({'roles': ['my_role']},
                                                   force_new=True)
  # provider.clear_creds() will clear all creds including those allocated by
  # role
  provider.clear_creds()


API Reference
-------------

The dynamic credentials module
''''''''''''''''''''''''''''''

.. automodule:: tempest.lib.common.dynamic_creds
   :members:

The pre-provisioned credentials module
''''''''''''''''''''''''''''''''''''''

.. automodule:: tempest.lib.common.preprov_creds
   :members:
