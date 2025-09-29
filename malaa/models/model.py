# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from datetime import datetime, date
import requests
import datetime
import json
import logging

from twisted.logger import _logger


class Partner(models.Model):
    # _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    financial_evaluation = fields.Many2one("financial.evaluation")
    occupation_history = fields.Many2one("occupation.history")
    financial_evaluation_ids = fields.One2many('financial.evaluation', 'partner_id', string="Financial Evaluations")
    occupation_history_ids = fields.One2many('occupation.history', 'partner_id', string="Occupation History")
    food_expenses = fields.Float(related='financial_evaluation.food_expenses', store=True)
    housing_expenses = fields.Float(related='financial_evaluation.housing_expenses')
    domestic_labor_wages = fields.Float(related='financial_evaluation.domestic_labor_wages')
    has_domestic_labor = fields.Boolean(related='financial_evaluation.has_domestic_labor')
    education_expenses = fields.Float(related='financial_evaluation.education_expenses')
    healthcare_expenses = fields.Float(related='financial_evaluation.healthcare_expenses')
    transportation_expenses = fields.Float(related='financial_evaluation.transportation_expenses')
    communication_expenses = fields.Float(related='financial_evaluation.communication_expenses')
    total_expenses = fields.Float(related='financial_evaluation.total_expenses')
    total_monthly_obligations = fields.Float(related='financial_evaluation.total_monthly_obligations')
    net_available_income_after_obligations = fields.Float(
        related='financial_evaluation.net_available_income_after_obligations')
    occupation_code = fields.Char(related='occupation_history.occupation_code')
    position = fields.Char(related='occupation_history.position')
    occupation_region = fields.Char(related='occupation_history.occupation_region')
    sector_type = fields.Char(related='occupation_history.sector_type')
    industry = fields.Char(related='occupation_history.industry')
    employer_name = fields.Char(related='occupation_history.employer_name')
    employment_start_date = fields.Date(related='occupation_history.employment_start_date')
    employment_end_date = fields.Date(related='occupation_history.employment_end_date')
    is_current_occupation = fields.Boolean(related='occupation_history.is_current_occupation')
    net_monthly_income =  fields.Float(
        related='financial_evaluation.net_monthly_income')
    customer_nationality = fields.Char()
    kyc_name = fields.Char()
    nationalitycode = fields.Char()


class FinancialEvaluation(models.Model):
    _name = 'financial.evaluation'
    _description = 'Financial Evaluation'

    net_monthly_income = fields.Float(string="Net Monthly Income")

    # Expense Breakdown
    partner_id = fields.Many2one('res.partner', string="Partner", required=True, ondelete='cascade')
    basic_salary = fields.Float(related='partner_id.basic_salary', required=True)
    food_expenses = fields.Float(string="Food Expenses")
    housing_expenses = fields.Float(string="Housing Expenses")
    housing_ownership_status = fields.Char(string="Housing Ownership Status")
    housing_utilities_included = fields.Boolean(string="Utilities Included")
    domestic_labor_wages = fields.Float(string="Domestic Labor Wages")
    has_domestic_labor = fields.Boolean(string="Has Domestic Labor")
    education_expenses = fields.Float(string="Education Expenses")
    dependents_count = fields.Integer(string="Dependents Count")
    healthcare_expenses = fields.Float(string="Healthcare Expenses")
    transportation_expenses = fields.Float(string="Transportation Expenses")
    communication_expenses = fields.Float(string="Communication Expenses")
    financial_obligation = fields.Many2one("financial.obligation")
    obligations_name = fields.Char(related='financial_obligation.name')
    credit_amount = fields.Float(related='financial_obligation.credit_amount')
    monthly_payment = fields.Float(related='financial_obligation.monthly_payment')
    payment_frequency = fields.Char(related='financial_obligation.payment_frequency')

    # Other Obligations
    obligation_ids = fields.One2many('financial.obligation', 'evaluation_id', string="Other Obligations")

    # Summary
    total_expenses = fields.Float(string="Total Expenses")
    total_monthly_obligations = fields.Float(string="Total Monthly Obligations")
    net_available_income_after_obligations = fields.Float(string="Net Available Income After Obligations")


class FinancialObligation(models.Model):
    _name = 'financial.obligation'
    _description = 'Financial Obligation'

    evaluation_id = fields.Many2one('financial.evaluation', string="Financial Evaluation")
    name = fields.Char(string="Obligation Name")
    credit_amount = fields.Float(string="Credit Amount")
    monthly_payment = fields.Float(string="Monthly Payment")
    payment_frequency = fields.Char(string="Payment Frequency")


class OccupationHistory(models.Model):
    _name = 'occupation.history'
    _description = 'Occupation History'

    partner_id = fields.Many2one('res.partner', string="Partner", required=True, ondelete='cascade')
    occupation_code = fields.Char(string="Occupation Code")
    position = fields.Char(string="Occupation Description")
    sector_type = fields.Char(string="Sector Type")
    occupation_region = fields.Char(string="occupation region")
    industry = fields.Char(string="Industry")
    employer_name = fields.Char(string="Employer Name")
    employment_start_date = fields.Date(string="Employment Start Date")
    employment_end_date = fields.Date(string="Employment End Date")
    is_current_occupation = fields.Boolean(string="Is Current Occupation")


class MalaaLoan(models.Model):
    _inherit = 'loan.order'
    _description = 'Loan request from Malaa'

    def update_loan_request_status(self):  # TODO: Update Status of loan in website & Malaa
        # base_url = 'https://fuelfinance.sa/api/webhook/loan-status' # Live URL
        base_url = 'https://stage.fuelfinance.sa/api/integration/odoo/loan-request' # Live URL
        # base_url = 'https://stage.fuelfinance.sa/api/integration/odoo/loan-request'  # UAT URL
        loan_id = self.loan_record
        status = self.state
        amount = self.loan_amount
        interest_rate = self.rate_per_month
        duration = self.loan_term
        reject_reason = self.new_reject_reason
        total_amount = self.loan_sum

        print(f"Loan ID: {loan_id}")
        print(f"Status: {status}")
        print(f"Amount: {amount}")
        print(f"Interest Rate: {interest_rate}")
        print(f"Duration: {duration}")

        # , "max_affordability": max_affordability, "score": score
        if self.state == 'approve':  # TODO: Update Status When The Loan is approved
            # Prepare payload
            payload = {
                "loan_id": loan_id,
                "status": "initial_approval",
                "maximum_affordability": {
                    "amount": amount,
                    "interest_rate": interest_rate,
                    "duration": duration,
                },
                "fuel_score": {
                    "fuel_evaluate_mini_range": self.fuel_evaluate_mini_range,
                    "fuel_evaluate_max_range": self.fuel_evaluate_max_range,
                    "fuel_evaluate_value": self.fuel_evaluate_value,
                    "fuel_evaluate_arabic_reasons": self.fuel_evaluate_arabic_reasons,
                    "fuel_evaluate_english_reasons": self.fuel_evaluate_english_reasons,
                    "loan_instrument": self.loan_instrument.id if self.loan_instrument else None,
                    "fuel_credit_instruments": self.fuel_credit_instruments,
                    "fuel_defaults_count": self.fuel_defaults_count,
                    "fuel_defaults_amount": self.fuel_defaults_amount,
                    "last_earliest_loan": str(self.last_earliest_loan) if isinstance(self.last_earliest_loan,
                                                                                     date) else self.last_earliest_loan,
                    "fuel_total_limits": self.fuel_total_limits,
                    "fuel_total_liabilities": self.fuel_total_liabilities,
                    "score_default_line": [
                        {
                            "year": line.year.year if isinstance(line.year, (date, datetime)) else line.year,
                            "product_type": line.product_type,
                        }
                        for line in self.score_default_line
                    ],
                    "score_enquiries_line": [
                        {
                            "year": line.year.year if isinstance(line.year, (date, datetime)) else line.year,
                            "product_type": line.product_type,
                        }
                        for line in self.score_enquiries_line
                    ],
                    "score_instrument_line": [
                        {
                            # "product_type_categorization": line.product_type_categorization,
                            "status": line.status,
                            "credit_limits": line.credit_limits,
                            "installment_amounts": line.installment_amounts,
                            "tenure": line.tenure,
                        }
                        for line in self.score_instrument_line
                    ],
                },
            }
            # Convert payload to JSON
            # payload_json = json.dumps(payload)
            try:
                payload_json = json.dumps(payload)
            except TypeError as e:
                print("Serialization Error:", e)
                raise
            headers = {
                'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", base_url, headers=headers, data=payload_json)
            # Example usage in an API request
            # response = requests.post(api_url, data=payload_json, headers={"Content-Type": "application/json"})

            # payload = json.dumps({"loan_id": loan_id, "status": 'initial_approval',
            #                       "maximum_affordability": {"amount": amount, "interest_rate": interest_rate,
            #                                                 "duration": duration},
            #                       "fuel_score":{}})
            # headers = {
            #     'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
            #     'Accept': 'application/json',
            #     'Content-Type': 'application/json'
            # }
            # response = requests.request("POST", base_url, headers=headers, data=payload)
            print(response)
            print(payload)
            # , "contract_url": contract_url
        elif self.state == 'buying':  # TODO: Update Status When Send contract to customers
            # Fetch installments for the loan
            loan_installments = self.env['loan.installment'].search([('loan_record', '=', loan_id)])
            installments_data = []
            for installment in loan_installments:
                sequence_number = int(installment.seq_name.split('-')[-1].strip())
                installments_data.append({
                    "sequence_number": sequence_number,
                    "due_date": installment.date.isoformat(),
                    "installment_amount": installment.installment_amount,
                    "interest_amount": installment.interest_amount,
                    "principal_amount": installment.principal_amount,
                    "status": installment.state,
                    "paid_at": (
                        installment.payment_id.date.isoformat()
                        if installment.payment_id and hasattr(installment.payment_id, 'date') and isinstance(
                            installment.payment_id.date, (datetime.date, datetime.datetime))
                        else None
                    ),
                    "paid_amount": installment.amount_paid,
                })
                # "contract_url": "contract_url",
                # "total_amount": total_amount,
                # "installments": installments_data
            # Create the payload
            payload_data = {
                "loan_id": loan_id,
                "status": "pending_contract",
            }
            # Convert to JSON for the API request
            payload = json.dumps(payload_data, indent=4)  # `indent=4` makes it pretty-printed
            headers = {
                'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            # Send the API request
            response = requests.request("POST", base_url, headers=headers, data=payload)
            print(response)
            print("Payload data (JSON):", payload)
        elif self.state == 'disburse':  # TODO: Update Status When the Contract is Disburse
            payload = json.dumps({"loan_id": loan_id, "status": 'pending_disburse'})
            headers = {
                'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", base_url, headers=headers, data=payload)
            print(response)
            print(payload)
        elif self.state == 'active':  # TODO: Update Status When the Loan is active
            payload = json.dumps({"loan_id": loan_id, "status": 'issued'})
            headers = {
                'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", base_url, headers=headers, data=payload)
            print(response)
            print(payload)
        elif self.state == 'reject':  # TODO: Update Status When the Loan is rejected
            payload = json.dumps(
                {"loan_id": loan_id, "status": 'rejected', "rejection_reason": reject_reason},
                ensure_ascii=False  # Preserve Arabic characters
            )
            headers = {
                'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=utf-8'
            }
            response = requests.request("POST", base_url, headers=headers,
                                        data=payload.encode('utf-8'))  # Encode as UTF-8
            print(response)
            print(payload)
        elif self.state == 'close':  # TODO: Update Status When the Loan is closed
            payload = json.dumps({"loan_id": loan_id, "status": 'closed'})
            headers = {
                'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", base_url, headers=headers, data=payload)
            print(response)
            print(payload)
        elif self.state == 'cancel':  # TODO: Update Status When the Loan is closed
            payload = json.dumps({"loan_id": loan_id, "status": 'Cancel'})
            headers = {
                'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", base_url, headers=headers, data=payload)
            print(payload)
        elif self.state == '0':  # TODO: Update Status When the Contract Canceled by customers
            payload = json.dumps({"loan_id": loan_id, "status": 'canceled'})
            headers = {
                'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", base_url, headers=headers, data=payload)
            print(response)
            print(payload)
        else:
            return

    def update_installments_status(self):  # TODO: Update Status of loan in website & Malaa
        # base_url = 'https://fuelfinance.sa/api/webhook/loan-status' # Live URL
        base_url = 'https://stage.fuelfinance.sa/api/integration/odoo/loan-request'  # UAT URL
        loan_id = self.loan_record

        loan_installments = self.env['loan.installment'].search([('loan_record', '=', loan_id)])
        installments_data = []
        for installment in loan_installments:
            sequence_number = int(installment.seq_name.split('-')[-1].strip())
            installments_data.append({
                "sequence_number": sequence_number,
                "due_date": installment.date.isoformat(),
                "installment_amount": installment.installment_amount,
                "interest_amount": installment.interest_amount,
                "principal_amount": installment.principal_amount,
                "status": installment.state,
                "paid_at": (
                    installment.payment_id.date.isoformat()
                    if installment.payment_id and hasattr(installment.payment_id, 'date') and isinstance(
                        installment.payment_id.date, (datetime.date, datetime.datetime))
                    else None
                ),
                "paid_amount": installment.amount_paid,
            })
        # Create the payload
        payload_data = {
            "loan_id": loan_id,
            "installments": installments_data
        }
        # Convert to JSON for the API request
        payload = json.dumps(payload_data, indent=4)  # `indent=4` makes it pretty-printed
        headers = {
            'x-secret': 'KDW3E8TtZoELBYqMeMWBpU2INbTddqsv',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        # Send the API request
        response = requests.request("POST", base_url, headers=headers, data=payload)
        print(response)
        print("Payload data (JSON):", payload)

    # def action_malaa_submit(self):
    #     self.update_loan_request_status()
