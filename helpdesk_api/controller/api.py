import json
import logging
import functools
import werkzeug.wrappers
from odoo import http, tools
from ..models.error import invalid_response, valid_response, invalid_error
from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import request, Response, date_utils, JsonRequest

DEFAULT_ERROR_RESPONSE = {
    "status": "failed",
    "message": "Internal Server Error"
}

_logger = logging.getLogger(__name__)

"""
    function for validate token **
        if the token not right it is mean unauthorized [401] **
             if the token right it is mean authorized and success [200] **
"""


def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
                                                                          order="id DESC", limit=1)

        if access_token_data.find_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap


def alternative_json_response(self, result=None, error=None):
    if isinstance(result, werkzeug.wrappers.Response):
        # this is what we expect in the helpdesk api
        return result

    mime = 'application/json'
    if result is None:
        result = DEFAULT_ERROR_RESPONSE
    body = json.dumps(result, default=date_utils.json_default, separators=(',', '"'))

    return Response(
        body, status=error and error.pop('http_status', 400) or 200,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )

"""
    first request [Route / GET]
         login and create access token **
             if the login data not right then wrong [403] **
                if the login data right then success and create the token [200] **
"""


class HelpDeskAPI(http.Controller):
    @http.route('/api/login', methods=["GET"], type="http", auth="none", csrf=False)
    def api_login(self, **post):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        params = ['db', 'login', 'password']
        params = {key: post.get(key) for key in params if post.get(key)}
        db, username, password = (
            params.get('db'),
            params.get('login'),
            params.get('password'),
        )
        _credentials_includes_in_body = all([db, username, password])
        if not _credentials_includes_in_body:
            headers = request.httprequest.headers
            db = headers.get('db')
            username = headers.get('username')
            password = headers.get('password')
            _credentials_includes_in_headers = all([db, username, password])
            if not _credentials_includes_in_headers:
                return invalid_response('missing error',
                                        'either of the following are missing [db, username , password]', 403, )
        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            return invalid_response('Access error', 'Error: %s' % aee.name)
        except AccessDenied as ade:
            return invalid_response('Access Denied', 'Login, Password or db invalid')
        except Exception as e:
            info = 'The Database name is not valid {}'.format((e))
            error = 'invalid_database'
            _logger.error(info)
            return invalid_response('wrong database name', error, 403)

        uid = request.session.uid
        if not uid:
            info = 'authentication failed'
            error = 'authentication failed'
            _logger.error(info)
            return invalid_response(401, error, info)

        access_token = request.env['api.access_token'].find_or_create_token(user_id=uid, create=True)

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
                    "access_token": access_token,
                    "company_name": request.env.user.company_name,
                    "country": request.env.user.country_id.name,
                    "contact_address": request.env.user.contact_address,
                }
            ),
        )

    def _validate_ticket(self, values):
        phone = values.get('partner_phone', '')
        email = values.get('partner_email', '')
        if len(phone) != 10:
            return False, invalid_response('validation', f'Phone number must be 10 digits', 400)
        if phone[0: 2] != '05':
            return False, invalid_response('validation', f'Phone number must start with "05"', 400)
        if not tools.single_email_re.match(email):
            return False, invalid_response('validation', f'Invalid email', 400)
        return True, None

    """
            second request [Route / POST]
                create the Ticket and lead in HelpDesk **
                     if the token or params not right then wrong [403] or internal server error [500] **
                        if the token and params right then success and create the customer date and lead [200] **
    """
    # @validate_token
    @http.route("/api/ticket/create", methods=["POST"], type="json", auth="public", csrf=False)
    def create_ticket(self, **post):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        user_id = request.uid
        user_obj = request.env['res.users'].browse(user_id)
        payload = request.jsonrequest
        required_keys = ['partner_email', 'partner_phone','sequence_num','team_id']
        allowed_keys = ['name', 'partner_name', 'description'] + required_keys
        values = dict()
        for key in required_keys:
            if key not in payload:
                return invalid_response('validation', f'Missing required key "{key}"', 400)
        for value in payload:
            if value in allowed_keys:
                values[value] = payload[value]
        ticket_valid, ticket_error_response = self._validate_ticket(values)
        if not ticket_valid:
            return ticket_error_response

        new_ticket_obj = request.env['helpdesk.ticket'].sudo().create(values)
        print(new_ticket_obj.id)
        if new_ticket_obj:
            result = {'message': 'success', 'status': True, 'record_id': new_ticket_obj.id}
            try:
                return valid_response(
                    [{'result': result, "message [200]": "Customer created successfully"}],
                    status=200)
            except Exception as e:
                info = "The field is not valid {}".format((e))
                error = "invalid_params"
                _logger.error(info)
                return invalid_response("wrong", error, 403)