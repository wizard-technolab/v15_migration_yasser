import numpy as np
import numpy_financial as npf
import psycopg2
from bs4 import BeautifulSoup
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, date, timedelta


class LoanScore(models.Model):
    _inherit = 'loan.order'
    _description = 'Loan Score'

    # CREDIT SCORE INFORMATION
    score_default_line = fields.One2many("score.default", 'loan_default_score')
    score_enquiries_line = fields.One2many("score.enquiries", 'loan_enquiries_score')
    score_instrument_line = fields.One2many("score.instrument", 'loan_instrument_score')
    default_score = fields.Many2one('score.default')
    enquiries_score = fields.Many2one('score.enquiries')
    instrument_score = fields.Many2one('score.instrument')

    fuel_evaluate_mini_range = fields.Float()
    fuel_evaluate_max_range = fields.Float()
    fuel_evaluate_value = fields.Float()
    fuel_evaluate_arabic_reasons = fields.Char()
    fuel_evaluate_english_reasons = fields.Char()

    # FINANCIAL SUMMARY AGGREGATE STATISTICS
    loan_instrument = fields.Many2one('credit.instrument.api', string='Score')
    fuel_credit_instruments = fields.Float(string="Fuel Credit Instruments", compute="_compute_fuel_credit_instruments",
                                           store=True)  # مجموع الطلبات النشطة بدون الجوال
    fuel_defaults_count = fields.Integer()  # مجموع الطلبات المتعثرة
    fuel_defaults_amount = fields.Float()  # اجمالي مبالغ الطلبات المتعثرة
    last_earliest_loan = fields.Date(readonly=True, compute='_compute_last_earliest_loan')  # تاريخ احدث طلب
    fuel_total_limits = fields.Float(default=1)  # اجمالي مبالغ الطلبات النشطة
    fuel_total_liabilities = fields.Float()  # اجمالي الالتزامات
    fuel_ava_defaults = fields.Float(compute='_compute_fuel_ava_defaults')  # متوسط التعثرات
    fuel_total_inquiries = fields.Integer()  # اجمالي عدد الاستعلامات
    limit_avar_requested = fields.Float(compute='_compute_limit_avar_requested')  # متوسط المبالغ التي طلبها  العميل خلال السنه

    ################################## Start Fuel Score ####################################
    @api.depends('creditInstrument.creditInstrumentStatusCode',
                 'creditInstrument.code',
                 'creditInstrument.ciLimit')
    def _compute_fuel_credit_instruments(self):
        for rec in self:
            active_instruments = self.env['credit.instrument.api'].search([
                ('creditInstrumentStatusCode', '=', 'A'),
                ('code', '!=', 'MBL')
            ])
            active = rec.creditInstrument.filtered(
                lambda r: r.creditInstrumentStatusCode == 'A' and r.code != 'MBL'
            )
            count_active_instruments = len(active)
            _logger.info(f"Active Instruments Count: {count_active_instruments}")
            _logger.info(f"Active Instruments: {active_instruments.ids}")
            if count_active_instruments > 0:
                rec.fuel_credit_instruments = rec.fuel_total_limits / count_active_instruments
            else:
                rec.fuel_credit_instruments = 0

    @api.depends('creditInstrument.creditInstrumentStatusCode', 'creditInstrument.ciIssuedDate')
    def _compute_last_earliest_loan(self):
        for rec in self:
            active_instruments = self.env['credit.instrument.api'].search([
                ('creditInstrumentStatusCode', '=', 'A')
            ])
            if active_instruments:
                try:
                    dates = [
                        datetime.strptime(instrument.ciIssuedDate, '%d/%m/%Y')
                        for instrument in active_instruments if instrument.ciIssuedDate
                    ]
                    rec.last_earliest_loan = max(dates).date() if dates else None
                except ValueError as e:
                    raise ValueError(f"Error parsing date: {e}. Ensure dates are in the format 'DD/MM/YYYY'.")
            else:
                rec.last_earliest_loan = None

    @api.depends('creditInstrument.creditInstrumentStatusCode', 'creditInstrument.ciLimit',
                 'creditInstrument.ciIssuedDate')
    def _compute_limit_avar_requested(self):
        current_year_start = datetime(datetime.now().year, 1, 1)
        current_year_end = datetime(datetime.now().year, 12, 31)

        for rec in self:
            active = []
            total_ci_limit = 0

            for r in rec.creditInstrument:
                if not r.ciIssuedDate:
                    _logger.warning(f"Empty ciIssuedDate for record ID {r.id}")
                    continue

                try:
                    issued_date = datetime.strptime(r.ciIssuedDate.strip(), '%d/%m/%Y')
                    if (r.creditInstrumentStatusCode == 'A'
                            and r.code != 'MBL'
                            and current_year_start <= issued_date <= current_year_end):
                        active.append(r)
                        total_ci_limit += r.ciLimit
                except ValueError:
                    _logger.warning(f"Invalid date format for ciIssuedDate: {r.ciIssuedDate}")
                    continue

            count_active_instruments = len(active)
            _logger.info(f"Active Instruments Count: {count_active_instruments}")
            _logger.info(f"Total ciLimit for Active Instruments: {total_ci_limit}")

            if count_active_instruments > 0:
                rec.limit_avar_requested = total_ci_limit / count_active_instruments
            else:
                rec.limit_avar_requested = 0

    @api.depends('simahDefault.code', 'simahDefault.pDefOutstandingBalance')
    def _compute_fuel_ava_defaults(self):
        for rec in self:
            defaults = self.env['simah.default.api'].search([('code', '!=', 'MBL'), ('code', '!=', 'LND')])
            if defaults:
                balances = [float(d.pDefOutstandingBalance or 0) for d in defaults]
                rec.fuel_ava_defaults = sum(balances) / len(balances) if balances else 0
            else:
                rec.fuel_ava_defaults = 0

    @api.model
    def _compute_average_fuel_defaults_amount(self):
        for rec in self:
            result = self.read_group(
                [('fuel_defaults_amount', '!=', 0)],
                ['fuel_defaults_amount'],
                []
            )
            if result:
                total = result[0].get('fuel_defaults_amount', 0)
                count = result[0].get('__count', 0)
                return total / count if count > 0 else 0
            return 0
    ################################## End Fuel Score ####################################

class ScoreDefault(models.Model):
    _name = 'score.default'
    _description = 'Score Default'

    # AGGREGATE DEFAULT INFORMATION
    loan_default_score = fields.Many2one('loan.order')
    year = fields.Date()
    product_type = fields.Char()


class ScoreEnquiries(models.Model):
    _name = 'score.enquiries'
    _description = 'Score Enquiry'

    # AGGREGATES OF PREVIOUS CREDIT INQUIRIES
    loan_enquiries_score = fields.Many2one('loan.order')
    year = fields.Date()
    product_type = fields.Char()


class creditInstrument(models.Model):
    _name = 'score.instrument'
    _description = 'Score Instrument'

    # CREDIT INSTRUMENTS AGGREGATE SUMMARY
    loan_instrument_score = fields.Many2one('loan.order')
    Product_type_categorization = fields.Char()
    status = fields.Char()
    credit_limits = fields.Float()
    installment_amounts = fields.Float()
    tenure = fields.Integer()
