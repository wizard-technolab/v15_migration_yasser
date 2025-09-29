import json  # Importing JSON module to handle JSON data
import logging  # Importing logging module to log messages
import functools  # Importing functools module to use function decorators
import werkzeug.wrappers  # Importing werkzeug.wrappers to work with HTTP responses
from odoo import http, tools  # Importing Odoo HTTP and tools modules
from ..models.error import invalid_response, valid_response, invalid_error  # Importing custom error handling functions
from odoo.http import request, Response, date_utils, JsonRequest  # Importing Odoo HTTP request and response handling modules

DEFAULT_ERROR_RESPONSE = {
    "status": "failed",
    "message": "Internal Server Error"
}  # Default response for internal server errors

_logger = logging.getLogger(__name__)  # Setting up logging for this module

"""
    Function for validating token **
        If the token is not correct, it means unauthorized [401] **
        If the token is correct, it means authorized and success [200] **
"""

def validate_token(func):
    @functools.wraps(func)  # Ensuring the wrapped function retains its name and docstring
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")  # Retrieving the access token from the request header
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)  # Responding with an error if token is missing
        access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
                                                                          order="id DESC", limit=1)  # Searching for the token in the database

        if access_token_data.find_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)  # Responding with an error if token is invalid

        request.session.uid = access_token_data.user_id.id  # Setting the session user ID
        request.uid = access_token_data.user_id.id  # Setting the request user ID
        return func(self, *args, **kwargs)  # Proceeding with the original function

    return wrap  # Returning the wrapped function

def alternative_json_response(self, result=None, error=None):
    # Source for this method: https://stackoverflow.com/a/71262562
    if isinstance(result, werkzeug.wrappers.Response):
        # This is what we expect in the helpdesk API
        return result

    mime = 'application/json'  # Setting the MIME type for the response
    if result is None:
        result = DEFAULT_ERROR_RESPONSE  # Using the default error response if result is None
    body = json.dumps(result, default=date_utils.json_default, separators=(',', '"'))  # Serializing the result to JSON

    return Response(
        body, status=error and error.pop('http_status', 400) or 200,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )  # Creating and returning a JSON response

"""
    First request [Route / GET]
        Login and create access token **
            If the login data is not correct, respond with an error [403] **
            If the login data is correct, respond with success and create the token [200] **
"""

class EarlyPayment(http.Controller):
    def _validate_ticket(self, values):
        phone = values.get('partner_phone', '')  # Retrieving the partner phone from the values
        request_date = values.get('request_date', '')  # Retrieving the request date from the values
        return True, None  # Returning True and None as placeholders

    """
        Second request [Route / POST]
            Create the Early Payment Request **
                If the token or params are not correct, respond with an error [403] or internal server error [500] **
                If the token and params are correct, respond with success and create the customer data and request [200] **
    """

    # @validate_token
    @http.route("/api/payment/create", methods=["POST"], type="json", auth="public", csrf=False)
    def create_payment(self, **post):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)  # Setting custom JSON response method
        user_id = request.uid  # Retrieving the user ID from the request
        user_obj = request.env['res.users'].browse(user_id)  # Fetching the user object
        payload = request.jsonrequest  # Getting the JSON payload from the request
        allowed_keys = ['name', 'contract_no', 'request_date', 'payment_method', 'payment_type', 'payment_amount',
                        'source_money', 'customer_relation', 'payer_name', 'payer_id']  # Defining allowed keys for the payload
        values = dict()  # Initializing an empty dictionary for values
        for key in allowed_keys:
            if key not in payload:
                return invalid_response('validation', f'Missing required key "{key}"', 400)  # Returning an error if a required key is missing
        for value in payload:
            if value in allowed_keys:
                values[value] = payload[value]  # Adding allowed values to the dictionary
        ticket_valid, ticket_error_response = self._validate_ticket(values)  # Validating the ticket
        if not ticket_valid:
            return ticket_error_response  # Returning an error response if the ticket is not valid

        new_object_obj = request.env['early.payment'].sudo().create(values)  # Creating a new early payment object
        if new_object_obj:
            result = {'message': 'success', 'status': True, 'record_id': new_object_obj.id}  # Preparing the success result
            try:
                return valid_response(
                    [{'result': result, "message [200]": "Customer created successfully"}],
                    status=200)  # Returning a success response
            except Exception as e:
                info = "The field is not valid {}".format((e))  # Preparing an error message for invalid fields
                error = "invalid_params"  # Setting the error type
                _logger.error(info)  # Logging the error
                return invalid_response("wrong", error, 403)  # Returning an error response
