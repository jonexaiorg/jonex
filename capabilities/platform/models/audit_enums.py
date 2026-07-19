

from enum import Enum


class LogType(str, Enum):

    LOGIN = "LOGIN"
    OPERATION = "OPERATION"
    SYSTEM = "SYSTEM"
    TASK = "TASK"


class Outcome(str, Enum):

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class LogLevel(str, Enum):

    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"




class AuditAction:



    AUTH_LOGIN = "auth.login"
    AUTH_EXCHANGE_TICKET = "auth.exchange_ticket"
    AUTH_LOGOUT = "auth.logout"


    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_PARSE = "document.parse"
    DOCUMENT_PARSE_DONE = "document.parse_done"
    DOCUMENT_PARSE_FAILED = "document.parse_failed"
    DOCUMENT_PARSE_RECOVER = "document.parse_recover"
    DOCUMENT_DELETE = "document.delete"


    HTTP_METHOD = "http.{method}"
