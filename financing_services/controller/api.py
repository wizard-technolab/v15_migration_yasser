# from asyncio import exceptions
# import zeep
from odoo.exceptions import ValidationError, UserError
from telnetlib import STATUS
import time
from datetime import datetime, timedelta
import json
import random
from odoo import http
from odoo.http import request
import requests
# from zeep import Client as ZeepClient, Client
from zeep.transports import Transport
# from suds.client import Client
import base64
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class FinancingAPI(http.Controller):

    @http.route('/api/form1',
                type='http', auth='public', website=True, csrf=False, methods=['PUT'])
    def form1_page(self, **kw):
        print("\n\n\n::: DATA FORM 1 :::")
        print(kw)
        ExpressionObject = request.env['expression.of.desire']
        values = self.prepare_expression_of_desire_data(**kw)
        record = ExpressionObject.sudo().create(values)
        if record.id:
            result = {'message': '', 'status': True, 'record_id': record.id}
        else:
            result = {'message': 'Faild', 'status': False}
        return json.dumps(result)

    @http.route('/api/form2', type='http', auth='public', website=True, csrf=False, methods=['PUT'])
    def form2_page(self, **kw):
        print("::: DATA FORM 2 :::")
        print(kw)
        CrmLeadObject = request.env['crm.lead']
        PartnerObject = request.env['res.partner']
        data = self.prepare_partner_data(**kw)
        try:
            partner_id = PartnerObject.sudo().create(data['partner'])
            # id_number = PartnerObject.sudo().create(data['partner'])
            # if kw.get('have_guarantor') == 'on':
            #     if 'name' in data['guarantor'] and data['guarantor']['name'] and len(data['guarantor']['name']) != 0:
            #         guarantor_id = PartnerObject.sudo().create(data['guarantor'])
            #         partner_id.guarantor_id = guarantor_id.id
            crm_id = CrmLeadObject.sudo().create({
                'name': '',
                'partner_id': partner_id.id,
                # 'id_number': id_number.id,
                'user_id': request.env.user.id,
            })
        except (ValidationError, ValueError, UserError) as e:
            result = {'message': str(e), 'status': False, }
            return json.dumps(result)
        for k in data['attachments']:
            Attachments = request.env['ir.attachment']
        name = data['attachments'][k].filename
        file = data['attachments'][k]
        attachment = file.read()
        attachment_id = Attachments.sudo().create({
            'name': name,
            'res_name': name,
            'type': 'binary',
            'res_model': 'crm.lead',
            'res_id': crm_id.id,
            'datas': base64.b64encode(attachment),
        })
        partner_attachment_id = Attachments.sudo().create({
            'name': name,
            'res_name': name,
            'type': 'binary',
            'res_model': 'res.partner',
            'res_id': partner_id.id,
            'datas': base64.b64encode(attachment),
        })

        if partner_id.id:
            result = {'message': 'success', 'status': True, 'record_id': partner_id.id}
            users = request.env.ref('loan.group_res_partner_sales').sudo().users.ids
            index = random.randrange(len(users))
            random_id = users[index]
            activity_object = request.env['mail.activity']
            activity_values = self.create_activity(random_id, partner_id.id, 'crm.lead', 'crm.model_crm_lead')
            activity_id = activity_object.sudo().create(activity_values)
            print('activity_id', activity_id)
        else:
            result = {'message': '', 'status': False}

        return json.dumps(result)

    def create_activity(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': request.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "New Request Loan",
            'note': "New Request Loan",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': request.env.ref('mail.mail_activity_data_todo').id,
        }

    @http.route('/api/form3', type='http', auth='public', website=True, csrf=False, methods=['PUT'])
    def form3_page(self, **kw):
        print("::: DATA FORM 3 :::")
        print(kw)
        HealthDeclaration = request.env['health.declaration']
        values = self.prepare_health_declaration(**kw)
        record = HealthDeclaration.sudo().create(values)
        if record.id:
            result = {'message': '', 'status': True, 'record_id': record.id}
        else:
            result = {'message': 'failed', 'status': False}
        return json.dumps(result)

    @http.route('/api/form4', type='http', auth='public', website=True, csrf=False, methods=['PUT'])
    def form4_page(self, **kw):
        """
            create hospital quotation
        """
        print("::: DATA FORM 4 :::")
        print(kw)
        # kw['seq'] = ''
        HospitalDeclaration = request.env['hospital.quotation']
        data = self.prepare_quotation_data(**kw)
        record = HospitalDeclaration.sudo().create(data)
        users = request.env.ref('loan.group_purchase_confirm').sudo().users.ids
        random_id = random.choice(users)
        index = random.randrange(len(users))
        random_id = users[index]
        activity_object = request.env['mail.activity']
        activity_values = record.create_activity(random_id, record.id, 'hospital.quotation',
                                                 'website_portal_custom.model_hospital_quotation')
        record.sudo().write({'activity_user_id': random_id})
        activity_id = activity_object.sudo().create(activity_values)
        if record.id:
            result = {'message': '', 'status': True, 'record_id': record.id}
        else:
            result = {'message': 'failed', 'status': False}
        return json.dumps(result)

    def prepare_quotation_data(self, **kw):
        """
            return a dic {} of data to create one record of hospital quotation
        """
        products = []
        data = {}
        for key in kw:
            if 'product_id_' in key:
                line_id = kw[key]
                index = 'product_amount_' + str(line_id)
                line_amount = kw[index]
                price_index = 'product_price_' + str(line_id)
                quantity_index = 'product_quantity_' + str(line_id)
                line_price = kw[price_index]
                line_quantity = kw[quantity_index]
                print("id: ", line_id, "amount: ", line_amount, "price: ", line_price, "quantity: ", line_quantity,
                      "\n\n\n")
                products.append((0, 0, {
                    'product_id': line_id,
                    'amount': line_amount,
                    'price': line_price,
                    'quantity': line_quantity,
                }))
            elif 'product_amount_' in key:
                pass
            elif 'product_price_' in key:
                pass
            elif 'product_quantity_' in key:
                pass
            else:
                data[key] = kw[key]
        data['product_ids'] = products
        return data

    def prepare_expression_of_desire_data(self, **kw):
        """
            prepare the date of expression of desire
        """
        return {
            'name': kw.get('name'),
            # 'id_number': kw.get('id_number'),
            'phone_number': kw.get('mobile_number'),
            'loan_type': kw.get('finaning_type'),
            'service_provider': kw.get('service_provider'),
            'service_amount': kw.get('service_amount'),
            'actual_beneficiary': kw.get('beneficiary'),
        }

    def prepare_health_declaration(self, **kw):
        """

        """
        return {
            'name': kw.get('full_name'),
            'birth_date': kw.get('birth_date'),
            'place_of_birth': kw.get('birth_place'),
            'address': kw.get('address'),
            'loan_amount': kw.get('loan_amount'),
            'loan_period': kw.get('loan_period'),
            'phone': kw.get('phone'),
            'weight': kw.get('weight'),
            'Height': kw.get('height'),
            'martial_status': kw.get('martial_status'),
            'work_nature': kw.get('work_nuture'),
            'unable_to_work_now_flag': kw.get('q1-check') == 'True' or False,
            'unable_to_work_now_text': kw.get('q1-deatils'),
            'unable_to_work_thirty_days_flag': kw.get('q2-check') == 'True' or False,
            'unable_to_work_thirty_days_text': kw.get('q2-deatils'),
            'suffered_accident_serious_damage_flag': kw.get('q3-check') == 'True' or False,
            'suffered_accident_serious_damage_text': kw.get('q3-deatils'),
            'disability_total_or_partial_flag': kw.get('q4-check') == 'True' or False,
            'disability_total_or_partial_text': kw.get('q4-deatils'),
            'treatment_fourteen_days_past_two_years_flag': kw.get('q5-check') == 'True' or False,
            'treatment_fourteen_days_past_two_years_text': kw.get('q5-deatils'),
            'heart_failure_flag': kw.get('b-q1-check') == 'True' or False,
            'diabetes_seven_kinds_flag': kw.get('b-q2-check') == 'True' or False,
            'cancer_flag': kw.get('b-q3-check') == 'True' or False,
            'hepatitis_flag': kw.get('b-q4-check') == 'True' or False,
            'reheumatic_fever_umatoid_arthrits_flag': kw.get('b-q5-check') == 'True' or False,
            'chronic_diseases_flag': kw.get('b-q6-check') == 'True' or False,
            'high_cholestrerol_flag': kw.get('b-q7-check') == 'True' or False,
            'athma_bronchitis_flag': kw.get('b-q8-check') == 'True' or False,
            'difficult_digestion_colon_flag': kw.get('b-q9-check') == 'True' or False,
            'thyroid_anemia_flag': kw.get('b-q10-check') == 'True' or False,
            'long_medical_condition_flag': kw.get('b-q11-check') == 'True' or False,
            'hiv_aids_flag': kw.get('b-q12-check') == 'True' or False,
            'psychiatric_illness_flag': kw.get('b-q13-check') == 'True' or False,
        }

    def prepare_partner_data(self, **kw):
        """
            prepare the data
        """
        name = kw.get('ar_first_name').strip() + ' ' + kw.get('ar_second_name').strip() + ' ' + kw.get(
            'ar_last_name').strip() + ' ' + kw.get('ar_family_name').strip()
        # en_name = kw.get('en_first_name').strip() + ' ' + kw.get('en_second_name').strip() + ' ' + kw.get('en_last_name').strip() + ' ' + kw.get('en_family_name').strip()
        partner = {
            # 'ar_first_name': kw.get('ar_first_name'),
            # 'ar_second_name': kw.get('ar_second_name'),
            # 'ar_last_name': kw.get('ar_last_name'),
            # 'ar_family_name': kw.get('ar_family_name'),
            # 'en_first_name': kw.get('en_first_name'),
            # 'en_second_name': kw.get('en_second_name'),
            # 'en_last_name': kw.get('en_last_name'),
            # 'en_family_name': kw.get('en_family_name'),
            'name': name,
            'gender': kw.get('gender'),
            # 'age': kw.get('age'),
            'identification_no': kw.get('id_iqama'),
            'phone_outside': kw.get('otp'),
            'place': kw.get('id_issue_place'),
            'release_of_date': kw.get('id_issue_date') if kw.get('id_issue_date') != '' else False,
            'birth_of_date': kw.get('birth_date') if kw.get('birth_date') != '' else False,
            'hijri_birth_date_day': kw.get('h_birth_date_day') if kw.get('h_birth_date_day') != '' else False,
            'hijri_birth_date_month': kw.get('h_birth_date_month'),
            'hijri_birth_date_year': kw.get('h_birth_date_year') if kw.get('h_birth_date_year') != '' else False,
            'expiry_of_date': kw.get('expiry_date') if kw.get('expiry_date') != '' else False,
            'nationality': kw.get('nationality'),
            'phone': kw.get('residence_phone'),
            'mobile': kw.get('mobile_phone'),
            # 'phone_outside': kw.get('internationl_mobile_phone'),
            'email': kw.get('email'),
            'certificate': kw.get('education_level'),
            'marital_status': kw.get('martial_status'),
            'number_dependents': kw.get('dependant_numbers'),
            'communicat_name': kw.get('friend_name'),
            'communicat_type': kw.get('friend_relation'),
            'communicat_phone': kw.get('friend_phone'),
            'relative_name': kw.get('relative_name'),
            'relative_type': kw.get('relative_relation'),
            'relative_phone': kw.get('relative_phone'),
            # 'have_relation': kw.get('have_relation'),
            'disclosure': kw.get('have_relation'),
            # 'member_name': kw.get('member_name'),
            'relation_name': kw.get('member_name'),
            # 'member_relation': kw.get('member_relation'),
            'relation_relative': kw.get('member_relation'),
            'city': kw.get('city'),
            'street2': kw.get('district'),
            'street': kw.get('street'),
            'unit_number': kw.get('unit_no'),
            'additional_code': kw.get('additional_no'),
            'zip': kw.get('postal_code'),
            # 'wasel': kw.get('wasel'),
            'home_type': kw.get('residencial_status'),
            'annual_rent': kw.get('annual_rent'),
            'service': kw.get('have_medical'),
            'service_type': kw.get('auth_provider'),
            # 'home_allowance': kw.get('residential_exp'),
            'cost_home': kw.get('residential_exp'),
            'clinic_name': kw.get('clinic_name'),
            'loan_amount': kw.get('medicial_fin_amount'),
            'period_loan': kw.get('fin_period'),
            # 'other_fin_period': kw.get('other_fin_period'),
            'about_us': kw.get('know_us'),
            # 'hostpital_know_us': kw.get('hostpital_know_us'),
            'offer_num': kw.get('quotation_number'),
            'sectors': kw.get('job_type'),
            'employer': kw.get('employer_name'),
            'type_loan': kw.get('job_title'),
            'years_work': kw.get('join_date') if kw.get('join_date') != '' else False,
            'work_phone': kw.get('work_phone'),
            'work_city': kw.get('work_city'),
            'work_area': kw.get('work_district'),
            'work_street': kw.get('work_street'),
            'work_mail': kw.get('work_email'),
            'total_salary': kw.get('salary'),
            'other_income': kw.get('other_income'),
            'total_income': kw.get('annuly_income'),
            'source': kw.get('income_source'),
            'education_exp': kw.get('education_exp'),
            # 'labor_exp': kw.get('labor_exp'),
            'cost_labor': kw.get('labor_exp'),
            # 'health_exp': kw.get('health_exp'),
            'personal_care_exp': kw.get('health_exp'),
            # 'phone_exp': kw.get('phone_exp'),
            'cost_telecom': kw.get('phone_exp'),
            'food_exp': kw.get('food_exp'),
            # 'other_obligation': kw.get('other_obligation'),
            'other_liability': kw.get('other_obligation'),
            'tran_exp': kw.get('transportation_exp'),
            # 'expected_future_exp': kw.get('expected_future_exp'),
            'cost_future': kw.get('expected_future_exp'),

        }
        guarantor = {
            'name': kw.get('guarantor_name'),
            'gender': kw.get('guarantor_gender'),
            # 'guarantor_age': kw.get('guarantor_age'),
            'identification_no': kw.get('guarantor_id_iqama'),
            'place': kw.get('guarantor_id_issue_place'),
            'release_of_date': kw.get('guarantor_id_issue_date') if kw.get('guarantor_id_issue_date') != '' else False,
            'birth_of_date': kw.get('guarantor_birth_date') if kw.get('guarantor_birth_date') != '' else False,
            'hijri_birth_date_month': kw.get('guarantor_hijri_birth_date_month') if kw.get(
                'guarantor_hijri_birth_date_month') != '' else False,
            'hijri_birth_date_year': kw.get('guarantor_hijri_birth_date_year') if kw.get(
                'guarantor_hijri_birth_date_year') != '' else False,
            'expiry_of_date': kw.get('guarantor_expiry_date') if kw.get('guarantor_expiry_date') != '' else False,
            'nationality': kw.get('guarantor_nationality'),
            'phone': kw.get('guarantor_residence_phone'),
            'mobile': kw.get('guarantor_mobile_phone'),
            'phone_outside': kw.get('guarantor_internationl_mobile_phone'),
            'email': kw.get('guarantor_email'),
            # 'guarantor_type': kw.get('guarantor_type'),
            'marital_status': kw.get('guarantor_martial_status'),
            'number_dependents': kw.get('guarantor_dependents'),
            'city': kw.get('guarantor_city'),
            'street2': kw.get('guarantor_district'),
            'street': kw.get('guarantor_street'),
            'unit_number': kw.get('guarantor_unit_no'),
            'additional_code': kw.get('guarantor_additional_no'),
            'zip': kw.get('guarantor_postal_code'),
            # 'guarantor_wasel': kw.get('guarantor_wasel'),
            'home_type': kw.get('guarantor_residencial_status'),
            'annual_rent': kw.get('guarantor_annual_rent'),
            'sectors': kw.get('guarantor_job_type'),
            'employer': kw.get('guarantor_employer_name'),
            'type_loan': kw.get('guarantor_job_title'),
            'years_work': kw.get('guarantor_join_date') if kw.get('guarantor_join_date') != '' else False,
            'work_phone': kw.get('guarantor_work_phone'),
            'work_city': kw.get('guarantor_work_city'),
            'work_area': kw.get('guarantor_work_district'),
            'work_street': kw.get('guarantor_work_street'),
            'work_mail': kw.get('guarantor_work_email'),
            'education_exp': kw.get('guarantor_education_exp'),
            'cost_home': kw.get('guarantor_housing_exp'),
            'cost_insurance': kw.get('guarantor_insurance_exp'),
            # 'guarantor_labor_exp': kw.get('guarantor_labor_exp'),
            'cost_labor': kw.get('guarantor_labor_exp'),
            # 'guarantor_health_exp': kw.get('guarantor_health_exp'),
            'personal_care_exp': kw.get('guarantor_health_exp'),
            # 'phone_exp': kw.get('guarantor_phone_exp'),
            'cost_telecom': kw.get('guarantor_phone_exp'),
            'food_exp': kw.get('guarantor_food_exp'),
            # 'guarantor_other_obligation': kw.get('guarantor_other_obligation'),
            'other_liability': kw.get('guarantor_other_obligation'),
            'tran_exp': kw.get('guarantor_transportation_exp'),
            # 'guarantor_expected_future_exp': kw.get('guarantor_expected_future_exp'),
            'cost_future': kw.get('guarantor_expected_future_exp'),

        }
        attachments = {
            'loan_attach': kw.get('load_attach'),
            'id_attach': kw.get('id_attach'),
            'salary_attach': kw.get('salary_attach'),
            'bank_certificate_attach': kw.get('bank_certificate_attach'),
            'bank_statement_attach': kw.get('bank_statement_attach'),
        }
        return {
            'partner': partner,
            'guarantor': guarantor,
            'attachments': attachments,
        }
