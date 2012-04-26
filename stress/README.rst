Quanta Research Cambridge OpenStack Stress Test System
======================================================

Nova is a distributed, asynchronous system that is prone to race condition
bugs. These bugs will not be easily found during
functional testing but will be encountered by users in large deployments in a
way that is hard to debug. The stress test tries to cause these bugs to happen
in a more controlled environment.

The basic idea of the test is that there are a number of actions, roughly
corresponding to the Compute API, that are fired pseudo-randomly at a nova 
cluster as fast as possible. These actions consist of what to do, how to
verify success, and a state filter to make sure that the operation makes sense.
For example, if the action is to reboot a server and none are active, nothing
should be done. A test case is a set of actions to be performed and the
probability that each action should be selected. There are also parameters
controlling rate of fire and stuff like that.

This test framework is designed to stress test a Nova cluster. Hence,
you must have a working Nova cluster with rate limiting turned off.

Environment
------------
This particular framework assumes your working Nova cluster understands Nova 
API 2.0. The stress tests can read the logs from the cluster. To enable this
you have to provide the hostname to call 'nova-manage' and
the private key and user name for ssh to the cluster in the
[stress] section of tempest.conf. You also need to provide the
value of --logdir in nova.conf:

  host_private_key_path=<path to private ssh key>
  host_admin_user=<name of user for ssh command>
  nova_logdir=<value of --logdir in nova.conf>
  controller=<hostname for calling nova-manage>
  max_instances=<limit on instances that will be created>

Also, make sure to set

log_level=CRITICAL

so that the API client does not log failed calls which are expected while
running stress tests.

The stress test needs the top-level tempest directory to be on PYTHONPATH
if you are not using nosetests to run.


Running the sample test
-----------------------

To test your installation, do the following (from the tempest directory):

  PYTHONPATH=. python stress/tests/user_script_sample.py

This sample test tries to create a few VMs and kill a few VMs.


Additional Tools
----------------

Sometimes the tests don't finish, or there are failures. In these
cases, you may want to clean out the nova cluster. We have provided
some scripts to do this in the ``tools`` subdirectory. To use these
tools, you will need to install python-novaclient.
You can then use the following script to destroy any keypairs,
floating ips, and servers::

stress/tools/nova_destroy_all.py
