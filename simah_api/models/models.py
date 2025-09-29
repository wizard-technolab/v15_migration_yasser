# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime,timedelta
from odoo import api, models, fields, _
import requests
from odoo.exceptions import ValidationError
import json
from dateutil import parser


class API(models.Model):
    _name = 'simah.simah'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'New Fields For Integration With Simah'

    
    bool_field = fields.Boolean()
    simah_token = fields.Char("SIMAH Token")
    simah_token_expiry = fields.Datetime("SIMAH Token Expiry")
    name = fields.Many2one('res.partner', string='Customer')
    simah_city_id = fields.Many2one('simah.city')
    city_id = fields.Integer(related='simah_city_id.city_id')
    id_number = fields.Char(related='name.identification_no', string='ID')
    first_name = fields.Char(related='name.first_name', string='First Name')
    family_name = fields.Char(related='name.family_name', string='Family Name')
    loan_amount = fields.Float(related='name.simah_amount', string='Loan Amount', store=True)
    birth_of_date = fields.Char(related='name.birth_of_date_hijri', string='DofB')
    gender = fields.Char(related='name.gender_simah', string='elm gender')
    expiry_date = fields.Char(related='name.expiry_of_date_hijri', string='Expire Date')
    reportDate = fields.Date(string='Report Date')
    enquiryType = fields.Char(string='Enquiry Type')
    productType = fields.Char(string='Product Type')
    enquiryNumber = fields.Char(string='Enquiry Number')
    numberOfApplicants = fields.Integer(string='Number Of Applicants')
    accountType = fields.Char(string='Account Type')
    referenceNumber = fields.Char(string='Reference Number')
    amount = fields.Float(string='Amount')
    memberType_id = fields.Integer(string='ID')
    memberType_code = fields.Char(string='Code')
    memberType_nameAr = fields.Char(string='NameAr')
    memberType_name = fields.Char(string='Name')
    statusReport_id = fields.Integer(string='Report Status ID')
    statusReport_code = fields.Char(string='Report Status Code')
    statusReport_nameAr = fields.Char(string='Report Status NameAr')
    statusReport_name = fields.Char(string='Report Status Name')
    iDNumber = fields.Char(string="ID Number", store=True)
    typeID = fields.Integer(string='Type ID')
    typeNameEN = fields.Char(string='Name EN')
    typeNameAR = fields.Char(string='Name AR')
    idTypeCode = fields.Char(string='ID Type Code')
    iDExpiryDate = fields.Char(string='ID Expiry Date')
    applicantTypeID = fields.Integer(string='Applicant Type ID')
    applicantTypeCode = fields.Char(string='Applicant Type Code')
    applicantTypeNameEN = fields.Char(string='Applicant Type')
    applicantTypeNameAR = fields.Char(string='Applicant Type NameAR')
    customerName = fields.Char(string='Customer Name')
    familyName = fields.Char(string='Family Name')
    firstName = fields.Char(string='First Name')
    secondName = fields.Char(string='Second Name')
    thirdName = fields.Char(string='Third Name')
    customerNameAr = fields.Char(string='Customer NameAr')
    familyNameAr = fields.Char(string='Family NameAr')
    firstNameAr = fields.Char(string='First NameAr')
    secondNameAr = fields.Char(string='Second NameAr')
    thirdNameAr = fields.Char(string='Third NameAr')
    dateOfBirth = fields.Char(string='DateOfBirth')
    # gender = fields.Char(string='Gender')
    customerCity = fields.Char(string='customer City')
    totalMonthlyIncome = fields.Char(string='Total Monthly Income')
    maritalStatusId = fields.Char(string='Marital Status Id')
    statusNameEN = fields.Char(string='Status NameEN')
    statusNameAR = fields.Char(string='Status NameAR')
    maritalStatusCode = fields.Char(string='Marital Status Code')
    couId = fields.Char(string='couid')
    couNameEN = fields.Char(string='couNameEN')
    couNameAR = fields.Char(string='couNameAR')
    couCode = fields.Char(string='couCode')

    # memberNarratives
    narrDateLoaded = fields.Date(string='Date Loaded')
    # narrLoadedBy
    memberCode = fields.Char(string='Member Code')
    memberNameEN = fields.Char(string='Member NameEN')
    memberNameAR = fields.Char(string='Member NameAR')
    # disclerText
    discTextDescAr = fields.Char(string='تنوية')
    discTextDescEn = fields.Char(string='Disclaimer')

    # summaryInfo
    summActiveCreditInstruments = fields.Float(string='Credit Instruments')
    summDefaults = fields.Float(string='Defaults')
    summEarliestIssueDate = fields.Char(string='Earliest Issue Date')
    summTotalLimits = fields.Float(string='Total Limits')
    summTotalGuaranteedLimits = fields.Float(string='Total Guaranteed Limits')
    summTotalLiablilites = fields.Float(string='Total Liablilites')
    summTotalGuaranteedLiablilites = fields.Float(string='Total Guaranteed Liablilites')
    summTotalDefaults = fields.Float(string='Total Defaults ')
    summCurrentDelinquentBalance = fields.Float(string='Delinquent Balance')
    summPreviousEnquires = fields.Integer(string='Previous Enquires')
    summPreviousEnquiresThisMonth = fields.Integer(string='Previous Enquires This Month')
    summGuaranteedCreditInstruments = fields.Float(string='Credit Instruments')

    # affordabilityResponseModel
    totalIncome = fields.Float(string='Total Income')
    totalCreditCommitment = fields.Float(string='Credit Commitment')
    totalNonCreditCommitment = fields.Float(string='Credit Commitment ')
    disposableIncome = fields.Float(string='Disposable Income ')
    additionalCreditCommitment = fields.Float(string='Additional Credit Commitment')
    excludedCreditCommitment = fields.Float(string='Excluded Credit Commitment')
    netCreditCommitment = fields.Float(string='Credit Commitment')
    isEligible = fields.Float(string='isEligible')
    # productAffordability
    # salariedNonMortgage
    applicableDBR = fields.Float(string='Applicable DBR')
    monthlyInstallmentLimit = fields.Float(string='Monthly Installment Limit')
    salariedNonMortgage_applicableDBR = fields.Char()
    salariedNonMortgage_monthlyInstallmentLimit = fields.Char()
    nonSalariedNonMortgage_applicableDBR = fields.Char()
    nonSalariedNonMortgage_monthlyInstallmentLimit = fields.Char()
    nonRedfMortgage_applicableDBR = fields.Char()
    nonRedfMortgage_monthlyInstallmentLimit = fields.Char()
    redfMortgage_applicableDBR = fields.Char()
    redfMortgage_monthlyInstallmentLimit = fields.Char()
    cityOfResidence_textEn = fields.Char()
    nationality_textAr = fields.Char()
    nationality_textAr = fields.Char()
    cityOfResidence_textAr = fields.Char()
    maritalStatus_textAr = fields.Char()
    maritalStatus_textAr = fields.Char()
    homeOwnership_textAr = fields.Char()
    homeOwnership_textAr = fields.Char()
    residentialType_textAr = fields.Char()
    residentialType_textAr = fields.Char()
    globalDBR = fields.Float(string='Global DBR')
    dbrForSalariedLoans = fields.Float(string='dbr For Salaried Loans')

    totalValueUsedIncaluculation = fields.Float(string='Total calculation')
    totalValueDeclaredByCustomer = fields.Float(string='Total By Customer')
    totalOutputValue = fields.Float(string='Total Output Value')

    # userInput
    basicIncome = fields.Float(string='basic Income')
    additionalIncome = fields.Float(string='Additional Income')
    isRetired = fields.Boolean(string='isRetired')
    breadwinner = fields.Boolean(string='breadwinner')

    numberOfDependents = fields.Float(string='number Of Dependents')
    numberOfDependentsInPrivateSchool = fields.Float(string='number Of DependentsInPrivateSchool')
    numberOfDependentsInPublicSchool = fields.Float(string='number Of DependentsInPublicSchool')
    numberOfHouseholdhelp = fields.Float(string='number Of Householdhelp')

    isRedfCustomer = fields.Boolean(string='isRedfCustomer')

    simahEnquiries = fields.One2many('simah.enquiries', 'simah', string="Previous Enquiries")
    creditInstrument = fields.One2many('credit.instrument', 'simah_simah', string="Credit Instrument")
    simahNarrative = fields.One2many('simah.narrative', 'simah_narr', string="Simah Narrative")
    simahAddress = fields.One2many('simah.addresses', 'simah_address', string="Simah Address")
    simahContact = fields.One2many('simah.contact', 'simah_contact', string="Simah Contact")
    simahEmployee = fields.One2many('simah.employee', 'simah_employee', string="Simah Employee")
    simahScore = fields.One2many('simah.score', 'simah_score', string="Simah Score")
    simahExpense = fields.One2many('simah.expense', 'simah_expense', string="Simah Expense")
    simahpersonalnarratives = fields.One2many('personal.narratives', 'simah_id', string="personal narratives")
    simahDefault = fields.One2many('simah.default', 'simah_default', string="simah Default")
    guarantorDefault = fields.One2many('guarantor.default', 'guarantor_default', string="guarantor Default")
    simahCheques = fields.One2many('simah.cheques', 'simah_cheques', string="Simah Cheques")
    simahJudgement = fields.One2many('simah.judgement', 'simah_judgement', string="Simah Judgement")
    publicNotices = fields.One2many('public.notices', 'public_notices', string="Public Notices")

    salary_certificate_doc = fields.Binary()
    salary_certificate_doc_name = fields.Char(compute='_compute_salary_certificate_doc_name')
    doc_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_private_rel', 'doc_id', 'attach_id3',
                                         string="Training Reference Document",
                                         help='You can attach the copy of your document', copy=False, required=True)
    credit_instrument = fields.Many2one('credit.instrument')
    simah_dbr = fields.Float(string='Simah Deduction', compute='compute_dbr', store=True)
    dbr_installment = fields.Float(string='DBR Amount', compute='calculate_dbr_amount', store=True)
    salary_rate = fields.Float(related='name.salary_rate')
    mtg_installment = fields.Float(string='MTG Installment')
    mtg = fields.Boolean(string='MTG')
    bool_field = fields.Boolean('hide button', default=False)

    def action_reset(self):
        self.bool_field = False
        self.message_post(body=datetime.today(), subject='this data Deleted')
        self.simahEnquiries.active = False
        self.creditInstrument.active = False
        self.simahAddress.active = False
        self.simahContact.active = False
        self.simahEmployee.active = False
        self.simahScore.active = False
        self.simahDefault.active = False
        self.guarantorDefault.active = False
        self.simahCheques.active = False
        self.simahJudgement.active = False
        self.publicNotices.active = False

    @api.depends('dbr_installment', 'salary_rate', 'simah_dbr')
    def compute_dbr(self):
        for rec in self:
            if rec.salary_rate > 0:
                rec.simah_dbr = (rec.dbr_installment / rec.salary_rate) * 100
            else:
                rec.salary_rate = 1

    @api.depends('credit_instrument', 'mtg_installment')
    def calculate_dbr_amount(self):
        installment = 0
        for rec in self:
            for r in rec.creditInstrument:
                if r.total_installment > 1:
                    installment = (r.total_installment + installment)
                    rec.dbr_installment = installment - rec.mtg_installment
                    print(rec.dbr_installment)
                else:
                    rec.dbr_installment = installment

    def _compute_salary_certificate_doc_name(self):
        for rec in self:
            rec.salary_certificate_doc_name = 'salary.pdf'
    def _simah_login(self):
        """Login to SIMAH API and return access token"""
        login_url = "https://spapiuat.simah.com/api/v1/Identity/login"
        payload = {
            "username": "fueladmin",
            "password": "fueladmin_123"
        }
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.post(login_url, headers=headers, json=payload)
        if response.status_code == 200:

            data = response.json()
            token = data.get("data", {}).get("token")
            if not token:
                raise ValueError("Login response did not contain a token")

            # Optionally save token in record for reuse
            self.simah_token = token
            self.simah_token_expiry = datetime.now() + timedelta(hours=24)
            print(self.simah_token_expiry,">>>>>>>>>>>>>>>>>",token)
            return token
        else:
            raise ValueError(f"SIMAH login failed: {response.text}")
    def _get_simah_token(self):
        """Return valid token (reuse if not expired, else login again)"""
        if self.simah_token and self.simah_token_expiry and self.simah_token_expiry > datetime.now():
            return self.simah_token
        return self._simah_login()
    def action_simah_api(self):
        self.bool_field = True
        self.message_post(body=datetime.today(), subject='The Customer was queried from SIMAH')
        token = self._get_simah_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        BASE_URL = 'https://spapiuat.simah.com/api/v2/enquiry/consumer/newv2'
        for rec in self:
            national_id = rec.id_number
            first_name = rec.first_name
            family_name = rec.family_name
            dob = rec.birth_of_date
            expiry_date = rec.expiry_date
            gender = rec.gender
            city_id = rec.city_id
            data = {"national_id": int(national_id), "first_name": first_name, "family_name": family_name, "dob": dob,
                    "expiry_date": expiry_date, "city_id": city_id, "gender": gender}
            response = requests.post(BASE_URL, json=data, headers=headers, verify=False)
            print(response)
            dic_re = response.json()
            print(dic_re)
            if response.status_code == 200:
                print("!!!!!!!!!!!!!!!!!200")
                dic_data = dic_re.get('data')
                for rec in self:
                    d = parser.parse(dic_data[0]['reportDetails']['reportDate']).date()
                    print("\n", "------------", d)
                    rec.reportDate = parser.parse(dic_data[0]["reportDate"]).date()
                    # ['reportDetails']
                    rec.reportDate = d
                    rec.enquiryType = dic_data[0]['reportDetails']['enquiryType']
                    rec.productType = dic_data[0]['reportDetails']['productType']
                    rec.enquiryNumber = dic_data[0]['reportDetails']['enquiryNumber']
                    rec.numberOfApplicants = dic_data[0]['reportDetails']['numberOfApplicants']
                    rec.accountType = dic_data[0]['reportDetails']['accountType']
                    rec.referenceNumber = dic_data[0]['reportDetails']['referenceNumber']
                    rec.amount = dic_data[0]['reportDetails']['amount']
                    # ['reportDetails']['memberType']
                    rec.memberType_id = dic_data[0]['reportDetails']['memberType']['id']
                    rec.memberType_code = dic_data[0]['reportDetails']['memberType']['code']
                    rec.memberType_nameAr = dic_data[0]['reportDetails']['memberType']['nameAr']
                    rec.memberType_name = dic_data[0]['reportDetails']['memberType']['name']
                    # ['reportDetails']['status']
                    rec.statusReport_id = dic_data[0]['reportDetails']['status']['id']
                    rec.statusReport_code = dic_data[0]['reportDetails']['status']['code']
                    rec.statusReport_nameAr = dic_data[0]['reportDetails']['status']['nameAr']
                    rec.statusReport_name = dic_data[0]['reportDetails']['status']['name']
                    # ['providedDemographicsInfo']
                    rec.iDNumber = dic_data[0]['providedDemographicsInfo']['demIDNumber']
                    print("################", rec.iDNumber)
                    rec.iDExpiryDate = dic_data[0]['providedDemographicsInfo']['demIDExpiryDate']
                    # ['providedDemographicsInfo']['demIDType']
                    rec.typeID = dic_data[0]['providedDemographicsInfo']['demIDType']['typeID']
                    rec.typeNameEN = dic_data[0]['providedDemographicsInfo']['demIDType']['typeNameEN']
                    rec.typeNameAR = dic_data[0]['providedDemographicsInfo']['demIDType']['typeNameAR']
                    rec.idTypeCode = dic_data[0]['providedDemographicsInfo']['demIDType']['idTypeCode']
                    # ['providedDemographicsInfo']['demApplicantType']
                    rec.applicantTypeID = dic_data[0]['providedDemographicsInfo']['demApplicantType'][
                        'applicantTypeID']
                    rec.applicantTypeCode = dic_data[0]['providedDemographicsInfo']['demApplicantType'][
                        'applicantTypeCode']
                    rec.applicantTypeNameEN = dic_data[0]['providedDemographicsInfo']['demApplicantType'][
                        'applicantTypeNameEN']
                    rec.applicantTypeNameAR = dic_data[0]['providedDemographicsInfo']['demApplicantType'][
                        'applicantTypeNameAR']
                    # ['providedDemographicsInfo']
                    rec.customerName = dic_data[0]['providedDemographicsInfo']['demCustomerName']
                    rec.familyName = dic_data[0]['providedDemographicsInfo']['demFamilyName']
                    rec.firstName = dic_data[0]['providedDemographicsInfo']['demFirstName']
                    rec.secondName = dic_data[0]['providedDemographicsInfo']['demSecondName']
                    rec.thirdNameAr = dic_data[0]['providedDemographicsInfo']['demThirdName']
                    rec.customerNameAr = dic_data[0]['providedDemographicsInfo']['demCustomerNameAr']
                    rec.familyNameAr = dic_data[0]['providedDemographicsInfo']['demFamilyNameAr']
                    rec.firstNameAr = dic_data[0]['providedDemographicsInfo']['demFirstNameAr']
                    rec.secondNameAr = dic_data[0]['providedDemographicsInfo']['demSecondNameAr']
                    rec.thirdNameAr = dic_data[0]['providedDemographicsInfo']['demThirdNameAr']
                    rec.dateOfBirth = dic_data[0]['providedDemographicsInfo']['demDateOfBirth']
                    rec.gender = dic_data[0]['providedDemographicsInfo']['demGender']
                    rec.customerCity = dic_data[0]['providedDemographicsInfo']['demCustomerCity']
                    rec.totalMonthlyIncome = dic_data[0]['providedDemographicsInfo']['demTotalMonthlyIncome']
                    # ['providedDemographicsInfo']['demMaritalStatus']
                    rec.maritalStatusId = dic_data[0]['providedDemographicsInfo']['demMaritalStatus'][
                        'matrialStatusId']
                    rec.statusNameEN = dic_data[0]['providedDemographicsInfo']['demMaritalStatus']['statusNameEN']
                    rec.statusNameAR = dic_data[0]['providedDemographicsInfo']['demMaritalStatus']['statusNameAR']
                    rec.maritalStatusCode = dic_data[0]['providedDemographicsInfo']['demMaritalStatus'][
                        'maritalStatusCode']
                    # ['providedDemographicsInfo']['demNationality']
                    rec.couId = dic_data[0]['providedDemographicsInfo']['demNationality']['couid']
                    rec.couNameEN = dic_data[0]['providedDemographicsInfo']['demNationality']['couNameEN']
                    rec.couNameAR = dic_data[0]['providedDemographicsInfo']['demNationality']['couNameAR']
                    rec.couCode = dic_data[0]['providedDemographicsInfo']['demNationality']['couCode']

                    # ['availableDemographicsInfo']
                    rec.iDNumber = dic_data[0]['providedDemographicsInfo']['demIDNumber']
                    rec.iDExpiryDate = dic_data[0]['providedDemographicsInfo']['demIDExpiryDate']
                    # ['availableDemographicsInfo']['demIDType']
                    rec.typeID = dic_data[0]['providedDemographicsInfo']['demIDType']['typeID']
                    rec.typeNameEN = dic_data[0]['providedDemographicsInfo']['demIDType']['typeNameEN']
                    rec.typeNameAR = dic_data[0]['providedDemographicsInfo']['demIDType']['typeNameAR']
                    rec.idTypeCode = dic_data[0]['providedDemographicsInfo']['demIDType']['idTypeCode']
                    # ['availableDemographicsInfo']['demApplicantType']
                    rec.applicantTypeID = dic_data[0]['providedDemographicsInfo']['demApplicantType'][
                        'applicantTypeID']
                    rec.applicantTypeCode = dic_data[0]['providedDemographicsInfo']['demApplicantType'][
                        'applicantTypeCode']
                    rec.applicantTypeNameEN = dic_data[0]['providedDemographicsInfo']['demApplicantType'][
                        'applicantTypeNameEN']
                    rec.applicantTypeNameAR = dic_data[0]['providedDemographicsInfo']['demApplicantType'][
                        'applicantTypeNameAR']
                    # ['availableDemographicsInfo']
                    rec.customerName = dic_data[0]['providedDemographicsInfo']['demCustomerName']
                    rec.familyName = dic_data[0]['providedDemographicsInfo']['demFamilyName']
                    rec.firstName = dic_data[0]['providedDemographicsInfo']['demFirstName']
                    rec.secondName = dic_data[0]['providedDemographicsInfo']['demSecondName']
                    rec.thirdNameAr = dic_data[0]['providedDemographicsInfo']['demThirdName']
                    rec.customerNameAr = dic_data[0]['providedDemographicsInfo']['demCustomerNameAr']
                    rec.familyNameAr = dic_data[0]['providedDemographicsInfo']['demFamilyNameAr']
                    rec.firstNameAr = dic_data[0]['providedDemographicsInfo']['demFirstNameAr']
                    rec.secondNameAr = dic_data[0]['providedDemographicsInfo']['demSecondNameAr']
                    rec.thirdNameAr = dic_data[0]['providedDemographicsInfo']['demThirdNameAr']
                    rec.dateOfBirth = dic_data[0]['providedDemographicsInfo']['demDateOfBirth']
                    rec.gender = dic_data[0]['providedDemographicsInfo']['demGender']
                    rec.customerCity = dic_data[0]['providedDemographicsInfo']['demCustomerCity']
                    rec.totalMonthlyIncome = dic_data[0]['providedDemographicsInfo']['demTotalMonthlyIncome']
                    # ['availableDemographicsInfo']['demMaritalStatus']
                    rec.maritalStatusId = dic_data[0]['providedDemographicsInfo']['demMaritalStatus'][
                        'matrialStatusId']
                    rec.statusNameEN = dic_data[0]['providedDemographicsInfo']['demMaritalStatus']['statusNameEN']
                    rec.statusNameAR = dic_data[0]['providedDemographicsInfo']['demMaritalStatus']['statusNameAR']
                    rec.maritalStatusCode = dic_data[0]['providedDemographicsInfo']['demMaritalStatus'][
                        'maritalStatusCode']
                    # ['availableDemographicsInfo']['demNationality']
                    rec.couId = dic_data[0]['providedDemographicsInfo']['demNationality']['couid']
                    rec.couNameEN = dic_data[0]['providedDemographicsInfo']['demNationality']['couNameEN']
                    rec.couNameAR = dic_data[0]['providedDemographicsInfo']['demNationality']['couNameAR']
                    rec.couCode = dic_data[0]['providedDemographicsInfo']['demNationality']['couCode']

                    # ['prevEnquiries']
                    if dic_data[0]['prevEnquiries']:
                        for prevEnquirie in dic_data[0]['prevEnquiries']:
                            rec.simahEnquiries.create({
                                'prevEnqDate': prevEnquirie['prevEnqDate'],
                                'enqTypeCode': prevEnquirie['preEnqType']['enqTypeCode'],
                                'enqTypeDescriptionAr': prevEnquirie['preEnqType']['enqTypeDescriptionAr'],
                                'enqTypeDescriptionEn': prevEnquirie['preEnqType']['enqTypeDescriptionEn'],
                                'memberCode': prevEnquirie['prevEnqEnquirer']['memberCode'],
                                'memberNameEN': prevEnquirie['prevEnqEnquirer']['memberNameEN'],
                                'memberNameAR': prevEnquirie['prevEnqEnquirer']['memberNameAR'],
                                'prevEnqMemberRef': prevEnquirie['prevEnqMemberRef'],
                                'prevEnquirerName': prevEnquirie['prevEnquirerName'],
                                'prevEnquirerNameAr': prevEnquirie['prevEnquirerNameAr'],
                                'productId': prevEnquirie['prevEnqProductTypeDesc']['productId'],
                                'code': prevEnquirie['prevEnqProductTypeDesc']['code'],
                                'textEn': prevEnquirie['prevEnqProductTypeDesc']['textEn'],
                                'textAr': prevEnquirie['prevEnqProductTypeDesc']['textAr'],
                                'prevEnqAmount': prevEnquirie['prevEnqAmount'],
                                'otherReason': prevEnquirie['otherReason'],
                                'simah': rec.id
                            })
                    # ['creditInstrumentDetails']
                    if dic_data[0]['creditInstrumentDetails']:
                        for creditInstrumentDetail in dic_data[0]['creditInstrumentDetails']:
                            try:
                                obj = rec.creditInstrument.create({
                                    'memberCode': creditInstrumentDetail['ciCreditor']['memberCode'],
                                    'memberNameEN': creditInstrumentDetail['ciCreditor']['memberNameEN'],
                                    'memberNameAR': creditInstrumentDetail['ciCreditor']['memberNameAR'],
                                    'productId': creditInstrumentDetail['ciProductTypeDesc']['productId'],
                                    'code': creditInstrumentDetail['ciProductTypeDesc']['code'],
                                    'textEn': creditInstrumentDetail['ciProductTypeDesc']['textEn'],
                                    'textAr': creditInstrumentDetail['ciProductTypeDesc']['textAr'],
                                    'ciAccountNumber': creditInstrumentDetail['ciAccountNumber'],
                                    'ciLimit': creditInstrumentDetail['ciLimit'],
                                    'ciIssuedDate': creditInstrumentDetail['ciIssuedDate'],
                                    'ciExpirationDate': creditInstrumentDetail['ciExpirationDate'],
                                    'creditInstrumentStatusCode': creditInstrumentDetail['ciStatus'][
                                        'creditInstrumentStatusCode'],
                                    'creditInstrumentStatusDescAr': creditInstrumentDetail['ciStatus'][
                                        'creditInstrumentStatusDescAr'],
                                    'creditInstrumentStatusDescEn': creditInstrumentDetail['ciStatus'][
                                        'creditInstrumentStatusDescEn'],
                                    'ciClosingDate': creditInstrumentDetail['ciClosingDate'],
                                    'ciTenure': creditInstrumentDetail['ciTenure'],
                                    'paymentFrequencyCodeDescEn': creditInstrumentDetail['ciPaymentFrequency'][
                                        'paymentFrequencyCodeDescEn'],
                                    'paymentFrequencyCodeDescAr': creditInstrumentDetail['ciPaymentFrequency'][
                                        'paymentFrequencyCodeDescAr'],
                                    'paymentFrequencyCodeName': creditInstrumentDetail['ciPaymentFrequency'][
                                        'paymentFrequencyCodeName'],
                                    'ciInstallmentAmount': creditInstrumentDetail['ciInstallmentAmount'],
                                    'salaryAssignmentFlagDescEn': creditInstrumentDetail['ciSalaryAssignmentFlag'][
                                        'salaryAssignmentFlagDescEn'],
                                    'salaryAssignmentFlagDescAr': creditInstrumentDetail['ciSalaryAssignmentFlag'][
                                        'salaryAssignmentFlagDescAr'],
                                    'salaryAssignmentFlagCode': creditInstrumentDetail['ciSalaryAssignmentFlag'][
                                        'salaryAssignmentFlagCode'],
                                    'consumerSecurityTypeDescEn': creditInstrumentDetail['ciConsumerSecurityType'][
                                        'consumerSecurityTypeDescEn'],
                                    'consumerSecurityTypeDescAr': creditInstrumentDetail['ciConsumerSecurityType'][
                                        'consumerSecurityTypeDescAr'],
                                    'consumerSecurityTypeCode': creditInstrumentDetail['ciConsumerSecurityType'][
                                        'consumerSecurityTypeCode'],
                                    'ciOutstandingBalance': creditInstrumentDetail['ciOutstandingBalance'],
                                    'ciPastDue': creditInstrumentDetail['ciPastDue'],
                                    'ciLastAmountPaid': creditInstrumentDetail['ciLastAmountPaid'],
                                    'ciLastPaymentDate': creditInstrumentDetail['ciLastPaymentDate'],
                                    'ciAsOfDate': creditInstrumentDetail['ciAsOfDate'],
                                    'ciNextDueDate': creditInstrumentDetail['ciNextDueDate'],
                                    'ciSummary': creditInstrumentDetail['ciSummary'],
                                    'ciBalloonPayment': creditInstrumentDetail['ciBalloonPayment'],
                                    'ciDownPayment': creditInstrumentDetail['ciDownPayment'],
                                    # 'nameEn': creditInstrumentDetail['ciSubProduct']['nameEn'],
                                    # 'nameAr': creditInstrumentDetail['ciSubProduct']['nameAr'],
                                    # 'ciSubProduct_code': creditInstrumentDetail['ciSubProduct']['ciSubProduct_code'],
                                    'ciDispensedAmount': creditInstrumentDetail['ciDispensedAmount'],
                                    'ciMaxInstalmentAmount': creditInstrumentDetail['ciMaxInstalmentAmount'],
                                    'jointApplicantDetail': creditInstrumentDetail['jointApplicantDetail'],
                                    'ciAverageInstallmentAmount': creditInstrumentDetail[
                                        'ciAverageInstallmentAmount'],
                                    'ciNumberOfApplicants': creditInstrumentDetail['ciNumberOfApplicants'],
                                    # 'jointApplicantFlag_code': creditInstrumentDetail['jointApplicantFlag']['jointApplicantFlag_code'],
                                    # 'jointApplicantFlag_textEn': creditInstrumentDetail['jointApplicantFlag']['jointApplicantFlag_textEn'],
                                    # 'jointApplicantFlag_textAr': creditInstrumentDetail['jointApplicantFlag']['jointApplicantFlag_textAr'],
                                    'simah_simah': rec.id
                                })
                            except ValueError:
                                print(f"Cannot convert '{creditInstrumentDetail}' to a float.")
                    else:
                        raise dic_data[0]['creditInstrumentDetails'].with_traceback(None) from creditInstrumentDetail
                    # [PrimaryDefault]
                    if dic_data[0]['primaryDefaults']:
                        for primarydefault in dic_data[0]['primaryDefaults']:
                            try:
                                obj = rec.simahDefault.create({
                                    'productId': primarydefault['pDefProductTypeDesc']['productId'],
                                    'code': primarydefault['pDefProductTypeDesc']['code'],
                                    'textEn': primarydefault['pDefProductTypeDesc']['textEn'],
                                    'textAr': primarydefault['pDefProductTypeDesc']['textAr'],
                                    'pDefAccountNo': primarydefault['pDefAccountNo'],
                                    'memberCode': primarydefault['pDefCreditor']['memberCode'],
                                    'memberNameEN': primarydefault['pDefCreditor']['memberNameEN'],
                                    'memberNameAR': primarydefault['pDefCreditor']['memberNameAR'],
                                    'pDefDateLoaded': primarydefault['pDefDateLoaded'],
                                    'pDefOriginalAmount': primarydefault['pDefOriginalAmount'],
                                    'pDefOutstandingBalance': primarydefault['pDefOutstandingBalance'],
                                    'defaultStatusDescEn': primarydefault['pDefaultStatuses']['defaultStatusDescEn'],
                                    'defaultStatusDescAr': primarydefault['pDefaultStatuses']['defaultStatusDescAr'],
                                    'defaultStatusCode': primarydefault['pDefaultStatuses']['defaultStatusCode'],
                                    'pDefSetteledDate': primarydefault['pDefSetteledDate'],
                                    'simah_default': rec.id
                                })
                            except ValueError:
                                print(f"Invalid input: '{primarydefault}' is not a valid integer.")
                    # [GuarantorDefault]
                    if dic_data[0]['guarantorDefaults']:
                        for guarantordefault in dic_data[0]['guarantorDefaults']:
                            try:
                                obj = rec.guarantorDefault.create({
                                    'productId': guarantordefault['gDefProductTypeDesc']['productId'],
                                    'code': guarantordefault['gDefProductTypeDesc']['code'],
                                    'textEn': guarantordefault['gDefProductTypeDesc']['textEn'],
                                    'textAr': guarantordefault['gDefProductTypeDesc']['textAr'],
                                    'gDefAccountNo': guarantordefault['gDefAccountNo'],
                                    'memberCode': guarantordefault['gDefCreditor']['memberCode'],
                                    'memberNameEN': guarantordefault['gDefCreditor']['memberNameEN'],
                                    'memberNameAR': guarantordefault['gDefCreditor']['memberNameAR'],
                                    'gDefDateLoaded': guarantordefault['gDefDateLoaded'],
                                    'gDefOriginalAmount': guarantordefault['gDefOriginalAmount'],
                                    'gDefOutstandingBalance': guarantordefault['gDefOutstandingBalance'],
                                    'defaultStatusDescEn': guarantordefault['gDefaultStatuses']['defaultStatusDescEn'],
                                    'defaultStatusDescAr': guarantordefault['gDefaultStatuses']['defaultStatusDescAr'],
                                    'defaultStatusCode': guarantordefault['gDefaultStatuses']['defaultStatusCode'],
                                    'gDefSetteledDate': guarantordefault['gDefSetteledDate'],
                                    'guarantor_default': rec.id
                                })
                            except ValueError:
                                print(f"Invalid input: '{guarantordefault}' is not a valid integer.")

                    # [bouncedCheque]
                    if dic_data[0]['bouncedCheques']:
                        for bouncedCheque in dic_data[0]['bouncedCheques']:
                            try:
                                obj = rec.simahCheques.create({
                                    'bcCheqDateLoaded': bouncedCheque['bcCheqDateLoaded'],
                                    'productId': bouncedCheque['bcProductTypeDesc']['productId'],
                                    'code': bouncedCheque['bcProductTypeDesc']['code'],
                                    'textEn': bouncedCheque['bcProductTypeDesc']['textEn'],
                                    'textAr': bouncedCheque['bcProductTypeDesc']['textAr'],
                                    'memberCode': bouncedCheque['bcCreditor']['memberCode'],
                                    'memberNameEN': bouncedCheque['bcCreditor']['memberNameEN'],
                                    'memberNameAR': bouncedCheque['bcCreditor']['memberNameAR'],
                                    'bcChequeNumber': bouncedCheque['bcChequeNumber'],
                                    'bcBalance': bouncedCheque['bcBalance'],
                                    'bcOutstandingBalance': bouncedCheque['bcOutstandingBalance'],
                                    'defaultStatusDescEn': bouncedCheque['bcDefaultStatuses']['defaultStatusDescEn'],
                                    'defaultStatusDescAr': bouncedCheque['bcDefaultStatuses']['defaultStatusDescAr'],
                                    'defaultStatusCode': bouncedCheque['bcDefaultStatuses']['defaultStatusCode'],
                                    'bcSetteledDate': bouncedCheque['bcSetteledDate'],
                                    'simah_cheques': rec.id
                                })
                            except ValueError:
                                print(f"Invalid input: '{bouncedCheque}' is not a valid integer.")

                    # ['Judgements']
                    if dic_data[0]['judgements']:
                        for judgement in dic_data[0]['judgements']:
                            try:
                                obj = rec.simahJudgement.create({
                                    'executionDate': judgement['executionDate'],
                                    'resolutionNumber': judgement['resolutionNumber'],
                                    'cityNameEn': judgement['cityNameEn'],
                                    'cityNameAr': judgement['cityNameAr'],
                                    'courtNameEn': judgement['courtNameEn'],
                                    'courtNameAr': judgement['courtNameAr'],
                                    'legalCaseNumber': judgement['legalCaseNumber'],
                                    'loadedDate': judgement['loadedDate'],
                                    'originalClaimedAmount': judgement['originalClaimedAmount'],
                                    'outstandingBalance': judgement['outstandingBalance'],
                                    'settlementDate': judgement['settlementDate'],
                                    'statusNameEn': judgement['statusNameEn'],
                                    'statusNameAr': judgement['statusNameAr'],
                                    'executionType': judgement['executionType'],
                                    'statusCode': judgement['statusCode'],
                                    'cityCode': judgement['cityCode'],
                                    'simah_judgement': rec.id
                                })
                            except ValueError:
                                print(f"Invalid input: '{judgement}' is not a valid integer.")

                    # ['Public Notice']
                    if dic_data[0]['publicNotices']:
                        for notice in dic_data[0]['publicNotices']:
                            try:
                                obj = rec.publicNotices.create({
                                    'dataLoad': notice['dataLoad'],
                                    'noticeType': notice['noticeType'],
                                    'publication': notice['publication'],
                                    'text': notice['text'],
                                    'public_notices': rec.id
                                })
                            except ValueError:
                                print(f"Invalid input: '{notice}' is not a valid integer.")

                    # ['Addresses']
                    if dic_data[0]['addresses']:
                        for address in dic_data[0]['addresses']:
                            try:
                                obj = rec.simahAddress.create({
                                    'adrsDateLoaded': address['adrsDateLoaded'],
                                    'adrsAddressLineFirstDescAr': address['adrsAddressLineFirstDescAr'],
                                    'adrsAddressLineFirstDescEn': address['adrsAddressLineFirstDescEn'],
                                    'adrsAddressLineSecondDescAr': address['adrsAddressLineSecondDescAr'],
                                    'adrsAddressLineSecondDescEn': address['adrsAddressLineSecondDescEn'],
                                    'adrsPOBox': address['adrsPOBox'],
                                    'adrsPostalCode': address['adrsPostalCode'],
                                    'adrsCityDescAr': address['adrsCityDescAr'],
                                    'adrsCityDescEn': address['adrsCityDescEn'],
                                    'addressID': address['adrsAddressTypes']['addressID'],
                                    'addressTypeCode': address['adrsAddressTypes']['addressTypeCode'],
                                    'addressNameAR': address['adrsAddressTypes']['addressNameAR'],
                                    'addressNameEN': address['adrsAddressTypes']['addressNameEN'],
                                    'buildingNumber': address['nationalAddress']['buildingNumber'],
                                    'streetAr': address['nationalAddress']['streetAr'],
                                    'streetEn': address['nationalAddress']['streetEn'],
                                    'districtAr': address['nationalAddress']['districtAr'],
                                    'districtEn': address['nationalAddress']['districtEn'],
                                    'additionalNumber': address['nationalAddress']['additionalNumber'],
                                    'unitNumber': address['nationalAddress']['unitNumber'],
                                    'simah_address': rec.id
                                })
                            except ValueError:
                                print(f"Invalid input: '{address}' is not a valid integer.")

                    # ['contacts']
                    if dic_data[0]['contacts']:
                        for contact in dic_data[0]['contacts']:
                            obj = rec.simahContact.create({
                                'conCode': contact['conCode'],
                                'conAreaCode': contact['conAreaCode'],
                                'conPhoneNumber': contact['conPhoneNumber'],
                                'conExtension': contact['conExtension'],
                                'contactNumberTypeCode': contact['conNumberTypes']['contactNumberTypeCode'],
                                'contactNumberTypeDescriptionAr': contact['conNumberTypes'][
                                    'contactNumberTypeDescriptionAr'],
                                'contactNumberTypeDescriptionEn': contact['conNumberTypes'][
                                    'contactNumberTypeDescriptionEn'],
                                'simah_contact': rec.id
                            })
                    # ['employers']
                    if dic_data[0]['employers']:
                        for employer in dic_data[0]['employers']:
                            try:
                                obj = rec.simahEmployee.create({
                                    'empEmployerNameDescAr': employer['empEmployerNameDescAr'],
                                    'empEmployerNameDescEn': employer['empEmployerNameDescEn'],
                                    'empOccupationDescAr': employer['empOccupationDescAr'],
                                    'empOccupationDescEn': employer['empOccupationDescEn'],
                                    'empDateOfEmployment': employer['empDateOfEmployment'],
                                    'empDateLoaded': employer['empDateLoaded'],
                                    'empIncome': employer['empIncome'],
                                    'empTotalIncome': employer['empTotalIncome'],
                                    'adrsDateLoaded': employer['empAddress']['adrsDateLoaded'],
                                    'adrsAddressLineFirstDescAr': employer['empAddress'][
                                        'adrsAddressLineFirstDescAr'],
                                    'adrsAddressLineFirstDescEn': employer['empAddress'][
                                        'adrsAddressLineFirstDescEn'],
                                    'adrsAddressLineSecondDescAr': employer['empAddress'][
                                        'adrsAddressLineSecondDescAr'],
                                    'adrsAddressLineSecondDescEn': employer['empAddress'][
                                        'adrsAddressLineSecondDescEn'],
                                    'adrsPOBox': employer['empAddress']['adrsPOBox'],
                                    'adrsPostalCode': employer['empAddress']['adrsPostalCode'],
                                    'adrsCityDescAr': employer['empAddress']['adrsCityDescAr'],
                                    'adrsCityDescEn': employer['empAddress']['adrsCityDescEn'],
                                    # 'addressID': employer['empAddress']['adrsAddressTypes']['addressID'],
                                    # 'addressTypeCode': employer['empAddress']['adrsAddressTypes']['addressTypeCode'],
                                    # 'addressNameAR': employer['empAddress']['adrsAddressTypes']['addressNameAR'],
                                    # 'addressNameEN': employer['empAddress']['adrsAddressTypes']['addressNameEN'],
                                    'buildingNumber': employer['empAddress']['nationalAddress']['buildingNumber'],
                                    'streetAr': employer['empAddress']['nationalAddress']['streetAr'],
                                    'streetEn': employer['empAddress']['nationalAddress']['streetEn'],
                                    'districtAr': employer['empAddress']['nationalAddress']['districtAr'],
                                    'districtEn': employer['empAddress']['nationalAddress']['districtEn'],
                                    'additionalNumber': employer['empAddress']['nationalAddress'][
                                        'additionalNumber'],
                                    'unitNumber': employer['empAddress']['nationalAddress']['unitNumber'],
                                    'employerStatusTypeCode': employer['empStatusType']['employerStatusTypeCode'],
                                    'employerStatusTypeDescAr': employer['empStatusType'][
                                        'employerStatusTypeDescAr'],
                                    'employerStatusTypeDescEn': employer['empStatusType'][
                                        'employerStatusTypeDescEn'],
                                    'simah_employee': rec.id
                                })
                            except ValueError:
                                print(f"Invalid input: '{employer}' is not a valid integer.")

                    # ['summaryInfo']
                    rec.summActiveCreditInstruments = dic_data[0]['summaryInfo']['summActiveCreditInstruments']
                    rec.summDefaults = dic_data[0]['summaryInfo']['summDefaults']
                    rec.summEarliestIssueDate = dic_data[0]['summaryInfo']['summEarliestIssueDate']
                    rec.summTotalLimits = dic_data[0]['summaryInfo']['summTotalLimits']
                    rec.summTotalGuaranteedLimits = dic_data[0]['summaryInfo']['summTotalGuaranteedLimits']
                    rec.summTotalLiablilites = dic_data[0]['summaryInfo']['summTotalLiablilites']
                    rec.summTotalGuaranteedLiablilites = dic_data[0]['summaryInfo']['summTotalGuaranteedLiablilites']
                    rec.summTotalDefaults = dic_data[0]['summaryInfo']['summTotalDefaults']
                    rec.summCurrentDelinquentBalance = dic_data[0]['summaryInfo']['summCurrentDelinquentBalance']
                    rec.summPreviousEnquires = dic_data[0]['summaryInfo']['summPreviousEnquires']
                    rec.summPreviousEnquiresThisMonth = dic_data[0]['summaryInfo']['summPreviousEnquiresThisMonth']
                    rec.summGuaranteedCreditInstruments = dic_data[0]['summaryInfo']['summGuaranteedCreditInstruments']
                    # ['score']
                    if dic_data[0]['score']:
                        for score in dic_data[0]['score']:
                            try:
                                obj_score = rec.simahScore.create({
                                    'score': score['score'],
                                    'minimumScore': score['minimumScore'],
                                    'maximumScore': score['maximumScore'],
                                    'error': score['error'],
                                    'scoreIndex': score['scoreIndex'],
                                    # 'scoreCardCode': score['scoreCard']['scoreCardCode'],
                                    # 'scoreCardDescAr': score['scoreCard']['scoreCardDescAr'],
                                    # 'scoreCardDescEn': score['scoreCard']['scoreCardDescEn'],
                                    'scoreReasonCodeName': score['reasonCodes'][0]['scoreReasonCodeName'],
                                    'scoreReasonCodeDescAr': score['reasonCodes'][0]['scoreReasonCodeDescAr'],
                                    'scoreReasonCodeDescEn': score['reasonCodes'][0]['scoreReasonCodeDescEn'],
                                    'simah_score': rec.id
                                })
                            except ValueError:
                                print(f"Invalid input: '{score}' is not a valid integer.")
                    # disclerText
                    rec.discTextDescAr = dic_data[0]['disclerText']['discTextDescAr']
                    rec.discTextDescEn = dic_data[0]['disclerText']['discTextDescEn']
            else:
                raise ValidationError(_('Error : "%s" ') % (dic_re.get('messages')))

    def action_salary_certificate_data(self):
        self.bool_field = True
        url = 'https://simahnew.free.beeceptor.com/cr'
        headers = {
            'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg3MkI3RjZCNjYyODM5NjVENDMyODYzNjk5MDA3OUQxNzlGMzBBQjUiLCJ0eXAiOiJKV1QiLCJ4NXQiOiJoeXRfYTJb09XWFVNb1kybVFCNTBYbnpDclUifQ.eyJuYmYiOjE3MDIyOTQ0NjgsImV4cCI6MTcwMjI5ODA2OCwiaXNzIjoiaHR0cHM6Ly9zcGlkcy5rc2FjYi5jb20uc2EvIiwiYXVkIjpbImh0dHBzOi8vc3BpZHMua3NhY2IuY29tLnNhL3Jlc291cmNlcyIsImJi',
            'Content-Type': 'application/json'
        }
        for rec in self:
            national_id = rec.id_number
            dob = rec.birth_of_date
            data = {"national_id": int(national_id), "dob": dob}
            response = requests.post(url, json=data, headers=headers, verify=False)
            print(response)
            try:
                dic_re = response.json()
                if response.status_code == 200:
                    pdf_file = dic_re.get("data")
                    print(pdf_file)
                    ir_values = {
                        'name': "Salary.pdf",
                        'type': 'binary',
                        'datas': pdf_file,
                        'store_fname': pdf_file,
                        'res_model': 'simah.simah',
                        'res_id': rec.id,
                        'mimetype': 'application/x-pdf',
                    }
                    data_id = self.env['ir.attachment'].create(ir_values)
                    self.write({
                        'salary_certificate_doc': pdf_file,
                        'doc_attachment_id': [(6, 0, [data_id.id])]
                    })
                else:
                    raise ValidationError(_('Error : "%s" ') % (dic_re.get('messages')))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")


class SimahCity(models.Model):
    _name = 'simah.city'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Simah City'

    name = fields.Char()
    city_id = fields.Integer()
    english_name = fields.Char()
    code = fields.Char()

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|', ('name', operator, name), ('english_name', operator, name),
                      ('code', operator, name), ('city_id', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


class Enquiries(models.Model):
    _name = 'simah.enquiries'
    _description = 'Simah Enquiries'

    simah = fields.Many2one('simah.simah', string='Simah Date')
    prevEnqDate = fields.Char(string='Date of Enquiry')
    active = fields.Boolean(default=True)
    # preEnqType
    enqTypeCode = fields.Char(string='Enquirer Type')
    enqTypeDescriptionAr = fields.Char(string='Type DescriptionAr')
    enqTypeDescriptionEn = fields.Char(string='TypeDescriptionEn')
    # prevEnqEnquirer
    memberCode = fields.Char(string='Enquirer')
    memberNameEN = fields.Char(string='Member NameEN')
    memberNameAR = fields.Char(string='Member NameAR')

    prevEnqMemberRef = fields.Char(string='Enq Member Ref')
    prevEnquirerName = fields.Char(string='Enquiry Name')
    prevEnquirerNameAr = fields.Char(string='Name')
    # prevEnqProductTypeDesc
    productId = fields.Integer(string='Product ID')
    code = fields.Char(string='Product Type')
    textEn = fields.Char(string='TextEn')
    textAr = fields.Char(string='TextAr')

    prevEnqAmount = fields.Integer(string='Amount')
    otherReason = fields.Char(string='Other Reason')


class creditInstrument(models.Model):
    _name = 'credit.instrument'
    _description = 'Credit Instrument'

    simah_simah = fields.Many2one('simah.simah', string='Simah Instrument')
    active = fields.Boolean(default=True)
    # ciCreditor
    memberCode = fields.Char(string='Creditor')
    memberNameEN = fields.Char(string='Member NameEN')
    memberNameAR = fields.Char(string='Member NameAR')
    # ciProductTypeDesc
    productId = fields.Char(string='Product Id')
    code = fields.Char(string='Product Type')
    textEn = fields.Char(string='text En')
    textAr = fields.Char(string='text Ar')

    ciAccountNumber = fields.Char(string='Account Number')
    ciLimit = fields.Float(string='Limit')
    ciIssuedDate = fields.Char(string='Issue Date')
    ciExpirationDate = fields.Char(string='Expiry Date')

    # ciStatus
    creditInstrumentStatusCode = fields.Char(string='Status')
    creditInstrumentStatusDescAr = fields.Char(string='credit Instrument StatusDescAr')
    creditInstrumentStatusDescEn = fields.Char(string='credit Instrument StatusDescEn')

    ciClosingDate = fields.Char(string='Close Date')
    ciTenure = fields.Integer(string='Tenure')

    # ciPaymentFrequency
    paymentFrequencyCodeDescEn = fields.Char(string='payment Frequency CodeDescEn')
    paymentFrequencyCodeDescAr = fields.Char(string='payment Frequency CodeDescAr')
    paymentFrequencyCodeName = fields.Char(string='payment Frequency')

    ciInstallmentAmount = fields.Float(string='Installment Amount')

    # ciSalaryAssignmentFlag
    salaryAssignmentFlagDescEn = fields.Char(string='salary Assignment FlagDescEn')
    salaryAssignmentFlagDescAr = fields.Char(string='salary Assignment FlagDescAr')
    salaryAssignmentFlagCode = fields.Char(string='salary Flag')

    # ciConsumerSecurityType
    consumerSecurityTypeDescEn = fields.Char(string='Consumer Security TypeDescEn')
    consumerSecurityTypeDescAr = fields.Char(string='Consumer Security TypeDescAr')
    consumerSecurityTypeCode = fields.Char(string='Consumer Security TypeCode')

    ciOutstandingBalance = fields.Float(string='Outstanding Balance')
    ciPastDue = fields.Float(string='Past Due')
    ciLastAmountPaid = fields.Float(string='Last Amount Paid')
    ciLastPaymentDate = fields.Char(string='Last Payment Date')
    ciAsOfDate = fields.Char(string='As Of Date')
    ciNextDueDate = fields.Char(string='Next Due Date')
    ciSummary = fields.Char(string='Last 24 Cycles')
    ciBalloonPayment = fields.Float(string='ciBalloonPayment')
    ciDownPayment = fields.Float(string='ciDownPayment')
    ciDispensedAmount = fields.Float(string='ciDispensedAmount')
    ciMaxInstalmentAmount = fields.Float(string='ciMaxInstalmentAmount')
    # ciSubProduct
    nameEn = fields.Char(string='NameEn')
    nameAr = fields.Char(string='NameAr')
    ciSubProduct_code = fields.Char(string='Code')

    # multiInstalmentDetails
    multi_instalment_details_ids = fields.One2many('multi.instalment.details', 'credit_instrument_id',
                                                   string="multi Instalment Details")

    jointApplicantDetail = fields.Char(string='joint Applicant Detail')
    ciAverageInstallmentAmount = fields.Float(string='ciAverage Installment Amount')
    ciNumberOfApplicants = fields.Integer(string='ciNumber Of Applicants')

    # jointApplicantFlag
    jointApplicantFlag_code = fields.Char(string='code')
    jointApplicantFlag_textEn = fields.Char(string='textEn')
    jointApplicantFlag_textAr = fields.Char(string='textAr')

    total_installment = fields.Float(compute='sum_total_installmnt', store=True)
    credit_value = fields.Float(compute='sum_total_installmnt', store=True)
    ciInstallment = fields.Float()

    @api.depends('code', 'creditInstrumentStatusCode', 'ciInstallmentAmount', 'ciLimit',
                 'ciInstallment')
    def sum_total_installmnt(self):
        for rec in self:
            if rec.code != 'ADFL' and 'AQAR' and 'COM' and 'LND' and 'MBL' and 'NET' and 'PE' and 'RCSR' and 'SMS' and 'WAT' and 'HBIL':
                if rec.creditInstrumentStatusCode != 'C':
                    if rec.code == 'MBL' or rec.ciClosingDate != 0:
                        rec.total_installment = 0
                    elif rec.code == 'CHC':
                        rec.credit_value = rec.ciLimit * 0.05
                        rec.total_installment = rec.credit_value
                    elif rec.code == 'CRC':
                        rec.credit_value = rec.ciLimit * 0.05
                        rec.total_installment = rec.credit_value
                    elif rec.code == 'LCRC':
                        rec.credit_value = rec.ciLimit * 0.05
                        rec.total_installment = rec.credit_value
                    elif rec.code == 'CDC':
                        rec.credit_value = rec.ciLimit * 0.05
                        rec.total_installment = rec.credit_value
                    else:
                        rec.total_installment = rec.ciInstallmentAmount
                elif rec.creditInstrumentStatusCode == 's':
                    rec.total_installment = 0
                else:
                    rec.total_installment = 0
            else:
                pass


class MemberNarratives(models.Model):
    _name = 'simah.narrative'  # Define the technical name of the model
    _description = 'Simah Narrative'  # Provide a human-readable description for the model

    simah_narr = fields.Many2one('simah.simah',
                                 string='Simah Narrative')  # Define a Many2one relation to 'simah.simah', linking this narrative to a Simah record
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active; default is True

    # Narrative Details
    narrDateLoaded = fields.Char(
        string='Narrative Date Loaded')  # Field to store the date when the narrative data was loaded
    memberCode = fields.Char(string='Member Code')  # Field to store the member code
    memberNameEN = fields.Char(string='Member Name EN')  # Field to store the member name in English
    memberNameAR = fields.Char(string='Member Name AR')  # Field to store the member name in Arabic
    narrativeTypeDescAr = fields.Char(
        string='Narrative Type DescAr')  # Field to store the narrative type description in Arabic
    narrativeTypeDescEn = fields.Char(
        string='Narrative Type DescEn')  # Field to store the narrative type description in English
    narrativeTypeCode = fields.Char(string='Narrative Type Code')  # Field to store the narrative type code

    # Narrative Text
    narrTextDescAr = fields.Char(string='Text DescAr')  # Field to store the narrative text in Arabic
    narrTextDescEn = fields.Char(string='Text DescEn')  # Field to store the narrative text in English


class MultiInstalmentDetails(models.Model):
    _name = 'multi.instalment.details'  # Define the technical name of the model
    _description = 'Multi Instalment Details'  # Provide a human-readable description for the model

    startDate = fields.Char(string='Start Date')  # Field to store the start date of the instalment
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active; default is True
    instalmentAmount = fields.Float(string='Instalment Amount')  # Field to store the amount of each instalment
    credit_instrument_id = fields.Many2one('credit.instrument',
                                           string='Credit Instrument')  # Define a Many2one relation to 'credit.instrument', linking this instalment to a credit instrument


class PersonalNarratives(models.Model):
    _name = 'personal.narratives'  # Define the technical name of the model
    _description = 'Personal Narratives'  # Provide a human-readable description for the model

    simah_id = fields.Many2one('simah.simah',
                               string='Personal Narratives')  # Define a Many2one relation to 'simah.simah', linking this narrative to a Simah record
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active; default is True

    # Narrative Details
    narrDateLoaded = fields.Char(
        string='Narrative Date Loaded')  # Field to store the date when the narrative data was loaded
    narrativeTypeDescAr = fields.Char(
        string='Narrative Type DescAr')  # Field to store the narrative type description in Arabic
    narrativeTypeDescEn = fields.Char(
        string='Narrative Type DescEn')  # Field to store the narrative type description in English
    narrativeTypeCode = fields.Char(string='Narrative Type Code')  # Field to store the narrative type code

    # Narrative Text
    narrTextDescAr = fields.Char(string='Text DescAr')  # Field to store the narrative text in Arabic
    narrTextDescEn = fields.Char(string='Text DescEn')  # Field to store the narrative text in English


class Addresses(models.Model):
    _name = 'simah.addresses'  # Define the technical name of the model
    _description = 'Simah Address'  # Provide a human-readable description for the model

    simah_address = fields.Many2one('simah.simah',
                                    string='Simah Address')  # Define a Many2one relation to 'simah.simah', linking this address to a Simah record

    adrsDateLoaded = fields.Char(string='Date Loaded')  # Field to store the date when the address data was loaded
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active; default is True

    # Fields for address types
    addressID = fields.Integer(string='Address ID')  # Field to store the unique address ID
    addressTypeCode = fields.Char(string='Type Code')  # Field to store the type code for the address
    addressNameAR = fields.Char(string='NameAR')  # Field to store the address name in Arabic
    addressNameEN = fields.Char(string='NameEN')  # Field to store the address name in English

    # Fields for address lines
    adrsAddressLineFirstDescAr = fields.Char(
        string='Address LineAr')  # Field to store the first line of the address in Arabic
    adrsAddressLineFirstDescEn = fields.Char(
        string='Address LineEn')  # Field to store the first line of the address in English
    adrsAddressLineSecondDescAr = fields.Char(
        string='Address LineAr')  # Field to store the second line of the address in Arabic
    adrsAddressLineSecondDescEn = fields.Char(
        string='Address LineEn')  # Field to store the second line of the address in English

    adrsPOBox = fields.Char(string='PO Box')  # Field to store the PO Box number
    adrsPostalCode = fields.Char(string='Postal Code')  # Field to store the postal code

    adrsCityDescAr = fields.Char(string='City Ar')  # Field to store the city name in Arabic
    adrsCityDescEn = fields.Char(string='City En')  # Field to store the city name in English

    # Fields for national address
    buildingNumber = fields.Char(string='Building Number')  # Field to store the building number
    streetAr = fields.Char(string='StreetAr')  # Field to store the street name in Arabic
    streetEn = fields.Char(string='StreetEn')  # Field to store the street name in English
    districtAr = fields.Char(string='DistrictAr')  # Field to store the district name in Arabic
    districtEn = fields.Char(string='DistrictEn')  # Field to store the district name in English
    additionalNumber = fields.Char(
        string='Additional Number')  # Field to store any additional number related to the address
    unitNumber = fields.Char(string='Unit Number')  # Field to store the unit number


class PrimaryDefault(models.Model):
    _name = 'simah.default'  # Define the technical name of the model
    _description = 'Simah Default'  # Provide a human-readable description for the model

    simah_default = fields.Many2one('simah.simah',
                                    string='Primary Default')  # Define a Many2one relation to 'simah.simah', linking this primary default to a Simah record
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active; default is True

    # Fields for product type description
    productId = fields.Char('Product Id')  # Field to store the product ID associated with the primary default
    code = fields.Char('Code')  # Field to store a code related to the primary default
    textEn = fields.Char('textEn')  # Field to store the text description in English
    textAr = fields.Char('textAr')  # Field to store the text description in Arabic

    pDefAccountNo = fields.Char('pDefAccount No')  # Field to store the account number related to the primary default

    # Fields for creditor information
    memberCode = fields.Char('memberCode')  # Field to store the member code
    memberNameEN = fields.Char('memberNameEN')  # Field to store the member name in English
    memberNameAR = fields.Char('memberNameAR')  # Field to store the member name in Arabic

    pDefDateLoaded = fields.Char('pDef Date Loaded')  # Field to store the date when the primary default data was loaded
    pDefOriginalAmount = fields.Char(
        'pDef Original Amount')  # Field to store the original amount related to the primary default
    pDefOutstandingBalance = fields.Char(
        'pDef Outstanding Balance')  # Field to store the outstanding balance related to the primary default

    # Fields for default statuses
    defaultStatusDescEn = fields.Char(
        'default Status DescEn')  # Field to store the default status description in English
    defaultStatusDescAr = fields.Char(
        'default Status DescAr')  # Field to store the default status description in Arabic
    defaultStatusCode = fields.Char('default Status Code')  # Field to store the default status code

    pDefSetteledDate = fields.Char('pDef Setteled Date')  # Field to store the date when the primary default was settled


class GuarantorDefault(models.Model):
    _name = 'guarantor.default'  # Define the technical name of the model
    _description = 'Guarantor Default'  # Provide a human-readable description for the model

    guarantor_default = fields.Many2one('simah.simah',
                                        string='Guarantor Default')  # Define a Many2one relation to 'simah.simah', linking this guarantor default to a Simah record
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active; default is True

    # Fields for product type description
    productId = fields.Char('Product Id')  # Field to store the product ID associated with the guarantor default
    code = fields.Char('Code')  # Field to store a code related to the guarantor default
    textEn = fields.Char('textEn')  # Field to store the text description in English
    textAr = fields.Char('textAr')  # Field to store the text description in Arabic

    gDefAccountNo = fields.Char('gDef Account No')  # Field to store the account number related to the guarantor default

    # Fields for creditor information
    memberCode = fields.Char('memberCode')  # Field to store the member code
    memberNameEN = fields.Char('memberNameEN')  # Field to store the member name in English
    memberNameAR = fields.Char('memberNameAR')  # Field to store the member name in Arabic

    gDefDateLoaded = fields.Char(
        'gDef Date Loaded')  # Field to store the date when the guarantor default data was loaded
    gDefOriginalAmount = fields.Char(
        'gDef Original Amount')  # Field to store the original amount related to the guarantor default
    gDefOutstandingBalance = fields.Char(
        'gDef Outstanding Balance')  # Field to store the outstanding balance related to the guarantor default

    # Fields for default statuses
    defaultStatusDescEn = fields.Char(
        'default Status DescEn')  # Field to store the default status description in English
    defaultStatusDescAr = fields.Char(
        'default Status DescAr')  # Field to store the default status description in Arabic
    defaultStatusCode = fields.Char('default Status Code')  # Field to store the default status code

    gDefSetteledDate = fields.Char(
        'gDef Setteled Date')  # Field to store the date when the guarantor default was settled


class BouncedCheque(models.Model):
    _name = 'simah.cheques'  # Define the technical name of the model
    _description = 'Simah Cheques'  # Provide a human-readable description for the model

    simah_cheques = fields.Many2one('simah.simah',
                                    string='bounced Cheques')  # Define a Many2one relation to 'simah.simah', linking this cheque to a Simah record
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active; default is True

    bcCheqDateLoaded = fields.Date('bcCheqDate Loaded')  # Field to store the date when the cheque data was loaded

    # Fields for product type description
    productId = fields.Char('Product Id')  # Field to store the product ID associated with the cheque
    code = fields.Char('Code')  # Field to store a code related to the cheque
    textEn = fields.Char('textEn')  # Field to store the text description in English
    textAr = fields.Char('textAr')  # Field to store the text description in Arabic

    # Fields for creditor information
    memberCode = fields.Char('memberCode')  # Field to store the member code
    memberNameEN = fields.Char('memberNameEN')  # Field to store the member name in English
    memberNameAR = fields.Char('memberNameAR')  # Field to store the member name in Arabic

    bcChequeNumber = fields.Char('bc ChequeNumber')  # Field to store the cheque number
    bcBalance = fields.Char('bc Balance')  # Field to store the balance of the cheque
    bcOutstandingBalance = fields.Char('bcOutstanding Balance')  # Field to store the outstanding balance of the cheque

    # Fields for default statuses
    defaultStatusDescEn = fields.Char('defaultStatusDescEn')  # Field to store the default status description in English
    defaultStatusDescAr = fields.Char('defaultStatusDescAr')  # Field to store the default status description in Arabic
    defaultStatusCode = fields.Char('defaultStatusCode')  # Field to store the default status code

    bcSetteledDate = fields.Char('bc Setteled Date')  # Field to store the date when the cheque was settled


class SimahJudgement(models.Model):
    _name = 'simah.judgement'  # Define the technical name of the model
    _description = 'Simah Judgement'  # Provide a human-readable description for the model

    simah_judgement = fields.Many2one('simah.simah',
                                      string='bounced Judgement')  # Define a Many2one relation to 'simah.simah', linking this judgement to a Simah record
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active; default is True

    # Fields specific to Simah Judgement
    executionDate = fields.Char('execution Date')  # Field to store the date when the judgement was executed
    resolutionNumber = fields.Char('resolution Number')  # Field to store the resolution number of the judgement
    cityNameEn = fields.Char('city NameEn')  # Field to store the name of the city in English
    cityNameAr = fields.Char('city NameAr')  # Field to store the name of the city in Arabic
    courtNameEn = fields.Char('court NameEn')  # Field to store the name of the court in English
    courtNameAr = fields.Char('court NameAr')  # Field to store the name of the court in Arabic
    legalCaseNumber = fields.Char(
        'legal Case Number')  # Field to store the legal case number associated with the judgement
    loadedDate = fields.Char('loaded Date')  # Field to store the date when the judgement data was loaded
    originalClaimedAmount = fields.Char(
        'original Claimed Amount')  # Field to store the original amount claimed in the case
    outstandingBalance = fields.Char('outstanding Balance')  # Field to store the outstanding balance remaining
    settlementDate = fields.Char('settlement Date')  # Field to store the date when the settlement occurred
    statusNameEn = fields.Char('status NameEn')  # Field to store the status name in English
    statusNameAr = fields.Char('status NameAr')  # Field to store the status name in Arabic
    executionType = fields.Char('execution Type')  # Field to store the type of execution of the judgement
    statusCode = fields.Char('status Code')  # Field to store a code representing the status of the judgement
    cityCode = fields.Char('city Code')  # Field to store a code representing the city where the court is located


class PublicNotices(models.Model):
    _name = 'public.notices'  # Define the technical name of the model
    _description = 'Public Notices'  # Provide a human-readable description for the model

    public_notices = fields.Many2one('simah.simah',
                                     string='Public Notices')  # Define a Many2one relation to the 'simah.simah' model, linking to public notices
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active; default is True

    # Fields specific to Public Notices
    dataLoad = fields.Char(
        string='Data Load')  # Field to store information about the data load related to the public notice
    noticeType = fields.Char(string='Notice Type')  # Field to store the type of the notice (e.g., legal, public, etc.)
    publication = fields.Char(
        string='Publication')  # Field to store the name of the publication where the notice appears
    text = fields.Char(string='Text')  # Field to store the actual text of the public notice


class SimahContacts(models.Model):
    _name = 'simah.contact'  # Define the technical name of the model
    _description = 'Simah Contact'  # Provide a human-readable description for the model

    simah_contact = fields.Many2one('simah.simah',
                                    string='Contact')  # Define a Many2one relation to the 'simah.simah' model
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active, default is True

    # Contact Number Types
    contactNumberTypeCode = fields.Char(string='Type Code')  # Field for the type code of the contact number
    contactNumberTypeDescriptionAr = fields.Char(
        string='Phone Number Type')  # Field for the phone number type description in Arabic
    contactNumberTypeDescriptionEn = fields.Char(
        string='Type DescriptionEn')  # Field for the phone number type description in English
    conCode = fields.Char(string='Code')  # Field for a code associated with the contact number
    conAreaCode = fields.Char(string='Area Code')  # Field for the area code of the contact number
    conPhoneNumber = fields.Char(string='Phone Number')  # Field for the actual phone number
    conExtension = fields.Char(string='Extension')  # Field for the phone number extension


class SimahEmployee(models.Model):
    _name = 'simah.employee'  # Define the technical name of the model
    _description = 'Simah Employee'  # Provide a human-readable description for the model

    simah_employee = fields.Many2one('simah.simah',
                                     string='Employee')  # Define a Many2one relation to the 'simah.simah' model
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active, default is True

    # Employers
    empEmployerNameDescAr = fields.Char(
        string='Employer Name DescAr')  # Field for the employer name description in Arabic
    empEmployerNameDescEn = fields.Char(
        string='Employer Name DescEn')  # Field for the employer name description in English
    empOccupationDescAr = fields.Char(string='Occupation DescAr')  # Field for the occupation description in Arabic
    empOccupationDescEn = fields.Char(string='Occupation DescEn')  # Field for the occupation description in English
    empDateOfEmployment = fields.Char(string='Date Of Employment')  # Field for the date of employment
    empDateLoaded = fields.Char(string='Date Loaded')  # Field for the date when the data was loaded
    empIncome = fields.Float(string='Income')  # Field for the employee's income
    empTotalIncome = fields.Float(string='Total Income')  # Field for the employee's total income

    # Address Details
    adrsDateLoaded = fields.Char(string='Date Loaded')  # Field for the date when the address data was loaded

    # Address Types
    addressID = fields.Integer(string='Address ID')  # Field for the address ID
    addressTypeCode = fields.Char(string='Address Type')  # Field for the address type code
    addressNameAR = fields.Char(string='Address NameAR')  # Field for the address name in Arabic
    addressNameEN = fields.Char(string='Address NameEN')  # Field for the address name in English
    adrsAddressLineFirstDescAr = fields.Char(
        string='Address Line 1 DescAr')  # Field for the first line of the address in Arabic
    adrsAddressLineFirstDescEn = fields.Char(
        string='Address Line 1 DescEn')  # Field for the first line of the address in English
    adrsAddressLineSecondDescAr = fields.Char(
        string='Address Line 2 DescAr')  # Field for the second line of the address in Arabic
    adrsAddressLineSecondDescEn = fields.Char(
        string='Address Line 2 DescEn')  # Field for the second line of the address in English
    adrsPOBox = fields.Integer(string='PO Box')  # Field for the PO Box number
    adrsPostalCode = fields.Integer(string='Postal Code')  # Field for the postal code
    adrsCityDescAr = fields.Char(string='City DescAr')  # Field for the city description in Arabic
    adrsCityDescEn = fields.Char(string='City DescEn')  # Field for the city description in English

    # National Address Details
    buildingNumber = fields.Integer(string='Building Number')  # Field for the building number
    streetAr = fields.Char(string='StreetAr')  # Field for the street name in Arabic
    streetEn = fields.Char(string='StreetEn')  # Field for the street name in English
    districtAr = fields.Char(string='DistrictAr')  # Field for the district name in Arabic
    districtEn = fields.Char(string='DistrictEn')  # Field for the district name in English
    additionalNumber = fields.Integer(string='Additional Number')  # Field for any additional number
    unitNumber = fields.Integer(string='Unit Number')  # Field for the unit number

    # Employment Status Type
    employerStatusTypeCode = fields.Char(string='Type')  # Field for the employer status type code
    employerStatusTypeDescAr = fields.Char(
        string='Status Type DescAr')  # Field for the status type description in Arabic
    employerStatusTypeDescEn = fields.Char(
        string='Status Type DescEn')  # Field for the status type description in English


class SimahScore(models.Model):
    _name = 'simah.score'  # Define the technical name of the model
    _description = 'Simah Score'  # Provide a human-readable description for the model

    simah_score = fields.Many2one('simah.simah',
                                  string='Score')  # Define a Many2one relation to the 'simah.simah' model
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active, default is True
    score = fields.Float()  # Field to store the score value
    minimumScore = fields.Float('Minimum Score')  # Field to store the minimum score value
    maximumScore = fields.Float('Maximum Score')  # Field to store the maximum score value
    scoreIndex = fields.Float('Score Index')  # Field to store the score index
    error = fields.Char('Error')  # Field to store any error message related to the score

    # ScoreCard fields
    scoreCardCode = fields.Char('Score Card Code')  # Field to store the score card code
    scoreCardDescAr = fields.Char('Score Card DescAr')  # Field to store the score card description in Arabic
    scoreCardDescEn = fields.Char('Score Card DescEn')  # Field to store the score card description in English

    # ScoreReason fields
    scoreReasonCodeName = fields.Char('Score Reason Code Name')  # Field to store the score reason code name
    scoreReasonCodeDescAr = fields.Char(
        'Score Reason Code DescAr')  # Field to store the score reason code description in Arabic
    scoreReasonCodeDescEn = fields.Char(
        'Score Reason Code DescEn')  # Field to store the score reason code description in English
    simahScoreCodes = fields.One2many('simah.reason.code', 'simah_score_id',
                                      string="Simah Score Codes")  # Define a One2many relation to the 'simah.reason.code' model


class SimahReasonCodes(models.Model):
    _name = 'simah.reason.code'  # Define the technical name of the model
    _description = 'Simah Reason Code'  # Provide a human-readable description for the model

    scoreReasonCodeName = fields.Char('Score Reason Code Name')  # Field to store the name of the score reason code
    scoreReasonCodeDescAr = fields.Char(
        'Score Reason Code DescAr')  # Field to store the description of the score reason code in Arabic
    scoreReasonCodeDescEn = fields.Char(
        'Score Reason Code DescEn')  # Field to store the description of the score reason code in English
    simah_score_id = fields.Many2one('simah.score')  # Define a Many2one relation to the 'simah.score' model
    active = fields.Boolean(default=True)  # Boolean field to indicate if the record is active, default is True


class SimahExpense(models.Model):
    _name = 'simah.expense'  # Define the technical name of the model
    _description = 'Simah Expense'  # Provide a human-readable description for the model

    simah_expense = fields.Many2one('simah.simah',
                                    string='Expense')  # Define a Many2one relation to the 'simah.simah' model, named 'Expense'

    # Define fields for storing expense-related information

    nameEn = fields.Char(string='NameEn')  # Field to store the name of the expense in English
    nameAr = fields.Char(string='NameAr')  # Field to store the name of the expense in Arabic
    valueUsedIncaluculation = fields.Float(string='value calculation')  # Field to store the value used in calculations
    valueDeclaredByCustomer = fields.Float(
        string='value By Customer')  # Field to store the value declared by the customer
    outputValue = fields.Float(string='output Value')  # Field to store the output value of the expense
    isVerified = fields.Boolean(string='isVerified')  # Boolean field to indicate if the expense has been verified
