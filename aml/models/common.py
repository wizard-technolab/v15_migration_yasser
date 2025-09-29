# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details.
import datetime  # Import the datetime module for working with date and time
import json  # Import the json module for parsing and generating JSON
import logging  # Import the logging module for logging messages

import werkzeug.wrappers  # Import werkzeug.wrappers for creating HTTP responses

# Configure the logger for this module
_logger = logging.getLogger(__name__)


def default(o):
    """
    JSON serialization helper function.

    Converts datetime and bytes objects to JSON serializable formats.

    :param o: The object to be serialized.
    :return: The serialized object as a string.
    """
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()  # Convert date and datetime objects to ISO 8601 string format
    if isinstance(o, bytes):
        return str(o)  # Convert bytes objects to string


def valid_response(data, status=200):
    """
    Create a valid HTTP response for successful requests.

    Wraps the data in a JSON response object with a specified HTTP status code.

    :param data: The data to include in the response. Can be a list, dictionary, or string.
    :param status: The HTTP status code for the response (default is 200 OK).
    :return: A werkzeug Response object with JSON-encoded data.
    """
    # If data is not a string, include a count of items; otherwise, set count to 1
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}
    # Create and return a werkzeug Response object with JSON-encoded data
    return werkzeug.wrappers.Response(
        status=status,  # HTTP status code
        content_type="application/json; charset=utf-8",  # Set content type to JSON
        response=json.dumps(data, default=default),  # Encode data to JSON, using `default` function for serialization
    )


def invalid_response(typ, message=None, status=401):
    """
    Create an HTTP response for invalid requests.

    Wraps error information in a JSON response object with a specified HTTP status code.

    :param typ: The type of error or issue encountered.
    :param message: A description of the error (optional).
    :param status: The HTTP status code for the response (default is 401 Unauthorized).
    :return: A werkzeug Response object with JSON-encoded error information.
    """
    # Create and return a werkzeug Response object with JSON-encoded error information
    return werkzeug.wrappers.Response(
        status=status,  # HTTP status code
        content_type="application/json; charset=utf-8",  # Set content type to JSON
        response=json.dumps(
            {
                "type": typ,  # Type of the error
                "message": str(message) if str(message) else "wrong arguments (missing validation)",
                # Error message or default text
            },
            default=datetime.datetime.isoformat,  # Use ISO format for date/time serialization
        ),
    )


def extract_arguments(limit="80", offset=0, order="id", domain="", fields=[]):
    """
    Parse and process additional query parameters sent with a request.

    Converts query parameters into a format suitable for querying and pagination.

    :param limit: The maximum number of records to return (default is 80).
    :param offset: The number of records to skip before starting to return results (default is 0).
    :param order: The field to sort results by (default is "id").
    :param domain: A string representing domain filter conditions.
    :param fields: A list of fields to include in the results.
    :return: A list containing processed domain expressions, fields, offset, limit, and order.
    """
    limit = int(limit)  # Convert limit to integer
    expresions = []  # Initialize expressions list for domain filters

    # Process domain filters if provided
    if domain:
        # Split domain string into tuples and parse them
        expresions = [tuple(preg.replace(":", ",").split(",")) for preg in domain.split(",")]
        expresions = json.dumps(expresions)  # Convert expressions to JSON string
        expresions = json.loads(expresions, parse_int=True)  # Parse JSON string back to list

    # Process fields if provided
    if fields:
        fields = fields.split(",")  # Convert fields string to list

    # Convert offset to integer if provided
    if offset:
        offset = int(offset)

    # Return a list of processed arguments
    return [expresions, fields, offset, limit, order]

