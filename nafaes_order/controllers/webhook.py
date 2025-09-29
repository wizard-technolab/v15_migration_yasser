import os  # Import the OS module to access environment variables
import json  # Import JSON module for handling JSON data
import logging  # Import logging module for logging errors and information
from base64 import b64encode  # Import base64 encoding function
from odoo import http  # Import http module from Odoo
from odoo.http import request, Response, \
    JsonRequest  # Import request, Response, and JsonRequest from Odoo's http module
from odoo.tools import date_utils  # Import date_utils from Odoo tools
from ..models.api_mixin import WEBHOOK_PATH, NAFAES_TOKEN  # Import constants from api_mixin module

_logger = logging.getLogger(__name__)  # Initialize the logger


class NafaesWebhook(http.Controller):  # Define a new controller class

    def alternative_json_response(self, result=None, error=None):
        # Set the MIME type for the response to JSON
        mime = 'application/json'
        if result is None:
            # If no result is provided, set a default error response
            result = {
                "status": "error",
                "header": {
                    "errorCode": "1",
                    "errorMessages": ['Error'],
                }
            }
        # Convert the result to a JSON string
        body = json.dumps(result, default=date_utils.json_default)

        # Return a Response object with the JSON body and appropriate headers
        return Response(
            body, status=error and error.pop('http_status', 200) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )

    @http.route(WEBHOOK_PATH, type="json", auth="none")
    def nafaes_webhook(self, *args, **kwargs):
        payload = request.jsonrequest  # Get the JSON payload from the request
        env_obj = request.env['res.users'].sudo()  # Get the environment object for user model with sudo permissions
        param_obj = env_obj.env[
            'ir.config_parameter'].sudo()  # Get the environment object for configuration parameters with sudo permissions
        secretKey = request.httprequest.args.get('secretKey', '')  # Get the secret key from the request arguments
        log_id = False  # Initialize log_id to False
        headers = request.httprequest.headers  # Get the request headers
        error_messages = []  # Initialize an empty list for error messages
        note = ''  # Initialize an empty note string
        username = os.getenv('NAFAES_WEBHOOK_USERNAME', '')  # Get webhook username from environment variable
        password = os.getenv('NAFAES_WEBHOOK_PASSWORD', '')  # Get webhook password from environment variable
        token_should_be = b64encode(f"{username}:{password}".encode('utf-8')).decode(
            "ascii")  # Encode the username and password in base64
        if token_should_be not in headers.get('Authorization',
                                              ''):  # Check if the Authorization header contains the correct token
            error_messages.append('Wrong username or password')  # Add error message if token is incorrect
        if not (username and password):  # Check if both username and password are set
            note += 'Username and password for webhook authorization are not set\n'  # Add note if username or password is missing
        note = '\n'.join(error_messages)  # Join error messages into a single string
        res = False  # Initialize res to False
        headers_to_log = {
            'X-Real-Ip': headers.get('X-Real-Ip', ''),  # Log the X-Real-Ip header
        }
        log_values = {
            'note': note,  # Include note in log values
            'header': json.dumps(headers_to_log),  # Convert headers to JSON string
        }
        if not error_messages:  # If there are no error messages
            try:
                # Call handle_request method on nafaes.order.result model and pass the payload, webhook path, secret key, and log values
                res, log_id = env_obj.env['nafaes.order.result'].handle_request(payload, WEBHOOK_PATH, secretKey,
                                                                                log_values=log_values)
            except Exception:  # Catch any exception
                error_messages.append('Internal server error')  # Add internal server error message

        success_response = {  # Define a success response structure
            "status": "success",
            "header": {
                "uuid": payload.get('header', {}).get('uuid', ''),  # Get UUID from payload header
                "errorCode": "",
                "errorMessages": [],
            }
        }
        failure_response = {  # Define a failure response structure
            "status": "error",
            "header": {
                "uuid": payload.get('header', {}).get('uuid', ''),  # Get UUID from payload header
                "errorCode": "1",
                "errorMessages": error_messages,  # Include error messages
            }
        }
        if res and not error_messages:  # Determine response data based on the presence of errors
            response_data = success_response
        else:
            response_data = failure_response

        if log_id:  # If log_id is set
            log_id.update_log({  # Update log with the response data
                'response': json.dumps(response_data),
            })
        request._json_response = self.alternative_json_response.__get__(request,
                                                                        JsonRequest)  # Set custom JSON response method on the request object
        return response_data  # Return the response data
