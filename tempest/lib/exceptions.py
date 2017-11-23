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

import testtools


class TempestException(Exception):
    """Base Tempest Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = "An unknown exception occurred"

    def __init__(self, *args, **kwargs):
        super(TempestException, self).__init__()
        try:
            self._error_string = self.message % kwargs
        except Exception:
            # at least get the core message out if something happened
            self._error_string = self.message
        if args:
            # If there is a non-kwarg parameter, assume it's the error
            # message or reason description and tack it on to the end
            # of the exception message
            # Convert all arguments into their string representations...
            args = ["%s" % arg for arg in args]
            self._error_string = (self._error_string +
                                  "\nDetails: %s" % '\n'.join(args))

    def __str__(self):
        return self._error_string

    def __repr__(self):
        return self._error_string


class RestClientException(TempestException,
                          testtools.TestCase.failureException):
    def __init__(self, resp_body=None, *args, **kwargs):
        if 'resp' in kwargs:
            self.resp = kwargs.get('resp')
        self.resp_body = resp_body
        message = kwargs.get("message", resp_body)
        super(RestClientException, self).__init__(message, *args, **kwargs)


class OtherRestClientException(RestClientException):
    pass


class ServerRestClientException(RestClientException):
    pass


class ClientRestClientException(RestClientException):
    pass


class InvalidHttpSuccessCode(OtherRestClientException):
    message = "The success code is different than the expected one"


class BadRequest(ClientRestClientException):
    status_code = 400
    message = "Bad request"


class Unauthorized(ClientRestClientException):
    status_code = 401
    message = 'Unauthorized'


class Forbidden(ClientRestClientException):
    status_code = 403
    message = "Forbidden"


class NotFound(ClientRestClientException):
    status_code = 404
    message = "Object not found"


class Conflict(ClientRestClientException):
    status_code = 409
    message = "Conflict with state of target resource"


class Gone(ClientRestClientException):
    status_code = 410
    message = "The requested resource is no longer available"


class PreconditionFailed(ClientRestClientException):
    status_code = 412
    message = "Precondition Failed"


class RateLimitExceeded(ClientRestClientException):
    status_code = 413
    message = "Rate limit exceeded"


class OverLimit(ClientRestClientException):
    status_code = 413
    message = "Request entity is too large"


class InvalidContentType(ClientRestClientException):
    status_code = 415
    message = "Invalid content type provided"


class UnprocessableEntity(ClientRestClientException):
    status_code = 422
    message = "Unprocessable entity"


class ServerFault(ServerRestClientException):
    status_code = 500
    message = "Got server fault"


class NotImplemented(ServerRestClientException):
    status_code = 501
    message = "Got NotImplemented error"


class TimeoutException(OtherRestClientException):
    message = "Request timed out"


class ResponseWithNonEmptyBody(OtherRestClientException):
    message = ("RFC Violation! Response with %(status)d HTTP Status Code "
               "MUST NOT have a body")


class ResponseWithEntity(OtherRestClientException):
    message = ("RFC Violation! Response with 205 HTTP Status Code "
               "MUST NOT have an entity")


class InvalidHTTPResponseBody(OtherRestClientException):
    message = "HTTP response body is invalid json or xml"


class InvalidHTTPResponseHeader(OtherRestClientException):
    message = "HTTP response header is invalid"


class UnexpectedContentType(OtherRestClientException):
    message = "Unexpected content type provided"


class UnexpectedResponseCode(OtherRestClientException):
    message = "Unexpected response code received"


class InvalidConfiguration(TempestException):
    message = "Invalid Configuration"


class InvalidIdentityVersion(TempestException):
    message = "Invalid version %(identity_version)s of the identity service"


class InvalidStructure(TempestException):
    message = "Invalid structure of table with details"


class InvalidAPIVersionString(TempestException):
    message = ("API Version String %(version)s is of invalid format. Must "
               "be of format MajorNum.MinorNum or string 'latest'.")


class JSONSchemaNotFound(TempestException):
    message = ("JSON Schema for %(version)s is not found in\n"
               " %(schema_versions_info)s")


class InvalidAPIVersionRange(TempestException):
    message = ("The API version range is invalid.")


class BadAltAuth(TempestException):
    """Used when trying and failing to change to alt creds.

    If alt creds end up the same as primary creds, use this
    exception. This is often going to be the case when you assume
    project_id is in the url, but it's not.

    """
    message = "The alt auth looks the same as primary auth for %(part)s"


class CommandFailed(Exception):
    def __init__(self, returncode, cmd, output, stderr):
        super(CommandFailed, self).__init__()
        self.returncode = returncode
        self.cmd = cmd
        self.stdout = output
        self.stderr = stderr

    def __str__(self):
        return ("Command '%s' returned non-zero exit status %d.\n"
                "stdout:\n%s\n"
                "stderr:\n%s" % (self.cmd,
                                 self.returncode,
                                 self.stdout,
                                 self.stderr))


class IdentityError(TempestException):
    message = "Got identity error"


class EndpointNotFound(TempestException):
    message = "Endpoint not found"


class InvalidCredentials(TempestException):
    message = "Invalid Credentials"


class InvalidScope(TempestException):
    message = "Invalid Scope %(scope)s for %(auth_provider)s"


class SSHTimeout(TempestException):
    message = ("Connection to the %(host)s via SSH timed out.\n"
               "User: %(user)s, Password: %(password)s")


class SSHExecCommandFailed(TempestException):
    """Raised when remotely executed command returns nonzero status."""
    message = ("Command '%(command)s', exit status: %(exit_status)d, "
               "stderr:\n%(stderr)s\n"
               "stdout:\n%(stdout)s")


class UnknownServiceClient(TempestException):
    message = "Service clients named %(services)s are not known"


class ServiceClientRegistrationException(TempestException):
    message = ("Error registering module %(name)s in path %(module_path)s, "
               "with service %(service_version)s and clients "
               "%(client_names)s: %(detailed_error)s")


class PluginRegistrationException(TempestException):
    message = "Error registering plugin %(name)s: %(detailed_error)s"


class VolumeBackupException(TempestException):
    message = "Volume backup %(backup_id)s failed and is in ERROR status"


class DeleteErrorException(TempestException):
    message = ("Resource %(resource_id)s failed to delete "
               "and is in ERROR status")


class InvalidTestResource(TempestException):
    message = "%(name)s is not a valid %(type)s, or the name is ambiguous"


class InvalidParam(TempestException):
    message = ("Invalid Parameter passed: %(invalid_param)s")
