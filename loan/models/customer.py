# -*- coding: utf-8 -*-
from email.policy import default
from zeep import Client as ZeepClient, helpers
from zeep.exceptions import Fault
from odoo.exceptions import ValidationError, UserError
import certifi
from odoo import api, models, fields, _
import random
import os
import logging
from datetime import datetime, date
from zeep.wsse.signature import Signature
from requests import Session
from zeep.transports import Transport
from hijri_converter import convert
import requests
import json

response_status = {

}
_logger = logging.getLogger(__name__)
SOAP_URL = 'https://otp.absher.sa/AbsherOTPService?WSDL'


# SOAP_URL = '{}?wsdl'.format(SOAP_URL_WITHOUT_WSDL)


class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Create Customer'

    user = fields.Many2one("res.users", readonly=True, string="User", default=lambda self: self.env.user)
    allow_loan = fields.Boolean(string="Allow Loan")
    is_customer = fields.Boolean(string="Customer", store=True)
    loan_request_year = fields.Integer(string="Loan Request Per Year", default=1)
    identification_no = fields.Char(string="Identification ID", store=True)
    birth_of_date = fields.Date(string="Birth Of Date")
    birth_of_date_hijri = fields.Char(compute='get_hijri_birth_of_date', readonly=True, store=True)
    expiry_of_date_hijri = fields.Char(compute='get_hijri_birth_of_date', readonly=True, store=True)
    age = fields.Integer(string="Age", compute='set_age', store=True)
    gender = fields.Selection([('male', 'M - Male'), ('female', 'F - Female'), ('none', 'None')],
                              compute='change_gender_value')
    gender_elm = fields.Char(string='Elm Gender')
    gender_code = fields.Char(compute='select_nationality_code', string='G Code', store=True, readonly=True)
    gender_simah = fields.Char(compute='change_gender_value', string='simah Code', store=True, readonly=True)
    occupationCode = fields.Char(string='Occupation Code', store=True, readonly=True)
    position = fields.Char(string='Occupation Desc', store=True, readonly=True)
    industry = fields.Char(string='Industry', store=True, readonly=True)
    nationality = fields.Selection([('saudi', 'Saudi'), ('foreign', 'Foreign')])
    nationality_code = fields.Char(compute='select_nationality_code', string='N Code', readonly=True, store=True,
                                   default='SAU')
    marital_status = fields.Selection([('single', 'Single'), ('married', 'Married')], string="marital Status")
    risk = fields.Selection([('low', 'Low Risk'), ('medium', 'Medium'), ('high', 'High')], string='Risk Level')
    certificate = fields.Selection(
        [('Diploma', 'Diploma'), ('Bachelor', 'Bachelor'), ('Secondary', 'Secondary'), ('Masters', 'Masters'),
         ('Doctorate', 'Doctorate'), ('Other', 'Other')])
    home_type = fields.Selection(
        [('Own place', 'Own place'), ('Rental', 'Rental'), ('Provided through work', 'Provided through work'),
         ('Living with parents', 'Living with parents')])
    sectors = fields.Selection(
        [('Private Sector', 'Private Sector'), ('Government Sector', 'Government'),
         ('Soldier', 'Soldier'), ('Retired', 'Retired')])
    release_of_date = fields.Date(string="Release Date")
    expiry_of_date = fields.Date(string="Expiry Date")
    issue_place = fields.Char(string="Issue Place")
    id_version_number = fields.Integer(string="Version Number")
    legal_status = fields.Char(string="Legal status")
    place = fields.Char(string="Place of issue", store=True)
    annual_rent = fields.Float(string="Annual Rent")

    id_number = fields.Many2one('aml.aml', string="ID number", readonly=True)
    iqama = fields.Char(related='id_number.iq_number', string="Iqama ID", readonly=True, store=True)
    employer = fields.Char(string='Employer', store=True)
    classification_employer = fields.Selection(
        [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    years_work = fields.Date(string='working Date')
    date_of_joining = fields.Char(string='working Date')
    employment_end_date = fields.Char(string='Employment End Date')
    is_current_occupation = fields.Char()
    years_number = fields.Integer(string='Years', compute='set_years_number', store=True)
    years_retire = fields.Date(string='Joining Date')
    basic_salary = fields.Float(string='Basic Salary')
    home_allowance = fields.Float(string='Home Allowance')
    transport_allowance = fields.Float(string='Transport Allowance')
    other_allowance = fields.Float(string='Other Allowance')
    insurance_discount = fields.Float(string='Insurance Discount')
    total_salary = fields.Float(string='Total Salary', compute='onchange_salary', store=True)
    other_income = fields.Float(string='Other Income', store=True)
    internal_deduction = fields.Float(string='Internal Deduction')
    check_deduction = fields.Boolean()
    total_income = fields.Float(string='Total Income', compute='onchange_income')
    loan_limit = fields.Float(string='Limit', compute='net_limit', store=True)
    compare_limit = fields.Float('Loan Limit', compute='net_limit', store=True)
    # loan_compare = fields.Float(string='Compare')
    salary_rate = fields.Float(string='Net Salary', default='1', compute='limit_loan', store=True)
    loan_imit_percentage = fields.Float(string='Loan Percentage')
    loan_imit_percentage_gov = fields.Float(string='Loan Percentage GOv')
    # limit_gov_percentage = fields.Float(string='Limit Percentage')
    # limit_man_percentage = fields.Float(string='Limit Percentage')
    # limit_sol_percentage = fields.Float(string='Limit Percentage')
    annual_income = fields.Float(string="Annually Income")
    source = fields.Char(string="Income Source", store=True)
    # loan_per = fields.Float(String='Percentage', compute='_loan_p ercentage')

    number_dependents = fields.Integer(string='Num Of Dependents', default='1')
    number_liability = fields.Float(string='ALL Liabilities', compute='_compute_total_liability', store=True)
    number_liability_report = fields.Float(string='ALL liability Report', compute='_compute_total_liability_report',
                                           store=True)
    liability = fields.Float(string='All Liability')
    education_exp = fields.Float(string='Education Expenses')
    food_exp = fields.Float(string='Food Expenses', store=True)
    tran_exp = fields.Float(string='Transport Expenses')
    personal_care_exp = fields.Float(string='Care Expenses')
    # cost_labor = fields.Float(string='Labor Expenses')
    cost_insurance = fields.Float(string='Insurance Expenses')
    cost_home = fields.Float(string='Home Expenses')
    cost_telecom = fields.Float(string='Telecom Expenses')
    cost_future = fields.Float(string='Future Expenses')

    disclosure = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')])
    relation_name = fields.Char(string="Name Of Member", store=True)
    relation_relative = fields.Char(string="Relative Relation", store=True)

    iban_number = fields.Char(string="IBAN Number", store=True)
    v_account = fields.Many2one('virtual.account.line', string="Virtual Account", domain=[('is_select', '=', False)],
                                store=True)
    iban_num = fields.Char(related='v_account.iban_num', store=True)
    iban_name = fields.Char(string="Bank Name")
    sadad_number = fields.Char(string="Sadad Number", store=True)
    bank_name = fields.Char(string="Bank Name", store=True)
    installment_comp = fields.Float(string='Simah Liability', compute='total_liability_company', store=True)
    deduction_before = fields.Float(string='Simah Deduction', compute='total_deduction_before', store=True)

    # term = fields.Integer(string='Term')
    # installment_monthly = fields.Float(string='Monthly installment', compute='_divide_month_installment', store=True,
    #                                    default='1')
    # total_installment_liability = fields.Float(string='Total Installment Company', compute='total_liability_company',
    #                                            store=True)
    other_liability = fields.Float(string='Other Liability')
    ratio = fields.Float(string='ratio')
    total_liability = fields.Float(string='Total Liability')
    installment_percentage = fields.Float(string='Installment Percentage')
    state = fields.Selection(
        [('review_kyc', 'review Kyc'), ('initial_approval', 'Initial approval'), ('create', 'Confirm'),
         ('final_approval', 'Final approval'),
         ('decision', 'Decision'), ('approve', 'Approve'),
         ('contract', 'Contract'), ('azm contract', 'Signed'), ('buying', 'Contract'), ('disburse', 'Disburse'),
         ('open', 'Open'), ('early', 'Early C'), ('close', 'Close'), ('cancel', 'Cancel'), ('reject', 'Reject'),
         ('archive', 'Archive'), ('new', 'New Application'), ('return', 'Return'), ('simah', 'Simah Check'),
         ('l1', 'L1'), ('l2', 'L2'), ('active', 'Active'), ('pending', 'Pending'), ('malaa', 'Final MFS')],
        string='All State', required=True, default='simah')

    loan_purpose = fields.Char(string="Loan Purpose", store=True)
    communicat_type = fields.Char(string="Relationship Type", store=True)
    communicat_phone = fields.Char(string="Communicat number", store=True)
    relative_name = fields.Char(string="Name of relative in home town", store=True)
    relative_type = fields.Char(string="Relative type", store=True)
    relative_phone = fields.Char(string="Phone number", store=True)

    service = fields.Boolean('Medical Service')
    offer_num = fields.Char(string="Price Offer Number", store=True)
    clinic_name = fields.Char(string="Clinic Name", store=True)
    service_provider = fields.Char(string="Service Provider", store=True)
    quotation_number = fields.Char(string="Quotation Number", store=True)
    loan_amount = fields.Monetary(string="Loan Amount", store=True)
    simah_amount = fields.Float(compute='update_record', string="Simah Amount", store=True)
    month_installment = fields.Monetary(related='installment_id.installment_amount', string="Month Installment",
                                        store=True)
    interest_rate = fields.Float(related='type_id.rate', string="Interest Rate", store=True)
    interest_amount = fields.Monetary(string="Interest Amount", compute='_interest_amount', store=True)
    total_loan = fields.Float(related='loan_id.total_loan', string="Loan Total", store=True)
    period_loan = fields.Selection(
        [('three', '3 Month'), ('six', '6 Month'), ('tow', '12 Month'), ('eighteen', '18 Month'), ('2four', '24 Month'),
         ('other', 'Other')], string="Loan Period")
    about_us = fields.Selection(
        [('billboards', 'Billboards'), ('sms', 'SMS'), ('social', 'Social Media'), ('friends', 'Relative Friends'),
         ('sales', 'Sales Representative'), ('radio', 'Radio'),
         ('clients', 'FUEL Clients')], string="About us")
    res_partner_line = fields.One2many('res.partner.line', 'partner_id', string="Credit Commitment")
    loan_id = fields.Many2one("loan.order", required=True, readonly=True)
    installment_id = fields.Many2one("loan.installment", readonly=True)
    type_id = fields.Many2one("loan.type", readonly=True)
    sequence = fields.Char(related='loan_id.seq_num', string='References', store=True)
    # loan_type_custom = fields.Many2one("loan.type", required=True, string="Loan Type")
    request_date = fields.Date(related='loan_id.request_date', string='Request Date', store=True)
    close_date = fields.Date(related='loan_id.request_date', string='Close Date', store=True)
    phone_outside = fields.Char(string='Phone Outside', store=True)

    personal_loan = fields.Float(string='Personal Loan', store=True)
    consumer_loan = fields.Float(string='Consumer Loan', store=True)
    rental_loan = fields.Float(string='Rental Loan', store=True)
    home_loans = fields.Float(string='Home Loan', store=True)
    credit_cards = fields.Float(string='Credit Cards', store=True)
    home_loan = fields.Boolean('Home Loan')
    gov_loan = fields.Boolean('Gov Support')

    unit_number = fields.Char(string="Unit Number", store=True)
    building_number = fields.Char(string="building Number", store=True)
    additional_code = fields.Char(string="Additional Code", store=True)
    rate_limit = fields.Float(string="Limit Rate", store=True)
    down_payment = fields.Float(string='Down Payment')

    loan_num = fields.One2many('loan.order', 'name', string='Loans',
                               domain=[('state', 'not in', ['new', 'reject', 'cancel'])])
    count_loan = fields.Integer('View Loan', compute='_count_loan', store=True)
    # installment_custom = fields.One2many('loan.order', 'name', string="Loan request")
    ispep = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')])
    region = fields.Selection(
        [('center', 'CEN - Central - الوسطى'),
         ('east', 'EST - Eastern - الشرقية'),
         ('west', 'WST - Western - الغربية'),
         ('south', 'STH - Southern - الجنوبية'),
         ('north', 'NOR - Northern - الشمالية')])
    industry = fields.Selection(
        [('comp', 'COM - companies'), ('telcom', 'TEL - Telecommunications'),
         ('interior', 'INT - Ministry of Interior Affairs'), ('defense', 'DEF - Ministry of Defense'),
         ('communications', 'COU -  The ministry of communications'),
         ('health', 'HELTH - Ministry of Health'),
         ('finance', 'FIN - Ministry of Finance'), ('education', 'EDU - The Ministry of Education'),
         ('departments', 'GOV - Government departments'), ('foreign', 'FOR - Ministry of Foreign Affairs'),
         ('service', 'SER - Ministry of Civil Service'), ('municipalities', 'MUN - Municipalities'),
         ('bank', 'BNK - Banks'), ('insurance', 'INS - Insurance'),
         ('education', 'HED - Ministry of Higher Education'), ('associations', 'ASS - Associations'),
         ('royal', 'ROY - The Royal Guard'), ('affairs', 'AFF - The Ministry of Foreign Affairs'),
         ('industry', 'IND - The Ministry of Industry'), ('national', 'NAT - National Guard'),
         ('airlines', 'AIR - Airlines'), ('court', 'COU - Royal Court'),
         ('navy', 'NAV - Navy'), ('justice', 'JUS - Ministry of Justice'),
         ('wishes', 'SOC - Social Wishes'), ('transport', 'TRA - Ministry of Transportation'),
         ('agriculture', 'AGR - Ministry Of Agriculture'), ('grievances', 'GRI - Board of Grievances'),
         ('sabek', 'SAB - Sabek'), ('hotel', 'HOT - Hotels'),
         ('air', 'AIF - Air Forces'), ('water', 'WAT - Ministry of Water'),
         ('labor', 'LAB - Ministry of Labor'), ('international', 'INO - International Organizations'),
         ('post', 'POS - Post Office'), ('information', 'INF - Ministry of Information'),
         ('command', 'BOD - Command Body'), ('housing', 'HOU - Ministry of Housing'),
         ('economy', 'ECO - Ministry of Economy'), ('petroleum', 'PET - Ministry of petroleum'),
         ('commerce', 'COM - Ministry of Commerce'), ('culture', 'CUL - Ministry of Culture'),
         ('hajj', 'HIA - Ministry of Hajj')
         ])
    position = fields.Selection(
        [('account', 'AC-Accountant'), ('accountclerk', 'D22-Accounts Clerk'), ('admin', 'D40-Administration'),
         ('air', 'D41-Airliner'), ('art', 'D42-Architect / Artest'), ('audit', 'AU-Auditor'),
         ('auto', 'D43-automotive'), ('banker', 'D7-Banker'), ('bankstaff', 'BA-Banker (Bank Staff)'),
         ('biot', 'D44-Biotechnology'), ('brig', 'BG-Brigadier General'), ('business', 'D45-Business MAN / Woman'),
         ('owner', 'D33-Business Owner'), ('captain', 'CAP-Captain'), ('cashier', 'CS-Cashier'),
         ('ceo', 'CEO-Chief Executive Officer'), ('ceo', 'CFO-Chief Financial Officer'), ('csg', 'CSG-Chief Sergeant'),
         ('clerk', 'CL-Clerk'), ('col', 'COL-Colonel'), ('programmer', 'CP-Computer Programmer'),
         ('consult', 'CO-Consultant'), ('cor', 'COR-Corporal'), ('construct', 'D46-Construction'),
         ('consultant', 'D48-Consultant'), ('contact', 'D47-Contacting'), ('customer', 'D49-Customer service'),
         ('customerservice', 'CSR-Customer Service Representative'), ('data', 'D13-Data Entry Clerk'),
         ('director', 'D34-Director'), ('head', 'DH-Division Head (Department)'), ('doctor', 'DR-Doctor'),
         ('engineer', 'EN-Engineer'), ('finance', 'D50-Financial'), ('soldier', 'FS-First Soldier'),
         ('lie', 'FL-First Lieutenant'), ('sergeant', 'FSS-First Staff Sergeant'), ('fore', 'ND4-ForeMan'),
         ('admin', 'D17-General and Admin Services'), ('gmanager', 'GM-General Manager'),
         ('govsector', 'D51-government sector'), ('practice', 'D52-Healthcare, practice. and tech.'),
         ('hr', 'D53-Human Resources'), ('imam', 'IMA-Imam'), ('it', 'D55-Information TTechnology'),
         ('insurance', 'D54-Insurance'), ('jour', 'JO-Journalist'), ('labor', 'LB-Labor'), ('law', 'LW-Lawyer'),
         ('advisor', 'LA-Legal Advisor'), ('lieu', 'LI-Lieutenant'), ('licol', 'LC-Lieutenant Colonel'),
         ('main', 'D57-Maintenance'), ('maj', 'Maj-Major'),
         ('major', 'MG-Major General'), ('nurse', 'D23-Male Nurse'), ('man', 'MGR-Manager'),
         ('manu', 'D58-Manufacturing'), ('marketing', 'MS-Marketing Specialist'), ('mech', 'ME-Mechanic'),
         ('mechanic', 'D59-Mechanical'), ('military', 'D60-Military'), ('mining', 'D61-Mining'), ('mua', 'D11-Muakib'),
         ('class', 'D74-Not Class Warning'),
         ('nunurse', 'NU-Nurse (Male / Female)'), ('ofc', 'OFC-Officer'), ('oth', 'OTH-Others'),
         ('per', 'D20-Personal Rel Officer'), ('petro', 'D62-Petrochemical'),
         ('ph', 'PH-Pharmacist'), ('pilot', 'PI-Pilot'), ('pro', 'PR-Professor'), ('bhd', 'D63-Professor or BHD'),
         ('public', 'D64-Public Relation'), ('prm', 'PRM-Public Relation Manager'), ('purchase', 'D12-Purchaser'),
         ('quality', 'D65-Quality Service'), ('real', 'D16-Real State'), ('rec', 'REC-Reception'), ('re', 'RE-Retired'),
         ('safety', 'D66-Safety / Environment'), ('sl', 'SL-Salesman'), ('sc', 'SC-Scientist'),
         ('security', 'D67-Security'), ('secretary', 'D4-Secretary'), ('sm', 'SM-Security Man'),
         ('emp', 'SE-Self Employed'), ('ser', 'SER-Sergeant'), ('ship', 'D69-Shipping'), ('sol', 'SO-Soldier'),
         ('sp', 'SP-Specialist'), ('sport', 'D8-Sportsman'), ('sergeant', 'SS-Staff Sergeant'),
         ('sk', 'SK-Storekeeper'), ('su', 'SU-Supervisor'), ('support', 'D70-Support service'), ('tc', 'TC-Teacher'),
         ('te', 'TE-Technician'), ('op', 'D14-Tel Operator'), ('tel', 'D71-Telecommunication'),
         ('tele', 'D72-Telemarketing'), ('tlr', 'TLR-Teller (Bank)'), ('tic', 'D19-Ticketing Clerk'),
         ('tra', 'D21-Training Officer'), ('trans', 'D73-Transportation'), ('ins', 'D75-Vehicle Ins Maine')])

    hospital_quotation = fields.Many2one('hospital.quotation')
    # name_hospital_quotation = fields.Char(related='hospital_quotation.customer_name', string="Customer Name",
    #                                       readonly=True, store=True)
    product_name = fields.Many2one('product.template', string="Product Name")
    crm_lead = fields.Many2one('crm.lead', string="CRM")
    crm_seq = fields.Char(related='crm_lead.seq', string="Seq", store=True)
    type_loan = fields.Char(string="Loan Type", store=True)
    url_file = fields.Char('URL', default='https://www.odoo.com', store=True)
    doc_attachment_id = fields.Many2many('ir.attachment', 'doc1_id', string="Document",
                                         help='You can attach the copy of your document', copy=False, required=True,
                                         groups="base.group_user")
    liability_ids = fields.One2many('customer.liability', 'liability_id', string='Liability')
    duration_in_occupation = fields.Char(string='Duration Occupation')
    loan_count = fields.Integer(compute='_compute_count')
    quotation_count = fields.Integer(compute='_compute_count_quotation')
    stage = fields.Many2one('crm.stage', string='Stage')
    stage_name = fields.Char(related='stage.name', string='Stage Name')
    elm_res_partner = fields.One2many('elm.yakeen.api', 'elm_name', string="ELM Address")
    pri_sector = fields.Many2one('private.sector.api')
    private_sector_ids = fields.One2many('private.sector.api', 'salary_certificate_id')
    gov_sector_ids = fields.One2many('government.sector.api', 'salary_certificate_gov')
    gov_sector = fields.Many2one('government.sector.api', name='GOV Sector')
    employmentStatus = fields.Char()
    bool_field = fields.Boolean('hide button', default=False)
    is_sales_manager = fields.Boolean(
        compute='_compute_is_sales_manager',
        string='Is Sales Manager',
    )

    @api.depends('user_id')
    def _compute_is_sales_manager(self):
        for record in self:
            record.is_sales_manager = self.env.user.has_group('loan.group_sales_manager')

    def action_salary_certificate_gov(self):
        self.bool_field = True
        url = 'https://fuelfinance.sa/api/simah/reports/salary-certificate'
        BASE_URL = 'https://simahnew.free.beeceptor.com/gov'
        headers = {
            'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg3MkI3RjZCNjYyODM5NjVENDMyODYzNjk5MDA3OUQxNzlGMzBBQjUiLCJ0eXAiOiJKV1QiLCJ4NXQiOiJoeXRfYTJb09XWFVNb1kybVFCNTBYbnpDclUifQ.eyJuYmYiOjE3MDIyOTQ0NjgsImV4cCI6MTcwMjI5ODA2OCwiaXNzIjoiaHR0cHM6Ly9zcGlkcy5rc2FjYi5jb20uc2EvIiwiYXVkIjpbImh0dHBzOi8vc3BpZHMua3NhY2IuY29tLnNhL3Jlc291cmNlcyIsImJi',
            'Content-Type': 'application/json'
        }

        for rec in self:
            national_id = rec.identification_no
            dob = rec.birth_of_date_hijri
            response_type = 2
            employer_type_id = 1
            data = {
                "national_id": int(national_id),
                "dob": dob,
                "response_type": response_type,
                "employer_type_id": employer_type_id
            }

            try:
                response = requests.post(url, json=data, headers=headers, verify=False, timeout=60)
                response.raise_for_status()

                print(f"Response Status Code: {response.status_code}")
                print(f"Response Content: {response.text}")

                if not response.text.strip():
                    raise ValidationError(_('Empty response from API. Please check the endpoint or server.'))

                dic_re = response.json()
                print(f"Parsed JSON Response: {json.dumps(dic_re, indent=4)}")

                if response.status_code == 200:
                    dic_data = dic_re.get('data')

                    if isinstance(dic_data, dict) and 'governmentSector' in dic_data and dic_data['governmentSector']:
                        for governmentsector in dic_data['governmentSector']:
                            try:
                                personal_info = governmentsector.get('personalInfo', {})
                                employer_info = governmentsector.get('employerInfo', {})
                                bank_info = governmentsector.get('bankInfo', {})
                                employment_info = governmentsector.get('employmentInfo', {})
                                payslip_info = governmentsector.get('payslipInfo', {})

                                rec.gov_sector_ids.create({
                                    'employeeNameAr': personal_info.get('employeeNameAr', ''),
                                    'employeeNameEn': personal_info.get('employeeNameEn', ''),
                                    'agencyCode': employer_info.get('agencyCode', ''),
                                    'agencyName': employer_info.get('agencyName', ''),
                                    'accountNumber': bank_info.get('accountNumber', ''),
                                    'bankCode': bank_info.get('bankCode', ''),
                                    'bankName': bank_info.get('bankName', ''),
                                    'employeeJobNumber': employment_info.get('employeeJobNumber', ''),
                                    'employeeJobTitle': employment_info.get('employeeJobTitle', ''),
                                    'agencyEmploymentDate': employment_info.get('agencyEmploymentDate', ''),
                                    'payMonth': payslip_info.get('payMonth', ''),
                                    'basicSalary': payslip_info.get('basicSalary', 0),
                                    'netSalary': payslip_info.get('netSalary', 0),
                                    'totalAllownces': payslip_info.get('totalAllownces', 0),
                                    'totalDeductions': payslip_info.get('totalDeductions', 0),
                                    'salary_certificate_gov': rec.id,
                                })
                                self.employer = employer_info.get('agencyName', '')
                                self.basic_salary = payslip_info.get('basicSalary', 0)
                                self.other_allowance = payslip_info.get('totalAllownces', 0)
                                self.date_of_joining = employment_info.get('agencyEmploymentDate', '')
                                self.iban_number = bank_info.get('accountNumber', '')
                                self.internal_deduction = payslip_info.get('totalDeductions', 0)
                                self.salary_rate = payslip_info.get('netSalary', 0)
                                self.bank_name = bank_info.get('bankName', '')

                                print(f"Internal Deduction: {self.internal_deduction}")

                            except ValueError:
                                print(f"Error: Cannot convert {governmentsector} to a float.")
                    else:
                        _logger.warning("Unexpected or empty 'data' field in response: %s",
                                        json.dumps(dic_re, indent=4))
                        raise ValidationError(
                            _('No valid data received. API Message: %s') % dic_re.get('messages', 'Unknown error'))
            except requests.exceptions.Timeout:
                raise ValidationError(_('API request timed out. Please try again later.'))
            except requests.exceptions.RequestException as e:
                raise ValidationError(_('API request failed: %s') % str(e))
            except ValueError as ve:
                raise ValidationError(_('Invalid JSON response: %s') % str(ve))
            except Exception as e:
                raise ValidationError(_('Unexpected error: %s') % str(e))

    # def action_salary_certificate_gov(self):
    #     self.bool_field = True
    #     url = 'https://fuelfinance.sa/api/simah/reports/salary-certificate'
    #     BASE_URL = 'https://simahnew.free.beeceptor.com/gov'
    #     headers = {
    #         'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg3MkI3RjZCNjYyODM5NjVENDMyODYzNjk5MDA3OUQxNzlGMzBBQjUiLCJ0eXAiOiJKV1QiLCJ4NXQiOiJoeXRfYTJb09XWFVNb1kybVFCNTBYbnpDclUifQ.eyJuYmYiOjE3MDIyOTQ0NjgsImV4cCI6MTcwMjI5ODA2OCwiaXNzIjoiaHR0cHM6Ly9zcGlkcy5rc2FjYi5jb20uc2EvIiwiYXVkIjpbImh0dHBzOi8vc3BpZHMua3NhY2IuY29tLnNhL3Jlc291cmNlcyIsImJi',
    #         'Content-Type': 'application/json'
    #     }
    #     for rec in self:
    #         national_id = rec.identification_no
    #         dob = rec.birth_of_date_hijri
    #         response_type = 2
    #         employer_type_id = 1
    #         data = {"national_id": int(national_id), "dob": dob, "response_type": response_type,
    #                 "employer_type_id": employer_type_id}
    #         response = requests.post(url, json=data, headers=headers, verify=False, timeout=60)
    #         print(response)
    #         dic_re = response.json()
    #         print(dic_re)
    #         if response.status_code == 200:
    #             dic_data = dic_re.get('data')
    #             if dic_data['governmentSector']:
    #                 for governmentsector in dic_data['governmentSector']:
    #                     try:
    #                         rec.gov_sector_ids.create({
    #                             'employeeNameAr': governmentsector['personalInfo']['employeeNameAr'],
    #                             'employeeNameEn': governmentsector['personalInfo']['employeeNameEn'],
    #                             'agencyCode': governmentsector['employerInfo']['agencyCode'],
    #                             'agencyName': governmentsector['employerInfo']['agencyName'],
    #                             'accountNumber': governmentsector['bankInfo']['accountNumber'],
    #                             'bankCode': governmentsector['bankInfo']['bankCode'],
    #                             'bankName': governmentsector['bankInfo']['bankName'],
    #                             'employeeJobNumber': governmentsector['employmentInfo']['employeeJobNumber'],
    #                             'employeeJobTitle': governmentsector['employmentInfo']['employeeJobTitle'],
    #                             'agencyEmploymentDate': governmentsector['employmentInfo']['agencyEmploymentDate'],
    #                             'payMonth': governmentsector['payslipInfo']['payMonth'],
    #                             'basicSalary': governmentsector['payslipInfo']['basicSalary'],
    #                             'netSalary': governmentsector['payslipInfo']['netSalary'],
    #                             'totalAllownces': governmentsector['payslipInfo']['totalAllownces'],
    #                             'totalDeductions': governmentsector['payslipInfo']['totalDeductions'],
    #                             'salary_certificate_gov': rec.id,
    #                         })
    #                         self.employer = governmentsector['employerInfo']['agencyName']
    #                         self.basic_salary = governmentsector['payslipInfo']['basicSalary']
    #                         self.other_allowance = governmentsector['payslipInfo']['totalAllownces']
    #                         self.date_of_joining = governmentsector['employmentInfo']['agencyEmploymentDate']
    #                         self.iban_number = governmentsector['bankInfo']['accountNumber']
    #                         self.internal_deduction = governmentsector['payslipInfo']['totalDeductions']
    #                         self.salary_rate = governmentsector['payslipInfo']['netSalary']
    #                         self.bank_name = governmentsector['bankInfo']['bankName']
    #                         print(self.internal_deduction)
    #                     except ValueError:
    #                         print(f"Cannot convert '{governmentsector}' to a float.")
    #             else:
    #                 raise ValidationError(_('Error : "%s" ') % (dic_re.get('messages')))

    def action_salary_certificate_data(self):
        self.bool_field = True
        url = 'https://fuelfinance.sa/api/simah/reports/salary-certificate'
        BASE_URL = 'https://simahnew.free.beeceptor.com/salary'
        headers = {
            'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg3MkI3RjZCNjYyODM5NjVENDMyODYzNjk5MDA3OUQxNzlGMzBBQjUiLCJ0eXAiOiJKV1QiLCJ4NXQiOiJoeXRfYTJb09XWFVNb1kybVFCNTBYbnpDclUifQ.eyJuYmYiOjE3MDIyOTQ0NjgsImV4cCI6MTcwMjI5ODA2OCwiaXNzIjoiaHR0cHM6Ly9zcGlkcy5rc2FjYi5jb20uc2EvIiwiYXVkIjpbImh0dHBzOi8vc3BpZHMua3NhY2IuY29tLnNhL3Jlc291cmNlcyIsImJi',
            'Content-Type': 'application/json'
        }

        for rec in self:
            national_id = rec.identification_no
            dob = rec.birth_of_date_hijri
            response_type = 2
            employer_type_id = 3
            data = {"national_id": int(national_id), "dob": dob, "response_type": response_type,
                    "employer_type_id": employer_type_id}

            try:
                response = requests.post(url, json=data, headers=headers, verify=False, timeout=60)
                response.raise_for_status()  # Raise an error for 4xx or 5xx responses

                # Debugging: Print response content before parsing
                print(f"Response Status Code: {response.status_code}")
                print(f"Response Content: {response.text}")

                # Ensure response is not empty before parsing JSON
                if not response.text.strip():
                    raise ValidationError(_('Empty response from API. Please check the endpoint or server.'))

                dic_re = response.json()  # Attempt JSON parsing

                # Debugging: Print parsed JSON
                print(f"Parsed JSON Response: {json.dumps(dic_re, indent=4)}")

                if response.status_code == 200:
                    dic_data = dic_re.get('data', {})

                    if 'privateSector' in dic_data and dic_data['privateSector']:
                        for privatesector in dic_data['privateSector'].get('employmentStatusInfo', []):
                            try:
                                rec.private_sector_ids.create({
                                    'fullName': privatesector.get('fullName', ''),
                                    'basicWage': privatesector.get('basicWage', 0),
                                    'housingAllowance': privatesector.get('housingAllowance', 0),
                                    'otherAllowance': privatesector.get('otherAllowance', 0),
                                    'fullWage': privatesector.get('fullWage', 0),
                                    'dateOfJoining': privatesector.get('dateOfJoining', ''),
                                    'employerName': privatesector.get('employerName', ''),
                                    'workingMonths': privatesector.get('workingMonths', 0),
                                    'employmentStatus': privatesector.get('employmentStatus', ''),
                                    'salaryStartingDate': privatesector.get('salaryStartingDate', ''),
                                    'establishmentActivity': privatesector.get('establishmentActivity', ''),
                                    'commercialRegistrationNumber': privatesector.get('commercialRegistrationNumber',
                                                                                      ''),
                                    'legalEntity': privatesector.get('legalEntity', ''),
                                    'dateOfBirth': privatesector.get('dateOfBirth', ''),
                                    'nationality': privatesector.get('nationality', ''),
                                    'gosinumber': privatesector.get('gosinumber', ''),
                                    # 'nationalUnifiedNo': privatesector.get('nationalUnifiedNo', ''),  # Ensure this key exists
                                    'salary_certificate_id': rec.id
                                })

                                self.employer = privatesector.get('employerName', '')
                                self.basic_salary = privatesector.get('basicWage', 0)
                                self.home_allowance = privatesector.get('housingAllowance', 0)
                                self.other_allowance = privatesector.get('otherAllowance', 0)
                                self.date_of_joining = privatesector.get('dateOfJoining', '')
                                self.employmentStatus = privatesector.get('employmentStatus', '')

                            except ValueError:
                                print(f"Error: Cannot convert {privatesector} to a float.")

                    else:
                        raise ValidationError(_('Error: %s') % (dic_re.get('messages', 'Unknown API Error')))

            except requests.exceptions.Timeout:
                raise ValidationError(_('API request timed out. Please try again later.'))
            except requests.exceptions.RequestException as e:
                raise ValidationError(_('API request failed: %s') % str(e))
            except requests.exceptions.JSONDecodeError:
                raise ValidationError(_('Invalid JSON response from API. Response Content: %s') % response.text)

    # def action_salary_certificate_data(self):
    #     self.bool_field = True
    #     url = 'https://fuelfinance.sa/api/simah/reports/salary-certificate'
    #     BASE_URL = 'https://simahnew.free.beeceptor.com/salary'
    #     headers = {
    #         'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg3MkI3RjZCNjYyODM5NjVENDMyODYzNjk5MDA3OUQxNzlGMzBBQjUiLCJ0eXAiOiJKV1QiLCJ4NXQiOiJoeXRfYTJb09XWFVNb1kybVFCNTBYbnpDclUifQ.eyJuYmYiOjE3MDIyOTQ0NjgsImV4cCI6MTcwMjI5ODA2OCwiaXNzIjoiaHR0cHM6Ly9zcGlkcy5rc2FjYi5jb20uc2EvIiwiYXVkIjpbImh0dHBzOi8vc3BpZHMua3NhY2IuY29tLnNhL3Jlc291cmNlcyIsImJi',
    #         'Content-Type': 'application/json'
    #     }
    #     for rec in self:
    #         national_id = rec.identification_no
    #         dob = rec.birth_of_date_hijri
    #         response_type = 2
    #         employer_type_id = 3
    #         data = {"national_id": int(national_id), "dob": dob, "response_type": response_type,
    #                 "employer_type_id": employer_type_id}
    #         response = requests.post(url, json=data, headers=headers, verify=False, timeout=60)
    #         print(response)
    #         dic_re = response.json()
    #         print(dic_re)
    #         if response.status_code == 200:
    #             dic_data = dic_re.get('data')
    #             if dic_data['privateSector']:
    #                 for privatesector in dic_data['privateSector']['employmentStatusInfo']:
    #                     try:
    #                         rec.private_sector_ids.create({
    #                             'fullName': privatesector['fullName'],
    #                             'basicWage': privatesector['basicWage'],
    #                             'housingAllowance': privatesector['housingAllowance'],
    #                             'otherAllowance': privatesector['otherAllowance'],
    #                             'fullWage': privatesector['fullWage'],
    #                             'dateOfJoining': privatesector['dateOfJoining'],
    #                             'employerName': privatesector['employerName'],
    #                             'workingMonths': privatesector['workingMonths'],
    #                             'employmentStatus': privatesector['employmentStatus'],
    #                             'salaryStartingDate': privatesector['salaryStartingDate'],
    #                             'establishmentActivity': privatesector['establishmentActivity'],
    #                             'commercialRegistrationNumber': privatesector['commercialRegistrationNumber'],
    #                             'legalEntity': privatesector['legalEntity'],
    #                             'dateOfBirth': privatesector['dateOfBirth'],
    #                             'nationality': privatesector['nationality'],
    #                             'gosinumber': privatesector['gosinumber'],
    #                             # 'nationalUnifiedNo': privatesector['nationalUnifiedNo'],
    #                             'salary_certificate_id': rec.id
    #                         })
    #                         self.employer = privatesector['employerName']
    #                         self.basic_salary = privatesector['basicWage']
    #                         self.home_allowance = privatesector['housingAllowance']
    #                         self.other_allowance = privatesector['otherAllowance']
    #                         self.date_of_joining = privatesector['dateOfJoining']
    #                         self.employmentStatus = privatesector['employmentStatus']
    #                     except ValueError:
    #                         print(f"Cannot convert '{privatesector}' to a float.")
    #             else:
    #                 raise ValidationError(_('Error : "%s" ') % (dic_re.get('messages')))

    def action_reset(self):
        self.bool_field = False
        self.message_post(body=datetime.today(), subject='this data Deleted')

    first_name = fields.Char()
    second_name = fields.Char()
    third_name = fields.Char()
    family_name = fields.Char()
    # simah_amount = fields.Float()
    english_name = fields.Char()

    @api.onchange('name')
    def action_split(self):
        for rec in self:
            if rec.name == '':
                char = rec.name.split()
                print(char)
                rec.first_name = char[0] if len(char) > 0 else ''
                rec.second_name = char[1] if len(char) > 1 else ''
                rec.third_name = char[2] if len(char) > 2 else ''
                rec.family_name = char[3] if len(char) > 3 else ''
            else:
                return False

    @api.depends('loan_amount')
    def update_record(self):
        for rec in self:
            if rec.loan_amount >= 0:
                rec.simah_amount = rec.loan_amount
            else:
                rec.simah_amount = 0

    # @api.onchange('identification_no')
    # def select_nationality(self):
    #     for rec in self:
    #         if [('rec.identification_no', '=like', 1)]:
    #             rec.nationality = 'saudi'
    #         elif [('rec.identification_no', '=like', 2)]:
    #             rec.nationality = 'foreign'
    #         else:
    #             pass

    # def zeep_client(self):
    #     try:
    #         session = Session()
    #         cert_path = '/home/ibrahim/Desktop/Fuel/integration/ELM/OTP/ELM C/fuel_finance.cer'
    #         private_key_filename = "/home/ibrahim/Desktop/Fuel/integration/ELM/OTP/ELM C/fuelfinance.key.pem"
    #         public_key_filename = "/home/ibrahim/Desktop/Fuel/integration/ELM/OTP/ELM C/fuelfinance.crt.pem"
    #         client_authorization = 'loOBu0r3Q1raBL8D3xl0USmooWcSkDE8ns/J0UnATbi513QuExmIY1gWUrRju6Oe'
    #         session.verify = cert_path
    #         transport = Transport(session=session)
    #         client = ZeepClient(SOAP_URL,
    #                             wsse=Signature(public_key_filename, private_key_filename, client_authorization),
    #                             transport=transport)
    #         _logger.info('# client: {}'.format(client))
    #         print('11111111111111111111111111111111111', client)
    #         return client
    #     except Fault as ex:
    #         raise UserError(ex)

    @api.depends('gender_elm')
    def change_gender_value(self):
        for rec in self:
            if rec.gender_elm == 'ذكر':
                rec.gender = 'male'
                rec.gender_simah = 1
            elif rec.gender_elm == 'أنثى':
                rec.gender = 'female'
                rec.gender_simah = 0
            elif rec.gender_elm == 'انثى':
                rec.gender = 'female'
                rec.gender_simah = 0
            else:
                rec.gender = 'none'
                rec.gender_simah = 1

    @api.depends('nationality', 'gender')
    def select_nationality_code(self):
        for rec in self:
            if rec.nationality == 'saudi':
                rec.nationality_code = 'SAU'
                if rec.gender == 'male':
                    rec.gender_code = 'M'
                elif rec.gender == 'female':
                    rec.gender_code = 'F'
                else:
                    rec.gender_code = 'U'
            elif rec.nationality == 'foreign':
                rec.nationality_code = 'FOR'
                if rec.gender == 'male':
                    rec.gender_code = 'M'
                elif rec.gender == 'female':
                    rec.gender_code = 'F'
                else:
                    rec.gender_code = 'U'
            else:
                rec.nationality_code = 'U'

    @api.onchange('v_account')
    def select_virtual_account(self):
        for rec in self:
            if rec.v_account:
                rec.v_account.is_select = True
            else:
                rec.v_account.is_select = False

    @api.depends('birth_of_date', 'expiry_of_date')
    def get_hijri_birth_of_date(self):
        for rec in self:
            if rec.birth_of_date:
                birth_of_date = convert.Gregorian.fromdate(rec.birth_of_date).to_hijri().dmyformat()
                rec.birth_of_date_hijri = birth_of_date
            else:
                rec.birth_of_date = ''

            if rec.expiry_of_date:
                ex_date = convert.Gregorian.fromdate(rec.expiry_of_date).to_hijri().dmyformat()
                rec.expiry_of_date_hijri = ex_date
            else:
                rec.expiry_of_date_hijri = ''

    # @api.model
    def verify_code(self):
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_sales_cancel').users:
                    print(user.name, 'user')

    @api.depends('installment_comp', 'salary_rate')
    def total_deduction_before(self):
        for rec in self:
            if rec.salary_rate > 0:
                rec.deduction_before = (rec.installment_comp / rec.salary_rate)
            else:
                rec.salary_rate == 1

    @api.depends('birth_of_date')
    def set_age(self):
        today_date = datetime.now().date()
        for rec in self:
            if rec.birth_of_date:
                birth_of_date = fields.Datetime.to_datetime(rec.birth_of_date).date()
                total_age = str(int((today_date - birth_of_date).days / 365))
                rec.age = total_age
            else:
                rec.age = 1

    @api.depends('years_work')
    def set_years_number(self):
        today_date = datetime.now().date()
        for rec in self:
            if rec.years_work:
                years_work = fields.Datetime.to_datetime(rec.years_work).date()
                total_years_number = str(int((today_date - years_work).days / 365))
                rec.years_number = total_years_number
            else:
                rec.years_number = 1

    # @api.depends('birth_of_date')
    #     def calculate_age(self):
    #         today = date.today()
    #         return today.year - self.birth_of_date.year - (
    #                 (today.month, today.day) < (self.birth_of_date.month, self.birth_of_date.day))

    @api.depends('loan_amount')
    def _interest_amount(self):
        for rec in self:
            rec.interest_amount = rec.allow_loan * 1
            print(rec.interest_amount)

    @api.onchange('home_type')
    def monthly_rent(self):
        if self.home_type == 'Own place':
            self.cost_home = 500
        elif self.home_type == 'Rental':
            self.cost_home = 1000
        else:
            self.cost_home = 0

    # @api.constrains('age', 'sector')
    # def _check_age(self):
    #     print("Self..........", self)
    #     self.state = 'draft'
    #     if self.sector == 'private':
    #         print("Self..........", self)
    #         if self.age <= 21:
    #             raise ValidationError(_("The Age of this Customer does not Fit the Conditions"))
    #             self.state = 'reject'
    #         elif self.age >= 60:
    #             self.state = 'reject'
    #         raise ValidationError(_("The Age of this Customer does not Fit the Conditions"))
    #     elif self.sector == 'governmental':
    #         if self.age <= 21:
    #             raise ValidationError(_("The Age of this Customer does not Fit the Conditions"))
    #             self.state = 'reject'
    #         elif self.age >= 60:
    #             self.state = 'reject'
    #     elif self.sector == 'retired':
    #         if self.age <= 21:
    #             raise ValidationError(_("The Age of this Customer does not Fit the Conditions"))
    #             self.state = 'reject'
    #         elif self.age >= 65:
    #             self.state = 'reject'
    #     else:
    #         self.sector: 'businessmen'

    @api.onchange('cost_telecom', 'tran_exp', 'personal_care_exp', 'education_exp')
    def minimum(self):
        if self.cost_telecom <= 200:
            self.cost_telecom = 200
        if self.education_exp <= 66:
            self.education_exp = 66
        if self.tran_exp <= 350:
            self.tran_exp = 350
        if self.personal_care_exp <= 200:
            self.personal_care_exp = 200

    # @api.depends('food_exp', 'number_dependents')
    # def min_food(self):
    #     food = 300
    #     for rec in self:
    #         rec.food_exp = food * rec.number_dependents
    #         if rec.food_exp > 300:
    #             rec.food_exp = 300
    #         else:
    #             rec.food_exp = 300

    # def action_complete(self):
    #     # self.message_post(body="your message", partner_ids=[10])
    #     self.state = 'review done'
    #     return {
    #         'name': _('Write Note'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'mail.compose.message',
    #         'view_mode': 'form',
    #         'target': 'new',
    #     }
    #     for rec in self:
    #         users = self.env.ref('loan.group_loan_credit').users.ids
    #         user_id = self.env.user.id
    #         random_id = user_id
    #         while random_id == user_id:
    #             random_id = random.choice(users)
    #         activity_object = self.env['mail.activity']
    #         activity_values = self.activity_create_complete(random_id, rec.id, 'res.partner', 'base.model_res_partner')
    #         activity_id = activity_object.create(activity_values)
    #
    #     # rec.write({'state': 'review done'})
    #
    # def activity_create_complete(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "Customer  Reviewed",
    #         'note': "Customer data is Completed and Reviewed",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_partner_complete').id,
    #     }
    def action_reject(self):
        # for rec in self:
        #     if len(rec.crm_lead.mapped('stage_id.name')) == 1:
        #         proposition_stage_id = self.env['crm.stage'].search([('name', '=', 'الرفض من قبل الائتمان')])
        #         rec.crm_lead.write({'stage_id': proposition_stage_id})
        #         print(proposition_stage_id)
        #         print(rec.stage_name)
        phone = self.phone
        sms_reject = 'مرحباً بك عميلنا العزيز نشكر لك ثقتك في فيول للتمويل، يؤسفنا إبلاغك بأن طلب التمويل  غير مقبول. نشكر لك اختيارك فيول للتمويل. لمزيد من الاستفسارات نسعد بخدمتكم على الرقم  8001184000 '
        # encoded_data = base64.b64encode(bytes(sms_approve, 'utf_8')).decode()
        values = '''{
                          "userName": "Fuelfinancesa",
                          "numbers": "''' + phone + '''",
                          "userSender": "fuelfinance",
                          "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                          "msg": "''' + sms_reject + '''"
                        }'''

        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        values = values.encode()
        response = requests.post('https://www.msegat.com/gw/sendsms.php', data=values,
                                 headers=headers, timeout=60)

        print(response.status_code)
        print(response.headers)
        print(response.json())
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        self.message_post(body=datetime.today(),
                          subject=' The Customer Rejected - مرحباً بك عميلنا العزيز نشكر لك ثقتك في فيول للتمويل، يؤسفنا إبلاغك بأن طلب التمويل  غير مقبول. نشكر لك اختيارك فيول للتمويل. لمزيد من الاستفسارات نسعد بخدمتكم على الرقم  8001184000 ')
        self.state = 'reject'
        for rec in self:
            users = self.env.ref('loan.group_archive').users.ids
            user_id = self.env.user.id
            random_id = user_id
            while random_id == user_id:
                random_id = random.choice(users)
            activity_object = self.env['mail.activity']
            activity_values = self.activity_create_reject(random_id, rec.id, 'res.partner',
                                                          'base.model_res_partner')
            activity_id = activity_object.create(activity_values)
            # rec.write({'state': 'review done'})

    def activity_create_reject(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "The Customer Rejected",
            'note': "The Customer Rejected",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_reject').id,
        }

    def action_done(self):
        if not self.region:
            raise ValidationError(_("Please Select the Region!!!"))
        self.state = 'simah'
        self.message_post(body=datetime.today(),
                          subject='Move the Customer to Credit V - عميلنا العزيز تم إستلام طلبك وجاري معالجة الطلب، وسيتم الرد عليكم  نشكر لك اختيارك فيول للتمويل ولمزيد من الاستفسارات نسعد بخدمتك على الرقم 8001184000')
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        phone = self.phone
        sms_submit = 'عميلنا العزيز تم إستلام طلبك وجاري معالجة الطلب، وسيتم الرد عليكم  نشكر لك اختيارك فيول للتمويل ولمزيد من الاستفسارات نسعد بخدمتك على الرقم 8001184000 '
        values = '''{
                                  "userName": "Fuelfinancesa",
                                  "numbers": "''' + phone + '''",
                                  "userSender": "fuelfinance",
                                  "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                  "msg": "''' + sms_submit + '''"
                                }'''

        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        values = values.encode()
        response = requests.post('https://www.msegat.com/gw/sendsms.php', data=values,
                                 headers=headers, timeout=60)

        print(response.status_code)
        print(response.headers)
        # print(response.json())
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        return {
            'name': _('Loan Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.order',
            'view_mode': 'form',
            # 'res_id':  [('follower', '=', self.message_follower_ids)],
            'target': 'new',
            'domain': [('name', '=', self.id)],
            # 'user': [('follower', '=', self.message_follower_ids)],
            'context': {'default_name': self.id},
        }
        # users = self.env.ref('loan.group_loan_credit').users.ids
        # user_id = self.env.user.id

    #     random_id = user_id
    #     while random_id == user_id:
    #         random_id = random.choice(users)
    #         activity_object = self.env['mail.activity']
    #         activity_values = self.activity_create_done(random_id, rec.id, 'res.partner',
    #                                                     'base.model_res_partner')
    #         activity_id = activity_object.create(activity_values)
    #     # rec.write({'state': 'review done'})
    #
    # def activity_create_done(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "Data Completed",
    #         'note': "Completed Customer Data",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_partner_done').id,
    #     }
    def action_incomplete(self):
        if not self.region:
            raise ValidationError(_("Please Select the Region!!!"))
        # self.state = 'review done'
        self.message_post(body=datetime.today(),
                          subject='Send SMS to Customer, in complete data - عميلنا العزيز يرجى استيفاء المستندات المطلوبة بهدف استكمال إجراءات التمويل، نشكر لك اختيارك فيول للتمويل ولمزيد من الاستفسارات نسعد بخدمتك على الرقم 8001184000')
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        phone = self.phone
        sms_incomplete = 'عميلنا العزيز يرجى استيفاء المستندات المطلوبة بهدف استكمال إجراءات التمويل، نشكر لك اختيارك فيول للتمويل ولمزيد من الاستفسارات نسعد بخدمتك على الرقم 8001184000 '
        values = '''{
                                  "userName": "Fuelfinancesa",
                                  "numbers": "''' + phone + '''",
                                  "userSender": "fuelfinance",
                                  "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                  "msg": "''' + sms_incomplete + '''"
                                }'''

        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        values = values.encode()
        response = requests.post('https://www.msegat.com/gw/sendsms.php', data=values,
                                 headers=headers, timeout=60)

        print(response.status_code)
        print(response.headers)
        print(response.json())
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def action_close(self):
        # self.state = 'review done'
        self.message_post(body=datetime.today(),
                          subject='Send SMS to Customer, Close Request - عميلنا العزيز يرجى استيفاء المستندات المطلوبة بهدف استكمال إجراءات التمويل، نشكر لك اختيارك فيول للتمويل ولمزيد من الاستفسارات نسعد بخدمتك على الرقم 8001184000 ')
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        phone = self.phone
        sms_incomplete = 'عميلنا العزيز يرجى استيفاء المستندات المطلوبة بهدف استكمال إجراءات التمويل، نشكر لك اختيارك فيول للتمويل ولمزيد من الاستفسارات نسعد بخدمتك على الرقم 8001184000 '
        values = '''{
                                  "userName": "Fuelfinancesa",
                                  "numbers": "''' + phone + '''",
                                  "userSender": "fuelfinance",
                                  "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                  "msg": "''' + sms_incomplete + '''"
                                }'''

        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        values = values.encode()
        response = requests.post('https://www.msegat.com/gw/sendsms.php', data=values,
                                 headers=headers, timeout=60)

        print(response.status_code)
        print(response.headers)
        print(response.json())
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def action_draft(self):
        # return super(res_partner, self).unlink()
        self.state = 'return'

    def action_cancel_sales(self):
        self.loan_id.button_cancel()
        self.state = 'cancel'
        activity_object = self.env['mail.activity']
        activity_values = self.activity_create_cancel(self.id, 'res.partner', 'base.model_res_partner')
        activity_id = activity_object.create(activity_values)

    def activity_create_cancel(self, record_id, model_name, model_id):
        self.message_post(body=datetime.today(), subject='The Customer Canceled')
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "The Request Canceled",
            'note': "the Request has been canceled",
            'date_deadline': datetime.today(),
            'activity_type_id': self.env.ref('loan.mail_activity_activity_create_cancel').id,
        }

    def action_cancel(self):
        self.state = 'cancel'

    def action_re_review(self):
        # return super(res_partner, self).unlink()
        self.message_post(body=datetime.today(), subject='Re-Review to the Customer')
        self.state = 'return'
        activity_object = self.env['mail.activity']
        activity_values = self.activity_create_review(self.id, 'res.partner', 'base.model_res_partner')
        activity_id = activity_object.create(activity_values)

    def activity_create_review(self, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "The Request RE-Review",
            'note': "The Request will be reviewed again",
            'date_deadline': datetime.today(),
            'activity_type_id': self.env.ref('loan.mail_activity_activity_create_review').id,
        }

    #     return {
    #         'name': _('Write Note'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'mail.compose.message',
    #         'view_mode': 'form',
    #         'target': 'new',
    #     }
    #     activity_object = self.env['mail.activity']
    #     for follower in self.message_follower_ids:
    #         user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
    #         if user != self.env.user:
    #             if user in self.env.ref('loan.group_res_partner_sales').users:
    #                 # for rec in self:
    #                 #     users = self.env.ref('loan.group_sales_cancel').users.ids
    #                 #     user_id = self.env.user.id
    #                 #     random_id = user_id
    #                 #     while random_id == user_id:
    #                 #         random_id = random.choice(users)
    #                 #     activity_object = self.env['mail.activity']
    #                 activity_values = self.activity_create_draft(user.id, self.id, 'res.partner',
    #                                                              'base.model_res_partner')
    #                 activity_id = activity_object.create(activity_values)
    #
    # def activity_create_draft(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "Return Process",
    #         'note': "Customer data is not Completed and Returned",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_return_date').id,
    #     }

    def action_pending(self):
        self.state = 'pending'

    def action_confirm(self):
        self.state = 'l2'

    # def action_archive(self):
    #     self.state = 'reject'

    def action_close_admin(self):
        self.state = 'close'

    def action_approve(self):
        self.state = 'approve'

    def action_confirm_call(self):
        self.state = 'buying'

    def action_buying(self):
        self.state = 'contract'

    def action_reject_call(self):
        self.state = 'reject'

    def action_apply(self):
        self.state = 'disburse'

    def action_move(self):
        self.state = 'disburse'

    def action_send_back(self):
        self.state = 'return'

    def action_send_credit(self):
        self.state = 'return'

    def action_installment(self):
        self.state = 'simah'

    def action_l1(self):
        self.state = 'l1'

    def action_disburse(self):
        self.state = 'active'

    def action_open(self):
        self.state = 'active'

    def action_early(self):
        self.state = 'early'

    def action_set_reject(self):
        self.state = 'reject'

    def action_reject_credit(self):
        self.state = 'reject'

    # def action_admin_cancel(self):
    #     self.state = 'cancel'

    #     if self.installment_id:
    #         for installment in self.installment_id:
    #             installment.with_context({'force_delete': True}).unlink()
    #     for rec in self:
    #         users = self.env.ref('loan.group_customer_service').users.ids
    #         user_id = self.env.user.id
    #         random_id = user_id
    #         while random_id == user_id:
    #             random_id = random.choice(users)
    #         activity_object = self.env['mail.activity']
    #         activity_values = self.activity_create_relect(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
    #         activity_id = activity_object.create(activity_values)
    #
    # def activity_create_relect(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "Customer Reject",
    #         'note': "Customer request denied",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_reject_done').id,
    #     }

    @api.onchange('total_income')
    def _annual_income(self):
        for rec in self:
            if rec.total_income > 0:
                rec.annual_income = rec.total_income * 12
            else:
                rec.annual_income = 1

    @api.depends('personal_loan', 'consumer_loan', 'rental_loan', 'home_loans', 'credit_cards')
    def total_liability_company(self):
        for rec in self:
            rec.installment_comp = (rec.personal_loan + rec.consumer_loan + rec.rental_loan + rec.home_loans +
                                    rec.credit_cards)

    # @api.depends('loan_amount', 'term')
    # def _divide_month_installment(self):
    #     if self.term > 0:
    #         self.installment_monthly = self.loan_amount / self.term
    #     else:
    #         self.term == 1

    @api.depends('education_exp', 'food_exp', 'tran_exp', 'personal_care_exp', 'cost_future',
                 'cost_telecom', 'cost_home', 'other_liability')
    def _compute_total_liability(self):
        for rec in self:
            rec.number_liability = rec.education_exp + rec.tran_exp + rec.personal_care_exp + \
                                   rec.cost_telecom + rec.cost_future + rec.cost_home + rec.other_liability + \
                                   rec.food_exp

    @api.depends('education_exp', 'food_exp', 'tran_exp', 'personal_care_exp', 'cost_future',
                 'cost_telecom', 'cost_home', 'number_dependents')
    def _compute_total_liability_report(self):
        for rec in self:
            rec.number_liability_report = (rec.education_exp + rec.food_exp + rec.tran_exp + rec.personal_care_exp
                                           + rec.cost_telecom + rec.cost_future + rec.cost_home) * \
                                          rec.number_dependents

    # @api.constrains('number_dependents')
    # def compute_number_dependents(self):
    #     if self.number_dependents == 0:
    #         raise ValidationError(_("Number of dependents less than 1 !!!"))

    @api.depends('basic_salary', 'home_allowance', 'other_allowance', 'insurance_discount')
    def onchange_salary(self):
        for rec in self:
            rec.total_salary = rec.basic_salary + rec.home_allowance + rec.other_allowance - rec.insurance_discount

    @api.onchange('total_salary', 'other_income')
    def onchange_income(self):
        for rec in self:
            if rec.total_salary >= 0:
                rec.total_income = rec.total_salary + rec.other_income
            else:
                rec.total_income = 1

    @api.constrains('loan_num')
    def _count_loan(self):
        for partner in self:
            partner.count_loan = len(partner.loan_num)

    def action_view_loan(self):
        loan_num = self.env['loan.order'].search([('name', '=', self.id)])
        if loan_num:
            action = self.env.ref('loan.request_action').read()[0]
            action['domain'] = [('id', 'in', loan_num.ids), ('state', 'not in', ['new', 'reject', 'cancel'])]
            return action
        else:
            action = {'type': 'ir.actions.act_window_close'}

    # @api.constrains('iban_number')
    # def len_iban_number(self):
    #     if len(self.iban_number) < 24 or len(self.iban_number) > 24:
    #         raise ValidationError(_('Error ! IBAN Number Incorrect '))

    @api.constrains('identification_no')
    def len_identification_no(self):
        for rec in self:
            if len(rec.identification_no) != 10:
                raise ValidationError(_('Error ! Identification Id Incorrect'))

    @api.constrains('identification_no')
    def match_identification_no(self):
        for rec in self:
            if rec.identification_no and not rec.identification_no.startswith(('1', '2')):
                raise ValidationError(_('Error ! Identification Id must be starting 1 or 2'))

    @api.constrains('sadad_number')
    def len_sadad_number(self):
        for rec in self:
            rec.sadad_number == 1
            if len(str(rec.sadad_number)) < 14 or len(str(rec.sadad_number)) > 14:
                raise ValidationError(_('Error ! SADAD NUMBER Incorrect '))

    # @api.constrains('phone')
    # def check_phone(self):
    #     phone = self.env['res.partner'].search(
    #         [('phone', '=', self.phone), ('phone', '!=', True),
    #          ('id', '!=', self.id)])
    #     if phone:
    #         raise ValidationError(_('Exists ! Already a PHONE NUMBER exists in this Customer'))

    # @api.constrains('identification_no')
    # def check_identification_no(self):
    #     identification_id = self.env['res.partner'].search(
    #         [('identification_no', '=', self.identification_no), ('identification_no', '!=', True),
    #          ('id', '!=', self.id)])
    #     if identification_id:
    #         raise ValidationError(_('Exists ! Already a Identification Id exists in this Customer'))

    @api.constrains('identification_no')
    def _check_identification_id(self):
        iqama = self.env['aml.aml'].search(
            [('iq_number', '=', self.identification_no), ('iq_number', '!=', True),
             ('id', '!=', self.id)])
        if iqama:
            raise ValidationError(_('Exists ! This Customer Blocked'))

    def action_close_dialog_loan(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.depends('loan_limit')
    def net_limit(self):
        for rec in self:
            if rec.loan_limit >= 0:
                rec.compare_limit = rec.loan_limit
                print(rec.compare_limit)
                print(rec.loan_limit)
            else:
                rec.compare_limit = 1

    @api.depends('basic_salary', 'home_allowance', 'loan_imit_percentage', 'total_salary', 'sectors',
                 'liability', 'rate_limit', 'installment_comp', 'other_income', 'salary_rate',
                 'home_loan', 'gov_loan', 'internal_deduction')
    def limit_loan(self):
        for rec in self:
            rec.loan_limit = 1
            if rec.sectors == 'Retired':
                rec.rate_limit = 0.33
                rec.salary_rate = rec.basic_salary
            elif rec.sectors == 'Private Sector':
                rec.loan_imit_percentage = 9.75
                if rec.total_salary < 25000:
                    rec.rate_limit = 0.45
                    rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
                                        rec.loan_imit_percentage) / 100)
                    rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
                    rec.salary_rate = rec.salary_rate + rec.other_income
                    rec.loan_limit = rec.salary_rate * rec.rate_limit
                elif rec.total_salary >= 25000:
                    rec.rate_limit = 0.65
                    rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
                                        rec.loan_imit_percentage) / 100)
                    rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
                    rec.salary_rate = rec.salary_rate + rec.other_income
                    rec.loan_limit = rec.salary_rate * rec.rate_limit
                # rec.salary_rate = (((rec.basic_salary + rec.home_allowance) * rec.loan_imit_percentage) / 100)
                # rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
                # rec.salary_rate = rec.salary_rate + rec.other_income
                # rec.loan_limit = rec.salary_rate * rec.rate_limit
            elif rec.sectors == 'Government Sector':
                rec.loan_imit_percentage = 9
                if rec.total_salary < 25000:
                    rec.rate_limit = 0.45
                    rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
                                        rec.loan_imit_percentage) / 100)
                    rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
                    rec.salary_rate = rec.salary_rate + rec.other_income
                    rec.loan_limit = rec.salary_rate * rec.rate_limit
                elif rec.total_salary >= 25000:
                    rec.rate_limit = 0.65
                    rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
                                        rec.loan_imit_percentage) / 100)
                    rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
                    rec.salary_rate = rec.salary_rate + rec.other_income
                    rec.loan_limit = rec.salary_rate * rec.rate_limit
                # rec.salary_rate = (((rec.basic_salary + rec.home_allowance) * rec.loan_imit_percentage) / 100)
                # rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
                # rec.salary_rate = rec.salary_rate + rec.other_income
                # rec.loan_limit = rec.salary_rate * rec.rate_limit
            elif rec.sectors == 'Soldier':
                rec.loan_imit_percentage = 9
                if rec.total_salary < 25000:
                    rec.rate_limit = 0.45
                    rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
                                        rec.loan_imit_percentage) / 100)
                    rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
                    rec.salary_rate = rec.salary_rate + rec.other_income
                    rec.loan_limit = rec.salary_rate * rec.rate_limit
                elif rec.total_salary >= 25000:
                    rec.rate_limit = 0.65
                    rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
                                        rec.loan_imit_percentage) / 100)
                    rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
                    rec.salary_rate = rec.salary_rate + rec.other_income
                    rec.loan_limit = rec.salary_rate * rec.rate_limit
                # rec.salary_rate = (((rec.basic_salary + rec.home_allowance) * rec.loan_imit_percentage) / 100)
                # rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
                # rec.salary_rate = rec.salary_rate + rec.other_income
                # rec.compare_limit = rec.loan_limit
            else:
                rec.salary_rate = rec.basic_salary
        # for rec in self:
        #     if rec.installment_comp <= 0 | rec.home_loan == 0:
        #         rec.loan_limit = 1
        #         if rec.sectors == 'Retired':
        #             rec.rate_limit = 0.33
        #             rec.salary_rate = rec.basic_salary
        #             # rec.loan_limit = rec.salary_rate * rec.rate_limit
        #         elif rec.sectors == 'Private Sector':
        #             rec.loan_imit_percentage = 9.75
        #             rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                 rec.loan_imit_percentage) / 100)
        #             rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #             rec.salary_rate = rec.salary_rate + rec.other_income
        #             rec.rate_limit = 0.33
        #             rec.loan_limit = rec.salary_rate * rec.rate_limit
        #         elif rec.sectors == 'Government Sector':
        #             rec.loan_imit_percentage = 9
        #             rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                 rec.loan_imit_percentage) / 100)
        #             rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #             rec.salary_rate = rec.salary_rate + rec.other_income
        #             rec.rate_limit = 0.65
        #             rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             # rec.compare_limit = rec.loan_limit - rec.installment_comp
        #         elif rec.sectors == 'Soldier':
        #             rec.loan_imit_percentage = 9
        #             rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                 rec.loan_imit_percentage) / 100)
        #             rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #             rec.salary_rate = rec.salary_rate + rec.other_income
        #             rec.rate_limit = 0.65
        #             # rec.compare_limit = (rec.salary_rate * rec.rate_limit) - rec.installment_comp
        #             rec.compare_limit = rec.loan_limit - rec.installment_comp
        #         else:
        #             rec.salary_rate = rec.basic_salary
        # ***************************************************
        #     else:
        #         if rec.sectors == 'Private Sector':
        #             rec.loan_imit_percentage = 9.75
        #             if rec.total_salary <= 15000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.45
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     if rec.gov_loan == 0:
        #                         rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                             rec.loan_imit_percentage) / 100)
        #                         rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                         rec.salary_rate = rec.salary_rate + rec.other_income
        #                         rec.rate_limit = 0.55
        #                         rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                     elif rec.gov_loan == 1:
        #                         rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                             rec.loan_imit_percentage) / 100)
        #                         rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                         rec.salary_rate = rec.salary_rate + rec.other_income
        #                         rec.rate_limit = 0.65
        #                         rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             elif rec.total_salary > 15000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.45
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.65
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             elif rec.total_salary >= 25000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.65
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.65
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 # rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                 #                     rec.loan_imit_percentage) / 100)
        #                 # rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                 # rec.salary_rate = rec.salary_rate + rec.other_income
        #                 # rec.rate_limit = 0.65
        #                 # rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             else:
        #                 rec.salary_rate = rec.basic_salary
        #         elif rec.sectors == 'Government Sector':
        #             rec.loan_imit_percentage = 9
        #             if rec.total_salary <= 15000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.45
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     if rec.gov_loan == 0:
        #                         rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                             rec.loan_imit_percentage) / 100)
        #                         rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                         rec.salary_rate = rec.salary_rate + rec.other_income
        #                         rec.rate_limit = 0.55
        #                         rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                     elif rec.gov_loan == 1:
        #                         rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                             rec.loan_imit_percentage) / 100)
        #                         rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                         rec.salary_rate = rec.salary_rate + rec.other_income
        #                         rec.rate_limit = 0.65
        #                         rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             elif rec.total_salary > 15000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.45
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.65
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             elif rec.total_salary >= 25000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.65
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     if rec.gov_loan == 0:
        #                         rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                             rec.loan_imit_percentage) / 100)
        #                         rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                         rec.salary_rate = rec.salary_rate + rec.other_income
        #                         rec.rate_limit = 0.65
        #                         rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                     elif rec.gov_loan == 1:
        #                         rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                             rec.loan_imit_percentage) / 100)
        #                         rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                         rec.salary_rate = rec.salary_rate + rec.other_income
        #                         rec.rate_limit = 0.65
        #                         rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             else:
        #                 rec.salary_rate = rec.basic_salary
        #         elif rec.sectors == 'Soldier':
        #             rec.loan_imit_percentage = 9
        #             if rec.total_salary <= 15000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.45
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     if rec.gov_loan == 0:
        #                         rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                             rec.loan_imit_percentage) / 100)
        #                         rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                         rec.salary_rate = rec.salary_rate + rec.other_income
        #                         rec.rate_limit = 0.55
        #                         rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                     elif rec.gov_loan == 1:
        #                         rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                             rec.loan_imit_percentage) / 100)
        #                         rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                         rec.salary_rate = rec.salary_rate + rec.other_income
        #                         rec.rate_limit = 0.65
        #                         rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             elif rec.total_salary > 15000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.45
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                         rec.loan_imit_percentage) / 100)
        #                     rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                     rec.salary_rate = rec.salary_rate + rec.other_income
        #                     rec.rate_limit = 0.65
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             elif rec.total_salary > 25000:
        #                 rec.salary_rate = (((rec.basic_salary + rec.home_allowance) *
        #                                     rec.loan_imit_percentage) / 100)
        #                 rec.salary_rate = rec.total_salary - rec.salary_rate - rec.internal_deduction
        #                 rec.salary_rate = rec.salary_rate + rec.other_income
        #                 rec.rate_limit = 0.65
        #                 rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             else:
        #                 rec.salary_rate = rec.basic_salary
        #         elif rec.sectors == 'Retired':
        #             if rec.total_salary <= 15000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = rec.basic_salary
        #                     rec.rate_limit = 0.55
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     rec.salary_rate = rec.basic_salary
        #                     rec.rate_limit = 0.65
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             elif rec.total_salary > 15000:
        #                 if rec.home_loan == 0:
        #                     rec.salary_rate = rec.basic_salary
        #                     rec.rate_limit = 0.45
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 elif rec.home_loan == 1:
        #                     rec.salary_rate = rec.basic_salary
        #                     rec.rate_limit = 0.65
        #                     rec.loan_limit = rec.salary_rate * rec.rate_limit
        #             elif rec.total_salary > 25000:
        #                 rec.salary_rate = rec.basic_salary
        #                 rec.rate_limit = 0.65
        #                 rec.loan_limit = rec.salary_rate * rec.rate_limit
        #                 # rec.salary_rate = rec.basic_salary
        #         else:
        #             rec.salary_rate = rec.basic_salary

        # if self.sector == 'retired':
        #     if self.installment_comp <= 0:
        #         self.rate_limit = 0.25
        #         self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit
        #     if self.installment_comp > 0:
        #         self.rate_limit = 0.45
        #         self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit
        # elif self.sector == 'private':
        #     self.loan_imit_percentage = 9.75
        #     self.salary_rate = (((self.basic_salary + self.home_allowance) *
        #                          self.loan_imit_percentage) / 100)
        #     self.salary_rate = self.total_salary - self.salary_rate
        #     self.salary_rate = self.salary_rate + self.other_income
        #     if self.installment_comp <= 0:
        #         self.rate_limit = 0.33
        #         self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit
        #     elif self.installment_comp > 0:
        #         if self.total_salary <= 15000:
        #             self.rate_limit = 0.45
        #             self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit
        #         elif self.total_salary > 15000:
        #             self.rate_limit = 0.55
        #             self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit
        #         elif self.total_salary > 25000:
        #             self.rate_limit = 0.65
        #             self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit
        #
        # elif self.sector == 'governmental':
        #     self.loan_imit_percentage = 9
        #     self.salary_rate = (((self.basic_salary + self.home_allowance) *
        #                          self.loan_imit_percentage) / 100)
        #     self.salary_rate = self.total_salary - self.salary_rate
        #     self.salary_rate = self.salary_rate + self.other_income
        #     if self.installment_comp <= 0:
        #         self.rate_limit = 0.33
        #         self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit
        #     elif self.installment_comp > 0:
        #         if self.total_salary <= 15000:
        #             self.rate_limit = 0.45
        #             self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit
        #         elif self.total_salary > 15000:
        #             self.rate_limit = 0.55
        #             self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit
        #         elif self.total_salary > 25000:
        #             self.rate_limit = 0.65
        #             self.loan_limit = (self.total_salary + self.other_income) * self.rate_limit

    def _compute_count(self):
        for record in self:
            record.loan_count = self.env['loan.order'].search_count(
                [('name', '=', self.id)])

    def get_loan(self):
        self.ensure_one()
        return {
            'name': _('Loan Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.order',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('name', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_count_quotation(self):
        for record in self:
            record.quotation_count = self.env['hospital.quotation'].search_count(
                [('customer_id', '=', self.identification_no)])

    def get_quotation(self):
        return {
            'name': _('Hospital Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.quotation',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('customer_id', '=', self.identification_no)],
            'context': "{'create': False}"
        }

    def loan_get(self):
        return {
            'name': _('Loan Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.order',
            'view_mode': 'form',
            # 'res_id':  [('follower', '=', self.message_follower_ids)],
            'target': 'new',
            'domain': [('name', '=', self.id)],
            # 'user': [('follower', '=', self.message_follower_ids)],
            'context': {'default_name': self.id},
        }

        # @api.onchange('basic_salary', 'home_allowance', 'loan_imit_percentage', 'total_salary', 'sector',
        #               'loan_liability',
        #               'liability', 'loan_limit', 'total_liability')
        # def _limit_loan(self):
        #     if self.sector == 'private':
        #         self.loan_imit_percentage = 9.75
        #         self.loan_limit = ((self.basic_salary + self.home_allowance) * self.loan_imit_percentage) / 100
        #         self.loan_limit = self.total_salary - self.loan_limit
        #         if self.loan_liability > 0:
        #             if self.liability > 0:
        #                 self.loan_limit = self.loan_limit * 0.45
        #             elif self.total_liability > 0:
        #                 self.loan_limit = self.loan_limit * 0.55
        #         else:
        #             self.loan_limit = self.loan_limit * 0.33
        #     else:
        #         self.loan_imit_percentage = 9
        #         self.loan_limit = ((self.basic_salary + self.home_allowance) * self.loan_imit_percentage) / 100
        #         self.loan_limit = self.total_salary - self.loan_limit
        #         if self.loan_liability > 0:
        #             if self.liability > 0:
        #                 self.loan_limit = self.loan_limit * 0.45
        #             elif self.total_liability > 0:
        #                 self.loan_limit = self.loan_limit * 0.55
        #         else:
        #             self.loan_limit = self.loan_limit * 0.33


class res_partner_line(models.Model):
    _name = 'res.partner.line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Create Customer Liability'

    funding_authority = fields.Char(string="Funding Authority")
    liability_amount = fields.Float(string="Obligation Amount")
    monthly_installment = fields.Float(string="Monthly Installment")
    payment_status = fields.Char(string="Payment Status")
    partner_id = fields.Many2one('res.partner', string="Partner Id")
    # state_line = fields.Selection(related='partner_id.state', string='State Line')


class mail_activity_type(models.Model):
    _name = 'mail.activity.type'
    _inherit = 'mail.activity.type'
    _description = 'Change Field'

    lol = fields.Many2many('res.users', string='New Name')


# class hospital_quotation(models.Model):
#     _inherit = 'hospital.quotation'
#     _description = 'Show Form view form hospital quotation model'
#
#     hospital_quotation = fields.Many2one('hospital.quotation', 'customer_id')
#     name_hospital_quotation = fields.Char(related='hospital_quotation.customer_name', string="Customer Name",
#                                           readonly=True, store=True)
class LeadCrm(models.Model):
    # _name = 'crm.new'
    _inherit = 'crm.lead'
    _description = 'CRM'

    partner_name = fields.Many2one('res.partner', string='Customer data')
    id_number = fields.Char(string='Id Number', store=True)
    loan_counts = fields.Integer(compute='_compute_count')
    contact_counts = fields.Integer(compute='_compute_contact_count')

    def assign_customer_to_self(self):
        self.ensure_one()
        self.user_id = self.env.user

    def _compute_count(self):
        for record in self:
            record.loan_counts = self.env['loan.order'].search_count(
                [('identification_id', '=', self.id_number)])

    def get_loans(self):
        self.ensure_one()
        return {
            'name': _('Loan Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.order',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('identification_id', '=', self.id_number)],
            'context': "{'create': False}"
        }

    def _compute_contact_count(self):
        for record in self:
            record.contact_counts = self.env['res.partner'].search_count(
                [('identification_no', '=', self.id_number)])

    def get_contacts(self):
        self.ensure_one()
        return {
            'name': _('Customer Data'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('identification_no', '=', self.id_number)],
            'context': "{'create': False}"
        }


class IrAttachment(models.Model):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    doc1_id = fields.Many2one('res.partner')


class LoanTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    _description = 'helpdesk module changes'

    # sequence = fields.Char(string='Sequence Number', copy=False)
    sequence_num = fields.Char(string='Sequence Number', copy=False)
    sequence = fields.Selection([('com', 'COM/IN/00001'), ('inq', 'INQ/IN/00001')])
    ticket_link = fields.Html(string='Link')

    def action_solve_inq(self):
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        for rec in self:
            if rec.team_id.id == 1:
                phone = self.partner_phone
                name = self.name
                sequence = self.sequence_num
                link = self.ticket_link
                self.message_post(body=datetime.today(),
                                  subject='عميلنا العزيز تم معالجة استفساركم رقم، بإمكانك زيارة الموقع الالكتروني والإطلاع على الحل ولمزيد من الاستفسارات نأمل منكم التواصل معنا على الرقم 8001184000 خلال أوقات العمل الرسمية من الاحد الى الخميس من الساعة 9 صباحاً حتى 5 مساءً نشكرك على اختيارك فيول للتمويل')
                sms_solved = 'عميلنا العزيز تم معالجة استفساركم رقم' + sequence + ' ' + name + 'بإمكانك زيارة الموقع الالكتروني والإطلاع على الحل ولمزيد من الاستفسارات نأمل منكم التواصل معنا على الرقم 8001184000 خلال أوقات العمل الرسمية من الاحد الى الخميس من الساعة 9 صباحاً حتى 5 مساءً نشكرك على اختيارك فيول للتمويل'
                values = '''{
                                              "userName": "Fuelfinancesa",
                                              "numbers": "''' + phone + '''",
                                              "userSender": "fuelfinance",
                                              "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                              "msg": "''' + sms_solved + '''"
                                            }'''

                headers = {
                    'Content-Type': 'application/json;charset=UTF-8'
                }
                values = values.encode()
                response = requests.post('https://www.msegat.com/gw/sendsms.php',
                                         data=values,
                                         headers=headers, timeout=60)

                print(response.status_code)
                print(response.headers)
                print(response.json())
                print("team_id", self.team_id.id)
            elif rec.team_id.id == 2:
                phone = self.partner_phone
                name = self.name
                sequence = self.sequence_num
                link = self.ticket_link
                self.message_post(body=datetime.today(),
                                  subject='عميلنا العزيز تم معالجة الشكوى رقم وفي حال استمرار المشكلة نأمل منكم التواصل على الرقم 8001184000 خلال اوقات العمل الرسمية من الاحد الى الخميس من الساعة 9:00 صباحاً حتى 5:00 مساء  ')
                sms_solved = (
                        'عميلنا العزيز تم معالجة الشكوى رقم' + sequence + ' ' + name + 'وفي حال استمرار المشكلة نأمل منكم التواصل معنا على الرقم 8001184000     https://forms.office.com/r/ucez2T22pc?origin=lprLink ')
                values = '''{
                                                          "userName": "Fuelfinancesa",
                                                          "numbers": "''' + phone + '''",
                                                          "userSender": "fuelfinance",
                                                          "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                                          "msg": "''' + sms_solved + '''"
                                                        }'''

                headers = {
                    'Content-Type': 'application/json;charset=UTF-8'
                }
                values = values.encode()
                response = requests.post('https://www.msegat.com/gw/sendsms.php',
                                         data=values,
                                         headers=headers, timeout=60)

                print(response.status_code)
                print(response.headers)
                print(response.json())
                print("team_id", )
            else:
                raise ValidationError(_("Please Select the HelpDesk Channel!!!"))

    # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def action_close_inq(self):
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        for rec in self:
            if rec.team_id.id == 1:
                phone = self.partner_phone
                name = self.name
                sequence = self.sequence_num
                self.message_post(body=datetime.today(),
                                  subject='عميلنا العزيز نفيدكم انه تم اغلاق استفساركم  ' + sequence + ' رقم' + name + ' نشكر لكم تعاملكم مع فيول للتمويل ولمزيد من الاستفسارات نسعد بخدمتك على الرقم 8001184000  خلال اوقات العمل الرسمية من الاحد الى الخميس من الساعة 9:00 صباحاً حتى 5:00 مساء')
                sms_close = 'عميلنا العزيز نفيدكم انه تم اغلاق استفساركم رقم ' + sequence + ' ' + name + ' ولمزيد من الاستفسارات نأمل منكم التواصل معنا على الرقم 8001184000  خلال اوقات العمل الرسمية من الاحد الى الخميس من الساعة 9:00 صباحاً حتى 5:00 مساء  نشكر لكم تعاملكم مع فيول للتمويل '
                values = '''{
                                                  "userName": "Fuelfinancesa",
                                                  "numbers": "''' + phone + '''",
                                                  "userSender": "fuelfinance",
                                                  "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                                  "msg": "''' + sms_close + '''"
                                                }'''

                headers = {
                    'Content-Type': 'application/json;charset=UTF-8'
                }
                values = values.encode()
                response = requests.post('https://www.msegat.com/gw/sendsms.php',
                                         data=values,
                                         headers=headers, timeout=60)

                print(response.status_code)
                print(response.headers)
                print(response.json())
            # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            elif rec.team_id.id == 2:
                phone = self.partner_phone
                name = self.name
                sequence = self.sequence_num
                self.message_post(body=datetime.today(),
                                  subject='عميلنا العزيز نفيدكم انه تم اغلاق شكوى  ' + sequence + 'رقم ' + name + ' نشكر لكم تعاملكم مع فيول للتمويل ولمزيد من الاستفسارات نسعد بخدمتك على الرقم 8001184000  خلال اوقات العمل الرسمية من الاحد الى الخميس من الساعة 9:00 صباحاً حتى 5:00 مساء')
                sms_close = 'عميلنا العزيز نفيدكم انه تم اغلاق شكوى رقم ' + sequence + ' ' + name + ' نشكر لكم تعاملكم مع فيول للتمويل ولمزيد من الاستفسارات نسعد بخدمتك على الرقم 8001184000  خلال اوقات العمل الرسمية من الاحد الى الخميس من الساعة 9:00 صباحاً حتى 5:00 مساء   https://forms.office.com/r/ucez2T22pc?origin=lprLink'
                values = '''{
                                                  "userName": "Fuelfinancesa",
                                                  "numbers": "''' + phone + '''",
                                                  "userSender": "fuelfinance",
                                                  "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                                  "msg": "''' + sms_close + '''"
                                                }'''

                headers = {
                    'Content-Type': 'application/json;charset=UTF-8'
                }
                values = values.encode()
                response = requests.post('https://www.msegat.com/gw/sendsms.php',
                                         data=values,
                                         headers=headers, timeout=60)

                print(response.status_code)
                print(response.headers)
                print(response.json())
            else:
                raise ValidationError(_("Please Select the HelpDesk Channel!!!"))
            # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


class elm_yakeen(models.Model):
    _name = 'elm.yakeen.api'
    # _inherit = ['res.partner', 'portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Elm & Yakeen API'

    elm_name = fields.Many2one('res.partner', string='Customer data')
    city_id = fields.Char()
    elm_city = fields.Char()
    city_l2 = fields.Char()
    elm_street_name = fields.Char()
    street_l2 = fields.Char()
    elm_district = fields.Char()
    district_l2 = fields.Char()
    elm_unit_number = fields.Char()
    elm_additional_number = fields.Char()
    elm_building_number = fields.Char()
    elm_post_code = fields.Char()
    elm_location_coordinates = fields.Char()
    region_id = fields.Char()
    region_name = fields.Char()
    region_name_l2 = fields.Char()


# class SalaryCertificate(models.Model):
#     _name = 'salary.certificate'
#     _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
#     _description = 'Salary Certificate'
#
#     name = fields.Many2one('res.partner', string='Client')
#     id_number = fields.Char(related='name.identification_no', string='ID')
#     private_sector_ids = fields.One2many('private.sector', 'salary_certificate_id')
#     gov_sector_ids = fields.One2many('government.sector', 'salary_certificate_gov')
#     birth_of_date = fields.Char(related='name.birth_of_date_hijri', string='DofB')


class PrivateSector(models.Model):
    _name = 'private.sector.api'
    _description = 'Private Sector'

    # salary_certificate_id = fields.Many2one('salary.certificate')
    bool_field = fields.Boolean('hide button', default=False)
    salary_certificate_id = fields.Many2one('res.partner')
    fullName = fields.Char('Full Name')
    basicWage = fields.Float('Basic Wage')
    housingAllowance = fields.Float('Housing Allowance')
    otherAllowance = fields.Float('Other Allowance')
    fullWage = fields.Float('Full Wage')
    employerName = fields.Char('Employer Name')
    dateOfJoining = fields.Char('Date Of Joining')
    workingMonths = fields.Char('Working Months')
    employmentStatus = fields.Char('Employment Status')
    salaryStartingDate = fields.Char('Salary Starting Date')
    establishmentActivity = fields.Char('Establishment Activity')
    commercialRegistrationNumber = fields.Char('Commercial Registration Number')
    legalEntity = fields.Char('legal Entity')
    dateOfBirth = fields.Char('Date Of Birth')
    nationality = fields.Char('Nationality')
    gosinumber = fields.Char('Gosi Number')
    nationalUnifiedNo = fields.Char('National Unified No')


class GovSector(models.Model):
    _name = 'government.sector.api'
    _description = 'Government Sector'

    # salary_certificate_gov = fields.Many2one('salary.certificate')
    bool_field = fields.Boolean('hide button', default=False)
    salary_certificate_gov = fields.Many2one('res.partner')

    # personalInfo
    employeeNameAr = fields.Char('employee NameAr')
    employeeNameEn = fields.Char('employee NameEn')

    # employerInfo
    agencyCode = fields.Char('agency Code')
    agencyName = fields.Char('agency Name', store=True)

    # bankInfo
    accountNumber = fields.Char('account Number')
    bankCode = fields.Char('bank Code')
    bankName = fields.Char('bank Name')

    # employmentInfo
    employeeJobNumber = fields.Char('Job Number')
    employeeJobTitle = fields.Char('Job Title')
    agencyEmploymentDate = fields.Char('Employment Date')

    # payslipInfo
    payMonth = fields.Float('pay Month')
    basicSalary = fields.Float('basic Salary', store=True)
    netSalary = fields.Float('net Salary', store=True)
    totalAllownces = fields.Float('total Allownces')
    totalDeductions = fields.Float('total Deductions')
