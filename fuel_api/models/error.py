import ast  # Module for abstract syntax trees (not used in this code)
import datetime  # Module for working with dates and times
import json  # Module for working with JSON data
import logging  # Module for logging
import werkzeug.wrappers  # Werkzeug response wrappers for WSGI applications

_logger = logging.getLogger(__name__)  # Setting up a logger for this module

def default(o):
    """
    Default JSON serializer.
    Converts datetime objects to ISO format and bytes to string.
    :param o: Object to be serialized
    :return: Serialized object
    """
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()  # Convert datetime objects to ISO format
    if isinstance(o, bytes):
        return str(o)  # Convert bytes to string

def valid_response(data, status=200):
    """
    Creates a valid HTTP response.
    :param data: Data to be included in the response
    :param status: HTTP status code (default is 200)
    :return: A werkzeug response object with JSON data
    """
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data, default=default),  # Use custom default serializer
    )

def invalid_response(typ, message=None, status=403):
    """
    Creates an invalid HTTP response.
    :param typ: Type of error
    :param message: Error message
    :param status: HTTP status code (default is 403)
    :return: A werkzeug response object with JSON error data
    """
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(
            {"type": typ, "message": str(message) if str(message) else "wrong arguments (missing validation)"},
            default=datetime.datetime.isoformat,  # Use ISO format for datetime
        ),
    )

def invalid_error(data, status=500):
    """
    Creates an HTTP response for server errors.
    :param data: Error data
    :param status: HTTP status code (default is 500)
    :return: A werkzeug response object with JSON error data
    """
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data, default=default),  # Use custom default serializer
    )

def extract_arguments(limit="80", offset=0, order="id", domain="", fields=[]):
    """
    Extracts and parses arguments from the request.
    :param limit: Limit on the number of records (default is 80)
    :param offset: Offset for pagination (default is 0)
    :param order: Order by field (default is "id")
    :param domain: Domain filter (default is "")
    :param fields: List of fields to include (default is empty list)
    :return: List of parsed arguments [expressions, fields, offset, limit, order]
    """
    limit = int(limit)  # Convert limit to integer
    expresions = []
    if domain:
        # Convert domain string to a list of tuples
        expresions = [tuple(preg.replace(":", ",").split(",")) for preg in domain.split(",")]
        expresions = json.dumps(expresions)
        expresions = json.loads(expresions, parse_int=True)
    if fields:
        fields = fields.split(",")  # Split fields string into a list

    if offset:
        offset = int(offset)  # Convert offset to integer
    return [expresions, fields, offset, limit, order]  # Return parsed arguments
