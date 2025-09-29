import functools
import werkzeug.wrappers
from odoo import http, tools
from odoo.addons.fuel_api.models.error import invalid_response, valid_response, invalid_error
from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import request, Response, date_utils, JsonRequest
import json
import base64
import logging

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

    # return Response(
    #     body, status=error and error.pop('http_status', 400) or 200,
    #     headers=[('Content-Type', mime), ('Content-Length', len(body))]
    # )
    return Response(
        body, status=error and error.pop('http_status', 400) or 200,  # Set HTTP status code based on error or default to 200
        headers=[('Content-Type', mime), ('Content-Length', len(body))]  # Set headers for response
    )


"""
    first request [Route / GET]
         login and create access token ** 
             if the login data not right then wrong [403] ** 
                if the login data right then success and create the token [200] **
"""


class FuelAPI(http.Controller):
    @http.route('/api/login', methods=["GET"], type="http", auth="none", csrf=False)
    def api_login(self, **post):
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

    def _validate_request(self, values):
        # Phone : mandatory ( 10 digits)
        # Email : mandatory ( email format)
        # customer_id : mandatory ( 10 digits)
        phone = values.get('phone', '')
        email = values.get('email', '')
        if len(phone) != 10:
            return False, invalid_response('validation', f'Phone number must be 10 digits', 400)
        if phone[0: 2] != '05':
            return False, invalid_response('validation', f'Phone number must start with "05"', 400)
        if not tools.single_email_re.match(email):
            return False, invalid_response('validation', f'Invalid email', 400)
        if phone[0: 2] != '05':
            return False, invalid_response('validation', f'Phone number must start with "05"', 400)
        return True, None

    """
            second request [Route / POST]
                create the customer and lead in CRM ** 
                     if the token or params not right then wrong [403] or internal server error [500] ** 
                        if the token and params right then success and create the customer date and lead [200] **
    """

    # ++++++++++++++++++++++++++++++++++++++++++++   API params      ++++++++++++++++++++++++++++++++++++++++++++++#
    # @validate_token
    @http.route("/api/customer/create", methods=["POST"], type="json", auth="public", csrf=False)
    def create_customer(self, **post):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        payload = request.httprequest.data.decode()
        payload = json.loads(payload)
        customer_id = payload.get("customer_id")
        customer_name = payload.get("customer_name")
        first_name = payload.get("first_name")
        family_name = payload.get("family_name")
        english_name = payload.get("english_name")
        birth_date = payload.get("birth_date")
        email = payload.get("email")
        gender_elm = payload.get("gender_elm")
        occupationCode = payload.get("occupationCode")
        expiry_date = payload.get("expiry_date")
        phone = payload.get("phone")
        home_type = payload.get("home_type")
        certificate = payload.get("certificate")
        sectors = payload.get("sectors")
        employer = payload.get("employer")
        type_loan = payload.get("type_loan")
        loan_amount = payload.get("loan_amount")
        basic_salary = payload.get("basic_salary")
        service_provider = payload.get("service_provider")
        food_exp = payload.get("food_exp")
        cost_telecom = payload.get("cost_telecom")
        tran_exp = payload.get("tran_exp")
        cost_future = payload.get("cost_future")
        other_liability = payload.get("other_liability")
        attachment = payload.get("attachment_id")
        loan_purpose = payload.get("loan_purpose")
        duration_in_occupation = payload.get("duration_in_occupation")
        state = payload.get("state")
        rate_per_month = payload.get("rate")
        elm_city = payload.get("elm_city")
        elm_street_name = payload.get("elm_street_name")
        elm_district = payload.get("elm_district")
        elm_additional_number = payload.get("elm_additional_number")
        elm_building_number = payload.get("elm_building_number")
        elm_post_code = payload.get("elm_post_code")
        elm_location_coordinates = payload.get("elm_location_coordinates")
        loan_type = payload.get("loan_type")
        has_quotation = payload.get("has_quotation")
        nationality = payload.get("nationality")
        region = payload.get("region")
        industry = payload.get("industry")
        position = payload.get("position")
        loan_record = payload.get("loan_record")
        loan_term = payload.get("loan_term")
        request_type = payload.get("request_type")
        irr = payload.get("irr")
        yearly_irr = payload.get("yearly_irr")

        # Check if the loan order already exists
        existing_loan = request.env['loan.order'].sudo().search([
            ('loan_record', '=', loan_record)
        ])

        if existing_loan:
            _logger.info("Loan record already exists: %s", loan_record)
            return Response(json.dumps({
                'message': 'Loan record already exists',
                'status': False
            }), content_type='application/json', status=200)

        # ++++++++++++++++++++++++++++++++++++++++++++    Quotation Params        +++++++++++++++++++++++++++++++++++++#
        if request_type:
            if has_quotation:
                # partner_id = 14
                supplier_id = post.get("supplier_id")
                city = post.get("city")
                customer_name = post.get("customer_name")
                customer_id = post.get("customer_id")
                customer_phone = post.get("customer_phone")
                age = post.get("age")
                section_name = post.get("section_name")
                is_medical = post.get("is_medical")
                order_data = post.get("products")

                # supplier_id = payload.get("supplier_id")
                # supplier_name = payload.get("supplier_name")
                # city = payload.get("city")
                # customer_name = payload.get("customer_name")
                # customer_id = payload.get("customer_id")
                # customer_phone = payload.get("customer_phone")
                # is_medical = payload.get("is_medical")
                # order_data = payload.get("products")
                # partner_id_int = int(partner_id)
                # if partner_id:
                #     try:
                #         partner_id = int(partner_id)
                #     except ValueError:
                #         return {
                #             'status': 'error',
                #             'message': 'partner_id is not a valid integer'
                #         }, 400
                # else:
                #     return {
                #         'status': 'error',
                #         'message': 'partner_id is required but not provided'
                #     }, 400

                # order_id = request.env['purchase.order'].sudo().create({
                #     'partner_id': 14,
                #     'supplier_id': supplier_id,
                #     'supplier_name': supplier_name,
                #     'partner_ref': city,
                #     'customer_name': customer_name,
                #     'customer_phone': customer_phone,
                #     'customer_id': customer_id or None,
                #     'is_medical': is_medical,
                # })
                supplier_id_int = int(supplier_id)
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
                # if order_id:
                #     order_line_list = []
                #     for order_line in order_data:
                #         order_line_list.append((0, 0, {
                #             'product_id': 1,  # Assuming static product ID
                #             'name': order_line.get('name'),
                #             'product_qty': order_line.get('quantity'),
                #             'price_unit': order_line.get('price'),
                #             'price_subtotal': order_line.get('total')
                #         }))
                #     order_id.sudo().write({'order_line': order_line_list})

                # ++++++++++++++++++++++++++++++++++++++++++++    Yakeen API     ++++++++++++++++++++++++++++++++++++++++++++++#
                address_line = request.env['elm.yakeen.api'].sudo().create({
                    'elm_city': elm_city,
                    'elm_street_name': elm_street_name,
                    'elm_district': elm_district,
                    'elm_additional_number': elm_additional_number,
                    'elm_building_number': elm_building_number,
                    'elm_post_code': elm_post_code,
                    'elm_location_coordinates': elm_location_coordinates,
                })
                # ++++++++++++++++++++++++++++++++++++++++++++    Partner Params    ++++++++++++++++++++++++++++++++++++++++++#
                partner_obj = request.env['res.partner'].sudo().create({
                    'identification_no': customer_id,
                    'name': customer_name,
                    'first_name': first_name,
                    'family_name': family_name,
                    'english_name': english_name,
                    'birth_of_date': birth_date,
                    'email': email,
                    'expiry_of_date': expiry_date,
                    'phone': phone,
                    'gender_elm': gender_elm,
                    'occupationCode': occupationCode,
                    'certificate': certificate,
                    'home_type': home_type,
                    'sectors': sectors,
                    'employer': employer,
                    'type_loan': type_loan,
                    'loan_amount': loan_amount,
                    'basic_salary': basic_salary,
                    'service_provider': service_provider,
                    'food_exp': food_exp,
                    'cost_telecom': cost_telecom,
                    'tran_exp': tran_exp,
                    'cost_future': cost_future,
                    'other_liability': other_liability,
                    'loan_purpose': loan_purpose,
                    'duration_in_occupation': duration_in_occupation,
                    'state': state,
                    'elm_res_partner': address_line,
                    'nationality': nationality,
                    'region': region,
                    'industry': industry,
                    'position': position,
                })
                # ++++++++++++++++++++++++++++++++++++++++++++  Loan Data      ++++++++++++++++++++++++++++++++++++++++++++++#
                loan_obj = request.env['loan.order'].sudo().create({
                    'name': partner_obj.id,
                    'loan_type': loan_type,
                    'state': state,
                    'rate_per_month': rate_per_month,
                    'irr': irr,
                    'yearly_irr': yearly_irr,
                    'quotation_id': order_id.id,
                    'loan_record': loan_record,  # Ensure loan_record is set here
                })
                # ++++++++++++++++++++++++++++++++++++++++++++  Attachment    ++++++++++++++++++++++++++++++++++++++++++++++#
                request.env['ir.attachment'].sudo().create({
                    'name': 'attachment_name.pdf',
                    'type': 'binary',
                    'res_model': 'loan.order',
                    'res_id': loan_obj.id,
                    'raw': base64.b64decode(attachment),
                })

                request.env['ir.attachment'].sudo().create({
                    'name': 'attachment_name.pdf',
                    'type': 'binary',
                    'res_model': 'res.partner',
                    'res_id': partner_obj.id,
                    'raw': base64.b64decode(attachment),
                })
                # ++++++++++++++++++++++++++++++++++++++++++++   CRM Data      ++++++++++++++++++++++++++++++++++++++++++++++#
                request.env['crm.lead'].sudo().create({
                    'name': customer_name,
                    'partner_id': partner_obj.id,
                    'email_from': email,
                    'id_number': customer_id,
                    'phone': phone,
                    'type': 'opportunity',
                })
                try:
                    result = {'message': 'success', 'status': True, 'quotation_id': order_id.name}
                    return Response(json.dumps({
                        'result': result,
                        "message": "Loan Request and Quotation created successfully"
                    }), content_type='application/json', status=200)
                except Exception as e:
                    info = "The field is not valid {}".format((e))
                    error = "invalid_params"
                    _logger.error(info)
                    return Response(json.dumps({
                        'error': 'invalid_params',
                        'message': info
                    }), content_type='application/json', status=403)
            else:
                address_line = request.env['elm.yakeen.api'].sudo().create({
                    'elm_city': elm_city,
                    'elm_street_name': elm_street_name,
                    'elm_district': elm_district,
                    'elm_additional_number': elm_additional_number,
                    'elm_building_number': elm_building_number,
                    'elm_post_code': elm_post_code,
                    'elm_location_coordinates': elm_location_coordinates,
                })
                # ++++++++++++++++++++++++++++++++++++++++++++    Partner Params    ++++++++++++++++++++++++++++++++++++++++++#
                partner_obj = request.env['res.partner'].sudo().create({
                    'identification_no': customer_id,
                    'name': customer_name,
                    'first_name': first_name,
                    'family_name': family_name,
                    'english_name': english_name,
                    'birth_of_date': birth_date,
                    'email': email,
                    'expiry_of_date': expiry_date,
                    'phone': phone,
                    'gender_elm': gender_elm,
                    'occupationCode': occupationCode,
                    'certificate': certificate,
                    'home_type': home_type,
                    'sectors': sectors,
                    'employer': employer,
                    'type_loan': type_loan,
                    'loan_amount': loan_amount,
                    'basic_salary': basic_salary,
                    'service_provider': service_provider,
                    'food_exp': food_exp,
                    'cost_telecom': cost_telecom,
                    'tran_exp': tran_exp,
                    'cost_future': cost_future,
                    'other_liability': other_liability,
                    'loan_purpose': loan_purpose,
                    'duration_in_occupation': duration_in_occupation,
                    'state': state,
                    'elm_res_partner': address_line,
                    'nationality': nationality,
                    'region': region,
                    'industry': industry,
                    'position': position,
                })
                # ++++++++++++++++++++++++++++++++++++++++++++  Loan Data      ++++++++++++++++++++++++++++++++++++++++++++++#
                loan_obj = request.env['loan.order'].sudo().create({
                    'name': partner_obj.id,
                    'loan_type': loan_type,
                    'state': state,
                    'irr': irr,
                    'rate_per_month': rate_per_month,
                    'yearly_irr': yearly_irr,
                    'loan_term':loan_term,
                    'loan_record': loan_record,  # Ensure loan_record is set here
                })
                # ++++++++++++++++++++++++++++++++++++++++++++  Attachment    ++++++++++++++++++++++++++++++++++++++++++++++#
                request.env['ir.attachment'].sudo().create({
                    'name': 'attachment_name.pdf',
                    'type': 'binary',
                    'res_model': 'loan.order',
                    'res_id': loan_obj.id,
                    'raw': base64.b64decode(attachment),
                })

                request.env['ir.attachment'].sudo().create({
                    'name': 'attachment_name.pdf',
                    'type': 'binary',
                    'res_model': 'res.partner',
                    'res_id': partner_obj.id,
                    'raw': base64.b64decode(attachment),
                })

                # ++++++++++++++++++++++++++++++++++++++++++++   CRM Data      ++++++++++++++++++++++++++++++++++++++++++++++#
                request.env['crm.lead'].sudo().create({
                    'name': customer_name,
                    'partner_id': partner_obj.id,
                    'email_from': email,
                    'id_number': customer_id,
                    'phone': phone,
                    'type': 'opportunity',
                })
                try:
                    result = {'message': 'success', 'status': True}
                    return Response(json.dumps({
                        'result': result,
                        "message": "Loan Request created successfully"
                    }), content_type='application/json', status=200)
                except Exception as e:
                    info = "The field is not valid {}".format((e))
                    error = "invalid_params"
                    _logger.error(info)
                    return Response(json.dumps({
                        'error': 'invalid_params',
                        'message': info
                    }), content_type='application/json', status=403)
        else:
            address_line = request.env['elm.yakeen.api'].sudo().create({
                'elm_city': elm_city,
                'elm_street_name': elm_street_name,
                'elm_district': elm_district,
                'elm_additional_number': elm_additional_number,
                'elm_building_number': elm_building_number,
                'elm_post_code': elm_post_code,
                'elm_location_coordinates': elm_location_coordinates,
            })
            # ++++++++++++++++++++++++++++++++++++++++++++    Partner Params    ++++++++++++++++++++++++++++++++++++++++++#
            partner_obj = request.env['res.partner'].sudo().create({
                'identification_no': customer_id,
                'name': customer_name,
                'first_name': first_name,
                'family_name': family_name,
                'english_name': english_name,
                'birth_of_date': birth_date,
                'email': email,
                'expiry_of_date': expiry_date,
                'phone': phone,
                'gender_elm': gender_elm,
                'occupationCode': occupationCode,
                'certificate': certificate,
                'home_type': home_type,
                'sectors': sectors,
                'employer': employer,
                'type_loan': type_loan,
                'loan_amount': loan_amount,
                'basic_salary': basic_salary,
                'service_provider': service_provider,
                'food_exp': food_exp,
                'cost_telecom': cost_telecom,
                'tran_exp': tran_exp,
                'cost_future': cost_future,
                'other_liability': other_liability,
                'loan_purpose': loan_purpose,
                'duration_in_occupation': duration_in_occupation,
                'state': state,
                'elm_res_partner': address_line,
                'nationality': nationality,
                'region': region,
                'industry': industry,
                'position': position,
            })
            # ++++++++++++++++++++++++++++++++++++++++++++  Loan Data      ++++++++++++++++++++++++++++++++++++++++++++++#
            loan_obj = request.env['loan.order'].sudo().create({
                'name': partner_obj.id,
                'loan_type': loan_type,
                'loan_term': loan_term,
                'state': state,
                'irr': irr,
                'yearly_irr': yearly_irr,
                'rate_per_month': rate_per_month,
                'loan_record': loan_record,  # Ensure loan_record is set here
            })
            # ++++++++++++++++++++++++++++++++++++++++++++  Attachment    ++++++++++++++++++++++++++++++++++++++++++++++#
            request.env['ir.attachment'].sudo().create({
                'name': 'attachment_name.pdf',
                'type': 'binary',
                'res_model': 'loan.order',
                'res_id': loan_obj.id,
                'raw': base64.b64decode(attachment),
            })

            request.env['ir.attachment'].sudo().create({
                'name': 'attachment_name.pdf',
                'type': 'binary',
                'res_model': 'res.partner',
                'res_id': partner_obj.id,
                'raw': base64.b64decode(attachment),
            })

            # ++++++++++++++++++++++++++++++++++++++++++++   CRM Data      ++++++++++++++++++++++++++++++++++++++++++++++#
            request.env['crm.lead'].sudo().create({
                'name': customer_name,
                'partner_id': partner_obj.id,
                'email_from': email,
                'id_number': customer_id,
                'phone': phone,
                'type': 'opportunity',
            })
            try:
                result = {'message': 'success', 'status': True}
                return Response(json.dumps({
                    'result': result,
                    "message": "Fazaa Loan Request created successfully"
                }), content_type='application/json', status=200)
            except Exception as e:
                info = "The field is not valid {}".format((e))
                error = "invalid_params"
                _logger.error(info)
                return Response(json.dumps({
                    'error': 'invalid_params',
                    'message': info
                }), content_type='application/json', status=403)

            """
                    second request [Route / GET]
                        read the customer data from CRM ** 
                             if the token  not right then wrong [403] or internal server error [500] ** 
                                if the token right then success and create the customer date and lead [200] **
            """

    # @validate_token
    @http.route("/api/customer/data", methods=["POST"], type="http", auth="public", csrf=False)
    def get_customers(self, **post):
        user_id = request.uid
        user_obj = request.env['res.users'].sudo().browse(user_id)
        payload = request.httprequest.data.decode()
        payload = json.loads(payload)
        customer_id = payload.get("customer_id")

        loan_order = request.env['loan.order']
        read_customer = loan_order.with_user(user_obj).sudo().search([('identification_id', 'in', [customer_id])])
        if read_customer:
            status = 200
            customers_list = []
            for partner in read_customer:
                for f in partner._fields:
                    value_dict = {
                        'seq_num': partner.seq_num,
                        'state': partner.state,
                        'loan_amount': partner.loan_amount,
                        'interest_amount': partner.interest_amount,
                        'loan_sum': partner.loan_sum,
                        'loan_term': partner.loan_term,
                        'late_amount': partner.late_amount,
                        'remaining_amount': partner.remaining_amount,
                        'early_amount': partner.early_amount
                    }
                    try:
                        value_dict[f] = str(getattr(partner, f))
                    except AccessError as aee:
                        print(aee)
                customers_list.append(value_dict)
        else:
            customers_list = []
            status = 204
            value_dict = {
                "message": "ID not found or wrong"
            }
            customers_list.append(value_dict)

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                customers_list
            ),
        )

    # has_quotation
