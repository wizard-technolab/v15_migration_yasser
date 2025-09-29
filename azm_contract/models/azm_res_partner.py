# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
import os
import requests
import base64
import hmac
import hashlib
import calendar
import time
import logging
import json
import uuid
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

# TEST API INFO
TEST_API_KEY = 'IVna85r3xpW0lABdMNyLTgmhQS7Xo4d72t9vKo4YSeV/IQlsYXnmgK+lUD9LDj5tiyZ50MuveNvjcsy6km/SdosuAw8XqAbtlYdz5unxSSQ9jvylxZIqlrENLQKcpIZl42mdqymylKPo5ZVGj3yp7+dl/gfCXhjwNdqd048CWQA='
TEST_CLIENT_ID = 'tMNpcL0lOWOhAzDFz+QG/73Y3YGKf5Kvew6gC8rQnkRHwQGoaf+4og=='
TEST_SECRET_KEY = 'vgKFx9HdyqW+cno9x4Q2CginJE1bu/O8/2xOZQqj/ysf6oOIwDxTnixa+gWQ4YpoQ6x0BlUPwvci+6B7I25n++fiFoxoz1zWAGnxZt/hRTYFis4v/00D2HkY9j2wvaPjcYkVVHwjbxYrJIL7XC3u3TkRpnoO/VQ1MW0vJMJ3Rwer2uvRyQoUuKwp+HNc0BrHgVC2AAZDADO44wEaqO/7NQMvyyxmlJfFCcUenX1Ba6ezE71ZGkQKq3OsiaPveGJfTyUnCkeW1w5F28foVQWPRc1KyoV+8Fr2+j5GT59E+TdL0VvzFO2yQ0S6jmovLxp15lYpHiFB/jfYyNDBSXTxsA=='
TEST_DOMAIN = "api-sandbox.contracts.sa"

# PROD API INFO
PROD_API_KEY = '1KX2h5qa9RGe3tFi+hngkaP691Y0ftpPDB29sSFkfTDn3E4Fzj9xkbOIlRrih23tfxC0JDdtyeg5T/NrX7qN7E+necf62ZaOVxY7IpyP9t7fdT6pvq0ucm5Dw/E3Bs1RVbSmd/JuOgveE+b7fYlayQjfIKomsU7A/pICcPNcwEk='
PROD_CLIENT_ID = 'U/ibNj9li5JOpuGAyP72gncPF6arzd9P0BRpSOmMlvws+5c0zN2PSw=='
PROD_SECRET_KEY = "efON+pTP3zuclnnlNvIO2Ln5BXuTTMxnONT2BWF8mGlDL5MA8/GCTcuplbLvI+vSs/Wu0ariX2nHu+bmvbEUxtdP7yeLPVR/8gQT08aAFc6uMCrn1+QhCrdfUUDKgLILfzZvJXnAdmdwWkxUX6zwDBL8yqiWAMPlMTMwTnuzeadgXL1U4tiy0os1EcHGRyCrKN09VejOIHaWgNQoCc6HPyTqZJpqKa1BaIOB+lKa7YDFmTLmkm/1Bds29hMtmrmhQCpqAR6x8bR+VZcanaDuZJfTzlnwJZQb2Y3XqJhu7RamNpcU7N1r2IuR3sXwjSOqYjL3SKlxHWC4MghnUZmD/A=="
PROD_DOMAIN = "api.contracts.sa"

IS_TEST_MODE = os.getenv('CONTRACTS_SA_TEST', False)

API_KEY = IS_TEST_MODE and TEST_API_KEY or PROD_API_KEY
SECRET_KEY = IS_TEST_MODE and TEST_SECRET_KEY or PROD_SECRET_KEY
CLIENT_ID = IS_TEST_MODE and TEST_CLIENT_ID or PROD_CLIENT_ID
API_DOMAIN = IS_TEST_MODE and TEST_DOMAIN or PROD_DOMAIN

TAWARUQ_TYPE_ID = 1


class LoanOrder(models.Model):
    _inherit = 'loan.order'
    _description = 'Contract Model inherit in loan order'

    contractDocument = fields.Binary(string='Attachment')
    signedContractDocument = fields.Binary(string='Signed Contract')
    contractName = fields.Char(string='File Name')
    beneficiaryRegionCode = fields.Char(string='beneficiary RegionCode', default=1)
    responseTimeInMinutes = fields.Char(string='response TimeInMinutes', default=5)
    lang = fields.Char(string='Lang', default='string')
    signatureLang = fields.Char(string='Signature Lang', default='string')
    shareApprovalURL = fields.Char(string='share ApprovalURL', default=True)
    isSignatureMethodFingerprint = fields.Char(string='isSignature Method Fingerprint', default=True)
    isReadOnly = fields.Char(string='IsReadOnly', default=True)
    contractName = fields.Char(string='Contract Name')
    contractNumber = fields.Char(string='Contract Number')
    contractBeneficiaries = fields.Char(string='Contract Beneficiaries')
    allBeneficiaries = fields.Many2many('bebeficiary.integration', string='New Name')
    nameEN = fields.Char(related='name.name', string='English Name')
    res_name = fields.Char(string="Response Name")
    res_name_ar = fields.Char(string="Response Name AR")
    res_email = fields.Char(string="Response Email")
    res_mobile = fields.Char(string="Response Mobile")
    res_identification_id = fields.Char(string="Response ID Number")
    # Contract endpoint fields
    req_contract_no = fields.Char(string="Contract No")
    res_customerCR = fields.Char(string="Customer CR")
    res_contractNumber = fields.Char(string="Contract Number")
    res_beneficiaryIDNumbers = fields.Char(string="Beneficiary Number")
    res_contractStatusCode = fields.Char(string="Status Code")
    res_createdOn = fields.Char(string="Created On")
    res_signDate = fields.Char(string="Sign Date")
    res_unSignFile = fields.Binary(string="File")
    response_file_link = fields.Char(string="File sharing link")
    response_unSignFileLink = fields.Char(string="UnSign File Link")
    contract_name = fields.Char(compute='_compute_contract_name')
    contract_name_signed = fields.Char(compute='_compute_contract_name')
    sanad_group_ids = fields.One2many('sanad.group.integration', 'loan_id', string="Sanad Groups")

    def _compute_contract_name(self):
        for r in self:
            r.contract_name = f'{self.seq_num or self.id}.pdf'
            r.contract_name_signed = f'{self.seq_num or self.id} Signed.pdf'

    def write_file_from_report(self):
        self.ensure_one()
        tawaruq_report = 'loan.contract_loan_full_report'
        murabaha_report = 'loan.contract_loan_full_report_murabaha'
        report = self.loan_type.report_id
        if not report:
            xml_id = self.loan_type.id == TAWARUQ_TYPE_ID and tawaruq_report or murabaha_report
            report = self.env.ref(xml_id)
        report_output = report._render_qweb_pdf(res_ids=[self.id])
        self.write({
            'contractDocument': base64.b64encode(report_output[0]),
        })

    def print_file(self):
        print(self.contractDocument)

    def action_one_contract(self):
        current_GMT = time.gmtime()
        ############ get contract by number ##################
        # self.req_contract_no= 'test10'
        h1 = '''{\"contractNo\":\"'''
        data = str(h1) + self.req_contract_no + '"}'
        request_endpoint = '''/api/v2/Contract/Get/''' + self.req_contract_no
        request_method = "GET"
        connection_url = API_DOMAIN
        # timestamp = "1586345122"
        timestamp = str(calendar.timegm(current_GMT))
        secret_key = SECRET_KEY
        encoded_data = base64.b64encode(bytes(data, 'utf_8')).decode()
        message = '{0}\n{1}\n{2}\nt={3}&ed={4}'.format(request_method, connection_url, request_endpoint, timestamp,
                                                       encoded_data)
        signature = hmac.new(bytes(secret_key, 'utf_8'), msg=bytes(message, 'utf_8'), digestmod=hashlib.sha256).digest()
        calculated_signature = base64.b64encode(signature).decode()
        print(calculated_signature)
        print(signature)

        ################################### Code #######################################

        # BASE_URL = 'https://api-sandbox.contracts.sa/api/v2/Contract/Get/202200009'
        BASE_URL = f'https://{API_DOMAIN}/api/v2/Contract/Get/{self.req_contract_no}'
        headers = {
            'content-type': 'application/json',
            'X-Contracts-Timestamp': str(calendar.timegm(current_GMT)),
            'X-Contracts-ClientId': CLIENT_ID,
            'X-Contracts-APIKey': API_KEY,
            'X-Contracts-Signature': calculated_signature}
        if self.req_contract_no:
            response_string = ''
            response = requests.get(BASE_URL, headers=headers)
            res = json.loads(response.text)
            if response.status_code == 200:
                f_res = res.get('data')
                self.res_customerCR = f_res.get('customerCR')
                self.res_contractNumber = f_res.get('contractNumber')
                self.res_beneficiaryIDNumbers = f_res.get('beneficiaryIDNumbers')
                if f_res.get('contractStatusCode') == '2':
                    response_string = 'Need Beneficiary Approval'
                if f_res.get('contractStatusCode') == '1':
                    response_string = 'Signed'
                if f_res.get('contractStatusCode') == '6':
                    response_string = 'Canceled'
                self.res_contractStatusCode = response_string
                self.res_createdOn = f_res.get('createdOn')
                self.res_signDate = f_res.get('signDate')
                self.res_unSignFile = f_res.get('unSignFile')
            else:
                raise ValidationError(_('Error : "%s" ') % (res.get('messages')))
        else:
            raise ValidationError(_('This Customer has no uploaded contract before'))

    def action_one_beneficiary(self):
        current_GMT = time.gmtime()
        ############ get contract by number ##################
        h1 = '''{\"idNumber\":\"'''
        data = str(h1) + self.identification_id + '"}'
        request_endpoint = '''/api/v1/Beneficiary/''' + self.identification_id
        _logger.info(":::::::::::::::", request_endpoint)
        request_method = "GET"
        connection_url = API_DOMAIN
        timestamp = str(calendar.timegm(current_GMT))
        secret_key = SECRET_KEY
        encoded_data = base64.b64encode(bytes(data, 'utf_8')).decode()

        message = '{0}\n{1}\n{2}\nt={3}&ed={4}'.format(request_method, connection_url, request_endpoint, timestamp,
                                                       encoded_data)
        signature = hmac.new(bytes(secret_key, 'utf_8'), msg=bytes(message, 'utf_8'), digestmod=hashlib.sha256).digest()
        calculated_signature = base64.b64encode(signature).decode()

        ################################### Code #######################################

        BASE_URL = f'https://{API_DOMAIN}/api/v1/Beneficiary/{self.identification_id}'
        headers = {
            'content-type': 'application/json',
            'X-Contracts-Timestamp': str(calendar.timegm(current_GMT)),
            'X-Contracts-ClientId': CLIENT_ID,
            'X-Contracts-APIKey': API_KEY,
            'X-Contracts-Signature': calculated_signature}

        response = requests.get(BASE_URL, headers=headers)
        res = json.loads(response.text)
        f_res = res.get('data')
        if response.status_code == 200:
            self.res_name = f_res.get('name')
            self.res_name_ar = f_res.get('nameAr')
            self.res_email = f_res.get('email')
            self.res_mobile = f_res.get('mobile')
            self.res_identification_id = f_res.get('idNumber')

        else:
            raise ValidationError(_('Error : "%s" ') % (res.get('messages')))

    def action_cancel_contract(self):
        return

    def _get_contracts_sa_header(self, payload, domain, path, method="POST", is_json=True):
        timestamp = str(calendar.timegm(time.gmtime()))
        encoded_data = base64.b64encode(bytes(payload, 'utf_8')).decode()
        message = f'{method}\n{domain}\n{path}\nt={timestamp}&ed={encoded_data}'
        signature = hmac.new(bytes(SECRET_KEY, 'utf_8'), msg=bytes(message, 'utf_8'), digestmod=hashlib.sha256).digest()
        calculated_signature = base64.b64encode(signature).decode()

        res = {
            'X-Contracts-Timestamp': timestamp,
            'X-Contracts-ClientId': CLIENT_ID,
            'X-Contracts-APIKey': API_KEY,
            'X-Contracts-Signature': calculated_signature,
        }
        if (is_json):
            res.update({
                'Content-Type': 'application/json',
            })
        return res

    def _handle_contracts_payload(self, payload):
        # NOTE: separators are very important, otherwise the signature won't be correct because default separator includes spaces after the comma. Also ensure_ascii is important because we do not want Arabic characters to be encoded as with \u
        payload_to_sign = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        # why two payloads? Because Arabic messes up the signature, we need to sign with Arabic without the \u encoding, but the body of the request needs to be \u encoded!!!!
        payload_to_send = json.dumps(payload, separators=(',', ':'))
        return payload_to_sign, payload_to_send

    def action_upload_contract(self):
        if not self.contractDocument:
            self.write_file_from_report()

        responseTime = 24 * 60
        self.contractNumber = uuid.uuid4().hex[:10].upper()

        beneficiaryIdNumber = self.identification_id
        beneficiaryName = self.name.name
        beneficiaryNameAr = self.name.name
        beneficiaryMobileNumber = self.name.phone
        beneficiaryEmail = self.name.email
        sanad_reference = self.seq_num
        sanad_amount = str(int(self.remaining_amount))

        sanads = []

        if self.loan_term >= 37:
            monthly_installment = int(self.remaining_amount / self.loan_term)
            value1 = monthly_installment * 36
            value2 = int(self.remaining_amount) - value1

            sanads = [
                {
                    "total_value": str(value1),
                    "reference_id": f"{sanad_reference}-1",
                    "due_type": "upon request",
                    "due_date": (datetime.now(timezone.utc) + relativedelta(months=+60)).date().isoformat()
                },
                {
                    "total_value": str(value2),
                    "reference_id": f"{sanad_reference}-2",
                    "due_type":  "date",
                    "due_date": (datetime.now(timezone.utc) + relativedelta(months=+36)).date().isoformat()
                }
            ]
        else:
            sanads = [
                {
                    "total_value": sanad_amount,
                    "reference_id": sanad_reference,
                    "due_type":  "upon request",
                    "due_date": (datetime.now(timezone.utc) + timedelta(minutes=6)).date().isoformat()

                }
            ]
        for sanad in sanads:
            print("Due Date:", sanad["due_date"])

        payload = {
            "contractName": self.name.name,
            "contractNumber": self.contractNumber,
            "contractBeneficiaries": [
                {
                    "beneficiaryIdNumber": beneficiaryIdNumber,
                    "beneficiaryName": beneficiaryName,
                    "beneficiaryNameAr": beneficiaryNameAr,
                    "beneficiaryMobileNumber": beneficiaryMobileNumber,
                    "beneficiaryEmail": beneficiaryEmail,
                    "beneficiaryRegionCode": 1,
                    "responseTimeInMinutes": responseTime,
                    "lang": "ar",
                    "signatureLang": "ar",
                    "signLocationCode": 1,
                    "signPageCode": 5,
                    "shareApprovalURL": True,
                    "isSignatureMethodFingerprint": True,
                    "isReadOnly": False
                }
            ],
            "contractData": self.contractDocument.decode(),
            "sanadGroupRequest": {
                "debtor": {
                    "national_id": beneficiaryIdNumber
                },
                "debtor_phone_number": beneficiaryMobileNumber,
                "country_of_issuance": "SA",
                "city_of_issuance": "1",
                "country_of_payment": "SA",
                "city_of_payment": "1",
                "reference_id": sanad_reference,
                "total_value": sanad_amount,
                "currency": "SAR",
                "sanad_type": "multiple" if len(sanads) > 1 else "single",
                "max_approve_duration": responseTime,
                "issued_at": f"{datetime.now().isoformat()}Z",
                "reason": "Reason",
                "sanad": sanads
            },
            "waitingDays": 0
        }

        payload_to_sign, payload_to_send = self._handle_contracts_payload(payload)
        domain = API_DOMAIN
        path = "/api/v2/Contract/UploadContractWithSanad"  # Live contract
        sandbox_path = "/api/v2/Contract/UploadContractWithSanad"  # sandbox contract
        # sandbox_path = "https://sandbox.nafith.sa/api/sanad-group" # sandbox nafith
        full_url = f'https://{domain}{sandbox_path}'
        headers = self._get_contracts_sa_header(payload_to_sign, domain, sandbox_path)

        response = requests.post(full_url, headers=headers, data=payload_to_send)
        if response.status_code not in [200, 201]:
            error_message = f'Contract API Error: {response.status_code} : {response.text}'
            if self.env.user.id == 2:
                error_message = f'{error_message}\n{full_url}\n{json.dumps(headers)}\n{payload}'
            raise UserError(error_message)

        res = response.json()
        data = res.get('data', {})
        if res.get('succeeded') is True:
            self.response_file_link = data.get('fileSharingLink', '')
            self.response_unSignFileLink = data.get('unSignFileLink', '')
            return self._show_success_message(_('Contract uploaded successfully') + f' {self.contractNumber}')
        elif res.get('messages'):
            raise ValidationError(_('Error : "%s" ') % (res.get('messages')))
        elif res.get('errors'):
            raise ValidationError(_('Error : "%s" ') % (res.get('errors')))

    # def action_upload_contract(self):
    #     if not self.contractDocument:
    #         self.write_file_from_report()
    #     responseTime = 24 * 60
    #     self.contractNumber = uuid.uuid4().hex[:10].upper()
    #     beneficiaryIdNumber = self.identification_id
    #     beneficiaryName = self.name.name
    #     beneficiaryNameAr = self.name.name
    #     beneficiaryMobileNumber = self.name.phone
    #     beneficiaryEmail = self.name.email
    #     sanad_reference = self.seq_num
    #     sanad_amount = "{}".format(int(self.remaining_amount))
    #     # due_date = self.sanad_date
    #     payload = {
    #         "contractName": self.name.name,
    #         "contractNumber": self.contractNumber,
    #         "contractBeneficiaries": [
    #             {
    #                 "beneficiaryIdNumber": beneficiaryIdNumber,
    #                 "beneficiaryName": beneficiaryName,
    #                 "beneficiaryNameAr": beneficiaryNameAr,
    #                 "beneficiaryMobileNumber": beneficiaryMobileNumber,
    #                 "beneficiaryEmail": beneficiaryEmail,
    #                 "beneficiaryRegionCode": 1,
    #                 "responseTimeInMinutes": responseTime,
    #                 "lang": "ar",
    #                 "signatureLang": "ar",
    #                 "signLocationCode": 1,
    #                 "signPageCode": 5,
    #                 "shareApprovalURL": True,
    #                 "isSignatureMethodFingerprint": True,
    #                 "isReadOnly": False
    #             }
    #         ],
    #         "contractData": self.contractDocument.decode(),
    #         "sanadGroupRequest": {
    #             # country_of_issuance and contry_of_payment must be "SA" , sanad_type must be "single or multiple" , total_value must don't contain decimal with 0 must be "20000" , due_type must be "date or upon request",due_date must be a date only and must be future data like "2023/10/1"
    #             "debtor": {
    #                 "national_id": beneficiaryIdNumber
    #             },
    #             "debtor_phone_number": beneficiaryMobileNumber,
    #             "country_of_issuance": "SA",
    #             "city_of_issuance": "1",
    #             "country_of_payment": "SA",
    #             "city_of_payment": "1",
    #             "reference_id": sanad_reference,
    #             "total_value": sanad_amount,
    #             "currency": "SAR",
    #             "sanad_type": "single",
    #             "max_approve_duration": responseTime,
    #             "issued_at": f"{datetime.now().isoformat()}Z",
    #             "reason": "Reason",
    #             "sanad": [
    #                 {
    #                     "total_value": sanad_amount,
    #                     "reference_id": sanad_reference,
    #                     "due_type": "upon request",
    #                     "due_date": f"{(datetime.now(timezone.utc) + timedelta(minutes=6)).isoformat()}Z"
    #                     # "due_date": f"{datetime.now().isoformat()}Z",
    #                 }
    #             ]
    #         },
    #         "waitingDays": 0
    #     }
    #     payload_to_sign, payload_to_send = self._handle_contracts_payload(payload)
    #     domain = API_DOMAIN
    #     path = "/api/v2/Contract/UploadContractWithSanad"
    #     full_url = f'https://{domain}{path}'
    #     headers = self._get_contracts_sa_header(payload_to_sign, domain, path)
    #     response = requests.post(full_url, headers=headers, data=payload_to_send)
    #     if response.status_code not in [200, 201]:
    #         error_message = f'Contract API Error: {response.status_code} : {response.text}'
    #         if self.env.user.id == 2:
    #             error_message = f'{error_message}\n{full_url}\n{json.dumps(headers)}\n{payload}'
    #         raise UserError(error_message)
    #     res = response.json()
    #     data = res.get('data', {})
    #     if res.get('succeeded') is True:
    #         self.response_file_link = data.get('fileSharingLink', '')
    #         self.response_unSignFileLink = data.get('unSignFileLink', '')
    #         return self._show_success_message(_('Contract uploaded successfully') + f' {self.contractNumber}')
    #     elif res.get('messages'):
    #         raise ValidationError(_('Error : "%s" ') % (res.get('messages')))
    #     elif res.get('errors'):
    #         raise ValidationError(_('Error : "%s" ') % (res.get('errors')))

    def _show_success_message(self, message, title='Success', type='success', **kwargs):
        res = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': type,
                'sticky': True,
                # 'next': {'type': 'ir.actions.act_window_close'},
            },
        }
        res.update(**kwargs)
        return res

    def contracts_get_one(self):
        # this function is used for debugging purposes
        payload = {}
        payload_to_sign, payload_to_send = self._handle_contracts_payload(payload)
        domain = API_DOMAIN
        path = f"/api/v2/Contract/Get/{self.contractNumber}"
        full_url = f'https://{domain}{path}'
        headers = self._get_contracts_sa_header(payload_to_sign, domain, path, is_json=False, method="GET")
        response = requests.get(full_url, headers=headers, data=payload_to_send)
        if response.status_code not in [200, 201]:
            error_message = f'Contract API Error: {response.status_code} : {response.text}'
            if self.env.user.id == 2:
                error_message = f'{error_message}\n{full_url}\n{json.dumps(headers)}\n{payload}'
            raise UserError(error_message)

        with open(f'/tmp/contract{self.contractNumber}', 'w') as file:
            file.write(response.text)
        res = response.json()
        if res.get('succeeded') is True:
            data = res.get('data', {})
            statusCode = data['contractStatusCode']
            return self._show_success_message(str(data))
        return self._show_success_message('failed: ' + str(res), title='Error', type='danger')

    def contracts_get_all(self):
        # this function is used for debugging purposes
        payload = {}
        payload_to_sign, payload_to_send = self._handle_contracts_payload(payload)
        domain = API_DOMAIN
        path = "/api/v2/Contract/GetAll"
        full_url = f'https://{domain}{path}'
        headers = self._get_contracts_sa_header(payload_to_sign, domain, path, is_json=False, method="GET")
        response = requests.get(full_url, headers=headers, data=payload_to_send)
        if response.status_code not in [200, 201]:
            error_message = f'Contract API Error: {response.status_code} : {response.text}'
            if self.env.user.id == 2:
                error_message = f'{error_message}\n{full_url}\n{json.dumps(headers)}\n{payload}'
            raise UserError(error_message)

        with open(f'/tmp/contracts_sa_all_response.txt', 'w') as file:
            file.write(response.text)

    def action_download_signed_contract_loan(self, contractNumber):
        self.ensure_one()
        res = self._action_download_signed_contract(contractNumber)
        self.signedContractDocument = res['data']['file']
        return {
            # we need to reload, because the file field won't get populated in the form
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def _action_download_signed_contract(self, contractNumber):
        # this method can be used by other models, and must not assume self is a loan.order record
        payload = {
            "contractNo": contractNumber
        }
        payload_to_sign, payload_to_send = self._handle_contracts_payload(payload)
        domain = API_DOMAIN
        path = f"/api/v2/Contract/Download/Signed/{contractNumber}"
        full_url = f'https://{domain}{path}'
        headers = self._get_contracts_sa_header(payload_to_sign, domain, path, is_json=False, method="GET")
        response = requests.get(full_url, headers=headers, data=payload_to_send)
        if response.status_code not in [200, 201]:
            try:
                if response.json()['statusCode'] == 'E0032':
                    raise UserError(_('Contract not signed'))
            except Exception:
                pass
            error_message = f'Contract API Error: {response.status_code} : {response.text} \n {path}'
            if self.env.user.id == 2:
                error_message = f'{error_message}\n{full_url}\n{json.dumps(headers)}\n{payload}'
            raise UserError(error_message)

        res = response.json()

        if res.get('succeeded') is True:
            return res
        else:
            errors = 'Error'
            if 'messages' in res:
                errors = res.get('messages', '')
            elif 'errors' in res:
                errors = res.get('errors', '')
            raise ValidationError(_('Error : "%s" ') % (errors))

    def action_all_beneficiary(self):
        current_GMT = time.gmtime()
        ############ get contract by number ##################
        # data ="{\"beneficiaryIdNumber\":\"1005073497\",\"pageSize\":5,\"pageNumber\":1}"
        h1 = '''{\"beneficiaryIdNumber\":\"'''
        data = str(h1) + self.identification_id + '"}'
        request_endpoint = '''/api/v2/Contract/GetAllByBeneficiary/''' + self.identification_id
        request_method = "GET"
        connection_url = API_DOMAIN
        timestamp = str(calendar.timegm(current_GMT))
        secret_key = SECRET_KEY
        encoded_data = base64.b64encode(bytes(data, 'utf_8')).decode()
        message = '{0}\n{1}\n{2}\nt={3}&ed={4}'.format(request_method, connection_url, request_endpoint, timestamp,
                                                       encoded_data)
        signature = hmac.new(bytes(secret_key, 'utf_8'), msg=bytes(message, 'utf_8'), digestmod=hashlib.sha256).digest()
        calculated_signature = base64.b64encode(signature).decode()
        print(calculated_signature)
        print(signature)

        ################################### Code #######################################

        BASE_URL = f'https://{API_DOMAIN}/api/v2/Contract/GetAllByBeneficiary/{self.identification_id}'
        headers = {
            'content-type': 'application/json',
            'X-Contracts-Timestamp': str(calendar.timegm(current_GMT)),
            'X-Contracts-ClientId': CLIENT_ID,
            'X-Contracts-APIKey': API_KEY,
            'X-Contracts-Signature': calculated_signature}

        response = requests.get(BASE_URL, headers=headers)
        res = json.loads(response.text)
        if response.status_code == 200 and res.get('data'):
            f_res = res.get('data')
            ben_list = []
            ben_ids = []
            self.allBeneficiaries.unlink()
            response_string = ''
            for fr in f_res:
                if fr.get('contractStatusCode') == '2':
                    response_string = 'Need Beneficiary Approval'
                if fr.get('contractStatusCode') == '1':
                    response_string = 'Signed'
                if fr.get('contractStatusCode') == '6':
                    response_string = 'Canceled'

                ben_list = {
                    'customerCR': fr.get('customerCR'),
                    'contractNumber': fr.get('contractNumber'),
                    'beneficiaryIDNumbers': fr.get('beneficiaryIDNumbers'),
                    'contractStatusCode': response_string,
                    'createdOn': fr.get('createdOn'),
                    'signDate': fr.get('signDate'),
                    'unSignFile': fr.get('unSignFile')
                }
                b_id = self.env['bebeficiary.integration'].create(ben_list)
                ben_ids.append(b_id.id)

            self.allBeneficiaries = ben_ids
        else:
            raise ValidationError(_('Error : "%s" ') % (res.get('messages')))

    def action_get_sanad_groups(self):
        current_GMT = time.gmtime()
        data = "{}"
        request_endpoint = "/api/sanad-group/"
        request_method = "GET"
        connection_url = "sandbox.nafith.sa" if IS_TEST_MODE else "api.nafith.sa"
        timestamp = str(calendar.timegm(current_GMT))
        secret_key = SECRET_KEY

        encoded_data = base64.b64encode(bytes(data, 'utf_8')).decode()
        message = f'{request_method}\n{connection_url}\n{request_endpoint}\nt={timestamp}&ed={encoded_data}'
        signature = hmac.new(bytes(secret_key, 'utf_8'), msg=bytes(message, 'utf_8'),
                             digestmod=hashlib.sha256).digest()
        calculated_signature = base64.b64encode(signature).decode()

        BASE_URL = f'https://{connection_url}{request_endpoint}'
        headers = {
            'content-type': 'application/json',
            'X-Contracts-Timestamp': timestamp,
            'X-Contracts-ClientId': CLIENT_ID,
            'X-Contracts-APIKey': API_KEY,
            'X-Contracts-Signature': calculated_signature
        }

        response = requests.get(BASE_URL, headers=headers)
        if response.status_code != 200:
            raise UserError(_('Error retrieving sanad groups: %s') % response.text)

        res = response.json()
        if res.get('succeeded') is not True:
            raise ValidationError(_('Error: %s') % res.get('messages'))

        sanad_groups = res.get('data', [])
        self.env.cr.execute('DELETE FROM sanad_group_integration WHERE id>=1')

        for group in sanad_groups:
            self.env['sanad.group.integration'].create({
                'reference_id': group.get('reference_id'),
                'status': group.get('status'),
                'total_value': group.get('total_value'),
                'created_on': group.get('created_on'),
                'issued_at': group.get('issued_at'),
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class BeneficiariesIntegration(models.Model):
    _name = 'bebeficiary.integration'
    _description = 'beneficiary data'

    customerCR = fields.Char(string='CR')
    contractNumber = fields.Char(string="Contract Number", readonly=True)
    beneficiaryIDNumbers = fields.Char(string="ID Number", readonly=True)
    contractStatusCode = fields.Char(string="Status Code", readonly=True)
    createdOn = fields.Char(string="Created On", readonly=True)
    signDate = fields.Char(string="Sign Date", readonly=True)
    unSignFile = fields.Binary(string="File", readonly=True)

    def cancel_contract(self):
        loan_id = self.env['loan.order'].search([('allBeneficiaries', 'in', self.ids)], limit=1)
        if not loan_id:
            raise ValidationError(_('Loan not found for this beneficiary.'))

        loan_id.action_cancel()
        # self.name.action_cancel()
        self.state = 'cancel'
        current_GMT = time.gmtime()
        status = 6
        f1 = "false"
        h1 = '''{\"contractNumber\":\"'''
        data = str(h1) + self.contractNumber + '''",'''
        h2 = '''"statusCode\":'''
        data += str(h2) + str(6) + ''','''
        h3 = '''\"withCancellationContract\":'''
        data += str(h3) + f1 + '}'
        _logger.info(data)
        request_endpoint = "/api/v2/Contract/UpdateStatus"
        request_method = "PUT"
        connection_url = API_DOMAIN
        timestamp = str(calendar.timegm(current_GMT))
        secret_key = SECRET_KEY
        encoded_data = base64.b64encode(bytes(data, 'utf_8')).decode()
        message = '{0}\n{1}\n{2}\nt={3}&ed={4}'.format(request_method, connection_url, request_endpoint, timestamp,
                                                       encoded_data)
        signature = hmac.new(bytes(secret_key, 'utf_8'), msg=bytes(message, 'utf_8'), digestmod=hashlib.sha256).digest()
        calculated_signature = base64.b64encode(signature).decode()
        crc = uuid.uuid4().hex[:10].upper()
        numbers = range(6)

        ###########################################################code############################################

        BASE_URL = f'https://{API_DOMAIN}/api/v2/Contract/UpdateStatus'
        headers = {
            'X-Contracts-Timestamp': str(calendar.timegm(current_GMT)),
            'X-Contracts-ClientId': CLIENT_ID,
            'X-Contracts-APIKey': API_KEY,
            'X-Contracts-Signature': calculated_signature}
        # myobj = {"contractNumber":self.contractNumber,"statusCode":6}
        myobj = {"contractNumber": self.contractNumber, "statusCode": 6, "withCancellationContract": False}
        response = requests.put(BASE_URL, headers=headers, json=myobj)
        _logger.info(response)
        _logger.info(response.text)
        res = json.loads(response.text)
        # f_res = res.get('data')
        if res.get('messages'):
            raise ValidationError(_('Error : "%s" ') % (res.get('messages')))
        else:
            raise ValidationError(_('success: "%s" '))

    def action_download_signed_contract(self):
        self.ensure_one()
        loan_id = self.env['loan.order'].search([('allBeneficiaries', 'in', self.ids)])
        if not loan_id:
            raise UserError('Loan not found')
        if len(loan_id) > 1:
            raise UserError('Multiple loans linked to the same contract')
        return loan_id.action_download_signed_contract_loan(self.contractNumber)


class AllContractsIntegration(models.Model):
    _name = 'all.contracts.integration'
    _description = 'All Contracts Integration'

    customerCR = fields.Char(string='CR')
    contractNumber = fields.Char(string="Contract Number", readonly=True)
    beneficiaryIDNumbers = fields.Char(string="ID Number", readonly=True)
    contractStatusCode = fields.Char(string="Status Code", readonly=True)
    createdOn = fields.Char(string="Created On", readonly=True)
    signDate = fields.Char(string="Sign Date", readonly=True)
    unSignFile = fields.Binary(string="File", readonly=True)
    response_file_link = fields.Char(string="File sharing link")
    response_unSignFileLink = fields.Char(string="UnSign File Link")

    def action_all_contracts(self):
        current_GMT = time.gmtime()
        data = "{}"
        request_endpoint = "/api/v2/Contract/GetAll"
        request_method = "GET"
        connection_url = API_DOMAIN
        timestamp = str(calendar.timegm(current_GMT))
        secret_key = SECRET_KEY
        # payload= "{\"perPage\":\"200\",\"page\":1,\"competition_ids\":[1163,1162],\"team_id\":[],\"venus_id\":[]}"
        encoded_data = base64.b64encode(bytes(data, 'utf_8')).decode()
        message = '{0}\n{1}\n{2}\nt={3}&ed={4}'.format(request_method, connection_url, request_endpoint, timestamp,
                                                       encoded_data)
        signature = hmac.new(bytes(secret_key, 'utf_8'), msg=bytes(message, 'utf_8'), digestmod=hashlib.sha256).digest()
        calculated_signature = base64.b64encode(signature).decode()

        ################################### Code #######################################

        BASE_URL = f'https://{API_DOMAIN}/api/v2/Contract/GetAll'
        headers = {
            'content-type': 'application/json',
            'X-Contracts-Timestamp': str(calendar.timegm(current_GMT)),
            'X-Contracts-ClientId': CLIENT_ID,
            'X-Contracts-APIKey': API_KEY,
            'X-Contracts-Signature': calculated_signature}
        params = {}
        response = requests.get(BASE_URL, headers=headers, params=params)
        res = json.loads(response.text)
        if res.get('succeeded') == True:
            f_res = res.get('data')
            ben_list = []
            ben_ids = []
            self.env.cr.execute('''DELETE FROM all_contracts_integration WHERE id>=1''')
            response_string = ''
            for fr in f_res:
                if fr.get('contractStatusCode') == '2':
                    response_string = 'Need Beneficiary Approval'
                if fr.get('contractStatusCode') == '1':
                    response_string = 'Signed'
                if fr.get('contractStatusCode') == '6':
                    response_string = 'Canceled'

                ben_list = {
                    'customerCR': fr.get('customerCR'),
                    'contractNumber': fr.get('contractNumber'),
                    'beneficiaryIDNumbers': fr.get('beneficiaryIDNumbers'),
                    'contractStatusCode': response_string,
                    'createdOn': fr.get('createdOn'),
                    'signDate': fr.get('signDate'),
                    'response_file_link': fr.get('fileSharingLink'),
                    'unSignFile': fr.get('unSignFile'),
                    'response_unSignFileLink': fr.get('unSignFileLink')
                }
                b_id = self.create(ben_list)
            _logger.info("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK", b_id)
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            raise ValidationError(_('Error : "%s" ') % (res.get('messages')))


class SanadGroupIntegration(models.Model):
    _name = 'sanad.group.integration'
    _description = 'Sanad Group Integration'

    loan_id = fields.Many2one('loan.order', string="Loan")
    reference_id = fields.Char("Reference ID")
    status = fields.Char("Status")
    total_value = fields.Char("Total Value")
    issued_at = fields.Char("Issued At")
    created_on = fields.Char("Created On")

    @api.model
    def action_get_sanad_groups(self):
        self.env['loan.order'].action_get_sanad_groups()
        return {'type': 'ir.actions.client', 'tag': 'reload'}
