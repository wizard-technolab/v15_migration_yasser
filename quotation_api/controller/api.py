import base64
import json
import logging
import functools
from datetime import datetime
import werkzeug.wrappers
from odoo.exceptions import ValidationError, UserError
from odoo import http, tools
import random

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
    # sauce for this method: https://stackoverflow.com/a/71262562
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


class QuotationAPI(http.Controller):
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
                    # "crm_id": request.env.user.crm_id.id,
                    "access_token": access_token,
                    "company_name": request.env.user.company_name,
                    "country": request.env.user.country_id.name,
                    "contact_address": request.env.user.contact_address,
                }
            ),
        )

    def _validate_quotation(self, values):
        # Phone : mandatory ( 10 digits)
        # Email : mandatory ( email format)
        phone = values.get('phone', '')
        customer_phone = values.get('customer_phone', '')
        email = values.get('email', '')
        if len(phone) != 10:
            return False, invalid_response('validation', f'Phone number must be 10 digits', 400)
        if phone[0: 2] != '05':
            return False, invalid_response('validation', f'Phone number must start with "05"', 400)
        if len(customer_phone) != 10:
            return False, invalid_response('validation', f'Customer phone number must be 10 digits', 400)
        if customer_phone[0: 2] != '05':
            return False, invalid_response('validation', f'Customer phone number must start with "05"', 400)
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
    @http.route("/api/quotation/create", methods=["POST"], type="json", auth="public", csrf=False)
    def create_quotation(self, **post):
        # self.message_post(body=datetime.today(), subject='New Quotation From Vendor')
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        user_id = request.uid
        user_obj = request.env['res.users'].browse(user_id)
        payload = request.httprequest.data.decode()
        payload = json.loads(payload)
        payload = request.jsonrequest
        seq = payload.get("seq")
        clinic_name = payload.get("clinic_name")
        department_name = payload.get("department_name")
        phone = payload.get("phone")
        email = payload.get("email")
        doctor_name = payload.get("doctor_name")
        clinic_user_id = payload.get("clinic_user_id")
        customer_id = payload.get("customer_id")
        customer_name = payload.get("customer_name")
        customer_phone = payload.get("customer_phone")
        customer_amount = payload.get("customer_amount")
        attachment = payload.get("attachment_id")
        description = payload.get("description")

        product_id = payload.get("product_id")
        quantity = payload.get("quantity")
        price = payload.get("price")
        amount = payload.get("amount")

        # quotation_line = request.env['hospital.quotation.line'].sudo().create({
        #     'product_id': product_id,
        #     'quantity': quantity,
        #     'price': price,
        #     'amount': amount,
        # })
        new_quo_obj = request.env['hospital.quotation'].sudo().create({
            'seq': seq,
            'clinic_name': clinic_name,
            'department_name': department_name,
            'phone': phone,
            'email': email,
            'doctor_name': doctor_name,
            'clinic_user_id': clinic_user_id,
            'customer_id': customer_id,
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'customer_amount': customer_amount,
            # 'description': description,
            # 'product_ids': quotation_line,

        })
        attachment_obj = request.env['ir.attachment'].sudo().create({
            'name': 'attachment_name.pdf',
            'type': 'binary',
            'res_model': 'hospital.quotation',
            'res_id': new_quo_obj.id,
            'raw': base64.b64decode(attachment),
        })
        required_keys = ['email', 'phone','customer_phone']
        values = dict()
        for key in required_keys:
            if key not in payload:
                return invalid_response('validation', f'Missing required key "{key}"', 400)
        for value in payload:
            if value in new_quo_obj:
                values[value] = payload[value]
        ticket_valid, ticket_error_response = self._validate_quotation(values)
        if not ticket_valid:
            return ticket_error_response

        if new_quo_obj:
            result = {'message': 'success', 'status': True,
                      'record_id': new_quo_obj.id, 'attachment': attachment_obj}
            try:
                return valid_response(
                    [{'result': result, "message [200]": "Quotation created successfully"}],
                    status=200)
            except Exception as e:
                info = "The field is not valid {}".format((e))
                error = "invalid_params"
                _logger.error(info)
                return invalid_response("wrong", error, 403)

        for rec in self:
            users = self.env.ref('loan.group_loan_approval').users.ids
            user_id = self.env.user.id
            random_id = user_id
            while random_id == user_id:
                random_id = random.choice(users)
            activity_object = self.env['mail.activity']
            activity_values = self.activity_create_quotation(random_id, rec.id, 'hospital.quotation', 'website_portal_custom.hospital_quotation_form')
            activity_id = activity_object.create(activity_values)
            print(activity_id)

    def activity_create_quotation(self, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "The Quotation Created",
            'note': "The Quotation Created",
            'date_deadline': datetime.today(),
            'activity_type_id': self.env.ref('website_portal_custom.mail_activity_create_quotation').id,
        }


    # line_keys = ['product_id', 'quantity', 'price', 'amount']
    # allowed_keys = ['seq', 'clinic_name', 'department_name', 'doctor_name', 'clinic_user_id', 'customer_name',
    #                 'customer_id', 'description','product_ids'] + required_keys
    # line_values = dict()
    # for value in payload:
    #     if value in allowed_keys:
    #         values[value] = payload[value]
    # print(value)
    # for lvalue in payload:
    #     if lvalue in line_keys:
    #         line_values[lvalue] = payload[lvalue]
    # new_quotation_obj = request.env['hospital.quotation'].sudo().create(values)
    # quotation_line_obj = request.env['hospital.quotation.line'].sudo().create(line_values)
