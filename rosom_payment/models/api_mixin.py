import os
import logging
import uuid
import requests
import json
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, registry, _, SUPERUSER_ID
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta
from .api_util import pfx_to_pem
import logging
_logger = logging.getLogger(__name__)
# Date format used by the Rosom API
ROSOM_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
# ROSOM_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
ROSOM_DATE_FORMAT_WITH_MICROSECONDS = '%Y-%m-%dT%H:%M:%S.%f'
ROSOM_DATE_FORMAT_WITHOUT_MICROSECONDS = '%Y-%m-%dT%H:%M:%S'
# Logger instance for this module
_logger = logging.getLogger(__name__)


class rosom_api_mixin(models.AbstractModel):
    _name = "rosom.api.mixin"
    _description = "Rosom Api Mixin"

    def get_base_url(self):
        '''Returns the base URL for the Rosom API from environment variables.'''
        # Uncomment the line below to use a different URL for testing
        return os.getenv('ROSOM_URL', 'https://rosomtest.brightware.com.sa')
        #return os.getenv('ROSOM_URL', 'https://rosomapi.brightware.com.sa:41527')

    def rosom_get_common_headers(self, is_json=True):
        '''Returns HTTP headers for API requests.'''
        content_type = 'application/json'  # Default content type
        if not is_json:
            content_type = 'application/x-www-form-urlencoded'  # Change content type if not JSON
        return {
            'Accept': 'application/json',
            'Content-Type': content_type
        }

    def rosom_auth(self):
        '''Returns paths and passwords for the PFX certificate.'''
        if os.getenv('ROSOM_API_SET_WEAK_SSL'):
            # Allow weak SSL settings if specified
            requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=0'
        # Uncomment the line below for a different PFX path and password
        # return os.getenv('ROSOM_PFX_PATH', '/etc/odoo/rosom.pfx'), os.getenv('ROSOM_PFX_PASSWORD', 'E#Pm0@!') old one
        return os.getenv('ROSOM_PFX_PATH', '/etc/odoo/ROSOMSandbox.pfx'), os.getenv('ROSOM_PFX_PASSWORD', 'Rsch$32@') 
       # return os.getenv('ROSOM_PFX_PATH', '/etc/rosom/NEWPFX.pfx'), os.getenv('ROSOM_PFX_PASSWORD', 'Fuel@2030')

    def rosom_get_merchant_id(self):
        '''Returns the merchant ID.'''
        #return '10077'
        return '12454' 
        # Old merchant ID was 12454

    def rosom_get_program_id(self):
        '''Returns the program ID.'''
        #return '175'
        return '2756' 
        # Old program ID was 2756

    def rosom_format_datetime(self, value):
        '''Formats a datetime object as a string in ROSOM_DATE_FORMAT.'''
        try:
            # Try formatting with microseconds first
            return value.strftime(ROSOM_DATE_FORMAT_WITH_MICROSECONDS)
        except ValueError:
            # If it fails (likely because microseconds are missing), fall back to the format without microseconds
            return value.strftime(ROSOM_DATE_FORMAT_WITHOUT_MICROSECONDS)
        # return value.strftime(ROSOM_DATE_FORMAT)

    def rosom_string_to_datetime(self, value):
        '''Converts a string in ROSOM_DATE_FORMAT to a datetime object.'''
        ROSOM_DATE_FORMAT_WITH_MICROSECONDS = '%Y-%m-%dT%H:%M:%S.%f'
        ROSOM_DATE_FORMAT_WITHOUT_MICROSECONDS = '%Y-%m-%dT%H:%M:%S'
        try:
            # Try parsing with microseconds first
            return datetime.strptime(value, ROSOM_DATE_FORMAT_WITH_MICROSECONDS)
        except ValueError:
            # If it fails, fall back to the format without microseconds
            return datetime.strptime(value, ROSOM_DATE_FORMAT_WITHOUT_MICROSECONDS)
        # return datetime.strptime(value, ROSOM_DATE_FORMAT)

    def rosom_create_bill(self, loan, is_reschedule=False):
        '''Creates or updates a bill in the Rosom system based on a given loan.'''
        # Detere which fields to use based on the is_reschedule flag
        installment_field = 'reschedule_installment_ids' if is_reschedule else 'installment_ids'
        loan_field = 'reschedule_loan_id' if is_reschedule else 'loan_id'

        cert_path, cert_pass = self.rosom_auth()  # Get certificate path and password
        url = f'{self.get_base_url()}/RosomAPI/api/Bill/CreateSingleBill'
        bill_obj = self.env['rosom.bill']

        fullname = loan.name.name.strip()
        name_parts = fullname.split(' ')
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[-1] if len(name_parts) > 1 else ''
        if not (first_name and last_name):
            raise UserError('Unable to get first or last name')
        mobile = loan.name.phone and loan.name.phone.replace(' ', '')[-10:]

        # Access installments based on the is_reschedule flag
        installments = getattr(loan, installment_field)
        todo = installments and installments[0]
        if len(installments) > 1:
            todo += installments[1]

        today = date.today()
        now = datetime.now()
        bill_create_days = 19
        bill_create_date_odoo = datetime(now.year, now.month, bill_create_days)
        # bill_create_date_odoo = [datetime(now.year, now.month, day) for day in bill_create_days]
        # datetime(now.year, now.month, 25)
        last_installment = installments[-1]
        bill_create_date = self.rosom_format_datetime(bill_create_date_odoo)

        # Check if a bill already exists
        bill_id = bill_obj.search([(loan_field, '=', loan.id)], limit=1)
        InvoiceStatus = "BillNew" if not bill_id else "BillUpdated"
        formatted_seq = loan.seq_num.replace('/', ' ').replace('  ', ' ').strip()
        # min_partial = 0
        # for inst in loan.installment_ids:
        #     if inst.state == 'unpaid':
        #         min_partial += inst.installment_amount
        #     elif inst.state == 'partial':
        #         min_partial += inst.remaining_amount

        MinPartialAmount = loan.installment_ids[0].installment_amount + loan.late_amount
        invoice = {
            "InvoiceId": loan.seq_num.replace("/", "").replace(" ", "").replace("LOAN", ""),
            "InvoiceStatus": InvoiceStatus,
            "DisplayInfo": formatted_seq,
            "AmountDue": installments[0].installment_amount + loan.late_amount,
            "CreateDate": bill_create_date,
        }

        bill_values = {
            loan_field: loan.id,
            "MinPartialAmount": MinPartialAmount,
        }
        bill_values.update(invoice)
        bill_values.update({
            "CreateDate": bill_create_date_odoo,
        })

        if bill_id:
            bill_id.write(bill_values)
        else:
            bill_id = bill_obj.create(bill_values)

        invoice.update({
            "BillType": "Recurring",
            "PaymentRange": {
                "MinPartialAmount": MinPartialAmount,
            },
        })

        invoice_item = {
            "Beneficiary": {
                "Id": str(loan.name.identification_no),
                "FirstName": first_name,
                "LastName": last_name,
                "MobileNo": mobile,
                "Lang": "AR",
            },
        }
        invoice_item.update(invoice)

        payload = json.dumps({
            "UUID": str(uuid.uuid4()),
            "Timestamp": self.rosom_format_datetime(datetime.now()),
            "MerchantId": self.rosom_get_merchant_id(),
            "ProgramId": self.rosom_get_program_id(),
            "Invoice": invoice_item,
        })
        headers = self.rosom_get_common_headers()

        log_values = {
            'request': payload,
            'url': url,
            'type': 'multi_bill',
            'res_id': loan.id,
            'res_model': loan._name,
        }
        log_obj = self.env['rosom.api.log']
        log_id = log_obj.create_log(log_values)

        with pfx_to_pem(cert_path, cert_pass) as cert:
            requests.post(url, cert=cert, data=payload)
            response = requests.post(url, headers=headers, data=payload, cert=cert)

        try:
            response = response.json()
        except Exception:
            pass

        response_to_log = str(response)
        try:
            response_to_log = json.dumps(response)
        except Exception:
            pass

        log_id.update_log({
            'response': response_to_log,
        })

        if isinstance(response, dict):
            Status = response.get('Status', {})
            if Status.get('Code') == 0:
                bill_id.SADADNumber = response.get('SADADNumber', '')
            else:
                error_message = Status.get('Description')
                error_message = error_message and 'R API error: {}'.format(error_message) or 'R API error'
                raise UserError(error_message)
        return response


    def rosom_create_bills(self, loans, is_reschedule=False):
        '''Creates or updates multiple bills in the Rosom system based on a batch of loans.'''
        cert_path, cert_pass = self.rosom_auth()
        url = f'{self.get_base_url()}/RosomAPI/api/Bill/ProcessMultiBills'

        payload_invoices = []
        bill_obj = self.env['rosom.bill']
        log_obj = self.env['rosom.api.log']
        today = date.today()
        now = datetime.now()
        bill_create_days = 25
        bill_create_date_odoo = datetime(now.year, now.month, bill_create_days)
        invoice_map = {}
        for loan in loans:
            loan_field = 'reschedule_loan_id' if is_reschedule else 'loan_id'
            fullname = loan.name.name.strip()
            name_parts = fullname.split(' ')
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[-1] if len(name_parts) > 1 else ''
            bill_create_date = self.rosom_format_datetime(bill_create_date_odoo)
            # last_installment = installments[-1]

            if not (first_name and last_name):
                raise UserError(f'Cannot extract first/last name for {loan.name.name}')

            mobile = loan.name.phone and loan.name.phone.replace(' ', '')[-10:]
            if not mobile:
                raise UserError(f'Mobile number not set for {loan.name.name}')

            # Dates
            if loan.approve_date and loan.approve_date.day >= 15:
                bill_create_date_odoo = datetime(loan.approve_date.year, loan.approve_date.month + 1, 27)
            else:
                bill_create_date_odoo = datetime(loan.approve_date.year, loan.approve_date.month, 27)

            bill_create_date = self.rosom_format_datetime(bill_create_date_odoo)

         

            bill_id = bill_obj.search([('loan_id', '=', loan.id)], limit=1)
            invoice_status = "BillUpdated" if bill_id else "BillNew"
            amount_due = 0.0
            current_month = today.month
            current_year = today.year
            min_partial = loan.installment_ids[0].installment_amount + loan.late_amount

            for inst in loan.installment_ids.sorted('date'):
                due = inst.date

                if inst.state == 'paid':
                    continue
                if due and due.month == current_month and due.year == current_year:

                    if inst.state == 'unpaid':
                        
                        amount_due += round(inst.installment_amount + loan.late_amount, 2)
                    elif inst.state == 'partial':
                        remaining = inst.installment_amount - inst.amount_paid
                        amount_due += round(remaining + loan.late_amount, 2)

                elif due and due < today:
                    if inst == loan.installment_ids.sorted('date')[-1]:
                        amount_due = round(loan.late_amount,2)
                    else:
                        continue

                else:
                    continue

            formatted_seq = loan.seq_num.replace('/', ' ').replace('  ', ' ').strip()
            invoice_map[formatted_seq] = loan
            if (
                    bill_create_date_odoo.year > today.year
                    or (bill_create_date_odoo.year == today.year and bill_create_date_odoo.month > today.month)):
                _logger.info(
                    f"Skipping loan {loan.name} ({loan.seq_num}) "
                    f"because bill_create_date_odoo={bill_create_date_odoo.date()} is in the future."
                )
                continue
            invoice = {
                "Beneficiary": {
                    "Id": str(loan.name.identification_no),
                    "FirstName": first_name,
                    "LastName": last_name,
                    "MobileNo": mobile,
                    "Lang": "AR",
                },
                "InvoiceId": loan.seq_num.replace("/", "").replace(" ", "").replace("LOAN", ""),
                "InvoiceStatus": invoice_status,
                "BillType": "Recurring",
                "DisplayInfo": formatted_seq,
                "AmountDue": amount_due,
                "CreateDate": bill_create_date,
            }

            # if invoice["BillType"] == "OneTime":
            #     invoice["ExpiryDate"] = bill_expiry_date
            # else:
            #     invoice["PaymentRange"] = {
            #         "MinPartialAmount": loan.installment_ids[0].installment_amount + loan.late_amount
            #     }
            payload_invoices.append(invoice)

            # Create/update internal Odoo bill
            bill_vals = {
                'loan_id': loan.id,
                'InvoiceId': loan.seq_num.replace("/", "").replace(" ", "").replace("LOAN", ""),
                'InvoiceStatus': invoice_status,
                'DisplayInfo': invoice['DisplayInfo'],
                'AmountDue': invoice['AmountDue'],
                'MinPartialAmount': min_partial,
                'CreateDate': bill_create_date_odoo,
            }
            if bill_id:
                bill_id.write(bill_vals)
            else:
                bill_obj.create(bill_vals)
        if not payload_invoices:
            _logger.info("No invoices to send to Rosom. Skipping request.")
            return []
        if amount_due == 0.0:
            return []
        request_payload = json.dumps({
            "UUID": str(uuid.uuid4()),
            "Timestamp": self.rosom_format_datetime(datetime.now()),
            "MerchantId": self.rosom_get_merchant_id(),
            "ProgramId": self.rosom_get_program_id(),
            "Invoices": payload_invoices,
        })

        headers = self.rosom_get_common_headers()

        # Log and Send
        log_id = log_obj.create_log({
            'request': request_payload,
            'url': url,
            'type': 'multi_bill',
            'res_id': loans.ids[0] if len(loans) == 1 else None,
            'res_model': 'loan.order',
        })

        with pfx_to_pem(cert_path, cert_pass) as cert:
            requests.post(url, cert=cert, data=request_payload)
            response = requests.post(url, headers=headers, data=request_payload, cert=cert)

        try:
            response_data = response.json()
        except Exception:
            response_data = {'error': 'Non-JSON response'} 
        try:
            highlighted_response = log_id.highlight_errors_in_response(response_data)
            log_id.update_log({'response': highlighted_response})

        except Exception:
            log_id.update_log({'response': str(response_data)})

        errors = []
        if isinstance(response_data, list):
            for item in response_data:
                invoice_id = item.get("InvoiceId")
                sadad_number = item.get("SADADNumber")
                status = item.get("Status", {})
                status_code = status.get("Code")
                description = status.get("Description")
                severity = status.get("Severity")

                print(f"InvoiceId: {invoice_id}")
                print(f"  SADAD Number: {sadad_number}")
                print(f"  Status Code: {status_code}")
                print(f"  Description: {description}")
                print(f"  Severity: {severity}")
                if status_code == 0:
                    bill_obj = self.env['rosom.bill']
                    bill_id = bill_obj.search([('InvoiceId', '=', invoice_id)], limit=1)
                    bill_id.SADADNumber = sadad_number
                    # min_partial = 0
                    # for inst in loan.installment_ids:
                    #     if inst.state == 'unpaid':
                    #         min_partial += inst.installment_amount
                    #     elif inst.state == 'partial':
                    #         min_partial += inst.remaining_amount
                    min_partial = loan.installment_ids[0].installment_amount + loan.late_amount

                    bill_values = {
                        'loan_id': loan.id,
                        'InvoiceId': invoice_id,
                        'SADADNumber': sadad_number,
                        'InvoiceStatus': 'BillNew',
                        'AmountDue': amount_due,
                        'MinPartialAmount': min_partial,
                        'DisplayInfo': loan.seq_num,
                        'CreateDate': datetime.today(),
                    }
                    # loan.rosom_bill_error = False
                    if bill_id:
                        bill_id.SADADNumber = sadad_number

                    else:
                        print("Attempting to create rosom.bill with:", bill_values)
                        try:
                            bill = bill_obj.create(bill_values)
                            print("Created rosom.bill ID:", bill.id)
                        except Exception as e:
                            print("Failed to create rosom.bill:", e)
                else:
                    # for loan in loans:
                    #     if loan.invoice == invoice_id:
                            # loan.rosom_bill_error = True

                    errors.append(f"InvoiceId {invoice_id}: {description}")
        return


    def handle_request(self, payload, url, enable_log=True):
        '''Handles incoming webhook requests from Rosom and updates payment records.'''
        env_obj = self.sudo()  # Ensure user has sufficient rights
        payload_to_log = str(payload)
        try:
            payload_to_log = json.dumps(payload)  # Convert payload to JSON for logging
        except Exception:
            pass  # Ignore serialization errors

        # Access the rosom.bill model
        bill_obj = env_obj.env['rosom.bill']
        log_values = {
            'request': payload_to_log,
            'url': url,
            'type': 'webhook',
            'res_model': bill_obj._name,
        }
        log_obj = env_obj.env['rosom.api.log']
        if enable_log:
            log_id = log_obj.create_log(log_values)  # Log incoming request

        # Example payload for reference
        example_payload = {
            "MerchantId": "10000",
            "InvoiceId": "99999508505",
            "PaymentId": 999101,
            "SADADTransactionId": "5002325698",
            "BankTransactionId": "X600232565XS20dAA5",
            "PaidAmount": 270.25,
            "PaymentDate": "2019-08-19T00:23:37",
            "SADADNumber": "99999508505",
            "BankName": "RJHISARI",
            "DistrictCode": "11",
            "BranchCode": "50000",
            "AccessChannel": "INTERNET",
            "PmtMethod": "ACTDEB",
            "PmtType": "POST",
            "ServiceType": "UTIL"
        }
        values = payload
        # Search for existing bill and payment records
        bill_id = env_obj.env['rosom.bill'].search([('InvoiceId', '=', values['InvoiceId'])])
        values.update({
            'PaymentDate': self.rosom_string_to_datetime(values['PaymentDate']),  # Convert date string to datetime
            'bill_id': bill_id.id,
        })

        _logger.info(f"Updated values: {values}")
        payment_id = env_obj.env['rosom.payment'].search([('PaymentId', '=', values['PaymentId'])], limit=1)
        _logger.info(f"Payment search result: {payment_id.id}")
        if payment_id:
            payment_id.write(values)  # Update existing payment record
        # ///////////////////////START///////////////////////////////
        else:
            is_api_payment = True
            if is_api_payment:
                journal_id = 15
            else:
                journal_id = bill_id.loan_id.loan_type.payment_journal.id
            values.update({'journal_id': journal_id})
        # ///////////////////////END///////////////////////////////
            payment_id = env_obj.env['rosom.payment'].sudo().create(values)  # Create new payment record
            _logger.info(f"Created new payment: {payment_id}")
            payment_id.post_create()  # Post-processing after creation
            # Mark the first unpaid installment as paid
        unpaid_installment = bill_id.loan_id.installment_ids.filtered(lambda x: x.state == 'unpaid')
        first_unpaid_installment = unpaid_installment and unpaid_installment[0]
        if first_unpaid_installment:
            if first_unpaid_installment.state != 'paid' and first_unpaid_installment.state != 'partial':
                first_unpaid_installment.action_paid_installment(payment_id=payment_id)
