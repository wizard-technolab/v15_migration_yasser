import json  # Import JSON module for handling JSON data
import logging  # Import logging module for logging messages
import functools  # Import functools for higher-order functions
import werkzeug.wrappers  # Import werkzeug wrappers for HTTP responses
from odoo.tools import ustr  # Import ustr utility from Odoo tools
from odoo import http, _  # Import http module and translation function from Odoo
from odoo.exceptions import AccessDenied, AccessError  # Import exceptions for access errors
from odoo.http import request, Response, date_utils, JsonRequest  # Import HTTP request/response and utilities from Odoo
from odoo.addons.aml.models.error import valid_response, invalid_response, \
    invalid_error  # Import custom response functions

_logger = logging.getLogger(__name__)  # Initialize a logger for this module

DEFAULT_ERROR_RESPONSE = {  # Default response for internal server errors
    "status": "failed",
    "message": "Internal Server Error"
}


# Decorator to validate access token
def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")  # Get access token from request headers
        if not access_token:  # If access token is missing, return an invalid response
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
                                                                          order="id DESC", limit=1)

        if access_token_data.find_or_create_token(
                user_id=access_token_data.user_id.id) != access_token:  # Check if token is valid
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id  # Set user ID in session
        request.uid = access_token_data.user_id.id  # Set user ID in request
        return func(self, *args, **kwargs)  # Call the wrapped function

    return wrap  # Return the wrapped function


# Function to create an alternative JSON response
def alternative_json_response(self, result=None, error=None):
    if isinstance(result, werkzeug.wrappers.Response):  # If result is already a response, return it directly
        return result

    mime = 'application/json'  # Set MIME type to JSON
    if result is None:  # If result is None, use default error response
        result = DEFAULT_ERROR_RESPONSE
    body = json.dumps(result, default=date_utils.json_default, separators=(',', '"'))  # Serialize result to JSON

    return Response(  # Return an HTTP response with the JSON body
        body, status=error and error.pop('http_status', 400) or 200,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )


"""
    First request [Route / GET]
    - Login and create access token
    - If the login data is not correct, return error 403
    - If the login data is correct, return success and create the token (status 200)
"""


class QuotationAPI(http.Controller):  # Define a controller class for handling API requests
    @http.route('/aml/login', methods=["GET"], type="http", auth="none", csrf=False)
    def api_login(self, **post):
        request._json_response = alternative_json_response.__get__(request,
                                                                   JsonRequest)  # Set custom JSON response handler
        params = ['db', 'login', 'password']  # Define expected parameters
        params = {key: post.get(key) for key in params if post.get(key)}  # Extract parameters from POST data
        db, username, password = (
            params.get('db'),
            params.get('login'),
            params.get('password'),
        )
        _credentials_includes_in_body = all([db, username, password])  # Check if all credentials are provided
        if not _credentials_includes_in_body:  # If credentials are not in body, check headers
            headers = request.httprequest.headers
            db = headers.get('db')
            username = headers.get('username')
            password = headers.get('password')
            _credentials_includes_in_headers = all([db, username, password])  # Check if all credentials are in headers
            if not _credentials_includes_in_headers:  # If credentials are still missing, return an error
                return invalid_response('missing error',
                                        'either of the following are missing [db, username , password]', 403)
        try:
            request.session.authenticate(db, username, password)  # Authenticate the user
        except AccessError as aee:  # Handle access errors
            return invalid_response('Access error', 'Error: %s' % aee.name)
        except AccessDenied as ade:  # Handle access denied errors
            return invalid_response('Access Denied', 'Login, Password or db invalid')
        except Exception as e:  # Handle other exceptions
            info = 'The Database name is not valid {}'.format((e))
            error = 'invalid_database'
            _logger.error(info)
            return invalid_response('wrong database name', error, 403)

        uid = request.session.uid  # Get user ID from session
        if not uid:  # If user ID is not set, return an error
            info = 'authentication failed'
            error = 'authentication failed'
            _logger.error(info)
            return invalid_response(401, error, info)

        access_token = request.env['api.access_token'].find_or_create_token(user_id=uid,
                                                                            create=True)  # Create or find an access token

        return werkzeug.wrappers.Response(  # Return a response with the access token and user details
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
                    "access_token": access_token,
                    "company_name": request.env.user.company_name,
                    "country": request.env.user.country_id.name,
                    "contact_address": request.env.user.contact_address,
                }
            ),
        )

    # Route to list partners
    @http.route('/api/res_partner', type='http', auth='public', methods=['GET'], csrf=False)
    def list_partners(self, **kw):
        request._json_response = alternative_json_response.__get__(request,
                                                                   JsonRequest)  # Set custom JSON response handler

        user_id = request.uid  # Get user ID from request
        user_obj = request.env['res.users'].sudo().browse(user_id)  # Get user object
        customer = request.env['res.partner']  # Get partner model
        partners = customer.with_user(user_obj).sudo().search([])  # Search for partners
        partner_data = [{'customer_id': partner.identification_no,
                         'name': partner.name,
                         'EntityTypeID': partner.company_type,
                         'Nationality': partner.nationality,
                         'Phone': partner.phone,
                         'Mobile': partner.mobile,
                         'Birth Of Date': partner.birth_of_date,
                         } for partner in partners]  # Extract partner data into a list
        return request.make_response(ustr(partner_data))  # Return the partner data as a response
