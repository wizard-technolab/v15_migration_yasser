# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details.

import json  # Import json for handling JSON data
import logging  # Import logging for logging messages
import functools  # Import functools for function decorators
import werkzeug.wrappers  # Import werkzeug for HTTP response wrappers
from odoo import http, tools  # Import Odoo components for HTTP controllers and tools
from odoo.http import request, Response, date_utils, JsonRequest  # Import Odoo HTTP request and response components
from ..models.error import invalid_response, valid_response, invalid_error  # Import custom error response functions
from odoo.exceptions import (  # Import Odoo exceptions for handling errors
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)

DEFAULT_ERROR_RESPONSE = {  # Default response for errors
    "status": "failed",
    "message": "Internal Server Error"
}

_logger = logging.getLogger(__name__)  # Create a logger for this module

"""
    Function for validating token
        If the token is not correct, it means unauthorized [401]
        If the token is correct, it means authorized and success [200]
"""


def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")  # Get access token from request headers
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)

        # Search for the access token in the database
        access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
                                                                          order="id DESC", limit=1)

        # Check if the token is valid
        if access_token_data.find_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id  # Set user ID in the session
        request.uid = access_token_data.user_id.id  # Set user ID in the request
        return func(self, *args, **kwargs)  # Call the original function

    return wrap


def alternative_json_response(self, result=None, error=None):
    """Return a JSON response with specified result or error."""
    if isinstance(result, werkzeug.wrappers.Response):
        # If result is already a response, return it directly
        return result

    mime = 'application/json'  # Set MIME type for JSON
    if result is None:
        result = DEFAULT_ERROR_RESPONSE  # Use default error response if no result provided
    body = json.dumps(result, default=date_utils.json_default, separators=(',', '"'))  # Convert result to JSON

    return Response(
        body, status=error and error.pop('http_status', 400) or 200,
        # Set HTTP status code based on error or default to 200
        headers=[('Content-Type', mime), ('Content-Length', len(body))]  # Set headers for response
    )


"""
    First request [Route / GET]
        Login and create access token
            If login data is incorrect, return error [403]
            If login data is correct, create and return the token [200]
"""


class APIQuotation(http.Controller):
    @http.route('/api/login', methods=["GET"], type="http", auth="none", csrf=False)
    def api_login(self, **post):
        request._json_response = alternative_json_response.__get__(request,
                                                                   JsonRequest)  # Bind alternative_json_response to request

        params = ['db', 'login', 'password']
        params = {key: post.get(key) for key in params if post.get(key)}  # Extract parameters from POST data
        db, username, password = (
            params.get('db'),
            params.get('login'),
            params.get('password'),
        )
        _credentials_includes_in_body = all([db, username, password])  # Check if credentials are provided in the body
        if not _credentials_includes_in_body:
            headers = request.httprequest.headers
            db = headers.get('db')
            username = headers.get('username')
            password = headers.get('password')
            _credentials_includes_in_headers = all(
                [db, username, password])  # Check if credentials are provided in headers
            if not _credentials_includes_in_headers:
                return invalid_response('missing error',
                                        'either of the following are missing [db, username, password]', 403)

        try:
            request.session.authenticate(db, username, password)  # Authenticate the user
        except AccessError as aee:
            return invalid_response('Access error', 'Error: %s' % aee.name)  # Handle AccessError
        except AccessDenied as ade:
            return invalid_response('Access Denied', 'Login, Password or db invalid')  # Handle AccessDenied
        except Exception as e:
            info = 'The Database name is not valid {}'.format((e))
            error = 'invalid_database'
            _logger.error(info)
            return invalid_response('wrong database name', error, 403)  # Handle other exceptions

        uid = request.session.uid
        if not uid:
            info = 'authentication failed'
            error = 'authentication failed'
            _logger.error(info)
            return invalid_response(401, error, info)  # Handle authentication failure

        access_token = request.env['api.access_token'].find_or_create_token(user_id=uid,
                                                                            create=True)  # Create or find access token

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "uid": uid,
                    "user_context": request.session.get_context() if uid else {},
                    "company_id": request.env.user.company_id.id if uid else None,
                    "company_ids": request.env.user.company_ids.ids if uid else None,
                    "partner_id": request.env.user.partner_id.id,
                    # "crm_id": request.env.user.crm_id.id,
                    "access_token": access_token,
                    "company_name": request.env.user.company_name,
                    "country": request.env.user.country_id.name,
                    "contact_address": request.env.user.contact_address,
                }
            ),
        )

    def _validate_quotation(self, values):
        """Validate the quotation data."""
        # Phone: mandatory (10 digits)
        customer_phone = values.get('customer_phone', '')
        customer_id = values.get('customer_id', '')
        # email = values.get('email', '')
        if len(customer_phone) != 10:
            return False, invalid_response('validation', f'Customer phone number must be 10 digits', 400)
        if customer_phone[0: 2] != '05':
            return False, invalid_response('validation', f'Customer phone number must start with "05"', 400)
        if len(customer_id) != 10:
            return False, invalid_response('validation', f'Customer ID number must be 10 digits', 400)
        return True, None

    """
        Second request [Route / POST]
            Create the Ticket and lead in HelpDesk
                If the token or params are not correct, return error [403] or internal server error [500]
                If the token and params are correct, create the customer data and lead [200]
    """

    @http.route("/api/create/quotation", methods=["POST"], type="json", auth="public", csrf=False)
    def create_quotation(self, **post):
        """Create a quotation and associated order."""
        try:
            payload = request.jsonrequest  # Get JSON request payload

            # Extract data from payload
            supplier_id = post.get("supplier_id")
            city = post.get("city")
            customer_name = post.get("customer_name")
            customer_id = post.get("customer_id")
            customer_phone = post.get("customer_phone")
            age = post.get("age")
            section_name = post.get("section_name")
            is_medical = post.get("is_medical")
            order_data = post.get("products")

            supplier_id_int = int(supplier_id)  # Convert supplier_id to integer
            # Create a purchase order
            order_id = request.env['purchase.order'].sudo().create({
                'partner_id': supplier_id_int,
                'partner_ref': city,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'customer_id': customer_id,
                'is_medical': is_medical,
                'age': age,
                'section_name': section_name
            })

            if order_id:
                order_line_list = []
                for order_line in order_data:
                    order_line_list.append((0, 0, {
                        'product_id': 1,  # Assuming static product ID
                        'name': order_line.get('name'),
                        'product_qty': order_line.get('quantity'),
                        'price_unit': order_line.get('price'),
                        'price_subtotal': order_line.get('total')
                    }))
                # Update the order with line items
                order_id.sudo().write({'order_line': order_line_list})
                result = {'message': 'success', 'status': True, 'record_id': order_id.id}
                try:
                    return valid_response(
                        [{'result': result, "message [200]": "Quotation created successfully"}],
                        status=200)
                except Exception as e:
                    info = "The field is not valid {}".format((e))
                    error = "invalid_params"
                    _logger.error(info)
                    return invalid_response("wrong", error, 403)
        except Exception as e:
            _logger.error(f"Error occurred: {e}")
            return invalid_response("error", "An error occurred while processing the request", 500)
