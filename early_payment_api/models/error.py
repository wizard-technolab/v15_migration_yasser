import datetime  # Importing datetime to handle date and time objects
import json  # Importing json to handle JSON serialization
import logging  # Importing logging to log messages

import werkzeug.wrappers  # Importing Werkzeug wrappers for HTTPS responses

_logger = logging.getLogger(__name__)  # Setting up logging for this module


# Function to convert non-serializable objects to serializable format
def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):  # Check if the object is a date or datetime
        return o.isoformat()  # Convert to ISO format string
    if isinstance(o, bytes):  # Check if the object is bytes
        return str(o)  # Convert bytes to string


# Function to create a valid HTTPS response
def valid_response(data, status=200):
    """
    Valid Response
    This will be returned when the HTTP request was successfully processed.
    :param data: The data to be included in the response
    :param status: The HTTP status code (default is 200)
    :return: A Werkzeug response object with JSON data
    """
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}  # Wrap data with count
    return werkzeug.wrappers.Response(
        status=status,  # Set the HTTPS status code
        content_type="application/json; charset=utf-8",  # Set the content type to JSON with UTF-8 encoding
        response=json.dumps(data, default=default),  # Serialize the data to JSON using the default serializer
    )


# Function to create an invalid HTTPS response
def invalid_response(typ, message=None, status=403):
    """
    Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server.
    :param typ: The type of error
    :param message: The error message
    :param status: The HTTP status code (default is 403)
    :return: A Werkzeug response object with JSON error data
    """
    return werkzeug.wrappers.Response(
        status=status,  # Set the HTTP status code
        content_type="application/json; charset=utf-8",  # Set the content type to JSON with UTF-8 encoding
        response=json.dumps(
            {"type": typ, "message": str(message) if str(message) else "wrong arguments (missing validation)", },
            default=datetime.datetime.isoformat,  # Serialize the data to JSON using datetime's isoformat
        ),
    )


# Function to create an invalid error response
def invalid_error(data, status=500):
    """
    Invalid Error Response
    This will be the return value whenever the server runs into an error
    either from the client or the server.
    :param data: The error data to be included in the response
    :param status: The HTTP status code (default is 500)
    :return: A Werkzeug response object with JSON error data
    """
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}  # Wrap data with count
    return werkzeug.wrappers.Response(
        status=status,  # Set the HTTPS status code
        content_type="application/json; charset=utf-8",  # Set the content type to JSON with UTF-8 encoding
        response=json.dumps(data, default=default),  # Serialize the data to JSON using the default serializer
    )


# Function to extract and parse arguments from a request
def extract_arguments(limit="80", offset=0, order="id", domain="", fields=[]):
    """
    Parse additional data sent along request.
    :param limit: The maximum number of records to return (default is 80)
    :param offset: The number of records to skip (default is 0)
    :param order: The order in which to return records (default is 'id')
    :param domain: The domain filter to apply to the records
    :param fields: The fields to include in the response
    :return: A list containing expressions, fields, offset, limit, and order
    """
    limit = int(limit)  # Convert limit to integer
    expresions = []  # Initialize an empty list for domain expressions
    if domain:  # If a domain filter is provided
        expresions = [tuple(preg.replace(":", ",").split(",")) for preg in domain.split(",")]  # Parse the domain filter
        expresions = json.dumps(expresions)  # Serialize to JSON
        expresions = json.loads(expresions, parse_int=True)  # Deserialize back to Python objects
    if fields:  # If fields are provided
        fields = fields.split(",")  # Split the fields into a list

    if offset:  # If an offset is provided
        offset = int(offset)  # Convert offset to integer
    return [expresions, fields, offset, limit, order]  # Return the parsed arguments as a list
