from datetime import timedelta
from odoo import api, fields, models, _  # Import Odoo modules for API, fields, models, and translation
import logging
import threading
import time

_logger = logging.getLogger(__name__)


class api_loan_order(models.Model):
    _inherit = 'loan.order'  # Inherit from the existing 'loan.order' model
    _description = "Inherit from Loan module"  # Provide a description for the model extension

    def auto_salary_certificate(self):
        for rec in self:
            if rec.loan_type.id == 3:  # New condition
                try:
                    if rec.sector_loan == 'Private Sector':
                        rec.name.action_salary_certificate_data()
                        rec.name.limit_loan()
                    elif rec.sector_loan == 'Government Sector':
                        rec.name.action_salary_certificate_gov()
                        rec.name.limit_loan()
                    elif rec.sector_loan == 'Soldier':
                        rec.name.action_salary_certificate_gov()
                        rec.name.limit_loan()
                    _logger.info(f"auto_salary_certificate executed successfully for record ID {rec.id}")
                    return 200  # Success response
                except Exception as e:
                    _logger.error(f"Error executing auto_salary_certificate for record ID {rec.id}: {e}")
                    return 400  # Failure response
            else:
                _logger.info(f"Loan Type {rec.loan_type} is not 3. Skipping salary certificate processing.")
                return 400  # Failure response for unsupported loan types

    def auto_simah_api(self):
        _logger.info("Executing auto_simah_api with state: %s", self.state)
        if self.loan_type.id == 3:
            self.get_compute_irr()
            _logger.info("State is 'auto' for record ID: %s", self.id)
            self.action_simah_api()  # Execute the action for the SIMAH API
            self.compute_installment()  # Compute the installment

            if self.deduction_after <= 0.45 and self.name.employmentStatus == 'نشيط':
                if self.creditInstrument:
                    should_approve = False
                    for instrument in self.creditInstrument:
                        _logger.info(
                            f"Checking Credit Instrument Code: {instrument.code}, Status: {instrument.creditInstrumentStatusCode}")
                        if instrument.code != 'MBL' and instrument.creditInstrumentStatusCode == 'W':
                            for default in self.simahDefault:
                                if instrument.ciAccountNumber == default.pDefAccountNo:
                                    if default.pDefOutstandingBalance == 0:
                                        should_approve = False
                                    else:
                                        should_approve = True
                                else:
                                    should_approve = True
                        break
                    if should_approve:
                        self.reject_reason_default()
                        self.action_set_to_reject_credit()
                    else:
                        if self.irr == 0:
                            self.get_compute_irr()
                        else:
                            self.action_approve_loan()
                else:
                    if self.irr == 0:
                        self.get_compute_irr()
                    else:
                        self.action_approve_loan()
            else:
                self.reject_reason_default()
                self.action_set_to_reject_credit()
        else:
            _logger.info("Skipping record ID: %s as state is not 'auto'", self.id)

    def run_delayed_functions(self, record_id):
        self.get_compute_irr()
        record = self.browse(record_id)
        if record:
            salary_certificate_response = record.auto_salary_certificate()  # Call the function and capture the response
            if salary_certificate_response == 200:  # Check if the response is 200
                record.auto_simah_api()  # Call the next function
            else:
                _logger.info(
                    f"auto_salary_certificate() for record ID {record_id} did not return 200. Skipping auto_simah_api().")
        return record

    @api.model
    def auto_fazaa(self):
        records = self.search([('loan_type.id', '=', '3')])
        # record = self.browse(record_id)
        if records:
            salary_certificate_response = self.auto_salary_certificate()  # Call the function and capture the response
            if salary_certificate_response == 200:  # Check if the response is 200
                self.get_compute_irr()
                self.auto_simah_api()  # Call the next function
            else:
                _logger.info(
                    f"auto_salary_certificate() for record ID {records} did not return 200. Skipping auto_simah_api().")
        return records


    @api.model
    def create(self, vals):
        record = super(api_loan_order, self).create(vals)
        if record.loan_type.id == 3:
            # Get the administrator user (or another user with the right access)
            # admin_user = self.env.ref('base.user_admin')  # You can change this to a specific user
            self.get_compute_irr()
            odoobot = self.env.ref('base.user_odoo')
            # Schedule the cron job after 1 minute
            self.env['ir.cron'].create({
                'name': 'Run auto functions for loan order',
                'model_id': self.env.ref('loan.model_loan_order').id,
                # Replace 'module_name' with your actual module name
                'state': 'code',
                'code': f'model.run_delayed_functions({record.id})',
                'interval_type': 'minutes',  # Execute after 1 minute
                'interval_number': 1,  # 1 minute delay
                'nextcall': fields.Datetime.now() + timedelta(minutes=1),  # Set nextcall 1 minute from now
                'numbercall': 1,  # Execute only once
                'user_id': odoobot.id,  # Execute as admin user
            })
        return record

    @api.model
    def auto_simah_api_for_records(self):
        records = self.search([('loan_type.id', '=', '3')])
        _logger.info("Found %d records with type 'تورق - فزعة'", len(records))
        for record in records.sudo():  # Use sudo to bypass ACLs
            _logger.info("Processing record ID: %s", record.id)
            record.auto_simah_api()  # Call the method for each record
        if not records:
            _logger.info("No records found with with type 'تورق - فزعة' to process.")

    # def auto_simah_api(self):
    #     _logger.info("Executing auto_simah_api with state: %s", self.state)
    #     # Ensure we are checking the state of a record
    #     if self.state == 'auto':
    #         _logger.info("State is 'auto' for record ID: %s", self.id)
    #         # self.auto_salary_certificate()  # Execute the action for the Salary Certificate API
    #         self.action_simah_api()  # Execute the action for the SIMAH API
    #         self.compute_installment()  # Compute the installment
    #         # Check the deduction_after condition
    #         if self.deduction_after <= 0.45 or self.name.employmentStatus == 'نشيط':
    #             _logger.info('Passed initial check: deduction_after = %s, employmentStatus = %s', self.deduction_after,
    #                          self.name.employmentStatus)
    #             if self.credit_instrument.code == 'MBL' and self.credit_instrument.creditInstrumentStatusCode == 'W':
    #                 self.credit_instrument.ensure_one()
    #                 # code = getattr(self.credit_instrument, 'code', None)
    #                 # status_code = getattr(self.credit_instrument, 'creditInstrumentStatusCode', None)
    #                 # if code == 'MBL' and status_code == 'W':
    #                 #     # Approve the loan
    #                 self.action_approve_loan()
    #                 _logger.info('Approved loan for record ID: %s with deduction_after: %s', self.id,
    #                              self.deduction_after)
    #                 _logger.info('Approved loan for record ID: %s with employmentStatus: %s', self.id,
    #                              self.name.employmentStatus)
    #                 _logger.info('Approved loan for record ID: %s with creditInstrumentStatusCode: %s', self.id,
    #                              self.credit_instrument.creditInstrumentStatusCode)
    #                 _logger.info('Approved loan for record ID: %s with Code: %s', self.id,
    #                              self.credit_instrument.code)
    #             else:
    #                 # Reject the loan if conditions are not met
    #                 self.reject_reason_default()  # Set the default rejection reason
    #                 self.action_set_to_reject_credit()  # Reject the credit
    #                 _logger.info('Rejected credit for record ID: %s. CreditInstrument Code: %s, Status: %s', self.id,
    #                              self.credit_instrument.code, self.credit_instrument.creditInstrumentStatusCode)
    #         else:
    #             # Rejection due to not passing the deduction or employment status check
    #             self.reject_reason_default()  # Set the default rejection reason
    #             self.action_set_to_reject_credit()  # Reject the credit
    #             _logger.info(
    #                 'Rejected credit for record ID: %s due to high deduction_after: %s or non-active employment status: %s',
    #                 self.id, self.deduction_after, self.name.employmentStatus)
    #
    #     else:
    #         _logger.info("Skipping record ID: %s as state is not 'auto'", self.id)


