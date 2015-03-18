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

import contextlib
import logging as orig_logging
import os
import re
import urlparse

import boto
from boto import ec2
from boto import exception
from boto import s3
from oslo_log import log as logging
import six

from tempest_lib import exceptions as lib_exc

import tempest.clients
from tempest.common.utils import file_utils
from tempest import config
from tempest import exceptions
import tempest.test
from tempest.thirdparty.boto.utils import wait

CONF = config.CONF
LOG = logging.getLogger(__name__)


def decision_maker():
    A_I_IMAGES_READY = True  # ari,ami,aki
    S3_CAN_CONNECT_ERROR = None
    EC2_CAN_CONNECT_ERROR = None
    secret_matcher = re.compile("[A-Za-z0-9+/]{32,}")  # 40 in other system
    id_matcher = re.compile("[A-Za-z0-9]{20,}")

    def all_read(*args):
        return all(map(file_utils.have_effective_read_access, args))

    materials_path = CONF.boto.s3_materials_path
    ami_path = materials_path + os.sep + CONF.boto.ami_manifest
    aki_path = materials_path + os.sep + CONF.boto.aki_manifest
    ari_path = materials_path + os.sep + CONF.boto.ari_manifest

    A_I_IMAGES_READY = all_read(ami_path, aki_path, ari_path)
    boto_logger = logging.getLogger('boto')
    level = boto_logger.logger.level
    # suppress logging for boto
    boto_logger.logger.setLevel(orig_logging.CRITICAL)

    def _cred_sub_check(connection_data):
        if not id_matcher.match(connection_data["aws_access_key_id"]):
            raise Exception("Invalid AWS access Key")
        if not secret_matcher.match(connection_data["aws_secret_access_key"]):
            raise Exception("Invalid AWS secret Key")
        raise Exception("Unknown (Authentication?) Error")
    # NOTE(andreaf) Setting up an extra manager here is redundant,
    # and should be removed.
    openstack = tempest.clients.Manager()
    try:
        if urlparse.urlparse(CONF.boto.ec2_url).hostname is None:
            raise Exception("Failed to get hostname from the ec2_url")
        ec2client = openstack.ec2api_client
        try:
            ec2client.get_all_regions()
        except exception.BotoServerError as exc:
                if exc.error_code is None:
                    raise Exception("EC2 target does not looks EC2 service")
                _cred_sub_check(ec2client.connection_data)

    except lib_exc.Unauthorized:
        EC2_CAN_CONNECT_ERROR = "AWS credentials not set," +\
                                " also failed to get it from keystone"
    except Exception as exc:
        EC2_CAN_CONNECT_ERROR = str(exc)

    try:
        if urlparse.urlparse(CONF.boto.s3_url).hostname is None:
            raise Exception("Failed to get hostname from the s3_url")
        s3client = openstack.s3_client
        try:
            s3client.get_bucket("^INVALID*#()@INVALID.")
        except exception.BotoServerError as exc:
            if exc.status == 403:
                _cred_sub_check(s3client.connection_data)
    except Exception as exc:
        S3_CAN_CONNECT_ERROR = str(exc)
    except lib_exc.Unauthorized:
        S3_CAN_CONNECT_ERROR = "AWS credentials not set," +\
                               " failed to get them even by keystoneclient"
    boto_logger.logger.setLevel(level)
    return {'A_I_IMAGES_READY': A_I_IMAGES_READY,
            'S3_CAN_CONNECT_ERROR': S3_CAN_CONNECT_ERROR,
            'EC2_CAN_CONNECT_ERROR': EC2_CAN_CONNECT_ERROR}


class BotoExceptionMatcher(object):
    STATUS_RE = r'[45]\d\d'
    CODE_RE = '.*'  # regexp makes sense in group match

    def match(self, exc):
        """:returns: Returns with an error string if it does not match,
               returns with None when it matches.
        """
        if not isinstance(exc, exception.BotoServerError):
            return "%r not an BotoServerError instance" % exc
        LOG.info("Status: %s , error_code: %s", exc.status, exc.error_code)
        if re.match(self.STATUS_RE, str(exc.status)) is None:
            return ("Status code (%s) does not match"
                    "the expected re pattern \"%s\""
                    % (exc.status, self.STATUS_RE))
        if re.match(self.CODE_RE, str(exc.error_code)) is None:
            return ("Error code (%s) does not match" +
                    "the expected re pattern \"%s\"") %\
                   (exc.error_code, self.CODE_RE)
        return None


class ClientError(BotoExceptionMatcher):
    STATUS_RE = r'4\d\d'


class ServerError(BotoExceptionMatcher):
    STATUS_RE = r'5\d\d'


def _add_matcher_class(error_cls, error_data, base=BotoExceptionMatcher):
    """
        Usable for adding an ExceptionMatcher(s) into the exception tree.
        The not leaf elements does wildcard match
    """
    # in error_code just literal and '.' characters expected
    if not isinstance(error_data, six.string_types):
        (error_code, status_code) = map(str, error_data)
    else:
        status_code = None
        error_code = error_data
    parts = error_code.split('.')
    basematch = ""
    num_parts = len(parts)
    max_index = num_parts - 1
    add_cls = error_cls
    for i_part in six.moves.xrange(num_parts):
        part = parts[i_part]
        leaf = i_part == max_index
        if not leaf:
            match = basematch + part + "[.].*"
        else:
            match = basematch + part

        basematch += part + "[.]"
        if not hasattr(add_cls, part):
            cls_dict = {"CODE_RE": match}
            if leaf and status_code is not None:
                cls_dict["STATUS_RE"] = status_code
            cls = type(part, (base, ), cls_dict)
            setattr(add_cls, part, cls())
            add_cls = cls
        elif leaf:
            raise LookupError("Tries to redefine an error code \"%s\"" % part)
        else:
            add_cls = getattr(add_cls, part)


# TODO(afazekas): classmethod handling
def friendly_function_name_simple(call_able):
    name = ""
    if hasattr(call_able, "im_class"):
        name += call_able.im_class.__name__ + "."
    name += call_able.__name__
    return name


def friendly_function_call_str(call_able, *args, **kwargs):
    string = friendly_function_name_simple(call_able)
    string += "(" + ", ".join(map(str, args))
    if len(kwargs):
        if len(args):
            string += ", "
    string += ", ".join("=".join(map(str, (key, value)))
                        for (key, value) in kwargs.items())
    return string + ")"


class BotoTestCase(tempest.test.BaseTestCase):
    """Recommended to use as base class for boto related test."""

    @classmethod
    def skip_checks(cls):
        super(BotoTestCase, cls).skip_checks()
        if not CONF.compute_feature_enabled.ec2_api:
            raise cls.skipException("The EC2 API is not available")
        if not CONF.identity_feature_enabled.api_v2 or \
                not CONF.identity.auth_version == 'v2':
            raise cls.skipException("Identity v2 is not available")

    @classmethod
    def setup_credentials(cls):
        super(BotoTestCase, cls).setup_credentials()
        cls.os = cls.get_client_manager()

    @classmethod
    def resource_setup(cls):
        super(BotoTestCase, cls).resource_setup()
        cls.conclusion = decision_maker()
        # The trash contains cleanup functions and paramaters in tuples
        # (function, *args, **kwargs)
        cls._resource_trash_bin = {}
        cls._sequence = -1
        if (hasattr(cls, "EC2") and
            cls.conclusion['EC2_CAN_CONNECT_ERROR'] is not None):
            raise cls.skipException("EC2 " + cls.__name__ + ": " +
                                    cls.conclusion['EC2_CAN_CONNECT_ERROR'])
        if (hasattr(cls, "S3") and
            cls.conclusion['S3_CAN_CONNECT_ERROR'] is not None):
            raise cls.skipException("S3 " + cls.__name__ + ": " +
                                    cls.conclusion['S3_CAN_CONNECT_ERROR'])

    @classmethod
    def addResourceCleanUp(cls, function, *args, **kwargs):
        """Adds CleanUp callable, used by tearDownClass.
        Recommended to a use (deep)copy on the mutable args.
        """
        cls._sequence = cls._sequence + 1
        cls._resource_trash_bin[cls._sequence] = (function, args, kwargs)
        return cls._sequence

    @classmethod
    def cancelResourceCleanUp(cls, key):
        """Cancel Clean up request."""
        del cls._resource_trash_bin[key]

    # TODO(afazekas): Add "with" context handling
    def assertBotoError(self, excMatcher, callableObj,
                        *args, **kwargs):
        """Example usage:
            self.assertBotoError(self.ec2_error_code.client.
                                 InvalidKeyPair.Duplicate,
                                 self.client.create_keypair,
                                 key_name)
        """
        try:
            callableObj(*args, **kwargs)
        except exception.BotoServerError as exc:
            error_msg = excMatcher.match(exc)
            if error_msg is not None:
                raise self.failureException, error_msg
        else:
            raise self.failureException, "BotoServerError not raised"

    @classmethod
    def resource_cleanup(cls):
        """Calls the callables added by addResourceCleanUp,
        when you overwrite this function don't forget to call this too.
        """
        fail_count = 0
        trash_keys = sorted(cls._resource_trash_bin, reverse=True)
        for key in trash_keys:
            (function, pos_args, kw_args) = cls._resource_trash_bin[key]
            try:
                func_name = friendly_function_call_str(function, *pos_args,
                                                       **kw_args)
                LOG.debug("Cleaning up: %s" % func_name)
                function(*pos_args, **kw_args)
            except BaseException:
                fail_count += 1
                LOG.exception("Cleanup failed %s" % func_name)
            finally:
                del cls._resource_trash_bin[key]
        super(BotoTestCase, cls).resource_cleanup()
        # NOTE(afazekas): let the super called even on exceptions
        # The real exceptions already logged, if the super throws another,
        # does not causes hidden issues
        if fail_count:
            raise exceptions.TearDownException(num=fail_count)

    ec2_error_code = BotoExceptionMatcher()
    # InsufficientInstanceCapacity can be both server and client error
    ec2_error_code.server = ServerError()
    ec2_error_code.client = ClientError()
    s3_error_code = BotoExceptionMatcher()
    s3_error_code.server = ServerError()
    s3_error_code.client = ClientError()
    valid_image_state = set(('available', 'pending', 'failed'))
    # NOTE(afazekas): 'paused' is not valid status in EC2, but it does not have
    # a good mapping, because it uses memory, but not really a running machine
    valid_instance_state = set(('pending', 'running', 'shutting-down',
                                'terminated', 'stopping', 'stopped', 'paused'))
    valid_volume_status = set(('creating', 'available', 'in-use',
                               'deleting', 'deleted', 'error'))
    valid_snapshot_status = set(('pending', 'completed', 'error'))

    gone_set = set(('_GONE',))

    @classmethod
    def get_lfunction_gone(cls, obj):
        """If the object is instance of a well know type returns back with
            with the correspoding function otherwise it assumes the obj itself
            is the function.
            """
        ec = cls.ec2_error_code
        if isinstance(obj, ec2.instance.Instance):
            colusure_matcher = ec.client.InvalidInstanceID.NotFound
            status_attr = "state"
        elif isinstance(obj, ec2.image.Image):
            colusure_matcher = ec.client.InvalidAMIID.NotFound
            status_attr = "state"
        elif isinstance(obj, ec2.snapshot.Snapshot):
            colusure_matcher = ec.client.InvalidSnapshot.NotFound
            status_attr = "status"
        elif isinstance(obj, ec2.volume.Volume):
            colusure_matcher = ec.client.InvalidVolume.NotFound
            status_attr = "status"
        else:
            return obj

        def _status():
            try:
                obj.update(validate=True)
            except ValueError:
                return "_GONE"
            except exception.EC2ResponseError as exc:
                if colusure_matcher.match(exc) is None:
                    return "_GONE"
                else:
                    raise
            return getattr(obj, status_attr)

        return _status

    def state_wait_gone(self, lfunction, final_set, valid_set):
        if not isinstance(final_set, set):
            final_set = set((final_set,))
        final_set |= self.gone_set
        lfunction = self.get_lfunction_gone(lfunction)
        state = wait.state_wait(lfunction, final_set, valid_set)
        self.assertIn(state, valid_set | self.gone_set)
        return state

    def waitImageState(self, lfunction, wait_for):
        return self.state_wait_gone(lfunction, wait_for,
                                    self.valid_image_state)

    def waitInstanceState(self, lfunction, wait_for):
        return self.state_wait_gone(lfunction, wait_for,
                                    self.valid_instance_state)

    def waitSnapshotStatus(self, lfunction, wait_for):
        return self.state_wait_gone(lfunction, wait_for,
                                    self.valid_snapshot_status)

    def waitVolumeStatus(self, lfunction, wait_for):
        return self.state_wait_gone(lfunction, wait_for,
                                    self.valid_volume_status)

    def assertImageStateWait(self, lfunction, wait_for):
        state = self.waitImageState(lfunction, wait_for)
        self.assertIn(state, wait_for)

    def assertInstanceStateWait(self, lfunction, wait_for):
        state = self.waitInstanceState(lfunction, wait_for)
        self.assertIn(state, wait_for)

    def assertVolumeStatusWait(self, lfunction, wait_for):
        state = self.waitVolumeStatus(lfunction, wait_for)
        self.assertIn(state, wait_for)

    def assertSnapshotStatusWait(self, lfunction, wait_for):
        state = self.waitSnapshotStatus(lfunction, wait_for)
        self.assertIn(state, wait_for)

    def assertAddressDissasociatedWait(self, address):

        def _disassociate():
            cli = self.ec2_client
            addresses = cli.get_all_addresses(addresses=(address.public_ip,))
            if len(addresses) != 1:
                return "INVALID"
            if addresses[0].instance_id:
                LOG.info("%s associated to %s",
                         address.public_ip,
                         addresses[0].instance_id)
                return "ASSOCIATED"
            return "DISASSOCIATED"

        state = wait.state_wait(_disassociate, "DISASSOCIATED",
                                set(("ASSOCIATED", "DISASSOCIATED")))
        self.assertEqual(state, "DISASSOCIATED")

    def assertAddressReleasedWait(self, address):

        def _address_delete():
            # NOTE(afazekas): the filter gives back IP
            # even if it is not associated to my tenant
            if (address.public_ip not in map(lambda a: a.public_ip,
                self.ec2_client.get_all_addresses())):
                    return "DELETED"
            return "NOTDELETED"

        state = wait.state_wait(_address_delete, "DELETED")
        self.assertEqual(state, "DELETED")

    def assertReSearch(self, regexp, string):
        if re.search(regexp, string) is None:
            raise self.failureException("regexp: '%s' not found in '%s'" %
                                        (regexp, string))

    def assertNotReSearch(self, regexp, string):
        if re.search(regexp, string) is not None:
            raise self.failureException("regexp: '%s' found in '%s'" %
                                        (regexp, string))

    def assertReMatch(self, regexp, string):
        if re.match(regexp, string) is None:
            raise self.failureException("regexp: '%s' not matches on '%s'" %
                                        (regexp, string))

    def assertNotReMatch(self, regexp, string):
        if re.match(regexp, string) is not None:
            raise self.failureException("regexp: '%s' matches on '%s'" %
                                        (regexp, string))

    @classmethod
    def destroy_bucket(cls, connection_data, bucket):
        """Destroys the bucket and its content, just for teardown."""
        exc_num = 0
        try:
            with contextlib.closing(
                    boto.connect_s3(**connection_data)) as conn:
                if isinstance(bucket, basestring):
                    bucket = conn.lookup(bucket)
                    assert isinstance(bucket, s3.bucket.Bucket)
                for obj in bucket.list():
                    try:
                        bucket.delete_key(obj.key)
                        obj.close()
                    except BaseException:
                        LOG.exception("Failed to delete key %s " % obj.key)
                        exc_num += 1
            conn.delete_bucket(bucket)
        except BaseException:
            LOG.exception("Failed to destroy bucket %s " % bucket)
            exc_num += 1
        if exc_num:
            raise exceptions.TearDownException(num=exc_num)

    @classmethod
    def destroy_reservation(cls, reservation):
        """Terminate instances in a reservation, just for teardown."""
        exc_num = 0

        def _instance_state():
            try:
                instance.update(validate=True)
            except ValueError:
                return "_GONE"
            except exception.EC2ResponseError as exc:
                if cls.ec2_error_code.\
                        client.InvalidInstanceID.NotFound.match(exc) is None:
                    return "_GONE"
                # NOTE(afazekas): incorrect code,
                # but the resource must be destoreyd
                if exc.error_code == "InstanceNotFound":
                    return "_GONE"

            return instance.state

        for instance in reservation.instances:
            try:
                instance.terminate()
                wait.re_search_wait(_instance_state, "_GONE")
            except BaseException:
                LOG.exception("Failed to terminate instance %s " % instance)
                exc_num += 1
        if exc_num:
            raise exceptions.TearDownException(num=exc_num)

    # NOTE(afazekas): The incorrect ErrorCodes makes very, very difficult
    # to write better teardown

    @classmethod
    def destroy_security_group_wait(cls, group):
        """Delete group.
           Use just for teardown!
        """
        # NOTE(afazekas): should wait/try until all related instance terminates
        group.delete()

    @classmethod
    def destroy_volume_wait(cls, volume):
        """Delete volume, tries to detach first.
           Use just for teardown!
        """
        exc_num = 0
        snaps = volume.snapshots()
        if len(snaps):
            LOG.critical("%s Volume has %s snapshot(s)", volume.id,
                         map(snaps.id, snaps))

        # NOTE(afazekas): detaching/attching not valid EC2 status
        def _volume_state():
            volume.update(validate=True)
            try:
                # NOTE(gmann): Make sure volume is attached.
                # Checking status as 'not "available"' is not enough to make
                # sure volume is attached as it can be in "error" state
                if volume.status == "in-use":
                    volume.detach(force=True)
            except BaseException:
                LOG.exception("Failed to detach volume %s" % volume)
                # exc_num += 1 "nonlocal" not in python2
            return volume.status

        try:
            wait.re_search_wait(_volume_state, "available")
            # not validates status
            LOG.info(_volume_state())
            volume.delete()
        except BaseException:
            LOG.exception("Failed to delete volume %s" % volume)
            exc_num += 1
        if exc_num:
            raise exceptions.TearDownException(num=exc_num)

    @classmethod
    def destroy_snapshot_wait(cls, snapshot):
        """delete snapshot, wait until it ceases to exist."""
        snapshot.delete()

        def _update():
            snapshot.update(validate=True)

        wait.wait_exception(_update)


# you can specify tuples if you want to specify the status pattern
for code in ('AddressLimitExceeded', 'AttachmentLimitExceeded', 'AuthFailure',
             'Blocked', 'CustomerGatewayLimitExceeded', 'DependencyViolation',
             'DiskImageSizeTooLarge', 'FilterLimitExceeded',
             'Gateway.NotAttached', 'IdempotentParameterMismatch',
             'IncorrectInstanceState', 'IncorrectState',
             'InstanceLimitExceeded', 'InsufficientInstanceCapacity',
             'InsufficientReservedInstancesCapacity',
             'InternetGatewayLimitExceeded', 'InvalidAMIAttributeItemValue',
             'InvalidAMIID.Malformed', 'InvalidAMIID.NotFound',
             'InvalidAMIID.Unavailable', 'InvalidAssociationID.NotFound',
             'InvalidAttachment.NotFound', 'InvalidConversionTaskId',
             'InvalidCustomerGateway.DuplicateIpAddress',
             'InvalidCustomerGatewayID.NotFound', 'InvalidDevice.InUse',
             'InvalidDhcpOptionsID.NotFound', 'InvalidFormat',
             'InvalidFilter', 'InvalidGatewayID.NotFound',
             'InvalidGroup.Duplicate', 'InvalidGroupId.Malformed',
             'InvalidGroup.InUse', 'InvalidGroup.NotFound',
             'InvalidGroup.Reserved', 'InvalidInstanceID.Malformed',
             'InvalidInstanceID.NotFound',
             'InvalidInternetGatewayID.NotFound', 'InvalidIPAddress.InUse',
             'InvalidKeyPair.Duplicate', 'InvalidKeyPair.Format',
             'InvalidKeyPair.NotFound', 'InvalidManifest',
             'InvalidNetworkAclEntry.NotFound',
             'InvalidNetworkAclID.NotFound', 'InvalidParameterCombination',
             'InvalidParameterValue', 'InvalidPermission.Duplicate',
             'InvalidPermission.Malformed', 'InvalidReservationID.Malformed',
             'InvalidReservationID.NotFound', 'InvalidRoute.NotFound',
             'InvalidRouteTableID.NotFound',
             'InvalidSecurity.RequestHasExpired',
             'InvalidSnapshotID.Malformed', 'InvalidSnapshot.NotFound',
             'InvalidUserID.Malformed', 'InvalidReservedInstancesId',
             'InvalidReservedInstancesOfferingId',
             'InvalidSubnetID.NotFound', 'InvalidVolumeID.Duplicate',
             'InvalidVolumeID.Malformed', 'InvalidVolumeID.ZoneMismatch',
             'InvalidVolume.NotFound', 'InvalidVpcID.NotFound',
             'InvalidVpnConnectionID.NotFound',
             'InvalidVpnGatewayID.NotFound',
             'InvalidZone.NotFound', 'LegacySecurityGroup',
             'MissingParameter', 'NetworkAclEntryAlreadyExists',
             'NetworkAclEntryLimitExceeded', 'NetworkAclLimitExceeded',
             'NonEBSInstance', 'PendingSnapshotLimitExceeded',
             'PendingVerification', 'OptInRequired', 'RequestLimitExceeded',
             'ReservedInstancesLimitExceeded', 'Resource.AlreadyAssociated',
             'ResourceLimitExceeded', 'RouteAlreadyExists',
             'RouteLimitExceeded', 'RouteTableLimitExceeded',
             'RulesPerSecurityGroupLimitExceeded',
             'SecurityGroupLimitExceeded',
             'SecurityGroupsPerInstanceLimitExceeded',
             'SnapshotLimitExceeded', 'SubnetLimitExceeded',
             'UnknownParameter', 'UnsupportedOperation',
             'VolumeLimitExceeded', 'VpcLimitExceeded',
             'VpnConnectionLimitExceeded',
             'VpnGatewayAttachmentLimitExceeded', 'VpnGatewayLimitExceeded'):
    _add_matcher_class(BotoTestCase.ec2_error_code.client,
                       code, base=ClientError)

for code in ('InsufficientAddressCapacity', 'InsufficientInstanceCapacity',
             'InsufficientReservedInstanceCapacity', 'InternalError',
             'Unavailable'):
    _add_matcher_class(BotoTestCase.ec2_error_code.server,
                       code, base=ServerError)


for code in (('AccessDenied', 403),
             ('AccountProblem', 403),
             ('AmbiguousGrantByEmailAddress', 400),
             ('BadDigest', 400),
             ('BucketAlreadyExists', 409),
             ('BucketAlreadyOwnedByYou', 409),
             ('BucketNotEmpty', 409),
             ('CredentialsNotSupported', 400),
             ('CrossLocationLoggingProhibited', 403),
             ('EntityTooSmall', 400),
             ('EntityTooLarge', 400),
             ('ExpiredToken', 400),
             ('IllegalVersioningConfigurationException', 400),
             ('IncompleteBody', 400),
             ('IncorrectNumberOfFilesInPostRequest', 400),
             ('InlineDataTooLarge', 400),
             ('InvalidAccessKeyId', 403),
             'InvalidAddressingHeader',
             ('InvalidArgument', 400),
             ('InvalidBucketName', 400),
             ('InvalidBucketState', 409),
             ('InvalidDigest', 400),
             ('InvalidLocationConstraint', 400),
             ('InvalidPart', 400),
             ('InvalidPartOrder', 400),
             ('InvalidPayer', 403),
             ('InvalidPolicyDocument', 400),
             ('InvalidRange', 416),
             ('InvalidRequest', 400),
             ('InvalidSecurity', 403),
             ('InvalidSOAPRequest', 400),
             ('InvalidStorageClass', 400),
             ('InvalidTargetBucketForLogging', 400),
             ('InvalidToken', 400),
             ('InvalidURI', 400),
             ('KeyTooLong', 400),
             ('MalformedACLError', 400),
             ('MalformedPOSTRequest', 400),
             ('MalformedXML', 400),
             ('MaxMessageLengthExceeded', 400),
             ('MaxPostPreDataLengthExceededError', 400),
             ('MetadataTooLarge', 400),
             ('MethodNotAllowed', 405),
             ('MissingAttachment'),
             ('MissingContentLength', 411),
             ('MissingRequestBodyError', 400),
             ('MissingSecurityElement', 400),
             ('MissingSecurityHeader', 400),
             ('NoLoggingStatusForKey', 400),
             ('NoSuchBucket', 404),
             ('NoSuchKey', 404),
             ('NoSuchLifecycleConfiguration', 404),
             ('NoSuchUpload', 404),
             ('NoSuchVersion', 404),
             ('NotSignedUp', 403),
             ('NotSuchBucketPolicy', 404),
             ('OperationAborted', 409),
             ('PermanentRedirect', 301),
             ('PreconditionFailed', 412),
             ('Redirect', 307),
             ('RequestIsNotMultiPartContent', 400),
             ('RequestTimeout', 400),
             ('RequestTimeTooSkewed', 403),
             ('RequestTorrentOfBucketError', 400),
             ('SignatureDoesNotMatch', 403),
             ('TemporaryRedirect', 307),
             ('TokenRefreshRequired', 400),
             ('TooManyBuckets', 400),
             ('UnexpectedContent', 400),
             ('UnresolvableGrantByEmailAddress', 400),
             ('UserKeyMustBeSpecified', 400)):
    _add_matcher_class(BotoTestCase.s3_error_code.client,
                       code, base=ClientError)


for code in (('InternalError', 500),
             ('NotImplemented', 501),
             ('ServiceUnavailable', 503),
             ('SlowDown', 503)):
    _add_matcher_class(BotoTestCase.s3_error_code.server,
                       code, base=ServerError)
