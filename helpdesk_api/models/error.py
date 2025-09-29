import datetime  # Import datetime module for handling date and time
import json  # Import json module for JSON encoding and decoding
import logging  # Import logging module for logging purposes

import werkzeug.wrappers  # Import werkzeug.wrappers for creating HTTP responses

# Set up logging
_logger = logging.getLogger(__name__)

def default(o):
    """
    Custom JSON serializer for objects not serializable by default json code.
    :param o: Object to serialize
    :return: Serialized representation of the object
    """
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()  # Convert date and datetime objects to ISO format strings
    if isinstance(o, bytes):
        return str(o)  # Convert bytes objects to strings

def valid_response(data, status=200):
    """
    Create a valid HTTP response with given data and status code.
    :param data: Data to include in the response body
    :param status: HTTP status code (default is 200)
    :return: HTTP response
    """
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}  # Prepare response data with count and data
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data, default=default),  # Serialize the data to JSON format
    )

def invalid_response(typ, message=None, status=403):
    """
    Create an invalid HTTP response with given error type, message, and status code.
    :param typ: Type of the error
    :param message: Error message (default is None)
    :param status: HTTP status code (default is 403)
    :return: HTTP response
    """
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(
            {"type": typ, "message": str(message) if message else "wrong arguments (missing validation)"},  # Prepare error data
            default=datetime.datetime.isoformat,  # Serialize datetime objects to ISO format
        ),
    )

def invalid_error(data, status=500):
    """
    Create an HTTP response for server errors with given data and status code.
    :param data: Data to include in the response body
    :param status: HTTP status code (default is 500)
    :return: HTTP response
    """
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}  # Prepare response data with count and data
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data, default=default),  # Serialize the data to JSON format
    )

def extract_arguments(limit="80", offset=0, order="id", domain="", fields=[]):
    """
    Parse additional data sent along with the request.
    :param limit: Limit on the number of records to retrieve (default is 80)
    :param offset: Offset for the records to retrieve (default is 0)
    :param order: Order by which to sort the records (default is "id")
    :param domain: Domain for filtering the records
    :param fields: Fields to include in the response
    :return: Parsed arguments as a list
    """
    limit = int(limit)  # Convert limit to integer
    expresions = []  # Initialize list for domain expressions
    if domain:
        # Parse and prepare domain expressions
        expresions = [tuple(preg.replace(":", ",").split(",")) for preg in domain.split(",")]
        expresions = json.dumps(expresions)
        expresions = json.loads(expresions, parse_int=True)
    if fields:
        fields = fields.split(",")  # Split fields into a list

    if offset:
        offset = int(offset)  # Convert offset to integer
    return [expresions, fields, offset, limit, order]  # Return parsed arguments as a list
