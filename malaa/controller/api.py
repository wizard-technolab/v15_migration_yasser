import functools
from random import random

import werkzeug.wrappers
# from python import address
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
        body, status=error and error.pop('http_status', 400) or 200,
        # Set HTTP status code based on error or default to 200
        headers=[('Content-Type', mime), ('Content-Length', len(body))]  # Set headers for response
    )


"""
    first request [Route / GET]
         login and create access token ** 
             if the login data not right then wrong [403] ** 
                if the login data right then success and create the token [200] **
"""


class malaaAPI(http.Controller):
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


class FinancialEvaluationController(http.Controller):

    @http.route('/api/financial_evaluation', type='json', auth='public', methods=['POST'])
    def create_financial_evaluation(self, **kwargs):
        data = request.jsonrequest
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        payload = request.httprequest.data.decode()
        payload = json.loads(payload)

        loan_record = payload.get("loan_record")

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

        # Extracting data from payload
        kyc_data = payload.get('kyc', {})
        customer_info = kyc_data.get('customer_info', {})
        contact_info = customer_info.get('contact_info', {})
        address_data = kyc_data.get('address', {})
        initial_offer_data = payload.get('initial_offer', {})
        current_occupation = kyc_data.get('current_occupation', {})
        region = current_occupation.get('region') 
        financial_evaluation_data = kyc_data.get('financial_evaluation', {})

        # Create Financial Evaluation
        expense_breakdown = financial_evaluation_data.get('expense_breakdown', {})
        other_obligations = financial_evaluation_data.get('other_obligations', {})
        summary_data = financial_evaluation_data.get('summary', {})

        english_first_name = customer_info.get('english_first_name', '').strip()
        english_second_name = customer_info.get('english_second_name', '').strip()
        english_third_name = customer_info.get('english_third_name', '').strip()
        english_last_name = customer_info.get('english_last_name', '').strip()

        english_name_parts = [
            english_first_name,
            english_second_name,
            english_third_name,
            english_last_name
        ]
        english_name = ' '.join(filter(None, english_name_parts))

        first_name = customer_info.get('first_name', '').strip()
        father_name = customer_info.get('father_name', '').strip()
        grand_father_name = customer_info.get('grand_father_name', '').strip()
        family_name = customer_info.get('family_name', '').strip()

        arabic_name_parts = [
            first_name,
            father_name,
            grand_father_name,
            family_name
        ]
        arabic_name = ' '.join(filter(None, arabic_name_parts))

        # Create Address
        address_line = {
            'elm_city': address_data.get('city', ''),
            'city_l2': address_data.get('city_l2', ''),
            'city_id': address_data.get('city_id', ''),
            'elm_street_name': address_data.get('street', ''),
            'street_l2': address_data.get('street_l2', ''),
            'elm_district': address_data.get('district', ''),
            'district_l2': address_data.get('district_l2', ''),
            'elm_additional_number': address_data.get('additional_number', ''),
            'elm_building_number': address_data.get('building_number', ''),
            'region_id': address_data.get('region_id', ''),
            'region_name': address_data.get('region_name', ''),
            'region_name_l2': address_data.get('region_name_l2', ''),
            'elm_post_code': address_data.get('post_code', ''),
        }
        address = request.env['elm.yakeen.api'].sudo().create(address_line)
        obligations_data = []
        for obligation in other_obligations:
            obligations_data.append((0, 0, {
                'name': obligation.get('name'),
                'credit_amount': obligation.get('credit_amount', 0),
                'monthly_payment': obligation.get('monthly_payment', 0),
                'payment_frequency': obligation.get('payment_frequency', 0),
            }))
        # Create Customer (Partner)
        partner_vals = {
            'kyc_name': customer_info.get('first_name', '') + ' ' + customer_info.get('family_name', ''),
            'first_name': first_name,
            'family_name': family_name,
            'name': arabic_name,
            'english_name': english_name,
            'email': contact_info.get('email', ''),
            'phone': contact_info.get('phone_number', ''),
            'mobile': contact_info.get('phone_number', ''),
            'street': address_data.get('street', ''),
            'city': address_data.get('city', ''),
            'zip': address_data.get('post_code', ''),
            'identification_no': customer_info.get('national_id', ''),
            'birth_of_date_hijri': customer_info.get('date_of_birth_h', ''),
            'expiry_of_date_hijri': customer_info.get('id_expiry_date_h', ''),
            'gender_elm': customer_info.get('gender', ''),
            'nationalitycode': customer_info.get('nationality_code', ''),
            'customer_nationality': customer_info.get('nationality', ''),
            'release_of_date': customer_info.get('id_issue_date', ''),
            'expiry_of_date': customer_info.get('id_expiry_date', ''),
            'place': customer_info.get('id_issue_place', ''),
            'id_version_number': customer_info.get('id_version_number', ''),
            'legal_status': customer_info.get('legal_status', ''),
            'number_dependents': customer_info.get('total_number_of_current_dependents', ''),
            # 'name': payload.get('customer_name', ''),
            'nationality': 'saudi',
            'region': region,
            'industry': current_occupation.get('industry', ''),
            'date_of_joining': current_occupation.get('employment_start_date', ''),
            'elm_res_partner': address,
            'state': payload.get('state'),
            'loan_amount': initial_offer_data.get('amount'),
            'sectors': current_occupation.get('sector_type'),
            'employer': current_occupation.get('employer_name'),
            'food_exp': expense_breakdown.get('food_expenses', {}).get('amount', 0),
            'cost_home': expense_breakdown.get('housing_expenses', {}).get('amount', 0),
            'education_exp': expense_breakdown.get('education_expenses', {}).get('amount', 0),
            'basic_salary': financial_evaluation_data.get('net_monthly_income', 0),
            'tran_exp': expense_breakdown.get('transportation_expenses', {}).get('amount', 0),
            'cost_telecom': expense_breakdown.get('communication_expenses', {}).get('amount', 0),
            'cost_future': expense_breakdown.get('healthcare_expenses', {}).get('amount', 0),
            'personal_care_exp': expense_breakdown.get('domestic_labor_wages', {}).get('amount', 0),
            'salary_rate': float(financial_evaluation_data.get('net_monthly_income', 0.0)),


        }
        partner = request.env['res.partner'].sudo().create(partner_vals)

        # Create Loan Order
        mfs_account = request.env['account.analytic.account'].sudo().search([('name', '=', 'MFS')], limit=1)
        if not mfs_account:
            raise ValueError("The 'MFS' analytic account does not exist.")

        loan_vals = {
            'loan_amount': initial_offer_data.get('amount'),
            'rate_per_month': initial_offer_data.get('interest_rate'),
            'loan_term': initial_offer_data.get('duration'),
            'name': partner.id,
            'state': payload.get('state'),
            'loan_type': payload.get('loan_type'),
            'loan_record': loan_record,
            'obligation_id': payload.get('obligation_id'),
            'account_analytic': mfs_account.id,
        }
        loan_order = request.env['loan.order'].sudo().create(loan_vals)

        evaluation_vals = {
            'net_monthly_income': financial_evaluation_data.get('net_monthly_income', 0),
            'partner_id': partner.id,
            'food_expenses': expense_breakdown.get('food_expenses', {}).get('amount', 0),
            'housing_expenses': expense_breakdown.get('housing_expenses', {}).get('amount', 0),
            'housing_ownership_status': expense_breakdown.get('housing_expenses', {}).get('ownership_status', ''),
            'housing_utilities_included': expense_breakdown.get('housing_expenses', {}).get('utilities_included',
                                                                                            False),
            'domestic_labor_wages': expense_breakdown.get('domestic_labor_wages', {}).get('amount', 0),
            'has_domestic_labor': expense_breakdown.get('domestic_labor_wages', {}).get('has_domestic_labor', False),
            'education_expenses': expense_breakdown.get('education_expenses', {}).get('amount', 0),
            'dependents_count': expense_breakdown.get('education_expenses', {}).get('dependents_count', 0),
            'transportation_expenses': expense_breakdown.get('transportation_expenses', {}).get('amount', 0),
            'communication_expenses': expense_breakdown.get('communication_expenses', {}).get('amount', 0),
            'healthcare_expenses': expense_breakdown.get('healthcare_expenses', {}).get('amount', 0),
            'total_expenses': summary_data.get('total_expenses', 0),
            'net_available_income_after_obligations': summary_data.get('net_available_income_after_obligations', 0),
            'obligation_ids':obligations_data,
        }
        evaluation = request.env['financial.evaluation'].sudo().create(evaluation_vals)

        # Update Occupation History
        request.env['occupation.history'].sudo().create({
            'partner_id': partner.id,
            'occupation_code': current_occupation.get('occupation_code', ''),
            'position': current_occupation.get('position', ''),
            'occupation_region': current_occupation.get('region', ''),
            'employment_start_date': current_occupation.get('employment_start_date', ''),
            'sector_type': current_occupation.get('sector_type', ''),
            'industry': current_occupation.get('industry', ''),
            'employer_name': current_occupation.get('employer_name', ''),
        })

        return {
            "success": True,
            "evaluation_id": evaluation.id,
            "partner_id": partner.id,
            "loan_id": loan_order.id
        }

        # return loan_order_record

    @http.route('/api/final_offer', type='json', auth='public', methods=['PUT'])
    def update_final_offer(self, **kwargs):
        # Parse incoming data
        data = request.jsonrequest

        # Extract loan request details
        loan_record = data.get("loan_request_id", "")
        final_offer = data.get("final_offer", {})

        # Extract final offer details
        loan_amount = final_offer.get("amount", 0)
        rate_per_month = final_offer.get("interest_rate", 0)
        loan_term = final_offer.get("duration", 0)

        # Find the existing loan record
        existing_loan = request.env['loan.order'].sudo().search([
            ('loan_record', '=', loan_record)
        ], limit=1)

        if not existing_loan:
            # Return an error if the loan record doesn't exist
            return Response(json.dumps({
                'message': 'Loan request not found',
                'status': False
            }), content_type='application/json', status=404)

        try:
            # Update the existing loan record
            existing_loan.sudo().write({
                'loan_amount': loan_amount,
                'rate_per_month': rate_per_month,
                'loan_term': loan_term,
                'state': 'simah'
            })

            # Response on successful update
            return Response(json.dumps({
                'message': 'Loan request updated successfully',
                'status': True,
                'loan_request_id': existing_loan.loan_record
            }), content_type='application/json', status=200)

        except Exception as e:
            # Error handling
            return Response(json.dumps({
                'message': 'Error updating loan request',
                'status': False,
                'error': str(e)
            }), content_type='application/json', status=500)
