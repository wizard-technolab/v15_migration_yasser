import datetime  # Import the datetime module for working with dates and times
import json  # Import the json module for JSON serialization
import logging  # Import the logging module for logging messages
import werkzeug.wrappers  # Import Werkzeug wrappers for creating HTTP responses

_logger = logging.getLogger(__name__)  # Create a logger object for this module


def default(o):
    """
    Custom JSON serializer for datetime and bytes objects.

    :param o: Object to be serialized
    :return: ISO formatted date string for datetime objects or string for bytes
    """
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()  # Convert datetime objects to ISO format for JSON serialization
    if isinstance(o, bytes):
        return str(o)  # Convert bytes to string for JSON serialization
    return o  # Return the object as-is if it's not datetime or bytes


def valid_response(data, status=200):
    """
    Returns a valid JSON response with a status code of 200 by default.

    :param data: Data to be included in the response
    :param status: HTTP status code (default: 200)
    :return: werkzeug.wrappers.Response object with JSON data
    """
    # Prepare the data structure for the response, including count of items and the data itself
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}
    # Create a JSON response with the specified status code and content type
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data, default=default),  # Serialize data to JSON
    )


def invalid_response(typ, message=None, status=403):
    """
    Returns an invalid JSON response indicating an error.

    :param typ: Type of the error
    :param message: Error message (default: "wrong arguments (missing validation)")
    :param status: HTTP status code (default: 403)
    :return: werkzeug.wrappers.Response object with JSON error data
    """
    # Create a JSON response with the specified status code and error information
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(
            {"type": typ, "message": str(message) if str(message) else "wrong arguments (missing validation)"},
            default=datetime.datetime.isoformat  # Serialize datetime objects to ISO format
        ),
    )


def invalid_error(data, status=500):
    """
    Returns an error JSON response with a status code of 500 by default.

    :param data: Error data to be included in the response
    :param status: HTTP status code (default: 500)
    :return: werkzeug.wrappers.Response object with JSON error data
    """
    # Prepare the data structure for the response, including count of items and the data itself
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}
    # Create a JSON response with the specified status code and content type
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data, default=default),  # Serialize data to JSON
    )


def extract_arguments(limit="80", offset=0, order="id", domain="", fields=[]):
    """
    Extracts and parses additional data sent along with the request.

    :param limit: Limit of records to return (default: "80")
    :param offset: Offset for pagination (default: 0)
    :param order: Field by which to order the results (default: "id")
    :param domain: Filtering domain (default: "")
    :param fields: List of fields to include in the results (default: [])
    :return: List containing expressions, fields, offset, limit, and order
    """
    limit = int(limit)  # Convert limit parameter to integer
    expresions = []  # Initialize list to hold domain expressions
    if domain:
        # Convert domain expressions from a comma-separated string to a list of tuples
        expresions = [tuple(preg.replace(":", ",").split(",")) for preg in domain.split(",")]
        expresions = json.dumps(expresions)  # Serialize expressions to JSON string
        expresions = json.loads(expresions, parse_int=True)  # Deserialize JSON string back to list
    if fields:
        fields = fields.split(",")  # Split fields parameter by commas to get a list of fields

    if offset:
        offset = int(offset)  # Convert offset parameter to integer
    return [expresions, fields, offset, limit, order]  # Return the extracted arguments as a list
