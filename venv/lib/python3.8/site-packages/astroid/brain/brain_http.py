# Copyright (c) 2018 Claudiu Popa <pcmanticore@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""Astroid brain hints for some of the `http` module."""
import textwrap

import astroid
from astroid.builder import AstroidBuilder


def _http_transform():
    code = textwrap.dedent(
        """
    from collections import namedtuple
    _HTTPStatus = namedtuple('_HTTPStatus', 'value phrase description')

    class HTTPStatus:

        # informational
        CONTINUE = _HTTPStatus(100, 'Continue', 'Request received, please continue')
        SWITCHING_PROTOCOLS = _HTTPStatus(101, 'Switching Protocols',
                'Switching to new protocol; obey Upgrade header')
        PROCESSING = _HTTPStatus(102, 'Processing', '')
        OK = _HTTPStatus(200, 'OK', 'Request fulfilled, document follows')
        CREATED = _HTTPStatus(201, 'Created', 'Document created, URL follows')
        ACCEPTED = _HTTPStatus(202, 'Accepted',
            'Request accepted, processing continues off-line')
        NON_AUTHORITATIVE_INFORMATION = _HTTPStatus(203,
            'Non-Authoritative Information', 'Request fulfilled from cache')
        NO_CONTENT = _HTTPStatus(204, 'No Content', 'Request fulfilled, nothing follows')
        RESET_CONTENT =_HTTPStatus(205, 'Reset Content', 'Clear input form for further input')
        PARTIAL_CONTENT = _HTTPStatus(206, 'Partial Content', 'Partial content follows')
        MULTI_STATUS = _HTTPStatus(207, 'Multi-Status', '')
        ALREADY_REPORTED = _HTTPStatus(208, 'Already Reported', '')
        IM_USED = _HTTPStatus(226, 'IM Used', '')
        MULTIPLE_CHOICES = _HTTPStatus(300, 'Multiple Choices',
            'Object has several resources -- see URI list')
        MOVED_PERMANENTLY = _HTTPStatus(301, 'Moved Permanently',
            'Object moved permanently -- see URI list')
        FOUND = _HTTPStatus(302, 'Found', 'Object moved temporarily -- see URI list')
        SEE_OTHER = _HTTPStatus(303, 'See Other', 'Object moved -- see Method and URL list')
        NOT_MODIFIED = _HTTPStatus(304, 'Not Modified',
            'Document has not changed since given time')
        USE_PROXY = _HTTPStatus(305, 'Use Proxy',
            'You must use proxy specified in Location to access this resource')
        TEMPORARY_REDIRECT = _HTTPStatus(307, 'Temporary Redirect',
            'Object moved temporarily -- see URI list')
        PERMANENT_REDIRECT = _HTTPStatus(308, 'Permanent Redirect',
            'Object moved permanently -- see URI list')
        BAD_REQUEST = _HTTPStatus(400, 'Bad Request',
            'Bad request syntax or unsupported method')
        UNAUTHORIZED = _HTTPStatus(401, 'Unauthorized',
            'No permission -- see authorization schemes')
        PAYMENT_REQUIRED = _HTTPStatus(402, 'Payment Required',
            'No payment -- see charging schemes')
        FORBIDDEN = _HTTPStatus(403, 'Forbidden',
            'Request forbidden -- authorization will not help')
        NOT_FOUND = _HTTPStatus(404, 'Not Found',
            'Nothing matches the given URI')
        METHOD_NOT_ALLOWED = _HTTPStatus(405, 'Method Not Allowed',
            'Specified method is invalid for this resource')
        NOT_ACCEPTABLE = _HTTPStatus(406, 'Not Acceptable',
            'URI not available in preferred format')
        PROXY_AUTHENTICATION_REQUIRED = _HTTPStatus(407,
            'Proxy Authentication Required',
            'You must authenticate with this proxy before proceeding')
        REQUEST_TIMEOUT = _HTTPStatus(408, 'Request Timeout',
            'Request timed out; try again later')
        CONFLICT = _HTTPStatus(409, 'Conflict', 'Request conflict')
        GONE = _HTTPStatus(410, 'Gone',
            'URI no longer exists and has been permanently removed')
        LENGTH_REQUIRED = _HTTPStatus(411, 'Length Required',
            'Client must specify Content-Length')
        PRECONDITION_FAILED = _HTTPStatus(412, 'Precondition Failed',
            'Precondition in headers is false')
        REQUEST_ENTITY_TOO_LARGE = _HTTPStatus(413, 'Request Entity Too Large',
            'Entity is too large')
        REQUEST_URI_TOO_LONG = _HTTPStatus(414, 'Request-URI Too Long',
            'URI is too long')
        UNSUPPORTED_MEDIA_TYPE = _HTTPStatus(415, 'Unsupported Media Type',
            'Entity body in unsupported format')
        REQUESTED_RANGE_NOT_SATISFIABLE = _HTTPStatus(416,
            'Requested Range Not Satisfiable',
            'Cannot satisfy request range')
        EXPECTATION_FAILED = _HTTPStatus(417, 'Expectation Failed',
            'Expect condition could not be satisfied')
        MISDIRECTED_REQUEST = _HTTPStatus(421, 'Misdirected Request',
            'Server is not able to produce a response')
        UNPROCESSABLE_ENTITY = _HTTPStatus(422, 'Unprocessable Entity')
        LOCKED = _HTTPStatus(423, 'Locked')
        FAILED_DEPENDENCY = _HTTPStatus(424, 'Failed Dependency')
        UPGRADE_REQUIRED = _HTTPStatus(426, 'Upgrade Required')
        PRECONDITION_REQUIRED = _HTTPStatus(428, 'Precondition Required',
            'The origin server requires the request to be conditional')
        TOO_MANY_REQUESTS = _HTTPStatus(429, 'Too Many Requests',
            'The user has sent too many requests in '
            'a given amount of time ("rate limiting")')
        REQUEST_HEADER_FIELDS_TOO_LARGE = _HTTPStatus(431,
            'Request Header Fields Too Large',
            'The server is unwilling to process the request because its header '
            'fields are too large')
        UNAVAILABLE_FOR_LEGAL_REASONS = _HTTPStatus(451,
            'Unavailable For Legal Reasons',
            'The server is denying access to the '
            'resource as a consequence of a legal demand')
        INTERNAL_SERVER_ERROR = _HTTPStatus(500, 'Internal Server Error',
            'Server got itself in trouble')
        NOT_IMPLEMENTED = _HTTPStatus(501, 'Not Implemented',
            'Server does not support this operation')
        BAD_GATEWAY = _HTTPStatus(502, 'Bad Gateway',
            'Invalid responses from another server/proxy')
        SERVICE_UNAVAILABLE = _HTTPStatus(503, 'Service Unavailable',
            'The server cannot process the request due to a high load')
        GATEWAY_TIMEOUT = _HTTPStatus(504, 'Gateway Timeout',
            'The gateway server did not receive a timely response')
        HTTP_VERSION_NOT_SUPPORTED = _HTTPStatus(505, 'HTTP Version Not Supported',
            'Cannot fulfill request')
        VARIANT_ALSO_NEGOTIATES = _HTTPStatus(506, 'Variant Also Negotiates')
        INSUFFICIENT_STORAGE = _HTTPStatus(507, 'Insufficient Storage')
        LOOP_DETECTED = _HTTPStatus(508, 'Loop Detected')
        NOT_EXTENDED = _HTTPStatus(510, 'Not Extended')
        NETWORK_AUTHENTICATION_REQUIRED = _HTTPStatus(511,
            'Network Authentication Required',
            'The client needs to authenticate to gain network access')
    """
    )
    return AstroidBuilder(astroid.MANAGER).string_build(code)


def _http_client_transform():
    return AstroidBuilder(astroid.MANAGER).string_build(
        textwrap.dedent(
            """
    from http import HTTPStatus

    CONTINUE = HTTPStatus.CONTINUE
    SWITCHING_PROTOCOLS = HTTPStatus.SWITCHING_PROTOCOLS
    PROCESSING = HTTPStatus.PROCESSING
    OK = HTTPStatus.OK
    CREATED = HTTPStatus.CREATED
    ACCEPTED = HTTPStatus.ACCEPTED
    NON_AUTHORITATIVE_INFORMATION = HTTPStatus.NON_AUTHORITATIVE_INFORMATION
    NO_CONTENT = HTTPStatus.NO_CONTENT
    RESET_CONTENT = HTTPStatus.RESET_CONTENT
    PARTIAL_CONTENT = HTTPStatus.PARTIAL_CONTENT
    MULTI_STATUS = HTTPStatus.MULTI_STATUS
    ALREADY_REPORTED = HTTPStatus.ALREADY_REPORTED
    IM_USED = HTTPStatus.IM_USED
    MULTIPLE_CHOICES = HTTPStatus.MULTIPLE_CHOICES
    MOVED_PERMANENTLY = HTTPStatus.MOVED_PERMANENTLY
    FOUND = HTTPStatus.FOUND
    SEE_OTHER = HTTPStatus.SEE_OTHER
    NOT_MODIFIED = HTTPStatus.NOT_MODIFIED
    USE_PROXY = HTTPStatus.USE_PROXY
    TEMPORARY_REDIRECT = HTTPStatus.TEMPORARY_REDIRECT
    PERMANENT_REDIRECT = HTTPStatus.PERMANENT_REDIRECT
    BAD_REQUEST = HTTPStatus.BAD_REQUEST
    UNAUTHORIZED = HTTPStatus.UNAUTHORIZED
    PAYMENT_REQUIRED = HTTPStatus.PAYMENT_REQUIRED
    FORBIDDEN = HTTPStatus.FORBIDDEN
    NOT_FOUND = HTTPStatus.NOT_FOUND
    METHOD_NOT_ALLOWED = HTTPStatus.METHOD_NOT_ALLOWED
    NOT_ACCEPTABLE = HTTPStatus.NOT_ACCEPTABLE
    PROXY_AUTHENTICATION_REQUIRED = HTTPStatus.PROXY_AUTHENTICATION_REQUIRED
    REQUEST_TIMEOUT = HTTPStatus.REQUEST_TIMEOUT
    CONFLICT = HTTPStatus.CONFLICT
    GONE = HTTPStatus.GONE
    LENGTH_REQUIRED = HTTPStatus.LENGTH_REQUIRED
    PRECONDITION_FAILED = HTTPStatus.PRECONDITION_FAILED
    REQUEST_ENTITY_TOO_LARGE = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    REQUEST_URI_TOO_LONG = HTTPStatus.REQUEST_URI_TOO_LONG
    UNSUPPORTED_MEDIA_TYPE = HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    REQUESTED_RANGE_NOT_SATISFIABLE = HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE
    EXPECTATION_FAILED = HTTPStatus.EXPECTATION_FAILED
    UNPROCESSABLE_ENTITY = HTTPStatus.UNPROCESSABLE_ENTITY
    LOCKED = HTTPStatus.LOCKED
    FAILED_DEPENDENCY = HTTPStatus.FAILED_DEPENDENCY
    UPGRADE_REQUIRED = HTTPStatus.UPGRADE_REQUIRED
    PRECONDITION_REQUIRED = HTTPStatus.PRECONDITION_REQUIRED
    TOO_MANY_REQUESTS = HTTPStatus.TOO_MANY_REQUESTS
    REQUEST_HEADER_FIELDS_TOO_LARGE = HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE
    INTERNAL_SERVER_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR
    NOT_IMPLEMENTED = HTTPStatus.NOT_IMPLEMENTED
    BAD_GATEWAY = HTTPStatus.BAD_GATEWAY
    SERVICE_UNAVAILABLE = HTTPStatus.SERVICE_UNAVAILABLE
    GATEWAY_TIMEOUT = HTTPStatus.GATEWAY_TIMEOUT
    HTTP_VERSION_NOT_SUPPORTED = HTTPStatus.HTTP_VERSION_NOT_SUPPORTED
    VARIANT_ALSO_NEGOTIATES = HTTPStatus.VARIANT_ALSO_NEGOTIATES
    INSUFFICIENT_STORAGE = HTTPStatus.INSUFFICIENT_STORAGE
    LOOP_DETECTED = HTTPStatus.LOOP_DETECTED
    NOT_EXTENDED = HTTPStatus.NOT_EXTENDED
    NETWORK_AUTHENTICATION_REQUIRED = HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED
    """
        )
    )


astroid.register_module_extender(astroid.MANAGER, "http", _http_transform)
astroid.register_module_extender(astroid.MANAGER, "http.client", _http_client_transform)
