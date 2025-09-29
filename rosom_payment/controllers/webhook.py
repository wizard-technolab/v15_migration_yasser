import logging  # Import the logging module for logging messages
from odoo import http  # Import http from Odoo for handling HTTP requests and routes
from odoo.api import SUPERUSER_ID  # Import SUPERUSER_ID for performing actions with superuser privileges
from odoo.http import request, JsonRequest  # Import request and JsonRequest for handling HTTP requests and JSON data
from odoo.addons.ff_api_common.controllers.api_helpers import \
    alternative_json_response  # Import custom JSON response helper

# Define the path for the webhook route
WEBHOOK_PATH = '/live'
# WEBHOOK_PATH = '/https://uat.fuelfinance.sa/Rosom/UpdateInvoice'
_logger = logging.getLogger(__name__)  # Create a logger object for this module


class RosomWebhook(http.Controller):
    @http.route(WEBHOOK_PATH,  type='json', auth='public', csrf=False)  # Define the route for the webhook with JSON request and no authentication
    def rosom_webhook(self, *args, **kwargs):
        """
        Handle incoming JSON requests for the webhook endpoint.

        :param args: Positional arguments from the request
        :param kwargs: Keyword arguments from the request
        :return: JSON response with status information
        """
        payload = request.jsonrequest  # Extract JSON data from the request
        env_obj = request.env['res.users'].with_user(
            SUPERUSER_ID)  # Get the environment object with superuser privileges

        # Call the handle_request method on 'rosom.api.mixin' with the payload and webhook path
        env_obj.env['rosom.api.mixin'].handle_request(payload, WEBHOOK_PATH)

        # Set the JSON response method for the request
        request._json_response = alternative_json_response.__get__(request, JsonRequest)

        # Return a JSON response indicating success
        return {
            "Status": {
                "Code": 0,  # Success code
                "Description": "Success",  # Success description
                "Severity": "Info"  # Severity level
            }
        }
