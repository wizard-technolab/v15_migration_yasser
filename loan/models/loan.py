# -*- coding: utf-8 -*-
import locale
from http.client import responses

import numpy as np
import numpy_financial as npf
import math
from bs4 import BeautifulSoup
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError, AccessError
from odoo.fields import Command
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser
import random
from hijri_converter import convert
import requests
import json
import time
import logging


_logger = logging.getLogger(__name__)


######################################################### * Loan Type * ###############################################

class LoanType(models.Model):
    _name = 'loan.type'
    _description = 'Loan Type'

    name = fields.Char(string='Loan Type', required=True, store=True, tracking=True)
    rate = fields.Float(store=True, string="Rate")
    is_select = fields.Boolean(string='is Select')
    security_type = fields.Selection([('no', 'NO'), ('yes', 'YES')], string='Security Type', default='no', store=True,
                                     readonly=True)
    product_type = fields.Selection([('pln', 'PLN'), ('mtg', 'MTG')], string='Product Type', default='pln', store=True,
                                    readonly=True)
    salary_flag = fields.Selection([('n', 'N'), ('y', 'Y')], string='Salary Assignment Flag', default='n', store=True,
                                   readonly=True)
    sub_product = fields.Selection([('t', 'TWRK'), ('m', 'MURB')], string='Sub Product Type', default='t', store=True)
    id_type = fields.Selection([('t', 'T'), ('r', 'R')], string='ID Type', default='t', store=True, readonly=True)
    disburse_account = fields.Many2one("account.account", required=True, string="Disburse Account")
    installment_account = fields.Many2one("account.account", required=True, string="Installment Account")
    interest_account = fields.Many2one("account.account", required=True, string="Interest Account")
    unearned_interest_account = fields.Many2one("account.account", required=True, string="Unearned Interest Account")
    disburse_journal = fields.Many2one("account.journal", required=True, string="Disburse Journal")
    payment_journal = fields.Many2one("account.journal", required=True, string="Payment Journal")
    report_id = fields.Many2one('ir.actions.report')

    @api.onchange('name')
    def select_loan_type(self):
        for rec in self:
            try:
                if rec.name:
                    rec.is_select = True
                elif rec.name:
                    rec.is_select = False
                else:
                    pass
            except ValueError:
                print(f"Cannot select '{rec.name}' .")


######################################################### * Loan Request * ############################################


class Loan(models.Model):
    _name = 'loan.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Loan Request'

    name = fields.Many2one("res.partner", required=True, string="Customer")
    loan_type = fields.Many2one("loan.type", string="Loan Type", domain=[('is_select', '=', False)], tracking=True,
                                store=True)
    trigger_loan_type = fields.Many2one("loan.type", string="Select Loan Type", domain=[('is_select', '=', False)])
    account_analytic = fields.Many2one("account.analytic.account", string="Flag")
    account_analytic_line = fields.Many2many(
        "crossovered.budget.lines",
        string="Budget Line",
        domain="[('analytic_account_id', '=', account_analytic)]"
    )
    account_budget_ids = fields.Many2many('crossovered.budget', string="Budgets")

    installment_line_id = fields.Many2one("loan.installment", string="Installments")
    loan_record = fields.Integer(required=True, index=True)  # this field for validation if the request Repeated
    request_date = fields.Date(readonly=True, default=lambda self: fields.datetime.now())
    date = fields.Date('Date')
    request_date_date = fields.Datetime(string='Request Date', readonly=True,
                                        default=lambda self: fields.datetime.now())
    as_of_date = fields.Datetime(string='AS Of Date', readonly=True,
                                 default=lambda self: fields.datetime.now())
    cycle_id = fields.Datetime(string='Cycle ID', readonly=True,
                               default=lambda self: fields.datetime.now())
    hijri_date = fields.Char(compute='get_hijri_date', readonly=True)
    approve_date = fields.Date('Approve Date', copy=False)
    cancel_date = fields.Date('Cancel Date', copy=False)
    close_date = fields.Date('Closure Date', copy=False, store=True, compute='action_close_loan')
    disbursement_date = fields.Date('Disbursement Date', copy=False)
    user = fields.Many2one("res.users", readonly=True, string="User", default=lambda self: self.env.user)
    credit_user = fields.Many2one("res.users", string="Credit User", domain=lambda self: [("groups_id", "=",
                                                                                           self.env.ref(
                                                                                               "loan.group_loan_credit").id)])
    crm_user_id = fields.Many2one("res.users", string="Sales User", domain=lambda self: [("groups_id", "=",
                                                                                          self.env.ref(
                                                                                              "loan.group_sales_exa_call").id)])
    company = fields.Many2one("res.company", readonly=True, string="Company", default=lambda self: self.env.company)
    loan_term = fields.Integer(string="Loan Term", default=1)
    loan_term_days = fields.Integer(string="Term Days")
    loan_amount = fields.Monetary(related='name.loan_amount', string="Loan Amount", copy=False,
                                  store=True)
    nationality_code = fields.Char(related='name.nationality_code', string="N Code", copy=False,
                                   store=True)
    loan_amount_negative = fields.Float(compute='amount_negative', string="Negative Amount", copy=False,
                                        store=True)
    remaining_principle_negative = fields.Float(compute='amount_negative', string="Negative Remaining Principle",
                                                copy=False,
                                                store=True)
    loan_amount_positive = fields.Float(compute='amount_negative', string="Amount to finance", copy=False,
                                        store=True)
    loan_sum = fields.Float(string='Total Loan', store=True, compute='get_total_loan')
    offer_number = fields.Char(related='name.offer_num', string="Offer Number", store=True)
    installment_type = fields.Selection([('M', 'Month'), ('Q', 'Quarter')], default='M', required="1")
    installment_frequency = fields.Char(compute='select_installment_frequency', string='Payment Frequency',
                                        readonly=True, store=True)
    interest_amount = fields.Monetary(string="Interest Amount", compute='get_interest_amount', store=True)
    paid_amount = fields.Monetary(string="Paid Amount", compute='get_total_interest', store=True)
    remaining_amount = fields.Monetary(string="Remaining Amount", compute='get_total_interest', default='1', store=True)
    remaining_interest = fields.Monetary(string="Remaining Interest", compute='get_total_interest', default='1',
                                         store=True)
    remaining_principle = fields.Monetary(string="Remaining Principle", compute='get_total_interest', default='1',
                                          store=True)
    fixed_remaining_amount = fields.Monetary(string="Fixed Remaining Amount", compute='get_total_interest', default='1',
                                             store=True)
    source = fields.Char(string="Source")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    # interest_apply = fields.Boolean(related='loan_type.apply_interest', string='Apply Interest', readonly=True)
    rate = fields.Float(compute='compute_rate_month', string='Interest Rate', readonly=True)
    rate_per_month = fields.Float(string='Interest Month', store=True)
    apr = fields.Float(string='APR', compute='calculate_apr', store=True)
    t_apr = fields.Float(string='T APR', store=True, default=1)
    irr = fields.Float(string='IRR', compute='get_compute_irr', store=True, default=0.0)
    new_apr = fields.Float(string='New APR', store=True, readonly=True)
    yearly_irr = fields.Float(string='Yearly IRR', compute='get_compute_irr', store=True, default=0.0)
    # ---------------------------------Start Reschedule Fields -----------------------------------
    reschedule_installment_ids = fields.One2many('loan.installment', 'reschedule_loan_id',
                                                 string='Reschedule Installment')
    reschedule_irr = fields.Float(string='Reschedule IRR', compute='reschedule_get_compute_irr', store=True)
    reschedule_loan_term = fields.Integer(string="ResLoan Term")
    reschedule_new_apr = fields.Float(string='Reschedule APR', store=True, readonly=True)
    reschedule_loan_amount = fields.Float(compute='amount_negative', string='Loan Amount', store=True, readonly=True)
    reschedule_total_loan = fields.Float(compute='compute_reschedule_amount', string='Total Loan', store=True,
                                         readonly=True)
    reschedule_interest_amount = fields.Float(compute='compute_reschedule_amount', string='Interest Amount',
                                              required=False)
    reschedule_remaining_principle_amount = fields.Monetary(string='Remaining Principle',
                                                            compute='get_reschedule_amounts', default='1')
    reschedule_remaining_interest_amount = fields.Monetary(string='Remaining Interest',
                                                           compute='get_reschedule_amounts', default='1')
    reschedule_remaining_total_amount = fields.Monetary(string='Remaining Total', compute='get_reschedule_amounts',
                                                        default='1',
                                                        store=False)
    reschedule_paid_amount = fields.Monetary(string='Paid amount', compute='get_reschedule_amounts', default='1',
                                             store=False)
    reschedule_late_amount = fields.Monetary(string='Late amount', compute='_compute_reschedule_final_amount',
                                             currency_field='currency_id')
    reschedule_late_interest_amount = fields.Monetary(compute='_compute_reschedule_final_amount')
    reschedule_early_amount = fields.Monetary(string='Early amount', compute='_compute_reschedule_final_amount',
                                              default='1',
                                              store=True)
    reschedule_early_interest_amount = fields.Monetary(compute='_compute_reschedule_final_amount')
    reschedule_unpaid_interest = fields.Monetary(compute='_compute_reschedule_final_amount')
    reschedule_unpaid_installment_ids = fields.Many2many('loan.installment', compute='_compute_reschedule_final_amount')
    # ---------------------------------End Reschedule Fields -----------------------------------

    interest_amount_month = fields.Monetary(string="Interest Amount Month", compute='get_interest_per_month',
                                            store=True)
    state = fields.Selection(
        [('review-kyc', 'Simah'), ('initial_approval', 'Initial approval'), ('create', 'Confirm'),
         ('final_approval', 'Final approval'),
         ('decision', 'Decision'), ('approve', 'Approve'), ('contract', 'Contract'), ('azm contract', 'Signed'),
         ('buying', 'Contract'), ('disburse', 'Disburse'), ('open', 'Open'), ('early', 'Early C'), ('close', 'Close'),
         ('cancel', 'Cancel'), ('reject', 'Reject'), ('archive', 'Archive'), ('new', 'New Application'),
         ('pending', 'Pending'),
         ('return', 'Return'), ('simah', 'Simah Check'),
         ('l1', 'L1'), ('l2', 'L2'), ('active', 'Active'), ('malaa', 'Final MFS')],
        string='Status', required=True)
    # track_visibility = 'onchange'

    seq_num = fields.Char(string='Request Reference', required=True, copy=False, readonly=True,
                          index=True, default=lambda self: _('New'))
    disburse_account = fields.Many2one("account.account", string="Disburse Account")
    disburse_journal = fields.Many2one("account.journal", string="Disburse Journal")
    disburse_journal_entry = fields.Many2one('account.move', string='Disburse Account Entry', copy=False)
    early_payment_id = fields.Many2one('account.payment', copy=False)
    early_move_id = fields.Many2one('account.move', string='Early Entry', copy=False)
    disburse_payment_id = fields.Many2one('account.payment', readonly=True)
    installment_ids = fields.One2many('loan.installment', 'loan_id', string='Installments')
    reschedule_date = fields.Date(string='Reschedule Date', required=False, store=True)
    applicant_type = fields.Char(string='Applicant Type', default='P', store=True, readonly=True)
    product_status = fields.Char(compute='select_product_status', string='Product Status', readonly=True, store=True)
    # installment_date = fields.Date(compute='edit_date_function', string='date', store=True)

    reject_reason = fields.Selection(
        [('1', 'Re-evaluation'), ('2', 'High DBR'), ('3', 'Income is Low'),
         ('4', 'The vehicle does not qualify for the companys terms'),
         ('5', 'The existing contract is less than permissible'), ('6', 'Age is less than allowed'),
         ('7', 'The age is greater than the allowed'), ('8', 'The documents are incorrect'),
         ('9', 'The information is incorrect'), ('10', 'Job is not supported'),
         ('11', 'The sponsor information is incorrect'), ('12', 'Exceeding the maximum financing amount'),
         ('13', 'The employer is not approved'), ('14', 'Negative site visit'), ('15', 'High risk company'),
         ('16', 'discontinued company'), ('17', 'Duplicate request'), ('18', 'Product not eligible'),
         ('19', 'Working period is low'), ('20', 'legal case'),
         ('12', 'He does not answer the phone'), ('22', 'There is no proof of income'),
         ('23', 'He has stumbled into the fuel company'), ('24', 'defaulted on fuel company'),
         ('25', 'Bad Payment history in Simah'), ('26', 'Stumbled upon a feature'),
         ('27', 'Customer risk is high'), ('28', 'rejected'),
         ('29', 'Out of area'), ('30', 'His position Stopped'),
         ('31', 'It is on the terrorist list'), ('32', 'Incomplete application form'),
         ('33', 'The existing balance is sufficient')], string='Reject Reason', copy=False)

    new_reject_reason = fields.Selection(
        [('العمر أقل من المسموح به', 'العمر أقل من المسموح به'), ('الراتب أقل من المطلوب', 'الراتب أقل من المطلوب '),
         ('سداد غير منتظم في سمه', 'سداد غير منتظم في سمه'),
         ('مخاطر العميل عالية', 'مخاطر العميل عالية'), ('مخاطر جهة العمل عالية', 'مخاطر جهة العمل عالية'),
         ('مدة الخدمة اقل من المسموح به', 'مدة الخدمة اقل من المسموح به'),
         ('إلتزامات إئتمانية عالية', 'إلتزامات إئتمانية عالية'), ('جهة العمل غير معتمدة', 'جهة العمل غير معتمدة'),
         ('المهنة غير معتمدة', 'المهنة غير معتمدة'),
         ('العمر أكبر من المسموح به', 'العمر أكبر من المسموح به'),
         ('تجاوز الحد الأقصى لمبلغ التمويل', 'تجاوز الحد الأقصى لمبلغ التمويل'),
         ('إلتزامات إئتمانية عالية Tabby & Tamara', 'إلتزامات إئتمانية عالية (Tabby & Tamara)'),
         (
             'غير منتظم بالسداد لدى شركة فيول في العقد الحالي',
             'غير منتظم بالسداد لدى شركة فيول للتمويل في العقد الحالي')],
        string='Reject Reasons')

    # ('13', 'The employer is not approved'), ('14', 'Negative site visit'), ('15', 'High risk company'),
    # ('16', 'discontinued company'), ('17', 'Duplicate request'), ('18', 'Product not eligible'),
    # ('19', 'Working period is low'), ('20', 'legal case'),
    # ('12', 'He does not answer the phone'), ('22', 'There is no proof of income'),
    # ('23', 'He has stumbled into the fuel company'), ('24', 'defaulted on fuel company'),
    # ('25', 'Bad Payment history in Simah'), ('26', 'Stumbled upon a feature'),
    # ('27', 'Customer risk is high'), ('28', 'rejected'),
    # ('29', 'Out of area'), ('30', 'His position Stopped'),
    # ('31', 'It is on the terrorist list'), ('32', 'Incomplete application form'),
    # ('33', 'The existing balance is sufficient')
    reject_user_id = fields.Many2one('res.users', 'Reject By', readonly=True, default=lambda self: self.env.user)
    reject_date = fields.Datetime(string='Reject Date', readonly=True, default=lambda self: fields.datetime.now())
    terminate_user_id = fields.Many2one('res.users', 'Terminate By', readonly=True, default=lambda self: self.env.user)
    terminate_date = fields.Datetime(string='Terminate Date', readonly=True, default=lambda self: fields.datetime.now())
    terminate_reason = fields.Text('Terminate Reason', copy=False)

    loan_amount_limiting = fields.Float(string="Loan Amount Limit",
                                        compute='_loan_amount_value',
                                        readonly=True, store=True)
    loan_limit_month = fields.Float(related='name.compare_limit', string='Limit', store=True)

    fees = fields.Float(string="Administrative fees", store=True)
    tax_id = fields.Float(store=True, string="Tax")
    tax_id_fees = fields.Float(store=True, string="Total Tax with Fees", compute='_get_total_tax_fees')

    iban = fields.Char(related='name.iban_number', string="IBAN Number")
    phone_customer = fields.Char(related='name.phone', string="Phone Number")
    identification_id = fields.Char(related='name.identification_no', string="Identification ID", store=True)
    birth_date = fields.Date(related='name.birth_of_date', string="BOfD")
    total_loan = fields.Float(string='Total', compute='_get_sum', store=True)
    nationality_loan = fields.Selection(related='name.nationality', string="Nationality")
    marital_status_loan = fields.Selection(related='name.marital_status', string="Loan Marital Status")
    gender_loan = fields.Char(related='name.gender_code', string="Gender", store=True)
    number_dependents_loan = fields.Integer(related='name.number_dependents', string="Number Dependents")
    certificate_level_loan = fields.Selection(related='name.certificate', string="Certificate Level Loan")
    employer_loan = fields.Char(related='name.employer', string="Employer")
    sector_loan = fields.Selection(related='name.sectors', string="Sector")
    years_work_loan = fields.Date(related='name.years_work', string="Years Work")
    classification_employer_loan = fields.Selection(related='name.classification_employer', string="Classification")
    years_retire_loan = fields.Date(related='name.years_retire', string="Joining Date")
    basic_salary_loan = fields.Float(related='name.basic_salary', string="Basic Salary")
    total_salary_loan = fields.Float(related='name.total_salary', string="Total Salary")
    total_liability_loan = fields.Float(related='name.total_liability', string="Total Liability Loan")
    installment_comp_loan = fields.Float(related='name.installment_comp', string="Installment")
    # store_comp_loan = fields.Float(related='name.total_installment_liability', string="Store")
    other_liability_loan = fields.Float(related='name.other_liability', string="Other")
    liability_loan = fields.Float(related='name.liability', string="Liability")
    installment_percentage_loan = fields.Float(related='name.installment_percentage', string="Installment Per")
    comment_loan = fields.Html(related='name.comment', string="Comment")
    installment_start_date = fields.Date(related='installment_ids.date', string="Start Date")
    installment_start_date_hijri = fields.Char(compute='get_hijri_date_installment', readonly=True)
    installment_end_date_hijri = fields.Char(compute='get_hijri_date_installment_end', readonly=True)
    installment_end_date = fields.Date(string="End Date", compute='your_function', store=True, readonly=0)
    reschedule_installment_start_date = fields.Date(string="Start Date", store=True)
    reschedule_installment_end_date = fields.Date(string="End Date", store=True)
    reschedule_interest_rate = fields.Float(compute='compute_reschedule_installment_amount', string='Interest Month',
                                            required=False)
    reschedule_installment_amount = fields.Float(string='Installment Amount', required=False)
    is_reschedule = fields.Boolean(string='Is Reschedule', compute='_compute_is_reschedule_loan', required=False,
                                   store=True)
    state_loan = fields.Selection(related='installment_ids.state', string='State loan')
    month_nb = fields.Integer(string='Month nb')

    installment_month = fields.Float(string='Current Deduction', compute='divid_installment', store=False, default='1')
    total_loan_4 = fields.Float(string='total loan', compute='multi_installment', store=True, default='1')
    old_installment = fields.Float(related='name.installment_comp', string='Old Installment', store=True, default='1')
    total_installment = fields.Float(string='Total Deduction', compute='installment_sum', store=True, default='1')
    # simah_installment = fields.Float(related='simah_ids.dbr_installment', string='Simah Installment', store=True)
    deduction_after = fields.Float(string=' Total DBR', compute='total_deduction_after', store=True)

    # simah_deduction = fields.Monetary(related='simah_data.simah_dbr',string='Simah DBR', store=True)
    deduction_simah_before = fields.Float(related='name.deduction_before', string="Simah Deduction")
    branch = fields.Selection([('manual', 'M-Manual'), ('online', 'O-Online')], string='Branch', required=True,
                              default='online')
    down_payment_loan = fields.Float(related='name.down_payment', string='Down Payment', compute='get_total_interest',
                                     store=True)
    down_payment_percent = fields.Float(string='DP Percentge')
    salary_net = fields.Float(related='name.salary_rate', string='Net Salary')
    crm_seq = fields.Char(string='Seq', store=True, compute='get_crm_seq')
    sanad_number = fields.Char(string='Sanad Number', store=True)
    report_file = fields.Binary()
    file_name = fields.Char()
    nafaes_amount = fields.Float(string='Nafaes Amount', store=True)
    payment_status = fields.Monetary(string='Payment Status', compute='compute_payment_status', default=0)
    late_amount = fields.Monetary(compute='_compute_final_amount', currency_field='currency_id')
    late_interest_amount = fields.Monetary(compute='_compute_final_amount')
    early_amount = fields.Monetary(compute='_compute_final_amount')
    early_interest_amount = fields.Monetary(compute='_compute_final_amount')
    unpaid_interest = fields.Monetary(compute='_compute_final_amount')
    unpaid_installment_ids = fields.Many2many('loan.installment', compute='_compute_final_amount')
    flag_send_sms = fields.Boolean()
    quotation_id = fields.Many2one('purchase.order')
    has_quotation = fields.Boolean(string='has_quotation?')
    installment_amount_loan = fields.Monetary(related='installment_ids.installment_amount', string='Installment Amount')
    principal_amount_loan = fields.Monetary(related='installment_ids.principal_amount', string='principal Amount')
    interest_amount_loan = fields.Monetary(related='installment_ids.interest_amount', string='interest Amount')
    date_loan = fields.Date(related='installment_ids.date', string='Date')
    contact_count = fields.Integer(compute='_compute_contact_counts')
    crm_count = fields.Integer(compute='_compute_crm_counts')
    loan_count = fields.Integer(compute='_compute_count')
    simah_count = fields.Integer(compute='_compute_simah')

    first_unpaid_installment = fields.Date(compute='get_first_unpaid_installment_date', string='Current Due',
                                           store=True)
    last_paid_installment = fields.Date(string='Last Paid Installment', compute='get_first_unpaid_installment_date',
                                        store=True)
    last_paid_installment_date = fields.Date(string='Last Paid Installment Date',
                                             compute='get_first_unpaid_installment_date',
                                             store=True)
    last_paid_installment_amount = fields.Float(string='Last Paid Installment Amount',
                                                compute='get_first_unpaid_installment_date', store=True)
    days_since_first_unpaid = fields.Integer(string='Late Days', compute='get_first_unpaid_installment_date',
                                             store=False)
    bkt = fields.Integer(string='BKT', compute='get_first_unpaid_installment_date',
                         store=True)
    obligation_id = fields.Char()
    show_close_button = fields.Boolean(
        string="Show Close Button",
        compute="_compute_show_close_button",
        store=False,  # This field is not stored in the database
    )
    active = fields.Boolean(string="Active", default=True)

    @api.onchange('account_analytic')
    def _onchange_account_analytic(self):
        self.account_analytic_line = [(5, 0, 0)]

    @api.onchange('account_analytic_line')
    def _onchange_account_analytic_line(self):
        for line in self.account_analytic_line:
            line.loan_order_budget = self

    # ------------------------------- All reschedule function ------------------------------------
    @api.depends('reschedule_installment_ids', 'reschedule_installment_ids.state',
                 'reschedule_installment_ids.interest_amount',
                 'reschedule_installment_ids.principal_amount', 'reschedule_interest_amount',
                 'reschedule_loan_amount')
    def get_reschedule_amounts(self):
        for rec in self:
            reschedule_paid_amount = 0
            total_interest_paid = 0
            total_principal_paid = 0

            if rec.is_reschedule:
                for installment in rec.reschedule_installment_ids:
                    print(f"Installment ID: {installment.id}, State: {installment.state}, "
                          f"Interest Amount: {installment.interest_amount}, Principal Amount: {installment.principal_amount}")

                    if installment.state == 'paid':
                        reschedule_paid_amount += installment.interest_amount + installment.principal_amount
                        total_interest_paid += installment.interest_amount
                        total_principal_paid += installment.principal_amount

            # Assign calculated values
            rec.reschedule_remaining_interest_amount = rec.reschedule_interest_amount - total_interest_paid if rec.reschedule_interest_amount else 0.0
            rec.reschedule_remaining_principle_amount = rec.reschedule_loan_amount - total_principal_paid if rec.reschedule_loan_amount else 0.0
            rec.reschedule_paid_amount = reschedule_paid_amount
            rec.reschedule_remaining_total_amount = (
                rec.reschedule_loan_amount + rec.reschedule_interest_amount - reschedule_paid_amount if rec.reschedule_loan_amount and rec.reschedule_interest_amount else 0.0
            )

    def _compute_reschedule_final_amount(self):
        for r in self:
            r._compute_reschedule_amounts()

    @api.depends('reschedule_installment_ids.principal_amount', 'reschedule_installment_ids.interest_amount',
                 'reschedule_installment_ids.date', 'reschedule_installment_ids.state',
                 'reschedule_installment_ids.amount_paid')
    def _compute_reschedule_amounts(self):
        for r in self:
            r_principle_amount = 0
            r_early_interest_amount = 0
            r_installment_counter = int(self.env['ir.config_parameter'].sudo().get_param('loan.early.installment', 3))
            r_unpaid_interest = 0  # Interest not paid due to early payment
            r_late_amount = 0  # Total late amount
            reschedule_unpaid_installment_ids = self.env['loan.installment'].browse([])  # Initialize properly

            print(f"\nProcessing Record ID: {r.id}")  # Debugging

            for installment_id in r.reschedule_installment_ids:
                if installment_id.state == 'paid':
                    continue

                reschedule_unpaid_installment_ids |= installment_id  # Add to the recordset
                r_principle_amount += installment_id.principal_amount

                # Debugging prints
                print(
                    f"Installment ID: {installment_id.id}, State: {installment_id.state}, Is Late: {installment_id.is_late}")
                print(
                    f"Principal: {installment_id.principal_amount}, Interest: {installment_id.interest_amount}, Amount Paid: {installment_id.amount_paid}")

                # Correct Calculation of Remaining Unpaid Amount
                remaining_unpaid_interest = max(installment_id.interest_amount - installment_id.amount_paid, 0)
                interest_paid = min(installment_id.amount_paid, installment_id.interest_amount)
                principal_paid = installment_id.amount_paid - interest_paid
                remaining_unpaid_principal = max(installment_id.principal_amount - principal_paid, 0)
                remaining_unpaid = remaining_unpaid_principal + remaining_unpaid_interest

                print(
                    f"Remaining Unpaid Principal: {remaining_unpaid_principal}, Remaining Unpaid Interest: {remaining_unpaid_interest}")

                # If installment is partial and late, add only the remaining unpaid amount
                if installment_id.state == 'partial' and installment_id.is_late:
                    print(f"Partial + Late Installment Detected: Adding remaining unpaid amount {remaining_unpaid}")
                    r_late_amount += remaining_unpaid

                # If installment is fully unpaid and late, take the full amount as late
                elif installment_id.state != 'partial' and installment_id.is_late:
                    full_late_amount = installment_id.principal_amount + installment_id.interest_amount
                    print(f"Fully Unpaid + Late Installment Detected: Adding {full_late_amount} to late amount.")
                    r_late_amount += full_late_amount

                # Early interest calculation
                if r_installment_counter > 0 or installment_id.is_late or installment_id.state == 'partial':
                    r_early_interest_amount += installment_id.interest_amount
                else:
                    r_unpaid_interest += installment_id.interest_amount

                if not installment_id.is_late:
                    r_installment_counter -= 1

            # Debugging Output
            print(f"Final Late Amount for Record {r.id}: {r_late_amount}")

            r.reschedule_late_amount = r_late_amount  # Only includes unpaid portion if installment is partial and late
            r.reschedule_early_amount = r_principle_amount + r_early_interest_amount
            r.reschedule_early_interest_amount = r_early_interest_amount
            r.reschedule_unpaid_interest = r_unpaid_interest
            r.reschedule_unpaid_installment_ids = reschedule_unpaid_installment_ids

    # ------------------------------- All reschedule function ------------------------------------

    @api.depends('loan_amount', 'interest_amount', 'down_payment_loan')
    def get_total_loan(self):
        for rec in self:
            rec.loan_sum = (rec.loan_amount + rec.interest_amount) - rec.down_payment_loan
            # rec.update({
            #     'loan_sum': (rec.loan_amount + rec.interest_amount) - rec.down_payment_loan,
            # })

    @api.model
    def create(self, vals):
        if 'loan_term' not in vals:
            loan_type = vals.get('loan_type')
            # Dynamically assign default value if loan_type_id is 1 or 2
            if loan_type in [1, 2, 9, 10]:
                vals['loan_term'] = 12  # Set your desired default value
            else:
                vals['loan_term'] = 1  # Safe default to pass validation
        return super(Loan, self).create(vals)

    @api.onchange('trigger_loan_type')
    def _onchange_trigger_loan_type_field(self):
        if self.trigger_loan_type:
            self.loan_type = self.trigger_loan_type.id
            print('loan_type', self.loan_type.id)

    @api.depends('account_analytic')
    def select_installment_frequency(self):
        for rec in self:
            if rec.account_analytic.total_planned_amount < 500000:
                raise ValidationError(_("The Flag Amount must be Greater than 50000 !!!"))
                print('amount', rec.account_analytic.total_planned_amount)

    @api.depends('installment_type')
    def select_installment_frequency(self):
        for rec in self:
            if rec.installment_type == 'M':
                rec.installment_frequency = 'M'
            elif rec.installment_type == 'Q':
                rec.installment_frequency = 'Q'
            else:
                pass

    @api.depends('state')
    def select_product_status(self):
        for rec in self:
            if rec.state == 'active':
                rec.product_status = 'A'
            elif rec.state == 'close':
                rec.product_status = 'C'
            else:
                pass

    @api.depends('loan_amount', 'down_payment_loan', 'remaining_principle')
    def amount_negative(self):
        for rec in self:
            rec.loan_amount_negative = -abs(rec.loan_amount - rec.down_payment_loan)
            rec.loan_amount_positive = (rec.loan_amount - rec.down_payment_loan)
            rec.remaining_principle_negative = -abs(rec.remaining_principle)
            rec.reschedule_loan_amount = rec.remaining_principle

    @api.constrains('loan_term')
    def less_loan_term(self):
        for rec in self:
            if rec.loan_term >= 61:
                raise ValidationError(_('Error ! Loan Term must be Less Than 60 Months'))
            elif rec.loan_term < 1:
                raise ValidationError(_('Error ! Loan Term must be More Than or equal 1 Month'))

    # def generate_report_file(self):
    #     report_name = "loan.contract_loan_full"
    #     pdf = self.env['report'].sudo().get_pdf([self.id], report_name)
    #     self.report_file = base64.encodestring(pdf)

    @api.depends('installment_amount_loan', 'loan_term')
    def multi_installment(self):
        for rec in self:
            rec.total_loan_4 = (rec.installment_amount_loan * rec.loan_term)

    def get_divided_date(self, recieved_date):
        """
            get day, month and year
        """
        print("\n\n,,,,,,,,,,,,,,,,,", recieved_date)
        if recieved_date:
            return [recieved_date.year, recieved_date.month, recieved_date.day]
        else:
            return [0, 0, 0]

    # @api.model
    # def action_loan_pipeline(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("loan.request_action")
    #     return self._action_update_to_pipeline(action)

    # @api.constrains('identification_id')
    # def check_identification_id(self):
    #     identification_id = self.env['loan.order'].search(
    #         [('identification_id', '=', self.identification_id), ('identification_id', '!=', True),
    #          ('id', '!=', self.id)])
    #     if identification_id:
    #         raise ValidationError(_('Exists ! This customer Already has a Loan Request'))

    # @api.constrains('sanad_number')
    # def len_sanad_number(self):
    #     for rec in self:
    #         rec.sanad_number == 1
    #         if len(str(rec.sanad_number)) < 15 or len(str(rec.sanad_number)) > 15:
    #             raise ValidationError(_('Error ! SANAD NUMBER Incorrect '))

    @api.onchange('name')
    def onchange_name(self):
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_loan_credit').users:
                    print(user.name, 'user')
        # for rec in self:
        #     if rec.name:
        #         partner = rec.name
        #     else:
        #         partner = rec.env['res.partner'].search([('identification_no', '=', rec.identification_id)])
        #     if not partner:
        #         reg = {
        #             'name': rec.contact_name,
        #             'identification_id': rec.identification_id,
        #             'type': 'contact',
        #         }
        #         partner = rec.env['res.partner'].create(reg)
        #         name = partner.id
        #     reg = {
        #         'res_id': rec.id,
        #         'res_model': 'loan.order',
        #         'name': rec.name,
        #     }
        #     if not rec.env['mail.followers'].search(
        #             [('res_id', '=', rec.id), ('res_model', '=', 'loan.order'), ('user', '=', rec.user.id)]):
        #         follower_id = rec.env['mail.followers'].create(reg)
        #         print(rec.user.id)

    # create new follower after a create new loan order
    # @api.onchange('name')
    # def onchange_partner_id(self):
    #     for follower in self.message_follower_ids:
    #         user = self.env['res.users'].search([('name', '=', follower.partner_id.id)],limit=1)
    #         if user != self.env.user:
    #             if user in self.env.ref('loan.group_sales_cancel').users:
    #                 value = self.create(user.id, follower)
    #                 value_id = activity_object.create(value)
    # self.env['loan.order'].create(follower)

    # rec.follower = self.env['res.partner'].search([('name', '=', rec.name.id)])
    # if not self.name:
    #     self.update({
    #         'user': False,
    #     })
    #     return
    # partner_user = self.name.user or self.name.commercial_partner_id.user
    # values = {
    #     'user': self.name and self.name.id or False,
    # }
    # user = self.name.id
    # if not self.env.context.get('not_self_saleperson'):
    #     user = user or self.env.context.get('default_user_id', self.name.create_uid.id)
    # if user and self.user.id != user:
    #     values['user'] = user

    #     if self.name:
    #         partner = self.name
    #     else:
    #         partner = self.env['res.partner'].search([('name', '=', self.name.id)])
    #     if not partner:
    #         reg = {
    #             'name': self.name or self.identification_id,
    #             # 'identification_no': self.identification_no,
    #             'type': 'contact',
    #         }
    #         partner = self.env['res.partner'].create(reg)
    #     name = partner.id
    #     reg = {
    #         'res_id': self.id,
    #         'res_model': 'loan.order',
    #         'name': name,
    #     }

    @api.depends('request_date')
    def get_hijri_date(self):
        if self.request_date:
            date = convert.Gregorian.fromdate(self.request_date).to_hijri().dmyformat()
            self.hijri_date = date
        else:
            self.installment_start_date == False

    @api.depends('installment_start_date')
    def get_hijri_date_installment(self):
        if self.installment_start_date:
            date = convert.Gregorian.fromdate(self.installment_start_date).to_hijri().dmyformat()
            self.installment_start_date_hijri = date
        else:
            self.installment_start_date == False

    @api.depends('installment_end_date')
    def get_hijri_date_installment_end(self):
        if self.installment_end_date:
            date = convert.Gregorian.fromdate(self.installment_end_date).to_hijri().dmyformat()
            self.installment_end_date_hijri = date
        else:
            self.installment_end_date == False

    @api.depends('name')
    def get_crm_seq(self):
        for rec in self:
            if rec.crm_seq == 'False':
                rec.crm_seq = self.env['crm.lead'].search([('partner_id', '=', rec.name.id)]).seq
            else:
                rec.crm_seq == 'True'

    @api.depends('loan_sum', 'loan_term')
    def divid_installment(self):
        for rec in self:
            if rec.loan_amount > 0 and rec.loan_term > 0:
                rec.installment_month = rec.loan_sum / rec.loan_term
            else:
                rec.installment_month = 1.0
            # print(f"Computed installment_month: {rec.installment_month}")
            # rec.update({
            #     'installment_month': rec.fixed_remaining_amount / rec.loan_term,
            # })

    # @api.depends('approve_date', 'installment_start_date')
    # def date_function(self):
    #     fmt = '%Y-%m-%d'
    #     start_date = self.approve_date
    #     end_date = self.installment_start_date
    #     delta = end_date - start_date
    #     print(delta.days)
    # d1 = datetime.strptime(start_date, fmt)
    # d2 = datetime.strptime(end_date, fmt)
    # date_difference = str(d2 - d1)

    @api.depends('loan_sum', 'loan_amount_negative')
    def get_compute_irr(self):
        for rec in self:
            # Initialize default values
            rec.irr = 0.0
            rec.yearly_irr = 0.0

            # Ensure valid loan amount and term
            if rec.loan_amount > 0 and rec.loan_term > 0:
                amount_negative = rec.loan_amount_negative
                if amount_negative < 0:
                    array = [amount_negative]
                    installment = rec.loan_sum / rec.loan_term
                    array += [installment] * rec.loan_term

                    try:
                        result_array = np.array(array)
                        result = npf.irr(result_array)

                        if result is not None and not math.isnan(result):
                            rec.irr = result
                            rec.yearly_irr = result * 12
                            print("IRR:", result)
                        else:
                            rec.irr = 0.0
                            rec.yearly_irr = 0.0
                            print("IRR result is NaN.")
                    except Exception as e:
                        rec.irr = 0.0
                        rec.yearly_irr = 0.0
                        print(f"IRR calculation error: {e}")
                else:
                    print("Initial cash flow must be negative.")
            else:
                print("Invalid loan amount or term.")

    @api.depends('rate_per_month')
    def compute_rate_month(self):
        for rec in self:
            rec.rate = (rec.rate_per_month * 12)

    @api.onchange('down_payment_loan', 'loan_sum')
    def total_deduction_before(self):
        for rec in self:
            if rec.loan_sum > 0:
                rec.down_payment_percent = (rec.down_payment_loan / rec.loan_sum) * 100
            else:
                rec.loan_sum == 1

    @api.depends('old_installment', 'installment_month', 'dbr_installment')
    def installment_sum(self):
        for rec in self:
            rec.update({
                'total_installment': rec.old_installment + rec.installment_month + rec.dbr_installment,
            })

    @api.depends('total_installment', 'salary_net')
    def total_deduction_after(self):
        for rec in self:
            if rec.salary_net > 0:
                rec.deduction_after = rec.total_installment / rec.salary_net
            elif rec.salary_net <= 1:
                rec.deduction_after = 1

    @api.depends('installment_start_date', 'loan_term', 'request_date_date')
    def your_function(self):
        for rec in self:
            if rec.request_date_date.day <= 14:
                rec.installment_end_date = datetime.now() + relativedelta(months=rec.loan_term - 1, day=27)
            else:
                rec.installment_end_date = datetime.now() + relativedelta(months=rec.loan_term - 0, day=27)

    @api.depends('installment_start_date', 'loan_term')
    def edit_date_function(self):
        inc_month = 1
        for rec in self:
            rec.installment_end_date = datetime.now() + relativedelta(months=rec.loan_term - 1, day=27)

    @api.depends('interest_amount', 'loan_amount', 'fees', 'tax_id')
    def _get_sum(self):
        for rec in self:
            rec.update({
                'total_loan': rec.interest_amount + rec.loan_amount + rec.fees + rec.tax_id,
            })

    @api.depends('fees', 'tax_id')
    def _get_total_tax_fees(self):
        for rec in self:
            rec.update({
                'tax_id_fees': rec.fees + rec.tax_id,
            })

    @api.model
    def update_tax_fees(self):
        for rec in self:
            rec.tax_id_fees = rec.fees + rec.tax_id

    @api.model
    def update_remaining_amounts(self):
        for rec in self:
            print(f"Processing record ID: {rec.id}")
            paid_amount = 0
            total_interest_paid = 0
            total_principal_paid = 0
            if not rec.is_reschedule:
                # Debug installments
                for installment in rec.installment_ids:
                    print(f"Installment ID: {installment.id}, State: {installment.state}, "
                          f"Interest Amount: {installment.interest_amount}, Principal Amount: {installment.principal_amount}")
                    if installment.state == 'paid':
                        # paid_amount += installment.interest_amount + installment.principal_amount
                        paid_amount += installment.amount_paid
                        total_interest_paid += installment.interest_amount
                        total_principal_paid += installment.principal_amount
                    elif installment.state == 'partial':

                        remaining_interest = installment.interest_amount
                        remaining_principal = installment.principal_amount
                        amount_paid = installment.amount_paid

                        interest_paid = min(amount_paid, remaining_interest)
                        principal_paid = amount_paid - interest_paid

                        paid_amount += amount_paid
                        total_interest_paid += interest_paid
                        total_principal_paid += principal_paid
                # Calculate remaining values
                rec.remaining_interest = rec.interest_amount - total_interest_paid
                rec.remaining_principle = rec.loan_amount - total_principal_paid
                rec.paid_amount = paid_amount
                rec.remaining_amount = (rec.loan_amount + rec.interest_amount - rec.down_payment_loan) - paid_amount
                rec.fixed_remaining_amount = rec.remaining_amount
            else:
                pass

    @api.depends('rate', 'loan_term')
    def get_interest_per_month(self):
        for rec in self:
            rec.update({
                'interest_amount_month': rec.rate / rec.loan_term * 100,
            })
            # if rec.loan_term > 0:
            #
            # else:
            #     raise ValidationError(_('The Loan Term must be more than Zero'))

    def assign_customer_to_self(self):
        self.ensure_one()
        if not self.credit_user:  # Check if credit_user is not set yet
            self.credit_user = self.env.user  # Assign current user to credit_user
        else:
            raise UserError(
                "The Credit user has already been assigned and cannot be changed.")  # Prevent changes if already set

    def assign_to_sales_user(self):
        self.ensure_one()
        if not self.crm_user_id:  # Check if crm_user_id is not set yet
            self.crm_user_id = self.env.user  # Assign current user to crm_user_id
        else:
            raise UserError(
                "The Sales user has already been assigned and cannot be changed.")  # Prevent changes if already set

    def _compute_contact_counts(self):
        for record in self:
            record.contact_count = self.env['res.partner'].search_count(
                [('identification_no', '=', self.identification_id)])

    def get_contact(self):
        self.ensure_one()
        return {
            'name': _('Customer Data'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [('identification_no', '=', self.identification_id)],
            'context': "{'create': False}"
        }

    def _compute_crm_counts(self):
        for record in self:
            record.crm_count = self.env['crm.lead'].search_count(
                [('partner_id', '=', self.name.id)])

    def get_crm(self):
        self.ensure_one()
        return {
            'name': _('CRM'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'list',
            'target': 'current',
            'domain': [('partner_id', '=', self.name.id)],
            'context': "{'create': False}"
        }

    def _compute_simah(self):
        for record in self:
            record.simah_count = self.env['simah.simah'].search_count(
                [('name', '=', self.name.id)])

    def get_simah(self):
        self.ensure_one()
        return {
            'name': _('Simah Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'simah.simah',
            'view_mode': 'form',
            'target': 'current',
            'domain': [('name', '=', self.name.id)],
            # 'context': "{'create': False}"
            'context': {'default_name': self.name.id},
        }

    def _compute_count(self):
        for record in self:
            record.loan_count = self.env['loan.order'].search_count(
                [('name', '=', self.name.id)])

    def get_loan(self):
        self.ensure_one()
        return {
            'name': _('Loan Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.order',
            'view_mode': 'list',
            'target': 'current',
            'domain': [('name', '=', self.name.id)],
            'context': "{'create': False}"
        }

    def remove_fees_amount(self):
        loan_type_id = [1, 3]
        for rec in self:
            if rec.loan_type.id in loan_type_id:
                rec.fees = 0
                rec.tax_id = 0
            elif rec.loan_type.id == 2:
                rec.fees = rec.loan_amount_positive / 100  # 10% of loan amount
                rec.tax_id = rec.fees * 0.15  # 15% of fees

    @api.constrains('fees')
    def _compute_tax_id(self):
        for rec in self:
            if rec.fees >= 1:
                rec.tax_id = rec.fees * 15 / 100
            else:
                pass

    @api.constrains('loan_amount', 'down_payment_loan', 'loan_type')
    def _compute_fees(self):
        for rec in self:
            if rec.loan_type.id == 1 or 10:
                rec.fees = 0
                rec.tax_id = 0
            elif rec.loan_type.id == 2 or 9:
                rec.fees = ((rec.loan_amount * 1) - rec.down_payment_loan) / 100
            else:
                pass

    @api.depends('loan_amount', 'rate_per_month', 'loan_term', 'down_payment_loan')
    def get_interest_amount(self):
        for rec in self:
            rec._compute_fees()
            if rec.account_analytic.name == "MFS":
                if 'rate_per_month' in rec:  # Assuming the field is already populated from the API
                    api_rate_per_month = rec.rate_per_month
                else:
                    raise ValidationError(_('Rate per month is missing for account "MFS".'))
            else:
                api_rate_per_month = None  # Default to None for non-MFS accounts
            if rec.loan_type.id == 3 or rec.loan_type.id == 10:  # Corrected logical OR
                if rec.loan_term > 0:
                    valid_numbers = (300, 500, 700, 900)
                    if rec.loan_amount in valid_numbers:
                        if rec.loan_term == 1:
                            rec.interest_amount = (rec.loan_amount - rec.down_payment_loan) * rec.loan_term
                        elif rec.loan_term == 2:
                            rec.rate_per_month = api_rate_per_month if api_rate_per_month is not None else 0.50
                            rec.interest_amount = ((
                                                           rec.loan_amount - rec.down_payment_loan) * rec.rate_per_month) * rec.loan_term
                        elif rec.loan_term == 3:
                            rec.rate_per_month = api_rate_per_month if api_rate_per_month is not None else 0.33
                            rec.interest_amount = ((
                                                           rec.loan_amount - rec.down_payment_loan) * rec.rate_per_month) * rec.loan_term
                    elif 901 <= rec.loan_amount < 2500:
                        if rec.loan_term <= 6:
                            rec.rate_per_month = api_rate_per_month if api_rate_per_month is not None else 0.25
                            rec.interest_amount = ((
                                                           rec.loan_amount - rec.down_payment_loan) * rec.rate_per_month) * rec.loan_term
                        else:
                            raise ValidationError(_('The Loan Term Should be Less than or equal to 6 Months'))
                    elif 2500 <= rec.loan_amount < 3500:
                        if rec.loan_term <= 9:
                            rec.rate_per_month = api_rate_per_month if api_rate_per_month is not None else 0.17
                            rec.interest_amount = ((
                                                           rec.loan_amount - rec.down_payment_loan) * rec.rate_per_month) * rec.loan_term
                        else:
                            raise ValidationError(_('The Loan Term Should be Less than or equal to 9 Months'))
                    elif 3500 <= rec.loan_amount < 5000:
                        if rec.loan_term <= 12:
                            rec.rate_per_month = api_rate_per_month if api_rate_per_month is not None else 0.135
                            rec.interest_amount = ((
                                                           rec.loan_amount - rec.down_payment_loan) * rec.rate_per_month) * rec.loan_term
                        else:
                            raise ValidationError(_('The Loan Term Should be Less than or equal to 12 Months'))
                    else:
                        print("The number is not in the range.")
                else:
                    raise ValidationError(_('The Loan Term Should be more than Zero'))
            else:
                if rec.loan_term > 0:
                    rec.interest_amount = ((rec.loan_amount - rec.down_payment_loan) *
                                           (
                                               api_rate_per_month if api_rate_per_month is not None else rec.rate_per_month)) * rec.loan_term
                else:
                    raise ValidationError(_('The Loan Term Should be more than Zero'))

    @api.model
    def update_bkt(self):
        for rec in self:
            # Determine the dataset to use
            if rec.is_reschedule and rec.reschedule_installment_ids:
                # Get the latest rescheduled installment
                relevant_installment = rec.reschedule_installment_ids.sorted(lambda r: r.date or r.id)[-1]
            elif not rec.is_reschedule and rec.installment_ids:
                # Get the latest normal installment
                relevant_installment = rec.installment_ids.sorted(lambda r: r.date or r.id)[-1]
            else:
                _logger.info("No installments available for computation.")
                continue  # Skip this record if no relevant installments exist

            # Extract correct overdue field (Replace `days_overdue` with actual field name)
            days_unpaid = getattr(relevant_installment, 'days_overdue', 0)  # Default to 0 if field doesn't exist

            # Compute `bkt`
            if days_unpaid == 0:
                rec.bkt = 0
            elif days_unpaid <= 29:
                rec.bkt = 1
            elif 30 <= days_unpaid <= 59:
                rec.bkt = 2
            elif 60 <= days_unpaid <= 89:
                rec.bkt = 3
            elif 90 <= days_unpaid <= 119:
                rec.bkt = 4
            elif 120 <= days_unpaid <= 149:
                rec.bkt = 5
            elif 150 <= days_unpaid <= 179:
                rec.bkt = 6
            elif 180 <= days_unpaid <= 209:
                rec.bkt = 7
            elif 210 <= days_unpaid <= 239:
                rec.bkt = 8
            elif 240 <= days_unpaid <= 269:
                rec.bkt = 9
            elif 270 <= days_unpaid <= 299:
                rec.bkt = 10
            elif days_unpaid >= 300:
                rec.bkt = (days_unpaid // 30) + 1
            else:
                rec.bkt = days_unpaid / 30

            _logger.info("Computed bkt: %s for record ID: %s", rec.bkt, rec.id)

    @api.model
    def update_remaining_amount(self):
        for rec in self:
            interest = 0
            principle = 0
            for installment in rec.installment_ids:
                if installment.state == 'unpaid':
                    interest += installment.interest_amount
                    principle += installment.principal_amount
            rec.remaining_interest = interest
            rec.remaining_principle = principle
            _logger.info('Remaining Interest: %s', rec.remaining_interest)
            _logger.info('Remaining Principle: %s', rec.remaining_principle)

    @api.depends('installment_ids', 'installment_ids.state', 'installment_ids.interest_amount',
                 'installment_ids.principal_amount', 'interest_amount', 'loan_amount')
    def get_total_interest(self):
        for rec in self:
            print(f"Processing record ID: {rec.id}")
            paid_amount = 0
            total_interest_paid = 0
            total_principal_paid = 0
            if not rec.is_reschedule:
                # Debug installments
                for installment in rec.installment_ids:
                    print(f"Installment ID: {installment.id}, State: {installment.state}, "
                          f"Interest Amount: {installment.interest_amount}, Principal Amount: {installment.principal_amount}")

                    if installment.state == 'paid':
                        # paid_amount += installment.interest_amount + installment.principal_amount
                        paid_amount += installment.amount_paid
                        total_interest_paid += installment.interest_amount
                        total_principal_paid += installment.principal_amount
                    elif installment.state == 'partial':

                        remaining_interest = installment.interest_amount
                        remaining_principal = installment.principal_amount
                        amount_paid = installment.amount_paid

                        interest_paid = min(amount_paid, remaining_interest)
                        principal_paid = amount_paid - interest_paid

                        paid_amount += amount_paid
                        total_interest_paid += interest_paid
                        total_principal_paid += principal_paid
                # Calculate remaining values
                rec.remaining_interest = rec.interest_amount - total_interest_paid
                rec.remaining_principle = rec.loan_amount - total_principal_paid
                rec.paid_amount = paid_amount
                rec.remaining_amount = (rec.loan_amount + rec.interest_amount - rec.down_payment_loan) - paid_amount
                rec.fixed_remaining_amount = rec.remaining_amount
            else:
                pass

    @api.onchange('installment_ids', 'interest_amount')
    def _onchange_total_interest(self):
        self.get_total_interest()

    @api.model
    def update_total_paid_and_remaining(self):
        for rec in self:
            # Initialize the variables
            paid_amount = 0
            remaining_amount = rec.loan_amount + rec.interest_amount - rec.down_payment_loan

            # Loop through the installments to calculate paid and remaining amounts
            for installment in rec.installment_ids:
                if installment.state == 'paid':
                    paid_amount += installment.installment_amount
                    print('Adding paid installment:', installment.installment_amount)

            # Calculate remaining amount after deducting the paid amount
            remaining_amount -= paid_amount

            # Update the record fields with the calculated values
            rec.paid_amount = paid_amount
            rec.remaining_amount = remaining_amount

            print('Total Paid Amount:', rec.paid_amount)
            print('Remaining Amount:', rec.remaining_amount)

    @api.model
    def update_installment_month(self):
        for rec in self:
            rec.installment_month = rec.installment_amount_loan

    @api.depends('installment_ids', 'late_amount', 'reschedule_installment_ids', 'reschedule_late_amount',
                 'is_reschedule')
    def get_first_unpaid_installment_date(self):
        for rec in self:
            # Select the appropriate fields based on is_reschedule
            if rec.is_reschedule:
                installment_ids = rec.reschedule_installment_ids
                late_amount = rec.reschedule_late_amount
            else:
                installment_ids = rec.installment_ids
                late_amount = rec.late_amount

            # Initialize default values
            rec.first_unpaid_installment = False
            rec.days_since_first_unpaid = 0
            rec.bkt = 0
            rec.last_paid_installment = False
            rec.last_paid_installment_amount = 0.0

            unpaid_installments = installment_ids.filtered(lambda inst: inst.state in ['unpaid', 'partial'])
            paid_installments = installment_ids.filtered(lambda inst: inst.state == 'paid')

            # Check if late_amount <= 0, then reset first_unpaid_installment and skip calculations
            if late_amount <= 0:
                rec.first_unpaid_installment = 0
            else:
                # If unpaid installments exist, calculate the first unpaid installment details
                if unpaid_installments:
                    first_unpaid_installment = min(unpaid_installments, key=lambda inst: inst.date)
                    rec.first_unpaid_installment = first_unpaid_installment.date

                    # Calculate the days since the first unpaid installment
                    first_unpaid_date = fields.Date.from_string(first_unpaid_installment.date)
                    current_date = fields.Date.context_today(rec)  # Use context_today for accurate date
                    rec.days_since_first_unpaid = (current_date - first_unpaid_date).days

                    # If late_amount > 0, calculate actual days based on the late amount
                    rec.days_since_first_unpaid = max(1, rec.days_since_first_unpaid)

                    # Calculate bkt (bucket)
                    if rec.days_since_first_unpaid == 0:
                        rec.bkt = 0
                    elif rec.days_since_first_unpaid <= 29:
                        rec.bkt = 1
                    elif rec.days_since_first_unpaid <= 59:
                        rec.bkt = 2
                    elif rec.days_since_first_unpaid <= 89:
                        rec.bkt = 3
                    elif rec.days_since_first_unpaid <= 119:
                        rec.bkt = 4
                    elif rec.days_since_first_unpaid <= 149:
                        rec.bkt = 5
                    elif rec.days_since_first_unpaid <= 179:
                        rec.bkt = 6
                    elif rec.days_since_first_unpaid <= 209:
                        rec.bkt = 7
                    elif rec.days_since_first_unpaid <= 239:
                        rec.bkt = 8
                    elif rec.days_since_first_unpaid <= 269:
                        rec.bkt = 9
                    elif rec.days_since_first_unpaid <= 299:
                        rec.bkt = 10
                    else:
                        rec.bkt = (rec.days_since_first_unpaid // 30) + 1

                    _logger.info('Computed bkt: %s', rec.bkt)
                else:
                    # No unpaid installments found, reset the fields
                    rec.first_unpaid_installment = False
                    rec.days_since_first_unpaid = 0
                    rec.bkt = 0

            # If paid installments exist, calculate the last paid installment details
            if paid_installments:
                last_paid_installment = max(paid_installments, key=lambda inst: inst.date)
                rec.last_paid_installment = last_paid_installment.date
                rec.last_paid_installment_date = last_paid_installment.payment_date
                rec.last_paid_installment_amount = last_paid_installment.installment_amount
            else:
                rec.last_paid_installment = False
                rec.last_paid_installment_amount = 0.0

    @api.constrains('name', 'identification_id')
    def check_number_of_client_loan(self):
        for rec in self:
            if rec.name and rec.identification_id:
                no_of_loan_allow = rec.name.allow_loan
                identification = rec.identification_id
                # start_date = date(date.today().year, 1, 1)
                # start_date = start_date.strftime('%Y-%m-%d')
                # end_date = date(date.today().year, 12, 31)
                # end_date = end_date.strftime('%Y-%m-%d')
                loan_num = rec.env['loan.order'].search(
                    [('identification_id', '=', identification),
                     ('state', 'not in', ['cancel', 'reject'])])

            # if len(loan_num) > no_of_loan_allow:
            #     raise ValidationError(_("This Customer allow only one Loan Request in Year !!!"))

    @api.depends('loan_limit_month')
    def _loan_amount_value(self):
        for rec in self:
            rec.loan_amount_limiting = rec.loan_limit_month

    @api.model
    def button_done(self):
        vals = {
            # 'loan_amount_limit': self.loan_amount_limit.id,
            'loan_month': self.loan_month.id,
        }
        self.env['loan.order'].create(vals)
        for rec in self:
            rec.write({'state': 'done'})

    @api.model
    def button_reset(self):
        for rec in self:
            rec.write({'state': 'simah'})

    @api.model
    def button_cancel(self):
        for rec in self:
            rec.write({'state': 'Cancel'})

    @api.model
    def create(self, vals):
        if vals.get('seq_num', _('New')) == _('New'):
            vals['seq_num'] = self.env['ir.sequence'].next_by_code('loan_seq') or _('New')
        res = super(Loan, self).create(vals)
        return res

    def get_monthly_interest(self):
        if self.rate and self.loan_term and self.loan_amount and self.installment_type:
            loan_term = self.loan_term
            if self.installment_type == 'month':
                loan_term = self.loan_term * 1
            k = 12
            i = self.rate / 100
            a = i / k or 0.00
            b = (1 - (1 / ((1 + (i / k)) ** loan_term))) or 0.00
            emi = ((self.loan_amount * a) / b) or 0.00
            tot_amt = emi * loan_term
            monthly_interest = (tot_amt - self.loan_amount) / loan_term
            return monthly_interest

    @api.depends('interest_amount', 'loan_amount')
    def get_total_amount_to_pay(self):
        for loan in self:
            loan.total_amount_to_pay = 0
            loan.total_amount_to_pay = loan.interest_amount + loan.loan_amount

    # Send
    # Message
    # To
    # Active
    # Customer
    # Send Data
    # ------------------------- | Send Message [Messgatiy]| -----------------------
    def send_messeage(self, phone, message):
        values = '''{
                                                            "userName": "Fuelfinancesa",
                                                              "numbers": "''' + phone + '''",
                                                              "userSender": "fuelfinance",
                                                              "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                                              "msg": "''' + message + '''"
                                                            }'''

        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        values = values.encode()
        requests.post('https://www.msegat.com/gw/sendsms.php',
                      data=values,
                      headers=headers)

    # ------------------------------------------------------
    # ------------------- | Rosom Cron  | ------------------
    # ------------------------------------------------------
    @api.model
    def rosom_monthly_invoice(self):
        _logger = logging.getLogger(__name__)
        _logger.info('++++++++++++++++++++++++ | Start Rosom Monthly Cron| +++++++++++++++++++++++')
        today_date = datetime.now().date()
        # Log today's date for troubleshooting
        _logger.info('Today\'s date: %s', today_date)
        if today_date.day == 26:
            _logger.info('Day = : %s', today_date.day)

            # Get all customers
            selected_loan_ids = self._context.get('active_ids', [])
            _logger.info('Selected loan IDs: %s', selected_loan_ids)

            selected_loans = self.env['loan.order'].search(
                [('id', 'in', selected_loan_ids), ('state', '=', 'active')]
            )

            _logger.info('Found Loans: %s', selected_loans)

            # current_date = datetime.now().date()
            current_date = datetime.strptime(f'{datetime.now()}'.split(' ')[0], '%Y-%m-%d').date()

            # Reference to the server action to be called
            # server_action = loan.action_create_rosom_bills()
            # self.env.ref(('loan.action_cron_rosom_monthly'))  # Adjust with your server action ID

            current_date = datetime.now().date()

            for loan in selected_loans:
                _logger.info('Processing Loan ID: %s', loan.id)
                for installment in loan.installment_ids:
                    _logger.info('Processing Installment: %s for Loan ID: %s', installment.id, loan.id)
                    _logger.info('Installment ID: %s, Date: %s, State: %s', installment.id, installment.date,
                                 installment.state)
                    # Check if installment is due today or overdue and is unpaid
                    if installment.date <= current_date and installment.state == 'unpaid':
                        try:
                            _logger.info('Creating Rosom bills for Loan ID: %s', loan.id)
                            result = loan.action_create_rosom_bills()
                            _logger.info('Rosom Created for Loan ID: %s, Result: %s', loan.id, result)
                            loan.message_post(body="Rosom Sent Successfully")
                        except Exception as e:
                            _logger.error('Failed to create Rosom for Loan ID: %s, Error: %s', loan.id, str(e))
                    else:
                        _logger.info('Installment not due or already paid for Loan ID: %s', loan.id)

        # _logger.info('++++++++++++++++++++++++ | Start Rosom Monthly Cron| +++++++++++++++++++++++')
        # today_date = datetime.now().date()
        #
        # # Log today's date for troubleshooting
        # _logger.info('Today\'s date: %s', today_date)
        #
        # if today_date.day == 24:
        #     _logger.info('Day = : %s', today_date.day)
        #
        #     # Get all customers
        #     selected_loan_ids = self._context.get('active_ids', [])
        #     _logger.info('Selected loan IDs: %s', selected_loan_ids)
        #
        #     selected_loans = self.env['loan.order'].search(
        #         [('id', 'in', selected_loan_ids), ('state', '=', 'simah')]
        #     )
        #
        #     _logger.info('Found Loans: %s', selected_loans)
        #
        #     current_date = datetime.now().date()
        #     for loan in selected_loans:
        #         _logger.info('Processing Loan ID: %s', loan.id)
        #         for installment in loan.installment_ids:
        #             _logger.info('Processing Installment: %s for Loan ID: %s', installment.id, loan.id)
        #             _logger.info('Installment ID: %s, Date: %s, State: %s', installment.id, installment.date,
        #                          installment.state)
        #
        #             # Check if installment date matches and is unpaid
        #             if installment.date == current_date and installment.state == 'unpaid':
        #                 try:
        #                     _logger.info('Creating Rosom bills for Loan ID: %s', loan.id)
        #                     result = loan.action_create_rosom_bills()
        #                     # result = loan.rosom_create_bills()
        #                     _logger.info('Rosom Created for Loan ID: %s, Result: %s', loan.id, result)
        #                     loan.message_post(body="Rosom Sent Successfully")
        #                 except Exception as e:
        #                     _logger.error('Failed to create Rosom for Loan ID: %s, Error: %s', loan.id, str(e))
        #             else:
        #                 _logger.info('Installment not due or already paid for Loan ID: %s', loan.id)

    # ------------------- | Sadad Message | ------------------
    def send_sadad_message(self):
        today_date = datetime.now().date()

        # Check if today is the 27th day of the month
        if today_date.day == 27:
            # Get all customers
            selected_customer_ids = self._context.get('active_ids', [])
            selected_customers = self.env['loan.order'].search(
                [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
            current_date = datetime.strptime(f'{datetime.now()}'.split(' ')[0], '%Y-%m-%d').date()
            for customer in selected_customers:
                for installment in customer.installment_ids:
                    if installment.date == current_date and installment.state == 'unpaid':
                        sadad_message = f"""
                        عزيزنا العميل
    تم اصدار فاتورة سداد من شركة فيول للتمويل بقيمة {installment.interest_amount} ريال، فضلاً بادر بسداد الفاتورة رقم: {customer.rosom_number}
     من خلال فواتير سداد عبر القنوات البنكية باستخدام رقم المفوتر في سداد:
    اسم المفوتر: رسوم
    رقم المفوتر: 901
                        """
                        if customer.name.phone:
                            self.send_messeage(customer.name.phone, sadad_message)
                        # Log the message in the chatter
                        customer.message_post(body=sadad_message)

    def send_message_installment_payment_date(self):
        today_date = datetime.now().date()
        # Calculate the due date for the installment (27th of the month)
        due_date = today_date.replace(day=24)
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])

        # Send Message For All Customer And Printed In Chatter
        for customer in selected_customers:
            current_date = datetime.strptime(f'{datetime.now()}'.split(' ')[0], '%Y-%m-%d')

            if customer.name.phone and customer.rosom_number and customer.name.iban_num and customer.late_amount == 0:
                # Format the installment amount
                formatted_installment_amount = round(customer.installment_month, 2)
                for installment in customer.installment_ids:
                    if installment.date.year == current_date.year and installment.date.month == current_date.month and installment.date.day == 27 and installment.state == 'unpaid':
                        # updated_installment_payment_message = f"""
                        #                             عميلنا العزيز، نود اشعاركم بإقتراب موعد القسط ({customer.installment_month}) ريال.لعقدكم رقم ({customer.seq_num}).
                        #                                 نرجو الالتزام بموعد السداد.
                        #                                 عبر القنوات التالية:
                        #                                 (رمز السداد 901 - {customer.rosom_number})
                        #                                 ( للتحويل  – {customer.name.iban_num} )
                        #                                 للتواصل 8001184000. أوقات العمل من الأحد إلى الخميس من الساعة 9ص إلى 5م.
                        #                                 نشكرك على اختيارك فيول للتمويل
                        #                              """
                        updated_installment_payment_message = f"""
                                                                           عميلنا العزيز، نود اشعاركم بإقتراب موعد القسط ({formatted_installment_amount}) ريال.لعقدكم رقم ({customer.seq_num}).
                               نرجو الالتزام بموعد السداد.
                               عبر القنوات التالية:
                               (رمز السداد 901 - {customer.rosom_number})
                               ( للتحويل  – {customer.name.iban_num})
                               للتواصل 8001184000. أوقات العمل من الأحد إلى الخميس من الساعة 9ص إلى 5م.
                               نشكرك على اختيارك فيول للتمويل
                                                                            """

                        values = '''{
                                                                               "userName": "Fuelfinancesa",
                                                                                 "numbers": "''' + customer.name.phone + '''",
                                                                                 "userSender": "fuelfinance",
                                                                                 "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                                                                 "msg": "''' + updated_installment_payment_message + '''"
                                                                               }'''

                        headers = {
                            'Content-Type': 'application/json;charset=UTF-8'
                        }
                        values = values.encode()
                        response = requests.post('https://www.msegat.com/gw/sendsms.php',
                                                 data=values,
                                                 headers=headers, timeout=60)

                        if response.status_code == 200:
                            # Save the message in the chatter
                            customer.message_post(body=updated_installment_payment_message)

    # =========== | Send Message IBAN Account To Customer | =======
    def send_message_iban_account(self):
        today_date = datetime.now().date()
        # Check if today is the 25th day of the month

        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])

        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            if customer.name.phone and customer.name.iban_num:
                message = f"""                
عزيزنا العميل :
يمكنكم السداد  لعقدكم رقم : {customer.seq_num}
 عبر القنوات التالية :
                                 رمز السداد : 901 
                                 رقم الفاتورة : {customer.rosom_number}
                                 رقم الايبان الخاص بكم لدي شركة فيول للتمويل بالبنك العربي الوطني : {customer.name.iban_num}
                                 للتواصل 8001184000
أوقات العمل من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
فيول للتمويل
                                  """

                if message is not None and customer.name.iban_num:
                    self.send_messeage(customer.name.phone, message)
                    # Log the message in the chatter
                    customer.message_post(body=message)

    ###############################################################
    ##################### | Calculate APR | #######################
    ###############################################################

    def xirr(self, values, dates, guess=0.1):

        """
            Calculate the XIRR (annualized internal rate of return) for cash flows with irregular intervals.

            Parameters:
            ----------
            values : list of float
                Cash flow amounts, with negative for outflows (investments) and positive for inflows (returns).

            dates : list of datetime
                Dates corresponding to each cash flow, indicating when each flow occurs.

            guess : float, optional
                Initial rate guess, defaulting to 0.1 (or 10%).

            Returns:
            -------
            float or None
                Estimated annualized return as a decimal, or `None` if convergence fails.

            """
        max_iterations = 1000
        tolerance = 1e-8
        days_in_year = 365.0

        rate = guess

        for _ in range(max_iterations):
            npv = sum(
                val / ((1 + rate) ** ((dates[idx] - dates[0]).days / days_in_year))
                for idx, val in enumerate(values)
            )

            derivative = sum(
                -(val * (dates[idx] - dates[0]).days) / (
                        days_in_year * ((1 + rate) ** ((dates[idx] - dates[0]).days / days_in_year + 1)))
                for idx, val in enumerate(values)
            )

            if abs(derivative) < tolerance:
                print("Derivative is too close to zero.")
                return None

            new_rate = rate - npv / derivative
            if abs(new_rate - rate) < tolerance:
                return new_rate

            rate = new_rate

        print("Failed to converge within the maximum number of iterations.")
        return None

    # Custom Calculate New APR
    def custom_calculate_new_apr(self):
        # This Custom Function For Calculate APR For Products [ Tawrruq - Murabaha] in Status [active - Close - early]
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', 'in', ['active', 'early', 'close']),
             ('loan_type', 'in', [1, 2])])

        for customer in selected_customers:
            customer.calculate_new_apr()
            customer.message_post(body="Calculate APR")

    # Calculate New APR
    def calculate_new_apr(self):
        # Installment Dates List
        date_list = [installment.date for installment in self.installment_ids]
        date_list.insert(0, self.approve_date)  # Add Approve Date To Installment Dates List

        # Installment Amount List
        installment_amount_list = [installment.installment_amount for installment in self.installment_ids]
        installment_amount_list.insert(0, -(
                self.loan_amount - self.tax_id_fees))  # Add Total And Admin fees by Mince to Installment Amount List

        # Call Function To Calculate
        apr = self.xirr(installment_amount_list, date_list) * 100  # ضرب في 100 عشان تكون نسبة مئوية

        # Display Result
        if apr is not None:
            print('+++++++++++++++++++++++')
            print(f"The APR is: {apr:.2f}%")
            formatted_apr = '{:.2f}'.format(apr)
            self.write({'apr': float(formatted_apr)})
            self.write({'new_apr': float(formatted_apr)})

    # Reschedule Calculate New APR
    def reschedule_calculate_new_apr(self):
        # Installment Dates List
        date_list = [installment.date for installment in self.reschedule_installment_ids]
        date_list.insert(0, self.approve_date)  # Add Approve Date To Installment Dates List

        # Installment Amount List
        installment_amount_list = [installment.installment_amount for installment in
                                   self.reschedule_installment_ids]
        installment_amount_list.insert(0, -(
            self.loan_amount))  # Add Total And Admin fees by Mince to Installment Amount List

        # Call Function To Calculate
        apr = self.xirr(installment_amount_list, date_list) * 100

        # Display Result
        if apr is not None:
            print('+++++++++++++++++++++++')
            print(f"The APR is: {apr:.2f}%")
            formatted_apr = '{:.2f}'.format(apr)
            self.write({'reschedule_new_apr': float(formatted_apr)})

    ###############################################################
    ################## | Collection BKT Messages Section | ########
    ###############################################################

    # +++++++++++ | Send Massage To BKT1 | ++++++++++++
    @api.model
    def send_installment_message_to_bkt_1(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            # Check If Customer rescheduled Or Not
            installments = customer.reschedule_installment_ids if customer.is_reschedule else customer.installment_ids
            # Check all installments for the customer
            for installment in installments:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state in ['unpaid', 'partial']:
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count == 1:
                    # ============ >New
                    # message = f"""
                    #                             لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                    #                              للتواصل 8001184000
                    #                              أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                    #                              فيول للتمويل. إدارة التحصيل
                    #                             """
                    formatted_amount = round(
                        customer.reschedule_late_amount if customer.is_reschedule else customer.late_amount, 2)
                    message = f"""
عميلنا العزيز، نشعركم بعدم سدادكم المبالغ المستحقة عليكم ({formatted_amount}) ريال لعقدكم رقم ({customer.seq_num}).
 الرجاء المبادرة بالسداد.
عبر القنوات التالية:
(رمز السداد 901 - {customer.rosom_number})
( للتحويل - {customer.name.iban_num} )
وذلك لسلامة سجلكم الائتماني. للتواصل 8001184000
أوقات العمل من الأحد إلى الخميس من الساعة 9ص إلى 5م.
في حال السداد يرجى تجاهل الرسالة
فيول للتمويل.إدارة التحصيل
"""

                    # Send message code goes here
                    if customer.name.phone and customer.rosom_number and customer.name.iban_num:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    #
    #     # +++++++++++ | Send Massage To BKT - 2 | ++++++++++++
    @api.model
    def send_installment_message_to_bkt_2(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            # Check If Customer rescheduled Or Not
            installments = customer.reschedule_installment_ids if customer.is_reschedule else customer.installment_ids
            # Check all installments for the customer
            for installment in installments:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state in ['unpaid', 'partial']:
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count == 2:
                    # ============ >New
                    # message = f"""
                    #                             لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                    #                              للتواصل 8001184000
                    #                              أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                    #                              فيول للتمويل. إدارة التحصيل
                    #                             """
                    formatted_amount = round(
                        customer.reschedule_late_amount if customer.is_reschedule else customer.late_amount, 2)
                    message = f"""
                    عميلنا العزيز، نشعركم بعدم سدادكم المبالغ المتأخرة عليكم ({formatted_amount}) ريال لعقدكم رقم ({customer.seq_num}).
 الرجاء سرعة المبادرة بالسداد.
عبر القنوات التالية:(رمز السداد 901 - {customer.rosom_number})
  ( للتحويل - {customer.name.iban_num} )
وذلك لسلامة سجلكم الائتماني. للتواصل 8001184000
أوقات العمل من الأحد إلى الخميس من الساعة 9ص إلى 5م.
فيول للتمويل.إدارة التحصيل

"""

                    # Send message code goes here
                    if customer.name.phone and customer.rosom_number and customer.name.iban_num:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    # +++++++++++ | Send Massage To Non Started BKT - 2 | ++++++++++++
    @api.model
    def send_installment_message_to_non_started_bkt_2(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            # Check If Customer rescheduled Or Not
            installments = customer.reschedule_installment_ids if customer.is_reschedule else customer.installment_ids
            # Check all installments for the customer
            for installment in installments:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state in ['unpaid', 'partial']:
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count == 2:
                    # ============ >New
                    # message = f"""
                    #                             لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                    #                              للتواصل 8001184000
                    #                              أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                    #                              فيول للتمويل. إدارة التحصيل
                    #                             """
                    formatted_amount = round(
                        customer.reschedule_late_amount if customer.is_reschedule else customer.late_amount, 2)
                    message = f"""
عميلنا العزيز، نشعركم بعدم سدادكم المبالغ المتأخرة عليكم ({formatted_amount}) لعقدكم رقم ({customer.seq_num})، منذ بداية العقد.
 الرجاء سرعة المبادرة بالسداد.
عبر القنوات التالية:(رمز السداد 901 - {customer.rosom_number})
  ( للتحويل - {customer.name.iban_num} )
 وذلك لسلامة سجلكم الائتماني. للتواصل 8001184000
 اوقات العمل من الأحد إلى الخميس من الساعة 9ص إلى 5م.
فيول للتمويل. إدارة التحصيل

"""

                    # Send message code goes here
                    if customer.name.phone and customer.rosom_number and customer.name.iban_num:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    # +++++++++++ | Send Massage To BKT - 3 - 28| ++++++++++++
    @api.model
    def send_installment_message_to_bkt_3_28(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            # Check If Customer rescheduled Or Not
            installments = customer.reschedule_installment_ids if customer.is_reschedule else customer.installment_ids
            # Check all installments for the customer
            for installment in installments:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state in ['unpaid', 'partial']:
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count == 3:
                    # ============ >New
                    # message = f"""
                    #                             لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                    #                              للتواصل 8001184000
                    #                              أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                    #                              فيول للتمويل. إدارة التحصيل
                    #                             """
                    formatted_amount = round(
                        customer.reschedule_late_amount if customer.is_reschedule else customer.late_amount, 2)
                    message = f"""
                    عميلنا العزيز، نأمل المبادرة بسرعة سداد المبالغ المتأخرة عليكم ({formatted_amount}) ريال لعقدكم رقم ({customer.seq_num})
 تفاديا لإتخاذ الإجراءات القانونية.ولسلامة سجلكم الائتماني. للتواصل 8001184000
 أوقات العمل من الأحد إلى الخميس من الساعة 9ص إلى 5م.
فيول للتمويل. إدارة التحصيل
"""

                    # Send message code goes here
                    if customer.name.phone:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    #     # +++++++++++ | Send Massage To BKT - 3| ++++++++++++
    @api.model
    def send_installment_message_to_bkt_3(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            # Check If Customer rescheduled Or Not
            installments = customer.reschedule_installment_ids if customer.is_reschedule else customer.installment_ids
            # Check all installments for the customer
            for installment in installments:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state in ['unpaid', 'partial']:
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count == 3:
                    # ============ >New
                    # message = f"""
                    #                             لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                    #                              للتواصل 8001184000
                    #                              أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                    #                              فيول للتمويل. إدارة التحصيل
                    #                             """
                    formatted_amount = round(
                        customer.reschedule_late_amount if customer.is_reschedule else customer.late_amount, 2)
                    message = f"""
                    عميلنا العزيز، نشعركم بعدم سدادكم المبالغ المتأخرة عليكم ({formatted_amount}) ريال لعقدكم رقم ({customer.seq_num}).
 نأمل سرعة المبادرة بالسداد.
عبر القنوات التالية:(رمز السداد 901 - {customer.rosom_number})
  ( للتحويل - {customer.name.iban_num} )
وذلك لسلامة سجلكم الائتماني. للتواصل 8001184000
أوقات العمل من الأحد إلى الخميس من الساعة 9ص إلى 5م.
فيول للتمويل.إدارة التحصيل
"""

                    # Send message code goes here
                    if customer.name.phone and customer.rosom_number and customer.name.iban_num:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    # +++++++++++ | Send Massage To BKT - 4 - Legal| ++++++++++++
    @api.model
    def send_installment_message_to_bkt_4_legal(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            # Check If Customer rescheduled Or Not
            installments = customer.reschedule_installment_ids if customer.is_reschedule else customer.installment_ids
            # Check all installments for the customer
            for installment in installments:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state in ['unpaid', 'partial']:
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count == 4:
                    # ============ >New
                    # message = f"""
                    #                             لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                    #                              للتواصل 8001184000
                    #                              أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                    #                              فيول للتمويل. إدارة التحصيل
                    #                             """
                    formatted_amount = round(
                        customer.reschedule_late_amount if customer.is_reschedule else customer.late_amount, 2)
                    message = f"""
                    عميلنا العزيز، نظرا لتكرار التواصل معكم لسداد المبالغ المستحقة عليكم ({formatted_amount}) ريال لعقدكم رقم ({customer.seq_num})
ولعدم تجاوبكم تم تحويل ملفكم للإدارة القانونية لاتخاذ الإجراءات القانونية.
نأمل المبادرة بسرعة السداد لإيقاف الإجراءات. للتواصل 8001184000.
أوقات العمل من الأحد إلى الخميس من الساعة 9ص إلى 5م.
فيول للتمويل. إدارة التحصيل
"""

                    # Send message code goes here
                    if customer.name.phone:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    #     # +++++++++++ | Send Massage To BKT - 4 | ++++++++++++
    @api.model
    def send_installment_message_to_bkt_4_normal(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            # Check If Customer rescheduled Or Not
            installments = customer.reschedule_installment_ids if customer.is_reschedule else customer.installment_ids
            # Check all installments for the customer
            for installment in installments:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state in ['unpaid', 'partial']:
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count == 4:
                    # ============ >New
                    # message = f"""
                    #                             لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                    #                              للتواصل 8001184000
                    #                              أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                    #                              فيول للتمويل. إدارة التحصيل
                    #                             """
                    formatted_amount = round(
                        customer.reschedule_late_amount if customer.is_reschedule else customer.late_amount, 2)
                    message = f"""
                   عميلنا العزيز، نشعركم بعدم سدادكم المبالغ المستحقة عليكم ({formatted_amount}) ريال لعقدكم رقم ({customer.seq_num}).
 نأمل سرعة المبادرة بالسداد.
عبر القنوات التالية:( رمز السداد 901 - {customer.rosom_number})
  ( للتحويل - {customer.name.iban_num} ) 
وذلك لسلامة سجلكم الائتماني. للتواصل 8001184000.
أوقات العمل من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
فيول للتمويل.إدارة التحصيل
                    """

                    # Send message code goes here
                    if customer.name.phone and customer.rosom_number and customer.name.iban_num:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    # +++++++++++ | Send Massage To Legal BKT 5 + | ++++++++++++
    @api.model
    def send_installment_message_to_bkt_5_legal(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            # Check If Customer rescheduled Or Not
            installments = customer.reschedule_installment_ids if customer.is_reschedule else customer.installment_ids
            # Check all installments for the customer
            for installment in installments:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state in ['unpaid', 'partial']:
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count >= 5:
                    # ============ >New
                    # message = f"""
                    #                             لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                    #                              للتواصل 8001184000
                    #                              أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                    #                              فيول للتمويل. إدارة التحصيل
                    #                             """

                    message = f"""
                     لإنهاء القضية المرفوعة ضدكم، نأمل المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
للتواصل 8001184000.
أوقات العمل من الأحد إلى الخميس من الساعة 9ص إلى 5م.
فيول للتمويل. إدارة التحصيل
"""

                    # Send message code goes here
                    if customer.name.phone:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    # +++++++++++ | Send Massage To BKT 5 + | ++++++++++++
    @api.model
    def send_installment_message_to_bkt_5_plus(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            # Check If Customer rescheduled Or Not
            installments = customer.reschedule_installment_ids if customer.is_reschedule else customer.installment_ids
            # Check all installments for the customer
            for installment in installments:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state in ['unpaid', 'partial']:
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count >= 5:
                    # ============ >New
                    # message = f"""
                    #                             لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                    #                              للتواصل 8001184000
                    #                              أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                    #                              فيول للتمويل. إدارة التحصيل
                    #                             """
                    formatted_amount = round(
                        customer.reschedule_late_amount if customer.is_reschedule else customer.late_amount, 2)
                    message = f"""
                     عميلنا العزيز، نشعركم بعدم سدادكم المبالغ المستحقة عليكم ({formatted_amount}) ريال لعقدكم رقم ({customer.seq_num}).
 نأمل سرعة المبادرة بالسداد.
عبر القنوات التالية:( رمز السداد 901 - {customer.rosom_number})
  ( للتحويل - {customer.name.iban_num} )
وذلك لسلامة سجلكم الائتماني. للتواصل 8001184000.
أوقات العمل من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
فيول للتمويل.إدارة التحصيل
"""

                    # Send message code goes here
                    if customer.name.phone and customer.rosom_number and customer.name.iban_num:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    ###############################################################
    ############## | End Collection BKT Messages Section | ########
    ###############################################################

    # =========== | Send Message Non-Started B1+2 | =======
    def send_message_non_started_b1_2(self):
        today_date = datetime.now().date()
        # Check if today is the 25th day of the month
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            formatted_installment_amount = round(customer.installment_month, 2)

            # Initialize message with a default value
            message = None

            # Check all installments for the customer
            for installment in customer.installment_ids:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state == 'unpaid':
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                if customer.paid_amount == 0:
                    # Define the message based on the number of unpaid overdue installments
                    if unpaid_overdue_count == 1 or unpaid_overdue_count == 2:
                        # ============ >New
                        message = f"""
                                                            عميلنا العزيز، لعدم سداد القسط الاول، منذ بداية العقد , يرجي المبادرة بسرعة السداد لسلامة السجل الائتماني الخاص بكم. للتواصل 8001184000.
                                                             أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                                                            وفي حال السداد نأمل تجاهل الرسالة
                                                             فيول للتمويل. إدارة التحصيل
                                                         """
                        if message != None:
                            if customer.name.phone:
                                self.send_messeage(customer.name.phone, message)
                                # Log the message in the chatter
                                customer.message_post(body=message)

    # =========== | Send Massage To BKT5 | =======
    @api.model
    def send_installment_message_to_bkt_5(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])
        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            formatted_installment_amount = round(customer.installment_month, 2)

            # Initialize message with a default value
            message = None

            # Check all installments for the customer
            for installment in customer.installment_ids:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state == 'unpaid':
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count >= 5:
                    # ============ >New
                    message = f"""
                                                لإنهاء القضية المرفوعة ضدكم، أرجو المبادرة بالتواصل مع إدارة التحصيل لدراسة الحلول الممكنة.
                                                 للتواصل 8001184000
                                                 أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                                                 فيول للتمويل. إدارة التحصيل
                                                """
                    # Send the message
                    if message != None:
                        # Send message code goes here
                        if customer.name.phone:
                            self.send_messeage(customer.name.phone, message)
                            # Log the message in the chatter
                            customer.message_post(body=message)

        # =========== | Send Massage To BKT4 | =======

    @api.model
    def send_installment_message_to_bkt_4(self):
        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])

        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            formatted_installment_amount = round(customer.installment_month, 2)

            # Initialize message with a default value
            message = None

            # Check all installments for the customer
            for installment in customer.installment_ids:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state == 'unpaid':
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if unpaid_overdue_count == 4:
                    # message = f"""عميلنا العزيز.
                    #             نأمل الإسراع في سداد القسط الشهري المستحق عليك تجنباً لاتخاذ الإجراءات القانونية.
                    #             ولمزيد من الاستفسارات نسعد بخدمتك على الرقم الموحد 8001184000 خلال أوقات العمل الرسمية من الأحد إلى الخميس من الساعة 9:30 صباحاً حتى الساعة 4:30 مساءً
                    #             فيول للتمويل/ إدارة التحصيل"""
                    # ============ >New
                    message = f"""
                                                   نظرا لتكرار التواصل معكم لسداد الأقساط المتأخرة عليكم ولعدم التجاوب تم تحويل ملفكم للإدارة القانونية لاتخاذ الإجراءات القانونية. بادر بالسداد فورا لإيقاف الاجراء. للتواصل 8001184000.
                                                   أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                                                    فيول للتمويل. إدارة التحصيل
                                           """

                # Send the message
                if message != None:
                    # Send message code goes here
                    if customer.name.phone:
                        self.send_messeage(customer.name.phone, message)
                        # Log the message in the chatter
                        customer.message_post(body=message)

    # Payment Date Reminders Massage
    # =========== | Send Massage To BKT-1-2-3-4 | =======
    def send_installment_reminder_messages(self):

        today_date = datetime.now().date()
        # Get all customers
        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].search(
            [('id', 'in', selected_customer_ids), ('state', '=', 'active')])

        # Send Message For All Customer And Printed In Chatter

        # Iterate over each customer
        for customer in selected_customers:
            # Initialize variables to track installment status
            unpaid_overdue_count = 0
            total_installments = 0
            formatted_installment_amount = round(customer.installment_month, 2)

            # Initialize message with a default value
            message = None

            # Check all installments for the customer
            for installment in customer.installment_ids:
                total_installments += 1
                # Check if installment is overdue, unpaid, and within the first three installments
                if installment.date < today_date and installment.state == 'unpaid':
                    unpaid_overdue_count += 1

            # Send message if there are unpaid overdue installments
            if unpaid_overdue_count > 0:
                # Define the message based on the number of unpaid overdue installments
                if (
                        unpaid_overdue_count == 1 or unpaid_overdue_count == 2 or unpaid_overdue_count == 4) and customer.paid_amount != 0:
                    message = f"""عميلنا العزيز، نقدر انشغالكم ونشعركم بعدم سداد الاقساط المستحقة حتى تاريخه. الرجاء سرعة المبادرة بالسداد. لسلامة سجلكم الائتماني. للتواصل 8001184000.
                                                            أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                                                            فيول للتمويل.إدارة التحصيل
                                                                                      """
                elif unpaid_overdue_count == 3:
                    message = f"""
                                          عميلنا العزيز، نأمل المبادرة بسرعة سداد المبالغ المستحقة عليكم تفاديا لاتخاذ الإجراءات القانونية.ولسلامة سجلكم الائتماني. 
                                          للتواصل 8001184000. أوقات الدوام من الأحد إلى الخميس من الساعة 9 ص إلى 5 م.
                                          فيول للتمويل. إدارة التحصيل                    
                                        """

            if message != None:
                # Send message code goes here
                if message and customer.name.phone:
                    self.send_messeage(customer.name.phone, message)
                    # Log the message in the chatter
                    customer.message_post(body=message)

    # Send Message To Active Customer
    def send_message_to_active_customer(self):
        message_body = """
                   السداد المبكر:

                   -  يساعدك على تقليل الضغط
                   - يحسن وضعك المالي
                   - يؤثر إيجابيًا على تقييم الائتمان الخاص بك وتقدر تاخذ قروض مستقبلًا.

                   #أسبوع_المال_العالمي
               """

        selected_customer_ids = self._context.get('active_ids', [])
        selected_customers = self.env['loan.order'].browse(selected_customer_ids)
        for customer in selected_customers:
            if customer.state == 'active':
                if customer.name.phone:
                    # Send Message
                    values = '''{
                                "userName": "Fuelfinancesa",
                                  "numbers": "''' + customer.name.phone + '''",
                                  "userSender": "fuelfinance",
                                  "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                  "msg": "''' + message_body + '''"
                                }'''

                    headers = {
                        'Content-Type': 'application/json;charset=UTF-8'
                    }
                    values = values.encode()
                    response = requests.post('https://www.msegat.com/gw/sendsms.php',
                                             data=values,
                                             headers=headers, timeout=60)
                    if response.status_code == 200:
                        customer.message_post(body=message_body)

    def action_sms_reminder(self):
        phone = self.phone_customer
        sequence = self.seq_num
        reject = self.new_reject_reason
        sms_reminder = 'عميلنا العزيز، نأمل الإسراع في سداد القسط الشهري المستحق عليك تجنب لاتخاذ الإجراءات القانونية - للاستفسار نرجو الاتصال على الرقم 8001184000'
        # encoded_data = base64.b64encode(bytes(sms_approve, 'utf_8')).decode()
        values = '''{
                          "userName": "Fuelfinancesa",
                          "numbers": "''' + phone + '''",
                          "userSender": "fuelfinance",
                          "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                          "msg": "''' + sms_reminder + '''"
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
        # self.name.action_reject_call()
        self.message_post(body=datetime.today(),
                          subject='A payment reminder has been sent - عميلنا العزيز، نأمل الإسراع في سداد القسط الشهري المستحق عليك تجنب لاتخاذ الإجراءات القانونية - للاستفسار نرجو الاتصال على الرقم 8001184000')

    def action_sms_warning(self):
        phone = self.phone_customer
        sequence = self.seq_num
        reject = self.new_reject_reason
        sms_reminder = 'عميلنا العزيز، نظراً لعدم تجاوبكم مع رسائل التحذير المتعلقة بدفع المبالغ المستحقة عليكم ل فيول للتمويل، نفيدكم انه قد تم إحالة ملفكم إلى الجهات المختصة لاتخاذ الإجراءات القانونية. يرجى التجاهل في حالة السداد او عدم وجود علاقة مع فيول للتمويل  للاستفسار الرجاء الاتصال بنا على الرقم 8001184000 من الساعة 09:30 صباحاً الى 04:30 مساءً من الاحد الى الخميس - قسم التحصيل'
        # encoded_data = base64.b64encode(bytes(sms_approve, 'utf_8')).decode()
        values = '''{
                          "userName": "Fuelfinancesa",
                          "numbers": "''' + phone + '''",
                          "userSender": "fuelfinance",
                          "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                          "msg": "''' + sms_reminder + '''"
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
        # self.name.action_reject_call()
        self.message_post(body=datetime.today(),
                          subject='A payment warning reminder has been sent - عميلنا العزيز، نظراً لعدم تجاوبكم مع رسائل التحذير المتعلقة بدفع المبالغ المستحقة عليكم ل فيول للتمويل، نفيدكم انه قد تم إحالة ملفكم إلى الجهات المختصة لاتخاذ الإجراءات القانونية. يرجى التجاهل في حالة السداد او عدم وجود علاقة مع فيول للتمويل  للاستفسار الرجاء الاتصال بنا على الرقم 8001184000 من الساعة 09:30 صباحاً الى 04:30 مساءً من الاحد الى الخميس - قسم التحصيل')

    def get_loan_account_journal(self):
        interest_account = installment_account = payment_journal = disburse_account = False
        if not self.loan_type:
            raise ValidationError(_("Please Select the Loan Type !!!"))
        if self.loan_type.interest_account:
            interest_account = self.loan_type.interest_account and self.loan_type.interest_account.id or False

        if self.loan_type.installment_account:
            installment_account = self.loan_type.installment_account and self.loan_type.installment_account.id or False

        if self.loan_type.payment_journal:
            payment_journal = self.loan_type.payment_journal and self.loan_type.payment_journal.id or False

        if self.loan_type.disburse_account:
            disburse_account = self.loan_type.disburse_account and self.loan_type.disburse_account.id or False

        return interest_account, installment_account, payment_journal, disburse_account

    def action_operation_cancel(self):
        self.message_post(body=datetime.today(), subject='the Loan Application Canceled By Oparetion User')
        self.name.action_cancel()
        if self.nafaes_order_id:
            self.nafaes_order_id.action_cancel()
        self.state = 'cancel'
        for rec in self:
            users = self.env.ref('loan.group_accounting_move').users.ids
            user_id = self.env.user.id
            random_id = user_id
            while random_id == user_id:
                random_id = random.choice(users)
            activity_object = self.env['mail.activity']
            activity_values = self.activity_create_cancel(random_id, rec.id, 'loan.order',
                                                          'loan.model_loan_order')
            activity_id = activity_object.create(activity_values)

    def action_confirmation_call_cancel(self):
        self.name.action_cancel()
        self.state = 'cancel'

    def action_sales_cancel(self):
        self.message_post(body=datetime.today(), subject='the Customer Canceled By Sales User')
        self.name.action_cancel()
        self.state = 'cancel'
        activity_object = self.env['mail.activity']
        # activity_values = self.activity_create_cancel(self.id, 'loan.order',  'loan.order',
        #                                                   'loan.model_loan_order')
        # activity_id = activity_object.create(activity_values)

    def action_tele_sales_cancel(self):
        self.message_post(body=datetime.today(), subject='the Customer Canceled By Tele Selas User')
        self.name.action_cancel()
        self.cancel_date = date.today()
        self.state = 'cancel'
        activity_object = self.env['mail.activity']
        # activity_values = self.activity_create_cancel(self.id,'loan.order',
        #                                                   'loan.model_loan_order')
        # activity_id = activity_object.create(activity_values)

    def activity_create_cancel(self, user_id, record_id, model_name, model_id):
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
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_activity_create_cancel').id,
        }

    def action_tele_sales_return(self):
        self.name.action_installment()
        self.message_post(body=datetime.today(), subject='The Request Sending Back To Credit From Tele Selas')
        self.state = 'simah'
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_function_credit').users:
                    activity_values = self.activity_back(user.id, self.id, 'loan.order', 'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)

    def action_tele_sales_protest(self):
        self.name.action_installment()
        message_body = f"""
                        <p style="color:red; font-size:14px;">
                            Objection to this request From Tele Sales on {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    """
        self.message_post(body=message_body, subject='Objection Notification')
        self.state = 'simah'
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_function_credit').users:
                    activity_values = self.activity_back(user.id, self.id, 'loan.order', 'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Note',
            'view_mode': 'form',
            'res_model': 'loan.note.wizard',
            'target': 'new',  # Open in a modal dialog
            'context': {'default_loan_id': self.id},  # Pass the loan ID to the wizard
        }

    def cancel_admin(self):
        self.message_post(body=datetime.today(), subject='Admin Canceled The Request')
        self.name.action_cancel()
        self.state = 'cancel'

    def open_admin(self):
        self.message_post(body=datetime.today(), subject='Admin Canceled The Request')
        self.name.action_open()
        self.state = 'active'

    # if record.partner_id:
    #     partner = record.partner_id
    # else:
    #     partner = env['res.partner'].search([('email', '=', record.email_from)])
    # if not partner:
    #     reg = {
    #         'name': record.contact_name or record.email_from,
    #         'email': record.email_from,
    #         'type': 'contact',
    #     }
    #     partner = env['res.partner'].create(reg)
    # partner_id = partner.id
    # reg = {
    #     'res_id': record.id,
    #     'res_model': 'crm.lead',
    #     'partner_id': partner_id,
    # }
    # if not env['mail.followers'].search(
    #         [('res_id', '=', record.id), ('res_model', '=', 'crm.lead'), ('partner_id', '=', partner_id)]):
    #     follower_id = env['mail.followers'].create(reg)

    # ///////////////////////////////////////////////////////////////////////////
    # partners_who_are_users = []
    # users = self.env['res.users'].search([])
    # for credit_user in users:
    #     if credit_user in self.env.ref('loan.group_loan_credit').users:
    #         partners_who_are_users.append(credit_user.partner_id.id)
    #         print('credit', credit_user)
    # followers = []
    # for partner in self.partner_id.message_partner_ids.ids:
    #     if partner in partners_who_are_users:
    #         followers.append(partner)
    # self.message_subscribe(followers)
    # ////////////////////////////////////////////////////////////////////////////
    # for follower in self.message_follower_ids:
    #     credit_user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
    #     if credit_user != self.env.user:
    #         if credit_user in self.env.ref('loan.group_loan_credit').users:
    #             print(credit_user.name, 'user')
    #             return super(credit_user, self).create(credit_user)
    # if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms'):
    #     if self.terms_type == 'html' and self.env.company.invoice_terms_html:
    #         baseurl = html_keep_url(self.get_base_url() + '/terms')
    #         values['note'] = _('Terms & Conditions: %s', baseurl)
    #     elif not is_html_empty(self.env.company.invoice_terms):
    #         values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
    # if not self.env.context.get('not_self_saleperson') or not self.team_id:
    #     default_team = self.env.context.get('default_team_id', False) or self.partner_id.team_id.id
    #     values['team_id'] = self.env['crm.team'].with_context(
    #         default_team_id=default_team
    #     )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)],
    #                            user_id=user_id)
    # self.update(values)
    # return {
    #     'name': _('Write Note'),
    #     'type': 'ir.actions.act_window',
    #     'res_model': 'mail.compose.message',
    #     'view_mode': 'form',
    #     'target': 'new',
    # }

    def action_incomplete(self):
        self.name.action_send_back()
        self.state = 'return'
        self.message_post(body=datetime.today(), subject='Send Back The Application to Sales')
        for rec in self:
            users = self.env.ref('loan.group_sales_return').users.ids
            user_id = self.env.user.id
            random_id = user_id
            while random_id == user_id:
                random_id = random.choice(users)
            activity_object = self.env['mail.activity']
            activity_values = self.activity_create_incomplete(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
            activity_id = activity_object.create(activity_values)

        # activity_object = self.env['mail.activity']
        # for follower in self.message_follower_ids:
        #     user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
        #     if user != self.env.user:
        #         if user in self.env.ref('loan.group_sales_cancel').users:
        #             activity_values = self.activity_create_incomplete(user.id, self.id, 'loan.order',
        #                                                               'loan.model_loan_order')
        #             activity_id = activity_object.create(activity_values)

    def activity_create_incomplete(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Incomplete Data",
            'note': "Customer data is incomplete, please check",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_partner_incomplete').id,
        }

    def action_back(self):
        # self.loan_id.action_set_done()
        self.name.action_installment()
        self.message_post(body=datetime.today(), subject='The Request Sending Back To Credit From Selas')
        self.state = 'simah'
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_function_credit').users:
                    activity_values = self.activity_back(user.id, self.id, 'loan.order', 'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)

    # def action_send_back_tele_selas(self):
    #     self.name.action_send_back()
    #     self.message_post(body=datetime.today(), subject='The Request Sending Back To Credit From Tele Selas')
    #     self.state = 'simah'
    #     activity_object = self.env['mail.activity']
    #     for follower in self.message_follower_ids:
    #         user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
    #         if user != self.env.user:
    #             if user in self.env.ref('loan.group_loan_credit').users:
    #                 activity_values = self.activity_back(user.id, self.id, 'loan.order', 'loan.model_loan_order')
    #                 activity_id = activity_object.create(activity_values)

    def activity_back(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Send Back The Request",
            'note': "The Loan application reviewed and done",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_back').id,
        }

    def action_conditional_approval(self):
        self.name.action_send_back()
        self.state = 'simah'
        self.message_post(body=datetime.today(), subject='Initial approval of the Customer')
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_sales_cancel').users:
                    activity_values = self.activity_Initial_approval(user.id, self.id, 'loan.order',
                                                                     'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)

    def activity_Initial_approval(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Initial approval",
            'note': "Initial approval of the Customer",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_Initial_approval').id,
        }

    def action_confirm_loan(self):
        if self.loan_amount <= 25000:
            self.name.action_approve()
            self.message_post(body=datetime.today(), subject='The customer Approved')
            self.state = 'approve'
            if self.loan_type:
                self.disburse_account = self.loan_type.disburse_account and self.loan_type.disburse_account.id or False
                self.disburse_journal = self.loan_type.disburse_journal and self.loan_type.disburse_journal.id or False
            self.approve_date = date.today()
            # self.exa_call_action_approve()
            self.approve_confirmation_call_action()
        else:
            self.message_post(body=datetime.today(), subject='The Loan Confirm')
            self.name.action_confirm()
            self.state = 'l2'
            for rec in self:
                users = self.env.ref('loan.group_loan_approval').users.ids
                user_id = self.env.user.id
                random_id = user_id
                while random_id == user_id:
                    random_id = random.choice(users)
                activity_object = self.env['mail.activity']
                activity_values = self.activity_create_confirm(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
                activity_id = activity_object.create(activity_values)
                # rec.write({'state': 'review done'})

    def activity_create_approve(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Loan Approval",
            'note': "Loan Request Approved",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_loan_done').id,
        }

    def activity_create_confirm(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Loan Confirm",
            'note': "The Request has been Reviewed and Confirmed",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_loan_approval').id,
        }

    # ++++++++++++++++++++++++++| Send Sticky Notification |+++++++++++++++++++++++++++
    @api.model
    def send_sticky_notification(self, message, notification_type):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '',
                'type': notification_type,
                'message': message,
                'sticky': False,
            }
        }
        return notification

    # ++++++++++++++++++++++++++| Exa Call Action |+++++++++++++++++++++++++++
    def exa_call_action_approve(self):
        # Step 1: Get the current Unix timestamp
        current_timestamp = int(time.time())

        # Step 2: Add 120 seconds (2 minutes) to the current timestamp
        future_timestamp = current_timestamp + 120

        self.create_installment_table_action()
        # self.create_installment_table_action()
        self.send_approve_message()
        self.name.action_approve()
        self.state = 'approve'
        client_phone = self.name.phone[1:]
        url = "https://api.exacall.io/voice/calls/schedule"
        headers = {"Content-Type": "application/json"}
        data = {
            "sid": "34dc318b-3bbb-40cb-8a03-98dcba4f9f2a",
            "call_flow_app": "05055160-a20f-4d76-841b-63907bd54824",
            "destination_type": "phone",
            "destination": f"966{client_phone}",
            "when": future_timestamp,
            "max_attempts": 3,
            "retry_after": "1h",
            "working_hours": True,
            "call_status_endpoint": "https://apiv2.exacall.io/fuel"
        }

        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            exa_call_response_status = response.json().get('status')
            if exa_call_response_status:
                return self.send_sticky_notification('Successfully Done', 'success')
            else:
                return self.send_sticky_notification('The Operation Failed', 'danger')
        else:
            return self.send_sticky_notification('The Operation Failed', 'danger')

    # -------------------- | Confirmation Call | --------------
    def confirmation_call_action(self):

        """
        Sends a POST request to the API to register a call.

        Returns:
            dict: JSON response from the API.
        """
        # url = "http://192.168.50.10:8020/Spine/api/CallList?camp_id=callback"
        production_url = "http://212.12.168.2:8020/Spine/api/CallList?camp_id=callback"
        payload = json.dumps([
            {
                "mobile": self.name.phone,
                "language": "ar"
            }
        ])
        headers = {
            'Content-Type': 'application/json',
            'API-KEY': 'API_edeb31f7-9b96-4cdb-80df646ef07e12cf'
        }

        response = requests.post(production_url, headers=headers, data=payload)

        try:
            if response.status_code == 200:
                if len(response.json()) != 0:
                    self.name.action_approve()
                    self.state = 'approve'
                    return self.send_sticky_notification('Successfully Done', 'success')
                else:
                    return self.send_sticky_notification('The Operation Failed', 'danger')
            else:
                return self.send_sticky_notification('The Operation Failed', 'danger')
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "response_text": response.text}

    # -------------------- | Approve Confirmation Call | --------------
    def approve_confirmation_call_action(self):
        """
        Sends a POST request to the API to register a call.

        Returns:
            dict: JSON response from the API.
        """
        # url = "http://192.168.50.10:8020/Spine/api/CallList?camp_id=callback"
        production_url = "http://212.12.168.2:8020/Spine/api/CallList?camp_id=callback"
        payload = json.dumps([
            {
                "mobile": self.name.phone,
                "language": "ar"
            }
        ])
        headers = {
            'Content-Type': 'application/json',
            'API-KEY': 'API_edeb31f7-9b96-4cdb-80df646ef07e12cf'
        }

        response = requests.post(production_url, headers=headers, data=payload)

        try:
            if response.status_code == 200:
                if len(response.json()) != 0:
                    self.create_installment_table_action()
                    self.send_approve_message()
                    self.name.action_approve()
                    self.state = 'approve'
                    return self.send_sticky_notification('Successfully Done', 'success')
                else:
                    return self.send_sticky_notification('The Operation Failed', 'danger')
            else:
                return self.send_sticky_notification('The Operation Failed', 'danger')
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "response_text": response.text}

    def exa_call_action(self):
        # Step 1: Get the current Unix timestamp
        current_timestamp = int(time.time())

        # Step 2: Add 120 seconds (2 minutes) to the current timestamp
        future_timestamp = current_timestamp + 120

        self.state = 'approve'
        self.name.action_approve()
        client_phone = self.name.phone[1:]
        url = "https://api.exacall.io/voice/calls/schedule"
        headers = {"Content-Type": "application/json"}
        data = {
            "sid": "34dc318b-3bbb-40cb-8a03-98dcba4f9f2a",
            "call_flow_app": "05055160-a20f-4d76-841b-63907bd54824",
            "destination_type": "phone",
            "destination": f"966{client_phone}",
            "when": future_timestamp,
            "max_attempts": 3,
            "retry_after": "1h",
            "working_hours": True,
            "call_status_endpoint": "https://apiv2.exacall.io/fuel"
        }

        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            exa_call_response_status = response.json().get('status')
            if exa_call_response_status:
                return self.send_sticky_notification('Successfully Done', 'success')
            else:
                return self.send_sticky_notification('The Operation Failed', 'danger')
        else:
            return self.send_sticky_notification('The Operation Failed', 'danger')

    # ++++++++++++++++++++++++++|START Reschedule Installment Table Action |+++++++++++++++++++++++++++
    @api.depends('remaining_amount', 'remaining_principle_negative')
    def reschedule_get_compute_irr(self):
        for rec in self:
            reschedule_irr = 0
            print(reschedule_irr)
            if rec.remaining_principle > 0 and rec.reschedule_loan_term > 0:
                array = []
                amount_negative = rec.remaining_principle_negative
                print('amount_negative :', amount_negative)
                if amount_negative < 0:  # Ensure the initial cash flow is negative
                    array.append(amount_negative)
                    # Add the positive cash flows
                    installment = rec.remaining_amount / rec.reschedule_loan_term
                    print('installment', installment)
                    for _ in range(rec.reschedule_loan_term):
                        array.append(installment)
                    # Perform the reschedule_irr calculation
                    try:
                        result_array = np.array(array)
                        print('result_array:', result_array)
                        if not np.any(np.isnan(result_array)):  # Ensure no NaN in the array
                            reschedule_irr = npf.irr(result_array)
                            print("Internal Rate of Return (Reschedule IRR): {:.2%}".format(reschedule_irr))
                            rec.reschedule_irr = reschedule_irr
                            print(rec.reschedule_irr)
                        else:
                            print("Array contains NaN values, cannot calculate IRR.")
                            rec.reschedule_irr = 0
                    except Exception as e:
                        print(f"Error calculating IRR: {e}")
                        rec.reschedule_irr = 0
                else:
                    print("Initial cash flow must be negative to calculate IRR.")
            else:
                print("Invalid remaining principle or reschedule loan term.")

    def compute_reschedule_loan_amount(self):
        paid_principle = 0
        for installment in self.installment_ids:
            print(installment.state)
            print(installment.principal_amount)
            if installment.state == 'paid':
                paid_principle += installment.principal_amount
        self.reschedule_loan_amount = self.loan_amount - paid_principle

        # ++++++++++++++++++++++++++| Create Installment Table Action |+++++++++++++++++++++++++++

    def compute_reschedule_amount(self):
        for record in self:
            record.reschedule_interest_amount = record.remaining_interest
            record.reschedule_total_loan = record.reschedule_interest_amount + record.reschedule_loan_amount

    def compute_reschedule_installment_amount(self):
        if self.reschedule_loan_term == 0 or self.reschedule_total_loan == 0:
            # Handle the case where loan term or total loan is zero
            self.reschedule_installment_amount = 0
        else:
            self.reschedule_installment_amount = self.reschedule_total_loan / self.reschedule_loan_term

        if self.reschedule_interest_amount > 0:
            # Validate the denominator to avoid ZeroDivisionError
            if self.reschedule_loan_amount > 0 and self.reschedule_loan_term > 0:
                self.reschedule_interest_rate = (
                        (self.reschedule_interest_amount * 100) /
                        (self.reschedule_loan_amount * self.reschedule_loan_term) / 12
                )
            else:
                self.reschedule_interest_rate = 0  # Default value if division cannot be performed
        else:
            self.reschedule_interest_amount = self.remaining_interest
            self.reschedule_interest_rate = self.rate_per_month

    def reschedule_action_reset(self):
        self.is_reschedule = False
        if self.reschedule_installment_ids:
            for installment in self.reschedule_installment_ids:
                installment.with_context({'force_delete': True}).unlink()

    def _compute_is_reschedule_loan(self):
        for record in self:
            record.is_reschedule = True

    def reschedule_installment(self):
        print('=========== | Start Reschedule | ================')
        self.reschedule_get_compute_irr()
        if self.remaining_principle > 0 and self.reschedule_loan_term > 0:
            print('=========== | Run Extenuate Reschedule | ================')
            today = self.reschedule_installment_start_date
            self.reschedule_date = datetime.today()
            if self.reschedule_installment_ids:
                for installment in self.reschedule_installment_ids:
                    installment.with_context({'force_delete': True}).unlink()
            inc_month = 1
            if self.installment_type == 'quarter':
                inc_month = 1

            # if self.state == 'active':
            #     request_date_date = self.request_date_date
            # else:
            #     request_date_date = today
            vals = []
            interest_account, installment_account, payment_journal, disburse_account = self.get_loan_account_journal()

            asce_ins_x = self.remaining_principle
            asce_ins_y = self.remaining_amount
            final_amount = asce_ins_x
            total_remaining_amount = asce_ins_y
            print('final amount:', final_amount)
            print('total remaining Amount:', total_remaining_amount)
            for i in range(1, self.reschedule_loan_term + 1):
                if self.loan_type.name:
                    term = self.reschedule_loan_term
                    total = self.remaining_amount
                    amount = self.remaining_principle
                    interest_x = self.remaining_interest
                    irr = self.reschedule_irr
                    print("IRR :", irr)
                    installment_x = total / term
                    # +++++++++++++ Calculate Installment ++++++++++++++++++#
                    interest_x = final_amount * irr
                    principle_x = installment_x - interest_x
                    desc_ins_x = amount - principle_x
                    desc_ins_y = total - installment_x
                    # +++++++++++++ Calculate Installment ++++++++++++++++++#
                final_amount = final_amount - principle_x
                total_remaining_amount = total_remaining_amount - installment_x
                # print('after final amount', final_amount)
                if today.day >= 15:
                    today = today.replace(day=27) + relativedelta(months=inc_month)
                else:
                    today = today.replace(day=27)
                vals.append((0, 0, {
                    'seq_name': 'RES - ' + self.seq_num + ' - ' + str(i),
                    'i_num': str(i),
                    'name': self.name and self.name.id or False,
                    'date': today,
                    'principal_amount': principle_x,
                    'interest_amount': interest_x,
                    'descending_installment': desc_ins_x,
                    'descending_installment_y': desc_ins_y,
                    'ascending_installment': final_amount,
                    'total_ascending_installment': total_remaining_amount,
                    'state': 'unpaid',
                    'interest_account': interest_account or False,
                    'disburse_account': disburse_account or False,
                    'installment_account': installment_account or False,
                    'payment_journal': payment_journal or False,
                    'currency_id': self.currency_id and self.currency_id.id or False,
                }))
            self.reschedule_installment_ids = vals
            print('================= | | ===========================')
            result = [installment for installment in self.reschedule_installment_ids]
            self.reschedule_installment_end_date = result[-1].date
            self.is_reschedule = True
            self.message_post(
                body=f"Rescheduled By Remaining Amount ({self.remaining_amount}) With Loan Term ({self.reschedule_loan_term})")
        self.compute_reschedule_installment_amount()
        self.get_reschedule_amounts()

    # ++++++++++++++++++++++++++| END Reschedule Installment Table Action |+++++++++++++++++++++++++++

    def create_installment_table_action(self):
        today = date.today()
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.with_context({'force_delete': True}).unlink()

        inc_month = 1
        if self.installment_type == 'quarter':
            inc_month = 1

        if self.state == 'simah':
            request_date_date = self.request_date_date
        else:
            request_date_date = today
        vals = []
        interest_account, installment_account, payment_journal, disburse_account = self.get_loan_account_journal()

        asce_ins_x = self.loan_amount
        asce_ins_y = self.loan_sum
        down = self.down_payment_loan
        final_amount = asce_ins_x - down
        total_loan_amount = asce_ins_y - down
        print('1', final_amount)
        for i in range(1, self.loan_term + 1):
            if self.loan_type.name:
                term = self.loan_term
                total = self.loan_sum
                amount = self.loan_amount - self.down_payment_loan
                interest_x = self.interest_amount
                irr = self.irr
                installment_x = total / term
                if self.state == 'simah':
                    if self.loan_term < 1 or self.loan_term > 61:
                        raise ValidationError(_("The Term cannot be less than 3 or more than 60 months"))
                    else:
                        interest_x = final_amount * irr
                        principle_x = installment_x - interest_x
                        desc_ins_x = amount - principle_x
                        desc_ins_y = total - installment_x
                else:
                    interest_x = final_amount * irr
                    principle_x = installment_x - interest_x
                    desc_ins_x = amount - principle_x
                    desc_ins_y = total - installment_x
            final_amount = final_amount - principle_x
            total_loan_amount = total_loan_amount - installment_x
            print('2', final_amount)
            if today.day >= 15:
                today = today.replace(day=27) + relativedelta(months=inc_month)
            else:
                today = today.replace(day=27)
            vals.append((0, 0, {
                'seq_name': 'INS - ' + self.seq_num + ' - ' + str(i),
                'i_num': str(i),
                'name': self.name and self.name.id or False,
                'date': today,
                'principal_amount': principle_x,
                'interest_amount': interest_x,
                'descending_installment': desc_ins_x,
                'descending_installment_y': desc_ins_y,
                'ascending_installment': final_amount,
                'total_ascending_installment': total_loan_amount,
                'state': 'unpaid',
                'interest_account': interest_account or False,
                'disburse_account': disburse_account or False,
                'installment_account': installment_account or False,
                'payment_journal': payment_journal or False,
                'currency_id': self.currency_id and self.currency_id.id or False,
            }))
        self.installment_ids = vals
        self.calculate_new_apr()

    # ++++++++++++++++++++++++++| Approve Message |+++++++++++++++++++++++++++
    def send_approve_message(self):
        phone = self.phone_customer
        seq = self.seq_num
        approve_message = f"""
عميلنا العزيز, شكراً لك لاختياركم شركة فيول للتمويل تمت الموافقة على طلب التمويل بمبلغ ( {"{:.2f}".format(self.loan_amount_positive)} ر س )  بقسط شهري ( {"{:.2f}".format(self.installment_month)} ) ومدة تمويلية ( {self.loan_term} ) شهر ,
 سيحل القسط الاول بتاريخ  ({self.installment_start_date})
 سيتم الإتصال بك للتأكيد
لمزيد من الاستفسارات نسعد بخدمتك على الرقم المجاني 8001184000 خلال أوقات العمل الرسمية من الأحد إلى الخميس من 9 صباحاً وحتى 5 مساءً, نشكر لكم اختياركم فيول للتمويل
"""

        values = '''{
                          "userName": "Fuelfinancesa",
                          "numbers": "''' + phone + '''",
                          "userSender": "fuelfinance",
                          "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                          "msg": "''' + approve_message + '''"
                        }'''

        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        values = values.encode()
        response = requests.post('https://www.msegat.com/gw/sendsms.php', data=values,
                                 headers=headers, timeout=60)
        self.name.action_confirm_call()

        self.message_post(body=datetime.today(),
                          subject=approve_message)

    # ++++++++++++++++++++++++++| Send Notification To Credit User  |+++++++++++++++++++++++++++
    def send_notification_to_user(self, group_id, summary, note):
        for rec in self:
            users = self.env.ref(f'loan.{group_id}').users.ids
            user_id = self.env.user.id
            random_id = user_id
            while random_id == user_id:
                random_id = random.choice(users)
            activity_object = self.env['mail.activity']
            activity_values = self.activity_create_call(random_id, rec.id, 'loan.order', 'loan.model_loan_order',
                                                        summary, note)
            activity_id = activity_object.create(activity_values)

    def send_po_status(self):  # API for send purchase order status to supplier
        quotation_id = self.quotation_id.name
        # url = "https://stage.fuelfinance.sa/api/webhook/purchase/order"
        url = "https://fuelfinance.sa/api/webhook/purchase/order"

        if self.state == 'buying':
            payload = json.dumps({
                "quotation_id": quotation_id,
                "purchase_order_status": True
            })
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            print(response)
            print(payload)
        else:
            payload = json.dumps({
                "quotation_id": quotation_id,
                "purchase_order_status": False
            })
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            print(response)
            print(payload)

    def send_contract_status(self):  # API for send contract status to supplier
        quotation_id = self.quotation_id.name
        url = "https://fuelfinance.sa/api/webhook/approve/contract"
        # url = "https://stage.fuelfinance.sa/api/webhook/approve/contract"
        if self.state == 'disburse':
            payload = json.dumps({
                "quotation_id": quotation_id,
                "contract_status": True
            })
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            print(response.text)
            print(payload)
        else:
            payload = json.dumps({
                "quotation_id": quotation_id,
                "contract_status": False
            })
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            print(response.text)
            print(response.text)

    def submit_nafaes(self):
        print('++++++++++++++++++ | Submit Nafaes Running ...| +++++++++++++++++')
        if self.loan_type.id == 2 or 3:
            self.ensure_one()
            res = self.action_call_done()
            self.message_post(subject='An item was purchased from Nafaes')
            if not self.nafaes_order_id:
                self._create_nafaes_order()
            return res
        elif self.loan_type.id == 1:
            print('ignore Nafaes API')
            self.send_po_status()
            self.message_post(subject='The purchase order has been send to supplier')
            self.ensure_one()
            self.action_call_done()
        else:
            pass
        self.name.action_confirm_call()
        self.state = 'buying'
        self.send_notification_to_user('group_customer_operation', "Customer Call Approve"
                                       , "Customer Approved and Call")

    def action_call_done(self):
        self.name.action_confirm_call()
        self.state = 'buying'
        self.send_notification_to_user('group_customer_operation', "Customer Call Approve"
                                       , "Customer Approved and Call")

        # activity_object = self.env['mail.activity']
        # for follower in self.message_follower_ids:
        #     user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
        #     if user != self.env.user:
        #         if user in self.env.ref('loan.group_loan_credit').users:
        #             activity_values = self.activity_send_back(user.id, self.id, 'loan.order', 'loan.model_loan_order')
        # today = date.today()
        # if self.installment_ids:
        #     for installment in self.installment_ids:
        #         installment.with_context({'force_delete': True}).unlink()
        #
        # inc_month = 1
        # if self.installment_type == 'quarter':
        #     inc_month = 1
        #
        # if self.state == 'simah':
        #     request_date_date = self.request_date_date
        # else:
        #     request_date_date = today
        # vals = []
        # interest_account, installment_account, payment_journal, disburse_account = self.get_loan_account_journal()
        #
        # asce_ins_x = self.loan_amount
        # asce_ins_y = self.loan_sum
        # down = self.down_payment_loan
        # final_amount = asce_ins_x - down
        # total_loan_amount = asce_ins_y - down
        # print('1', final_amount)
        # for i in range(1, self.loan_term + 1):
        #     if self.loan_type.name:
        #         term = self.loan_term
        #         total = self.loan_sum
        #         amount = self.loan_amount - self.down_payment_loan
        #         interest_x = self.interest_amount
        #         irr = self.irr
        #         installment_x = total / term
        #         if self.loan_term < 3 or self.loan_term > 61:
        #             raise ValidationError(_("The Term cannot be less than 3 or more than 60 months"))
        #         else:
        #             interest_x = final_amount * irr
        #             principle_x = installment_x - interest_x
        #             desc_ins_x = amount - principle_x
        #             desc_ins_y = total - installment_x
        #     final_amount = final_amount - principle_x
        #     total_loan_amount = total_loan_amount - installment_x
        #     print('2', final_amount)
        #     if today.day >= 15:
        #         today = today.replace(day=27) + relativedelta(months=inc_month)
        #     else:
        #         today = today.replace(day=27)
        #     vals.append((0, 0, {
        #         'seq_name': 'INS - ' + self.seq_num + ' - ' + str(i),
        #         'i_num': str(i),
        #         'name': self.name and self.name.id or False,
        #         'date': today,
        #         'principal_amount': principle_x,
        #         'interest_amount': interest_x,
        #         'descending_installment': desc_ins_x,
        #         'descending_installment_y': desc_ins_y,
        #         'ascending_installment': final_amount,
        #         'total_ascending_installment': total_loan_amount,
        #         'state': 'unpaid',
        #         'interest_account': interest_account or False,
        #         'disburse_account': disburse_account or False,
        #         'installment_account': installment_account or False,
        #         'payment_journal': payment_journal or False,
        #         'currency_id': self.currency_id and self.currency_id.id or False,
        #     }))
        #
        # self.installment_ids = vals
        # activity_object = self.env['mail.activity']
        # for rec in self:
        #     users = self.env.ref('loan.group_loan_credit').users.ids
        #     user_id = self.env.user.id
        #     random_id = user_id
        #     while random_id == user_id:
        #         random_id = random.choice(users)
        #     activity_object = self.env['mail.activity']
        #     activity_values = self.activity_create_call(random_id, rec.id, 'loan.order',
        #                                                 'loan.model_loan_order',
        #                                                 'Customer Call Approve', 'Customer Approved And Call')
        #     activity_id = activity_object.create(activity_values)

    def activity_create_call(self, user_id, record_id, model_name, model_id, summary, note):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': summary,
            'note': note,
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_call_done').id,
        }

    def delete_installments(self):
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.with_context({'force_delete': True}).unlink()

    def action_admin_done(self):
        self.name.action_confirm_call()
        self.message_post(body=datetime.today(), subject='The Call is done and customer Confirmed')
        self.state = 'buying'

    def action_back_to_nafaes(self):
        self.name.action_confirm_call()
        self.state = 'buying'
        self.send_notification_to_user('group_customer_operation', "Send Back from Accountant"
                                       , "The Request has been returned from the accountant")

    def action_nafaes(self):
        self.name.action_move()
        if self.loan_type.id == 2 or 3:
            self.message_post(body=datetime.today(), subject='The Product has been Buying')
        elif self.loan_type.id == 1:
            self.message_post(body=datetime.today(), subject='The Customer has been Signed contract')
            self.send_contract_status()
        else:
            pass
        self.state = 'disburse'
        for rec in self:
            users = self.env.ref('loan.group_accounting_move').users.ids
            user_id = self.env.user.id
            random_id = user_id
            while random_id == user_id:
                random_id = random.choice(users)
            activity_object = self.env['mail.activity']
            activity_values = self.activity_action_move(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
            activity_id = activity_object.create(activity_values)
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_sales_return').users:
                    activity_values = self.activity_action_success(user.id, self.id, 'loan.order',
                                                                   'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)

    def activity_action_move(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Contracts signed",
            'note': "Contracts signed with the customer",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_action_move').id,
        }

    def activity_action_success(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Contracts Success",
            'note': "Contracts signed and Success",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_action_contract_success').id,
        }

    #     for rec in self:
    #         users = self.env.ref('loan.group_archive').users.ids
    #         user_id = self.env.user.id
    #         random_id = user_id
    #         while random_id == user_id:
    #             random_id = random.choice(users)
    #         activity_object = self.env['mail.activity']
    #         activity_values = self.activity_create_nafaes(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
    #         activity_id = activity_object.create(activity_values)
    #         # rec.write({'state': 'review done'})
    #
    # def activity_create_nafaes(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "Nafaes",
    #         'note': "A Nafaes item was purchased",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_nafaes').id,
    #     }
    # ****** we need to check this flow with credit team ******
    def action_send_credit(self):
        self.name.action_send_credit()
        self.message_post(body=datetime.today(), subject='The Request Sending Back to Credit V')
        self.state = 'return'
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_loan_credit').users:
                    activity_values = self.activity_send_credit(user.id, self.id, 'loan.order', 'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)
            # rec.write({'state': 'review done'})

    def activity_send_credit(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Call Customer",
            'note': "Call Customer and approve to downpayment",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_credit').id,
        }

    # def action_call_reject(self):
    #     phone = self.phone_customer
    #     sequence = self.seq_num
    #     reject = self.new_reject_reason
    #     sms_reject = 'مرحباً بك عميلنا العزيز نشكر لك ثقتك في فيول للتمويل ، يؤسفنا إبلاغك بأن طلب التمويل رقم ' + sequence + ' غير مقبول. ' + reject + ' نشكر لك اختيارك فيول للتمويل. لمزيد من الاستفسارات نسعد بخدمتكم على الرقم  8001184000 '
    #     # encoded_data = base64.b64encode(bytes(sms_approve, 'utf_8')).decode()
    #     values = '''{
    #                       "userName": "Fuelfinancesa",
    #                       "numbers": "''' + phone + '''",
    #                       "userSender": "fuelfinance",
    #                       "apiKey": "972a5299aefb1551fe6be4bdd910fe46",
    #                       "msg": "''' + sms_reject + '''"
    #                     }'''
    #
    #     headers = {
    #         'Content-Type': 'application/json;charset=UTF-8'
    #     }
    #     values = values.encode()
    #     response = requests.post('https://private-anon-2a3cb1c12a-msegat.apiary-proxy.com/gw/sendsms.php', data=values,
    #                              headers=headers)
    #
    #     print(response.status_code)
    #     print(response.headers)
    #     # print(response.json())
    #     # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    #     self.name.action_reject_call()
    #     self.message_post(body=datetime.today(),
    #                       subject='The Call is Done and customer Rejected - مرحباً بك عميلنا العزيز نشكر لك ثقتك في فيول للتمويل، يؤسفنا إبلاغك بأن طلب التمويل نشكر لك اختيارك فيول للتمويل. لمزيد من الاستفسارات نسعد بخدمتكم على الرقم  8001184000')
    #     self.state = 'reject'
    #     for rec in self:
    #         users = self.env.ref('loan.group_archive').users.ids
    #         user_id = self.env.user.id
    #         random_id = user_id
    #         while random_id == user_id:
    #             random_id = random.choice(users)
    #         activity_object = self.env['mail.activity']
    #         activity_values = self.activity_create_call_reject(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
    #         activity_id = activity_object.create(activity_values)
    #         # rec.write({'state': 'review done'})
    #
    # def activity_create_call_reject(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "Customer Call Reject",
    #         'note': "Customer Reject and Call",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_call_reject').id,
    #     }
    def reject_fazaa_order(self):
        """
        This Function To Reject Order When In Fazaa Type
        """
        pass

    def action_set_to_reject(self):
        if not self.new_reject_reason:
            raise ValidationError(_("Please Add Reject Reason!!!"))
        phone = self.phone_customer
        sequence = self.seq_num
        reject = self.new_reject_reason
        sms_reject = 'مرحباً بك عميلنا العزيز نشكر لك ثقتك في فيول للتمويل ، يؤسفنا إبلاغك بأن طلب التمويل رقم ' + sequence + ' غير مقبول. ' + reject + ' نشكر لك اختيارك فيول للتمويل. لمزيد من الاستفسارات نسعد بخدمتكم على الرقم  8001184000 '
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
        # print(response.json())
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        self.name.action_reject_call()
        self.message_post(body=datetime.today(),
                          subject='The Call is Done and customer Rejected - مرحباً بك عميلنا العزيز نشكر لك ثقتك في فيول للتمويل، يؤسفنا إبلاغك بأن طلب التمويل نشكر لك اختيارك فيول للتمويل. لمزيد من الاستفسارات نسعد بخدمتكم على الرقم  8001184000')
        self.state = 'reject'
        self.name.action_set_reject()
        self.message_post(body=datetime.today(), subject='The customer Rejected')
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.with_context({'force_delete': True}).unlink()
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_sales_return').users:
                    activity_values = self.activity_create_reject(user.id, self.id, 'loan.order',
                                                                  'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)

    # def notification_to_tele_sales(self):
    #     for rec in self:
    #         users = self.env.ref('loan.group_user_tele_selas').users.ids
    #         user_id = self.env.user.id
    #         random_id = user_id
    #         while random_id == user_id:
    #             random_id = random.choice(users)
    #         activity_object = self.env['mail.activity']
    #         activity_values = self.activity_create_reject(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
    #         activity_id = activity_object.create(activity_values)

    def activity_create_reject(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Customer Reject",
            'note': "Customer request denied",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_reject_done').id,
        }

    def activity_create_call_reject(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Customer Call Reject",
            'note': "Customer Reject and Call",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_call_reject').id,
        }

    def reject_reason_default(self):
        self.new_reject_reason = 'إلتزامات إئتمانية عالية'

    def set_flag_default(self):
        res = super(Loan, self).default_get(fields)
        default_record = self.env['account.analytic.account'].search([], limit=1)
        if 'account_analytic' in fields:
            res['account_analytic'] = default_record.id if default_record else False
        return res

    def action_set_to_reject_credit(self):
        if not self.new_reject_reason:
            raise ValidationError(_("Please Add Reject Reason!!!"))
        phone = self.phone_customer
        sequence = self.seq_num
        reject = self.new_reject_reason
        sms_reject = 'مرحباً بك عميلنا العزيز نشكر لك ثقتك في فيول للتمويل ، يؤسفنا إبلاغك بأن طلب التمويل رقم ' + sequence + ' غير مقبول. ' + reject + ' نشكر لك اختيارك فيول للتمويل. لمزيد من الاستفسارات نسعد بخدمتكم على الرقم  8001184000 '
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
        # print(response.json())
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        self.name.action_reject_call()
        self.message_post(body=datetime.today(),
                          subject='The Call is Done and customer Rejected - مرحباً بك عميلنا العزيز نشكر لك ثقتك في فيول للتمويل، يؤسفنا إبلاغك بأن طلب التمويل نشكر لك اختيارك فيول للتمويل. لمزيد من الاستفسارات نسعد بخدمتكم على الرقم  8001184000')
        self.state = 'reject'
        self.name.action_reject_credit()
        self.message_post(body=datetime.today(), subject='The customer Rejected')
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.with_context({'force_delete': True}).unlink()
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_sales_return').users:
                    activity_values = self.activity_reject_credit(user.id, self.id, 'loan.order',
                                                                  'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)
        # for rec in self:
        #     users = self.env.ref('loan.group_archive').users.ids
        #     user_id = self.env.user.id
        #     random_id = user_id
        #     while random_id == user_id:
        #         random_id = random.choice(users)
        #     activity_object = self.env['mail.activity']
        #     activity_values = self.activity_create_call_reject(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
        #     activity_id = activity_object.create(activity_values)
        # for rec in self:
        #     users = self.env.ref('loan.group_res_partner_operation').users.ids
        #     user_id = self.env.user.id
        #     random_id = user_id
        #     while random_id == user_id:
        #         random_id = random.choice(users)
        #     activity_object = self.env['mail.activity']
        #     activity_values = self.activity_reject_credit(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
        #     activity_id = activity_object.create(activity_values)

    def activity_reject_credit(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Customer Reject",
            'note': "Customer request denied",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_reject_credit').id,
        }

    def activity_create_call_reject(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Customer Call Reject",
            'note': "Customer Reject and Call",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_call_reject').id,
        }

    def action_approve_loan(self):
        self.name.action_approve()
        self.message_post(body=datetime.today(), subject='The customer Approved')
        self.state = 'approve'
        if self.loan_type:
            self.disburse_account = self.loan_type.disburse_account and self.loan_type.disburse_account.id or False
            self.disburse_journal = self.loan_type.disburse_journal and self.loan_type.disburse_journal.id or False
        self.approve_date = date.today()

        # activity_object = self.env['mail.activity']
        # for follower in self.message_follower_ids:
        #     user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
        #     if user != self.env.user:
        #         if user in self.env.ref('loan.group_sales_cancel').users:
        #             activity_values = self.activity_create_approve(user.id, self.id, 'loan.order',
        #                                                            'loan.model_loan_order')
        #             activity_id = activity_object.create(activity_values)
        # self.exa_call_action_approve()
        self.approve_confirmation_call_action()
        # for rec in self:
        #     users = self.env.ref('loan.group_sales_cancel').users.ids
        #     user_id = self.env.user.id
        #     random_id = user_id
        #     while random_id == user_id:
        #         random_id = random.choice(users)
        #     activity_object = self.env['mail.activity']
        #     activity_values = self.activity_create_approve(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
        #     activity_id = activity_object.create(activity_values)
        # rec.write({'state': 'review done'})

    def activity_create_approve(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Loan Approval",
            'note': "Loan Request Approved",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_loan_done').id,
        }

    def action_apply(self):
        self.name.action_apply()
        self.message_post(body=datetime.today(), subject='The Call is Done and customer Rejected')
        self.state = 'disburse'
        # return {
        #     'name': _('Write Note'),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'mail.compose.message',
        #     'view_mode': 'form',
        #     'target': 'new',
        # }
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_sales_cancel').users:
                    activity_values = self.activity_apply_order(user.id, self.id, 'loan.order', 'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)
            # rec.write({'state': 'review done'})

    def activity_apply_order(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Customer Apply",
            'note': "The Customer's Financing Request is Accepted",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_apply_done').id,
        }

    def action_archive(self):
        self.write({'active': False})

    def action_unarchive(self):
        self.write({'active': True})

    def write(self, vals):
        if 'active' in vals:
            if not self.env.user.has_group('loan.group_admin'):
                raise AccessError(_("Only Admin users can archive or unarchive records."))
        return super().write(vals)

    # def action_archive(self):
    #     self.name.action_archive()
    #     self.message_post(body=datetime.today(), subject='The customer has been Archived')
    #     self.state = 'reject'
    #     activity_object = self.env['mail.activity']
    #     activity_values = self.activity_create_archive(self.id, 'loan.order', 'loan.model_loan_order')
    #     activity_id = activity_object.create(activity_values)

    def activity_create_archive(self, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "The Request Archiving",
            'note': "the Request has been Archive",
            'date_deadline': datetime.today(),
            'activity_type_id': self.env.ref('loan.mail_activity_create_archive').id,
        }

    def action_not_apply(self):
        self.name.action_move()
        self.state = 'contract'
        # return {
        #     'name': _('Write Note'),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'mail.compose.message',
        #     'view_mode': 'form',
        #     'target': 'new',
        # }
        for rec in self:
            users = self.env.ref('loan.group_sales').users.ids
            user_id = self.env.user.id
            random_id = user_id
            while random_id == user_id:
                random_id = random.choice(users)
            activity_object = self.env['mail.activity']
            activity_values = self.activity_not_apply_order(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
            activity_id = activity_object.create(activity_values)
            # rec.write({'state': 'review done'})

    def activity_not_apply_order(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Customer Not Apply",
            'note': "The Customer's Financing Request is Not Accepted, Offer Number wrong!!!",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_not_apply').id,
        }

    def action_apply_reject(self):
        # self.name.action_apply()
        self.state = 'reject'
        # return {
        #     'name': _('Write Note'),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'mail.compose.message',
        #     'view_mode': 'form',
        #     'target': 'new',
        # }
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_sales_cancel').users:
                    activity_values = self.activity_reject_order(user.id, self.id, 'loan.order',
                                                                 'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)
            # rec.write({'state': 'review done'})

    def activity_reject_order(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Customer Rejected",
            'note': "The Customer's Financing Request is Reject",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_apply_reject').id,
        }

    # def action_legal_apply(self):
    #     self.name.action_open()
    #     self.state = 'open'
    #     # return {
    #     #     'name': _('Write Note'),
    #     #     'type': 'ir.actions.act_window',
    #     #     'res_model': 'mail.compose.message',
    #     #     'view_mode': 'form',
    #     #     'target': 'new',
    #     # }
    #     for rec in self:
    #         users = self.env.ref('loan.group_accounting_move').users.ids
    #         user_id = self.env.user.id
    #         random_id = user_id
    #         while random_id == user_id:
    #             random_id = random.choice(users)
    #         activity_object = self.env['mail.activity']
    #         activity_values = self.activity_legal_check(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
    #         activity_id = activity_object.create(activity_values)
    #         # rec.write({'state': 'review done'})
    #
    # def activity_legal_check(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "Support to the order",
    #         'note': "The Customer's Support to the order Printed",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_legal_apply').id,
    #     }

    # user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
    # if user != self.env.user:
    #     if user in self.env.ref('loan.group_accounting_move').users:
    #         activity_values = self.activity_action_move(user.id, self.id, 'loan.order', 'loan.model_loan_order')
    #         activity_id = activity_object.create(activity_values)

    # def action_move_account(self):
    #     self.name.action_move()
    #     self.message_post(body=datetime.today(), subject='The Request Move to Accountant')
    #     self.state = 'disburse'
    #     for rec in self:
    #         users = self.env.ref('loan.group_accounting_move').users.ids
    #         user_id = self.env.user.id
    #         random_id = user_id
    #         while random_id == user_id:
    #             random_id = random.choice(users)
    #         activity_object = self.env['mail.activity']
    #         activity_values = self.activity_action_move(random_id, rec.id, 'loan.order', 'loan.model_loan_order')
    #         activity_id = activity_object.create(activity_values)
    #     activity_object = self.env['mail.activity']
    #     for follower in self.message_follower_ids:
    #         user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
    #         if user != self.env.user:
    #             if user in self.env.ref('loan.group_sales_cancel').users:
    #                 activity_values = self.activity_action_success(user.id, self.id, 'loan.order',
    #                                                                'loan.model_loan_order')
    #                 activity_id = activity_object.create(activity_values)
    #
    # def activity_action_move(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "Contracts signed",
    #         'note': "Contracts signed with the customer",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_action_move').id,
    #     }
    #
    # def activity_action_success(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "Contracts Success",
    #         'note': "Contracts signed and Success",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_action_contract_success').id,
    #     }

    def action_set_check(self):
        self.state = 'new'

    def action_set_done(self):
        self.state = 'simah'

    # def action_set_draft(self):
    #     self.name.action_draft()
    #     self.state = 'draft'
    #     activity_object = self.env['mail.activity']
    #     for follower in self.message_follower_ids:
    #         user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
    #         if user != self.env.user:
    #             if user in self.env.ref('loan.group_sales_cancel').users:
    #                 activity_values = self.activity_create_set_draft(user.id, self.id, 'res.partner',
    #                                                                  'base.model_res_partner')
    #                 activity_id = activity_object.create(activity_values)
    #
    # def activity_create_set_draft(self, user_id, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "SET To Draft",
    #         'note': "The Request SET To Draft",
    #         'date_deadline': datetime.today(),
    #         'user_id': user_id,
    #         'activity_type_id': self.env.ref('loan.mail_activity_create_set_draft').id,
    #     }

    # return super(Loan, self).unlink()

    def action_send_back(self):
        self.name.action_installment()
        self.message_post(body=datetime.today(), subject='The Request Sending Back')
        self.state = 'simah'
        activity_object = self.env['mail.activity']
        for follower in self.message_follower_ids:
            user = self.env['res.users'].search([('partner_id', '=', follower.partner_id.id)], limit=1)
            if user != self.env.user:
                if user in self.env.ref('loan.group_loan_credit').users:
                    activity_values = self.activity_send_back(user.id, self.id, 'loan.order', 'loan.model_loan_order')
                    activity_id = activity_object.create(activity_values)
            # rec.write({'state': 'review done'})

    def activity_send_back(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Send Back",
            'note': "The funding application must be reviewed",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_send_back').id,
        }

    def get_account_move_vals(self):
        if not self.disburse_journal:
            raise ValidationError(_("Select Disburse Journal !!!"))
        vals = {
            'date': self.disbursement_date,
            'ref': self.seq_num or 'Loan Disburse',
            'journal_id': self.disburse_journal and self.disburse_journal.id or False,
            'company_id': self.company and self.company.id or False,
        }
        return vals

    def get_debit_lines(self):
        if self.name and not self.name.property_account_receivable_id:
            raise ValidationError(_("Select Client Receivable Account !!!"))
        vals = {
            'partner_id': self.name and self.name.id or False,
            'account_id': self.name.property_account_receivable_id and self.name.property_account_receivable_id.id or False,
            'debit': self.loan_amount,
            'name': self.seq_num or '/',
            'date_maturity': self.disbursement_date,
        }
        return vals

    def get_credit_lines(self):
        if not self.disburse_account:
            raise ValidationError(_("Select Disburse Account !!!"))
        vals = {
            'partner_id': self.name and self.name.id or False,
            'account_id': self.disburse_account and self.disburse_account.id or False,
            'credit': self.loan_amount,
            'name': self.seq_num or '/',
            'date_maturity': self.disbursement_date,
        }
        return vals

    def action_disburse_loan(self):
        if self.approve_date:
            self.name.action_disburse()
            self.state = 'active'
            self.disbursement_date = date.today()
            self.message_post(body=datetime.today(), subject='The Customer financed')
            for rec in self:
                users = self.env.ref('loan.group_collection').users.ids
                user_id = self.env.user.id
                random_id = user_id
                while random_id == user_id:
                    random_id = random.choice(users)
                activity_object = self.env['mail.activity']
                activity_values = self.activity_create_group_legal(random_id, rec.id, 'loan.order',
                                                                   'loan.model_loan_order')
                activity_id = activity_object.create(activity_values)
                # rec.write({'state': 'review done'})
            self._generate_disburse_payment()
            if len(self) == 1:
                return {
                    'name': _('Payment'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.payment',
                    'res_id': self.disburse_payment_id.id,
                    'view_mode': 'form',
                    'target': 'new',
                }
        else:
            raise ValidationError(_("Please make sure that the customer agrees to it  !!!"))

    def activity_create_group_legal(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "The Customer Financed",
            'note': "The Customer Financed",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_legal').id,
        }

    # def action_auto_reminder(self):
    #     for rec in self:
    #         if rec.state != 'active':
    #             continue
    #         # rec.flag_send_sms = True
    #         else:
    #             phone = rec.phone_customer
    #             sms_reminder = str(
    #                 'عميلنا العزيز، نأمل الإسراع في سداد القسط الشهري المستحق عليك للاستفسار نرجو الاتصال على الرقم 8001184000')
    #             values = '''{
    #                               "userName": "Fuelfinancesa",
    #                               "numbers": "''' + phone + '''",
    #                               "userSender": "fuelfinance",
    #                               "apiKey": "972a5299aefb1551fe6be4bdd910fe46",
    #                               "msg": "''' + sms_reminder + '''"
    #                             }'''
    #
    #             headers = {
    #                 'Content-Type': 'application/json;charset=UTF-8'
    #             }
    #             values = values.encode()
    #             response = requests.post('https://private-anon-06174c23f3-msegat.apiary-proxy.com/gw/sendsms.php',
    #                                      data=values,
    #                                      headers=headers)
    #
    #             print(response.status_code)
    #             print(response.headers)
    #             print(response.json())
    #             print('!!!!!!!!!!!!!!!!!! yes')
    #             # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    #             rec.message_post(body=datetime.today(),
    #                              subject='Auto payment reminder has been sent - Day 1 of the month - عميلنا العزيز، نأمل الإسراع في سداد القسط الشهري المستحق عليك للاستفسار نرجو الاتصال على الرقم 8001184000')

    # def _cron_auto_reminder(self):
    #     fields.Date.today()
    #     today = fields.Date.from_string(fields.Date.context_today(self))
    #     if today.day != 29:
    #         return
    #     else:
    #         domain = [('date', '=', today), ('flag_send_sms', '=', False)]
    #         self.search(domain)._action_auto_reminder()
    #         print('!!!!!!!!!!!!!!!!!! yes', domain)

    def _action_second_auto_reminder(self):
        for rec in self:
            phone = rec.phone_customer
            sms_reminder = str(
                'عميلنا العزيز، نأمل الإسراع في سداد القسط الشهري المستحق عليك تجنب لاتخاذ الإجراءات القانونية للاستفسار نرجو الاتصال على الرقم 8001184000')
            # encoded_data = base64.b64encode(bytes(sms_approve, 'utf_8')).decode()
            values = '''{
                              "userName": "Fuelfinancesa",
                              "numbers": "''' + phone + '''",
                              "userSender": "fuelfinance",
                              "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                              "msg": "''' + sms_reminder + '''"
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
            # self.name.action_reject_call()
            rec.message_post(body=datetime.today(),
                             subject='Auto payment reminder has been sent - Day 5 of the month - عميلنا العزيز، نأمل الإسراع في سداد القسط الشهري المستحق عليك تجنب لاتخاذ الإجراءات القانونية للاستفسار نرجو الاتصال على الرقم 8001184000')

    def _cron_second_reminder(self):
        fields.Date.today()
        today = fields.Date.from_string(fields.Date.context_today(self))
        if today.day == 5:
            return
        domain = [('date', '=', today), ('state', '=', 'active')]
        self.search(domain)._action_second_auto_reminder()

    # def _action_second_auto_reminder(self):
    #     for rec in self:
    #         phone = rec.phone_customer
    #         sms_reminder = str(
    #             'عميلنا العزيز، نأمل الإسراع في سداد القسط الشهري المستحق عليك تجنب لاتخاذ الإجراءات القانونية للاستفسار نرجو الاتصال على الرقم 8001184000')
    #         # encoded_data = base64.b64encode(bytes(sms_approve, 'utf_8')).decode()
    #         values = '''{
    #                           "userName": "Fuelfinancesa",
    #                           "numbers": "''' + phone + '''",
    #                           "userSender": "fuelfinance",
    #                           "apiKey": "972a5299aefb1551fe6be4bdd910fe46",
    #                           "msg": "''' + sms_reminder + '''"
    #                         }'''
    #
    #         headers = {
    #             'Content-Type': 'application/json;charset=UTF-8'
    #         }
    #         values = values.encode()
    #         response = requests.post('https://private-anon-06174c23f3-msegat.apiary-proxy.com/gw/sendsms.php',
    #                                  data=values,
    #                                  headers=headers)
    #
    #         print(response.status_code)
    #         print(response.headers)
    #         print(response.json())
    #         # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    #         # self.name.action_reject_call()
    #         rec.message_post(body=datetime.today(),
    #                          subject='Auto payment reminder has been sent - Day 5 of the month - عميلنا العزيز، نأمل الإسراع في سداد القسط الشهري المستحق عليك تجنب لاتخاذ الإجراءات القانونية للاستفسار نرجو الاتصال على الرقم 8001184000')

    # def _cron_second_reminder(self):
    #     fields.Date.today()
    #     today = fields.Date.from_string(fields.Date.context_today(self))
    #     if today.day == 5:
    #         return
    #     domain = [('date', '=', today), ('state', '=', 'active')]
    #     self.search(domain)._action_second_auto_reminder()

    # if self.disbursement_date:
    #     account_move_val = self.get_account_move_vals()
    #     account_move_id = self.env['account.move'].create(account_move_val)
    #     vals = []
    #     if account_move_id:
    #         val = self.get_debit_lines()
    #         vals.append((0, 0, val))
    #         val = self.get_credit_lines()
    #         vals.append((0, 0, val))
    #         account_move_id.line_ids = vals
    #         self.disburse_journal_entry = account_move_id and account_move_id.id or False
    # if self.disburse_journal_entry:
    #     self.state = 'open'
    # self.compute_installment(self.disbursement_date)

    def action_open_loan(self):
        self.name.action_open()
        self.message_post(body=datetime.today(), subject='The Loan active')
        self.state = 'active'
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.action_early_installment()
                installment.action_paid_installment()
            for rec in self:
                if rec.remaining_amount > 0:
                    rec.paid_amount = rec.remaining_amount - rec.paid_amount

    # print(0, '//////////////////////////////////////////////////////////////')

    @api.depends('close_date')
    def action_close_loan(self):
        for rec in self:
            # Check if there are unpaid installments related to this loan
            unpaid_installments = rec.installment_ids.filtered(lambda i: i.state == 'unpaid')
            if unpaid_installments:
                raise ValidationError(_("There are still unpaid installments for this loan."))
            else:
                # Set state to 'close' and update the close date
                rec.state = 'close'
                rec.remaining_amount = 0
                rec.remaining_principle = 0
                rec.remaining_interest = 0
                rec.name.action_close_admin()
                rec.close_date = date.today() if rec.state == 'close' else rec.approve_date

    @api.depends('payment_status')
    def compute_payment_status(self):
        for rec in self:
            if rec.late_amount == 0:
                rec.payment_status = 0
            elif rec.late_amount == rec.installment_month:
                rec.payment_status = 1
            elif rec.late_amount == (rec.installment_month * 2):
                rec.payment_status = 2
            else:
                rec.payment_status = 0
                print(rec.payment_status)

    def _compute_final_amount(self):
        for r in self:
            r._compute_amounts()

    @api.depends('installment_ids.principal_amount', 'installment_ids.interest_amount', 'installment_ids.date')
    def _compute_amounts(self):
        for r in self:
            principle_amount = 0
            early_interest_amount = 0
            installment_counter = int(self.env['ir.config_parameter'].sudo().get_param('loan.early.installment', 3))
            unpaid_interest = 0  # Interest not paid due to early payment
            late_amount = 0  # Total late amount
            early_amount = 0  # Total early amount
            unpaid_installment_ids = self.env['loan.installment']

            for installment_id in r.installment_ids:
                if installment_id.state == 'paid':
                    continue

                unpaid_installment_ids += installment_id
                principle_amount += installment_id.principal_amount

                # If installment is partial, only consider the remaining unpaid portion if it's late
                if installment_id.state == 'partial' and installment_id.is_late:
                    remaining_unpaid = installment_id.principal_amount + installment_id.interest_amount - installment_id.amount_paid
                    late_amount += remaining_unpaid

                # If installment is fully unpaid and late, take the full amount as late
                elif installment_id.state != 'partial' and installment_id.is_late:
                    late_amount += installment_id.principal_amount + installment_id.interest_amount

                # Early interest calculation
                if installment_counter > 0 or installment_id.is_late or installment_id.state == 'partial':
                    early_interest_amount += installment_id.interest_amount
                else:
                    unpaid_interest += installment_id.interest_amount

                if not installment_id.is_late:
                    installment_counter -= 1

            r.late_amount = late_amount  # Only includes unpaid portion if installment is partial and late
            r.early_amount = principle_amount + early_interest_amount
            r.early_interest_amount = early_interest_amount
            r.unpaid_interest = unpaid_interest
            r.unpaid_installment_ids = unpaid_installment_ids

    def update_loan_status(self):  # TODO: Update Status of loan in website
        base_url = 'https://fuelfinance.sa/api/webhook/loan-status'
        # base_url = 'https://stage.fuelfinance.sa/api/webhook/loan-status'
        loan_id = self.loan_record
        status = self.state
        if self.state == 'close':
            payload = json.dumps({"loan_id": loan_id, "status": status})
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
            # payload = json.dumps({"loan_id": loan_id,"status": status})
            # headers = {
            #     'Accept': 'application/json',
            #     'Content-Type': 'application/json'
            # }
            # response = requests.request("POST", url, headers=headers, data=payload)
            # print(response)
            # print(payload)

        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def set_loan_close(self, is_early_payment=False):
        """Set the loan to 'closed' and create activities if all installments are paid."""
        for loan in self:
            if not is_early_payment and (loan.state != 'active' or not all(
                    installment.state == 'paid' for installment in loan.installment_ids)):
                raise UserError(_("The loan cannot be closed as not all installments are paid."))
            for rec in self:
                # Operations Group
                operation_users = self.env.ref('loan.group_customer_operation').users.ids
                user_id = self.env.user.id
                random_id = user_id
                while random_id == user_id:
                    random_id = random.choice(operation_users)
                activity_object = self.env['mail.activity']
                activity_values = self.activity_request_close(
                    random_id, rec.id, 'loan.order', 'loan.model_loan_order'
                )
                activity_object.create(activity_values)
                _logger.info(f"Activity created for Operations Group for Loan ID {rec.id}")
                # Collections Group
                collection_users = self.env.ref('loan.group_collection').users.ids
                random_id = user_id
                while random_id == user_id:
                    random_id = random.choice(collection_users)
                activity_values = self.activity_request_close(
                    random_id, rec.id, 'loan.order', 'loan.model_loan_order'
                )
                activity_object.create(activity_values)
                _logger.info(f"Activity created for Collections Group for Loan ID {rec.id}")

    def activity_request_close(self, user_id, record_id, model_name, model_id):
        """Return a dictionary to create the activity."""
        try:
            return {
                'res_model': model_name,
                'res_model_id': self.env.ref(model_id).id,
                'res_id': record_id,
                'summary': "Close Loan",
                'note': "The loan is fully paid and ready to be closed.",
                'date_deadline': date.today(),
                'user_id': user_id,
                'activity_type_id': self.env.ref('loan.mail_activity_close').id,
            }
        except Exception as e:
            _logger.error(f"Error creating activity request: {e}")
            return {}

    def action_early_payment(self):
        self.ensure_one()
        # Set the remaining values to 0 as requested
        self.remaining_amount = 0
        self.remaining_interest = 0
        self.remaining_principle = 0
        self.late_amount = 0
        self.name.action_early()
        self.close_date = date.today()
        self.state = 'early'
        self.message_post(body=datetime.today(), subject='The Request Early Payment')
        self.update_loan_status()
        self.set_loan_close(is_early_payment=True)

        payment_name = f'{self.seq_num or self.id} Early Payment'
        interest_account, installment_account, payment_journal, disburse_account = self.get_loan_account_journal()
        today = fields.Date.context_today(self)
        payment_values = {
            "partner_type": "customer",
            "payment_type": "inbound",
            "partner_id": self.name.id,
            "amount": self.early_amount,
            "date": today,
            "ref": payment_name,
            "journal_id": payment_journal,
        }
        self.early_payment_id = payment_id = self.env['account.payment'].create(payment_values)
        self.unpaid_installment_ids.write(
            {'flag_monthly_move': True})  # this will prevent the monthly entry cron job from duplicating the amount
        for installment_id in self.unpaid_installment_ids:
            installment_id.action_paid_installment(payment_id=payment_id)

        move_name = f'{self.seq_num} Early Payment'
        move_values = {
            'date': today,
            'partner_name': self.name.id,
            'identification_id': self.identification_id,
            'ref': self.seq_num or f'Loan Payment {self.id}',
            'journal_id': self.loan_type.payment_journal.id,
        }
        unearned_line_values = {
            'partner_id': self.name.id,
            'account_id': self.loan_type.unearned_interest_account.id,
            'debit': self.early_interest_amount + self.unpaid_interest,
            'name': move_name
        }
        interest_line_values = {
            'partner_id': self.name.id,
            'account_id': interest_account,
            'credit': self.early_interest_amount,
            'name': move_name
        }
        receivable_line_values = {
            'partner_id': self.name.id,
            'account_id': self.name.property_account_receivable_id.id,
            'credit': self.unpaid_interest,
            'name': move_name
        }
        # unearned_line_values and interest_line_values are in place of the normal monthly interest, but the difference is that, the amount can differs between credit and debit lines (of course the overall total is balanced)
        print(
            f'existing balance {payment_id.move_id.amount_total_signed} debit = {sum(payment_id.move_id.line_ids.mapped("debit"))} credit = {sum(payment_id.move_id.line_ids.mapped("credit"))}')
        print(
            f'#unearned_line_values {self.early_interest_amount} + {self.unpaid_interest} = {self.early_interest_amount + self.unpaid_interest}')
        print(unearned_line_values)
        print(f'#interest_line_values = {self.early_interest_amount}')
        print(interest_line_values)
        move_values['line_ids'] = [
            (Command.CREATE, 0, unearned_line_values),
            (Command.CREATE, 0, interest_line_values),
            (Command.CREATE, 0, receivable_line_values),
        ]
        if payment_id.move_id.amount_total_signed == 0:
            raise UserError('Amount 0')
        self.early_move_id = self.env['account.move'].create(move_values)
        # Send Message To Tell Customer To Tell Him The Installment Paid
        early_paid_message = f"""
                        عميلنا العزيز, شكراً لك على السداد. نأمل أن خدماتنا قد حازت على رضاك.
                        لمزيد من الاستفسارات نسعد بخدمتك على الرقم المجاني 8001184000 خلال أوقات العمل الرسمية من الأحد إلى الخميس من 9 صباحاً وحتى 5 مساءاً, نشكر لكم اختياركم فيول للتمويل.
                                                """
        if self.name.phone:
            self.send_messeage(self.name.phone, early_paid_message)
            self.message_post(body=early_paid_message)
        return {
            'name': _('Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'res_id': payment_id.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.depends('loan_amount', 'rate')
    def _get_interest(self):
        for rec in self:
            rec.update({
                'interest_amount': rec.loan_amount % rec.rate,
            })

    @api.onchange('remaining_amount', 'paid_amount', 'installment_amount_loan')
    def get_installment(self):
        for rec in self:
            rec.update({
                'paid_amount': rec.paid_amount + rec.installment_amount_loan,
                'remaining_amount': rec.remaining_amount - rec.installment_amount_loan,
            })

    @api.depends('remaining_interest', 'remaining_principle')
    def get_remaining_amount(self):
        interest = 0
        principle = 0
        for rec in self:
            for installment in rec.installment_ids:
                if installment.state == 'unpaid':
                    interest += installment.interest_amount
                    principle += installment.principal_amount
                else:
                    pass
                rec.remaining_interest = interest
                rec.remaining_principle = principle
                print('remaining_interest', rec.remaining_interest)
                print('remaining_principle', rec.remaining_principle)

    # @api.constrains('installment_month', 'loan_limit_month')
    # def compare_installment(self):
    #     for rec in self:
    #         if rec.installment_month >= rec.loan_limit_month:
    #             raise ValidationError(_("the monthly installments that are greater than the limit!!!"))

    # def create_notification(self):
    #     print('cron')
    #     action = self.env.ref('loan.request_action')
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': _('Warning!'),
    #             'message': '%s',
    #             'links': [{
    #                 'label': self.name.name,
    #                 'url': f'#action={action.id}&id={self.id}&model=loan.order',
    #             }],
    #             'sticky': False,
    #         }
    #     }
    # self.env['loan.order'].search([('identification_id', '=', self.identification_id), ('state', '=', 'create')])
    # if self.state == 'open':
    #     for installment in self.installment_ids:
    #         if installment.state == 'unpaid':
    # def compute_installment(self):
    #     self.name.action_installment()
    #     self.state = 'create'
    #     today = date.today()
    #     if self.installment_ids:
    #         for installment in self.installment_ids:
    #             installment.with_context({'force_delete': True}).unlink()
    #
    #     inc_month = 1
    #     if self.installment_type == 'quarter':
    #         inc_month = 1
    #
    #     amount = self.loan_amount
    #     interest = self.interest_amount
    #     total = self.remaining_amount
    #
    #     if self.state == 'create':
    #         request_date = self.request_date
    #     else:
    #         request_date = today
    #     vals = []
    #     interest_account, installment_account, payment_journal, disburse_account = self.get_loan_account_journal()
    #
    #     for i in range(1, self.loan_term + 1):
    #         if self.loan_type.name:
    #             amount = self.loan_amount / self.loan_term
    #             total = self.remaining_amount / self.loan_term
    #             # principal = self.loan_amount
    #
    #             if i <= interest:
    #                 if self.loan_term == 0:
    #                     raise ValidationError(_("The Term cannot be less than 1 months"))
    #                 elif self.loan_term == 1:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 100) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 2:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 99.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 3:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 99) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 4:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 98.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 5:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 98) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 6:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 97.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 7:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 97) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 8:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 96.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 9:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 96) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 10:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 95.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 11:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 95) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 12:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 94.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 13:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 94) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 14:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 93.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 15:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 93) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 16:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 92.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 17:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 92) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 18:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 91.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 19:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 91) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 20:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 90.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 21:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 90) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 22:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 89.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 23:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 89) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 24:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 88.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 25:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 88) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 26:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 87.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 27:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 87) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 28:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 86.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 29:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 86) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 30:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 85.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 31:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 85) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 32:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 84.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 33:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 84) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 34:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 83.5) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 35:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 83) / 100)
    #                     principal = total - interest
    #                 elif self.loan_term == 36:
    #                     interest = self.interest_amount / self.loan_term * ((self.loan_term - i + 82.5) / 100)
    #                     principal = total - interest
    #                 else:
    #                     raise ValidationError(_("The Term cannot be more than 36 months"))
    #             print(interest)
    #             # principal = self.loan_amount / self.loan_term
    #         request_date = request_date.replace(day=27) + relativedelta(months=inc_month)
    #         vals.append((0, 0, {
    #             'seq_name': 'INS - ' + self.seq_num + ' - ' + str(i),
    #             'name': self.name and self.name.id or False,
    #             'date': request_date,
    #             'principal_amount': principal,
    #             'interest_amount': interest,
    #             'state': 'unpaid',
    #             'interest_account': interest_account or False,
    #             'disburse_account': disburse_account or False,
    #             'installment_account': installment_account or False,
    #             'payment_journal': payment_journal or False,
    #             'currency_id': self.currency_id and self.currency_id.id or False,
    #         }))
    #     self.installment_ids = vals
    #
    #     self.message_post(body=datetime.today(), subject='Create Installment')
    #     activity_object = self.env['mail.activity']
    #     activity_values = self.activity_create_loan(self.id, 'loan.order', 'loan.model_loan_order')
    #     activity_id = activity_object.create(activity_values)
    #     if self.installment_ids:
    #         for installment in self.installment_ids:
    #             installment.with_context({'force_delete': True}).unlink()
    #
    # def activity_create_loan(self, record_id, model_name, model_id):
    #     """
    #         return a dictionary to create the activity
    #     """
    #     return {
    #         'res_model': model_name,
    #         'res_model_id': self.env.ref(model_id).id,
    #         'res_id': record_id,
    #         'summary': "The Request Created",
    #         'note': "The Request Will be Created",
    #         'date_deadline': datetime.today(),
    #         'activity_type_id': self.env.ref('loan.mail_activity_create_loan').id,
    #     }

    def send_to_l1(self):
        self._compute_fees()
        self.remove_fees_amount()
        for rec in self:
            if rec.state == 'simah':
                if rec.mtg or rec.mtg_installment > 0:
                    if rec.deduction_after > 0.65:
                        raise ValidationError(
                            _('The total DBR deduction after value is %s, which is more than 65%%.') % rec.deduction_after
                        )
                    # If deduction_after is <= 65, the record is valid, so pass
                else:
                    if rec.deduction_after > 0.45:
                        raise ValidationError(
                            _('The deduction after value is %s, which is more than 45%%.') % rec.deduction_after
                        )
                    # If deduction_after is <= 45, the record is valid, so pass
        self.state = 'l1'
        # self.check_total_dbr()
        self.name.action_l1()
        self.message_post(body=datetime.today(), subject='Submit Application to L1')
        for rec in self:
            users = self.env.ref('loan.group_credit_l1').users.ids
            user_id = self.env.user.id
            random_id = user_id
            while random_id == user_id:
                random_id = random.choice(users)
            activity_object = self.env['mail.activity']
            activity_values = self.activity_create_group_credit_l1(random_id, rec.id, 'loan.order',
                                                                   'loan.model_loan_order')
            activity_id = activity_object.create(activity_values)
            # rec.write({'state': 'review done'})

    def activity_create_group_credit_l1(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "Confirm",
            'note': "Send to Credit L1",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('loan.mail_activity_credit_l1').id,
        }

    def compute_installment(self):
        self.get_compute_irr()
        print('request_date', self.request_date)
        self._compute_fees()
        self.ensure_one()
        self.credit_user = self.env.user
        self.name.action_installment()
        self.state = 'simah'
        # today = date.today()
        # if self.installment_ids:
        #     for installment in self.installment_ids:
        #         installment.with_context({'force_delete': True}).unlink()
        #
        # inc_month = 1
        # if self.installment_type == 'quarter':
        #     inc_month = 1
        #
        # if self.state == 'simah':
        #     request_date_date = self.request_date_date
        # else:
        #     request_date_date = today
        # vals = []
        # interest_account, installment_account, payment_journal, disburse_account = self.get_loan_account_journal()
        #
        # asce_ins_x = self.loan_amount
        # asce_ins_y = self.loan_sum
        # down = self.down_payment_loan
        # final_amount = asce_ins_x - down
        # total_loan_amount = asce_ins_y - down
        # print('1', final_amount)
        # for i in range(1, self.loan_term + 1):
        #     if self.loan_type.name:
        #         term = self.loan_term
        #         total = self.loan_sum
        #         amount = self.loan_amount - self.down_payment_loan
        #         interest_x = self.interest_amount
        #         irr = self.irr
        #         installment_x = total / term
        #         if self.loan_term < 3 or self.loan_term > 61:
        #             raise ValidationError(_("The Term cannot be less than 3 or more than 60 months"))
        #         else:
        #             interest_x = final_amount * irr
        #             principle_x = installment_x - interest_x
        #             desc_ins_x = amount - principle_x
        #             desc_ins_y = total - installment_x
        #     final_amount = final_amount - principle_x
        #     total_loan_amount = total_loan_amount - installment_x
        #     print('2', final_amount)
        #     if request_date_date.day > 15:
        #         request_date_date = request_date_date.replace(day=27) + relativedelta(months=inc_month)
        #     else:
        #         request_date_date = request_date_date.replace(day=27)
        #     vals.append((0, 0, {
        #         'seq_name': 'INS - ' + self.seq_num + ' - ' + str(i),
        #         'i_num': str(i),
        #         'name': self.name and self.name.id or False,
        #         'date': request_date_date,
        #         'principal_amount': principle_x,
        #         'interest_amount': interest_x,
        #         'descending_installment': desc_ins_x,
        #         'descending_installment_y': desc_ins_y,
        #         'ascending_installment': final_amount,
        #         'total_ascending_installment': total_loan_amount,
        #         'state': 'unpaid',
        #         'interest_account': interest_account or False,
        #         'disburse_account': disburse_account or False,
        #         'installment_account': installment_account or False,
        #         'payment_journal': payment_journal or False,
        #         'currency_id': self.currency_id and self.currency_id.id or False,
        #     }))
        # self.installment_ids = vals
        # if self.installment_ids:
        #     for installment in self.installment_ids:
        #         installment.with_context({'force_delete': True}).unlink()
        #
        # inc_month = 1
        # if self.installment_type == 'quarter':
        #     inc_month = 1
        # if self.state == 'create':
        #     request_date_date = self.request_date_date
        # else:
        #     request_date_date = today
        # vals = []
        # interest_account, installment_account, payment_journal, disburse_account = self.get_loan_account_journal()
        #
        # asce_ins_x = self.loan_amount
        # down = self.down_payment_loan
        # final_amount = asce_ins_x - down
        # print('1', final_amount)
        # for i in range(1, self.loan_term + 1):
        #     if self.loan_type.name:
        #         term = self.loan_term
        #         total = self.loan_sum
        #         amount = self.loan_amount
        #         down = self.down_payment_loan
        #         interest_x = self.interest_amount
        #         irr = self.irr
        #         desc_ins_x = 1
        #         installment_x = total / term
        #         if self.loan_term < 3 or self.loan_term > 61:
        #             raise ValidationError(_("The Term cannot be less than 3 or more than 60 months"))
        #         else:
        #             interest_x = final_amount * irr
        #             principle_x = installment_x - interest_x
        #             desc_ins_x = amount - principle_x
        #     final_amount = final_amount - final_amount
        #     print('2', final_amount)
        #     if request_date_date.day > 15:
        #         request_date_date = request_date_date.replace(day=27) + relativedelta(months=inc_month)
        #     else:
        #         request_date_date = request_date_date.replace(day=27)
        #     vals.append((0, 0, {
        #         'seq_name': 'INS - ' + self.seq_num + ' - ' + str(i),
        #         'name': self.name and self.name.id or False,
        #         'date': request_date_date,
        #         'principal_amount': principle_x,
        #         'interest_amount': interest_x,
        #         'descending_installment': desc_ins_x,
        #         'ascending_installment': final_amount,
        #         'state': 'unpaid',
        #         'interest_account': interest_account or False,
        #         'disburse_account': disburse_account or False,
        #         'installment_account': installment_account or False,
        #         'payment_journal': payment_journal or False,
        #         'currency_id': self.currency_id and self.currency_id.id or False,
        #     }))
        # self.installment_ids = vals
        self.message_post(body=datetime.today(), subject='Create Installment')
        activity_object = self.env['mail.activity']
        activity_values = self.activity_create_loan(self.id, 'loan.order', 'loan.model_loan_order')
        activity_id = activity_object.create(activity_values)

    def activity_create_loan(self, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "The Request Created",
            'note': "The Request Will be Created",
            'date_deadline': datetime.today(),
            'activity_type_id': self.env.ref('loan.mail_activity_create_loan').id,
        }

    def archive_admin(self):
        # self.name.action_archive()
        self.message_post(body=datetime.today(), subject='The customer has been Archived by Admin')
        self.state = 'archive'

    def disburse_admin(self):
        self.name.action_disburse()
        self.message_post(body=datetime.today(), subject='The Request Move to Finance by Admin')
        self.state = 'disburse'

    def close_admin(self):
        self.name.action_close_admin()
        for rec in self:
            if rec.state == 'close':
                rec.close_date = date.today()
            else:
                rec.close_date = rec.close_date
        self.message_post(body=datetime.today(), subject='The customer has been Closed by Admin')
        self.state = 'close'
        self.update_loan_status()

    def control_admin(self):
        self._compute_fees()
        self.get_compute_irr()
        self.name.action_installment()
        self.state = 'simah'
        today = date.today()
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.with_context({'force_delete': True}).unlink()

        inc_month = 1
        if self.installment_type == 'quarter':
            inc_month = 1

        if self.state == 'simah':
            request_date_date = self.request_date_date
        else:
            request_date_date = today
        vals = []
        interest_account, installment_account, payment_journal, disburse_account = self.get_loan_account_journal()

        asce_ins_x = self.loan_amount
        asce_ins_y = self.loan_sum
        down = self.down_payment_loan
        final_amount = asce_ins_x - down
        total_loan_amount = asce_ins_y - down
        print('1', final_amount)
        for i in range(1, self.loan_term + 1):
            if self.loan_type.name:
                term = self.loan_term
                total = self.loan_sum
                amount = self.loan_amount - self.down_payment_loan
                interest_x = self.interest_amount
                irr = self.irr
                installment_x = total / term
                if self.loan_term < 1 or self.loan_term > 61:
                    raise ValidationError(_("The Term cannot be less than 3 or more than 60 months"))
                else:
                    interest_x = final_amount * irr
                    principle_x = installment_x - interest_x
                    desc_ins_x = amount - principle_x
                    desc_ins_y = total - installment_x
            final_amount = final_amount - principle_x
            total_loan_amount = total_loan_amount - installment_x
            print('2', final_amount)
            if request_date_date.day > 15:
                request_date_date = request_date_date.replace(day=27) + relativedelta(months=inc_month)
            else:
                request_date_date = request_date_date.replace(day=27)
            vals.append((0, 0, {
                'seq_name': 'INS - ' + self.seq_num + ' - ' + str(i),
                'i_num': str(i),
                'name': self.name and self.name.id or False,
                'date': request_date_date,
                'principal_amount': principle_x,
                'interest_amount': interest_x,
                'descending_installment': desc_ins_x,
                'descending_installment_y': desc_ins_y,
                'ascending_installment': final_amount,
                'total_ascending_installment': total_loan_amount,
                'state': 'unpaid',
                'interest_account': interest_account or False,
                'disburse_account': disburse_account or False,
                'installment_account': installment_account or False,
                'payment_journal': payment_journal or False,
                'currency_id': self.currency_id and self.currency_id.id or False,
            }))
        self.installment_ids = vals

    def _generate_disburse_payment(self):
        for r in self:
            payment_name = r.seq_num or f'Loan {r.id}'
            values = {
                "partner_type": "customer",
                "payment_type": "outbound",
                "partner_id": r.name.id,
                "amount": r.loan_amount,
                "date": fields.Date.context_today(self),
                "ref": payment_name,
                "journal_id": r.loan_type.disburse_journal.id,
            }
            payment_id = self.env['account.payment'].create(values)

            credit_line_name = payment_id.payment_reference or payment_name
            for line_id in payment_id.line_ids:
                line_id.name = line_id.name.replace('Customer Reimbursement', f'Disburse {payment_name}')
                if line_id.debit:
                    line_id.with_context(check_move_validity=False).debit += r.interest_amount
                if line_id.credit:
                    credit_line_name = line_id.name
            interest_line_values = {
                'partner_id': r.name.id,
                'account_id': r.loan_type.unearned_interest_account.id,
                'credit': r.interest_amount,
                'name': credit_line_name
            }
            payment_id.write({
                'line_ids': [(Command.CREATE, 0, interest_line_values)]
            })
            payment_id.move_id._check_balanced()  # this is very important, even though _check_balanced is called in the above write, but explicit all is backup for future changes, because we want to make sure the changes above are balanced
            self.disburse_payment_id = payment_id

    # ------------------ | Get Default City
    def _get_default_city_id(self):
        # Search for the city record with the given code
        riyadh_city = self.env['simah.city.api'].search([('code', '=', 'RIY')], limit=1)
        if riyadh_city:
            return riyadh_city.id
        else:
            # If Riyadh city is not found, return None or raise an error as per your requirement
            return False

    @api.depends('state', 'installment_ids.state')
    def _compute_show_close_button(self):
        """Compute if the close button should be visible."""
        for record in self:
            if (record.state == 'active' or 'early') and all(
                    installment.state == 'paid' for installment in record.installment_ids
            ):
                record.show_close_button = True
            else:
                record.show_close_button = False

    ######################################################### * Simah API * ###############################################
    # name = fields.Many2one('res.partner', string='Customer')
    simah_city_id = fields.Many2one('simah.city.api')
    city_id = fields.Integer(related='simah_city_id.city_id')
    first_name = fields.Char(related='name.first_name', string='First Name')
    family_name = fields.Char(related='name.family_name', string='Family Name')
    hijri_birth_of_date = fields.Char(related='name.birth_of_date_hijri', string="hijri DOfB")
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
    # nationality_textAr = fields.Char()
    cityOfResidence_textAr = fields.Char()
    maritalStatus_textAr = fields.Char()
    # maritalStatus_textAr = fields.Char()
    homeOwnership_textAr = fields.Char()
    # homeOwnership_textAr = fields.Char()
    residentialType_textAr = fields.Char()
    # residentialType_textAr = fields.Char()
    globalDBR = fields.Float(string='Global DBR')
    dbrForSalariedLoans = fields.Float(string='dbr For Salaried Loans')
    # applicableDBR = fields.Float(string='Applicable DBR')

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

    simahEnquiries = fields.One2many('simah.enquiries.api', 'simah', string="Previous Enquiries")
    creditInstrument = fields.One2many('credit.instrument.api', 'simah_simah', string="Credit Instrument")
    simahNarrative = fields.One2many('simah.narrative.api', 'simah_narr', string="Simah Narrative")
    simahAddress = fields.One2many('simah.addresses.api', 'simah_address', string="Simah Address")
    simahContact = fields.One2many('simah.contact.api', 'simah_contact', string="Simah Contact")
    simahEmployee = fields.One2many('simah.employee.api', 'simah_employee', string="Simah Employee")
    simahScore = fields.One2many('simah.score.api', 'simah_score', string="Simah Score")
    simahExpense = fields.One2many('simah.expense.api', 'simah_expense', string="Simah Expense")
    simahpersonalnarratives = fields.One2many('personal.narratives.api', 'simah_id', string="personal narratives")
    simahDefault = fields.One2many('simah.default.api', 'simah_default', string="simah Default")
    guarantorDefault = fields.One2many('guarantor.default.api', 'guarantor_default', string="guarantor Default")
    simahCheques = fields.One2many('simah.cheques.api', 'simah_cheques', string="Simah Cheques")
    simahJudgement = fields.One2many('simah.judgement.api', 'simah_judgement', string="Simah Judgement")
    publicNotices = fields.One2many('public.notices.api', 'public_notices', string="Public Notices")

    credit_instrument = fields.Many2one('credit.instrument.api')
    simah_dbr = fields.Float(string='Simah Deduction', compute='compute_dbr', store=True)
    dbr_installment = fields.Float(string='DBR Amount', compute='calculate_dbr_amount', store=True)
    mtg_installment = fields.Float(string='MTG Installment')
    mtg = fields.Boolean(string='MTG')
    is_ind = fields.Boolean(string='IND?')  # make internal_deduction field = 0
    bool_field = fields.Boolean('hide button', default=False)
    gov_sector = fields.Many2one('government.sector.api', name='GOV Sector')

    @api.onchange('is_ind', 'internal_deduction')
    def _onchange_is_internal_deduction(self):
        for rec in self:
            if rec.is_ind:
                if rec.gov_sector and rec.gov_sector.netSalary is not None:
                    rec.name.internal_deduction = 0.0
                    rec.name.salary_rate = rec.gov_sector.netSalary
                else:
                    rec.name.salary_rate = 0.0
            else:
                if rec.gov_sector and rec.gov_sector.totalDeductions is not None:
                    rec.name.internal_deduction = rec.gov_sector.totalDeductions
                else:
                    rec.name.internal_deduction = 0.0

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
        # self.dbr_installment = False

    @api.depends('dbr_installment', 'salary_net', 'simah_dbr')
    def compute_dbr(self):
        for rec in self:
            if rec.salary_net > 0:
                # rec.total_installment += rec.ciInstallmentAmount
                rec.simah_dbr = (rec.dbr_installment / rec.salary_net) * 100
                # print(rec.dbr_installment)
            else:
                rec.salary_net = 1

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

    def action_simah_api(self):
        self.bool_field = True
        self.message_post(body=datetime.today(), subject='The Customer was queried from SIMAH')
        BASE_URL = 'https://fuelfinance.sa/api/simah/reports/new-v2'
        # BASE_URL = 'https://simahnew.free.beeceptor.com/close'
        headers = {
            'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg3MkI3RjZCNjYyODM5NjVENDMyODYzNjk5MDA3OUQxNzlGMzBBQjUiLCJ0eXAiOiJKV1QiLCJ4NXQiOiJoeXRfYTJb09XWFVNb1kybVFCNTBYbnpDclUifQ.eyJuYmYiOjE3MDIyOTQ0NjgsImV4cCI6MTcwMjI5ODA2OCwiaXNzIjoiaHR0cHM6Ly9zcGlkcy5rc2FjYi5jb20uc2EvIiwiYXVkIjpbImh0dHBzOi8vc3BpZHMua3NhY2IuY29tLnNhL3Jlc291cmNlcyIsImJi',
            'Content-Type': 'application/json'
        }
        for rec in self:
            national_id = rec.identification_id
            first_name = rec.first_name
            family_name = rec.family_name
            dob = rec.hijri_birth_of_date
            expiry_date = rec.expiry_date
            gender = rec.gender
            city_id = 333
            data = {"national_id": int(national_id), "first_name": first_name, "family_name": family_name, "dob": dob,
                    "expiry_date": expiry_date, "city_id": city_id, "gender": gender}
            response = requests.post(BASE_URL, json=data, headers=headers, verify=False, timeout=60)
            print(response)
            # print(data)
            dic_re = response.json()
            print(dic_re)
            if response.status_code == 200:
                print("!!!!!!!!!!!!!!!!!200")
                dic_data = dic_re.get('data')
                # print("(((((((((((((((((((((((",dic_data)
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
                            enquiries_date = datetime.strptime(prevEnquirie['prevEnqDate'], '%d/%m/%Y').date()
                        for prevEnquirie in dic_data[0]['prevEnquiries']:
                            rec.score_enquiries_line.create({
                                'loan_enquiries_score': rec.id,
                                'year': enquiries_date,
                                'product_type': prevEnquirie['prevEnqProductTypeDesc']['code']
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
                        for creditInstrumentDetail in dic_data[0]['creditInstrumentDetails']:
                            rec.score_instrument_line.create({
                                'loan_instrument_score': rec.id,
                                'Product_type_categorization': creditInstrumentDetail['ciCreditor']['memberNameEN'],
                                'status': creditInstrumentDetail['ciStatus'][
                                    'creditInstrumentStatusDescAr'],
                                'credit_limits': creditInstrumentDetail['ciLimit'],
                                'installment_amounts': creditInstrumentDetail[
                                    'ciInstallmentAmount'],
                                'tenure': creditInstrumentDetail['ciTenure']
                            })
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
                        defaults_date = datetime.strptime(primarydefault['pDefDateLoaded'],
                                                          '%d/%m/%Y').date()
                        for primarydefault in dic_data[0]['primaryDefaults']:
                            rec.score_default_line.create({
                                'loan_default_score': rec.id,
                                'year': defaults_date,
                                'product_type': primarydefault['pDefProductTypeDesc']['code']
                            })
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
                                # معالجة bcCheqDateLoaded
                                raw_loaded_date = bouncedCheque.get('bcCheqDateLoaded')
                                formatted_loaded_date = None
                                if raw_loaded_date:
                                    try:
                                        formatted_loaded_date = datetime.strptime(raw_loaded_date, '%d/%m/%Y').date()
                                    except ValueError:
                                        formatted_loaded_date = None  # تجاهل التواريخ غير القابلة للتحويل

                                # معالجة bcSetteledDate
                                raw_settled_date = bouncedCheque.get('bcSetteledDate')
                                formatted_settled_date = None
                                if raw_settled_date:
                                    try:
                                        formatted_settled_date = datetime.strptime(raw_settled_date, '%d/%m/%Y').date()
                                    except ValueError:
                                        formatted_settled_date = None

                                # إنشاء السجل
                                obj = rec.simahCheques.create({
                                    'bcCheqDateLoaded': formatted_loaded_date,
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
                                    'bcSetteledDate': formatted_settled_date,
                                    'simah_cheques': rec.id
                                })
                            except Exception as e:
                                _logger.exception(f"Error while creating simahCheques record: {e}")

                    # if dic_data[0]['bouncedCheques']:
                    #     for bouncedCheque in dic_data[0]['bouncedCheques']:
                    #         try:
                    #             obj = rec.simahCheques.create({
                    #                 'bcCheqDateLoaded': bouncedCheque['bcCheqDateLoaded'],
                    #                 'productId': bouncedCheque['bcProductTypeDesc']['productId'],
                    #                 'code': bouncedCheque['bcProductTypeDesc']['code'],
                    #                 'textEn': bouncedCheque['bcProductTypeDesc']['textEn'],
                    #                 'textAr': bouncedCheque['bcProductTypeDesc']['textAr'],
                    #                 'memberCode': bouncedCheque['bcCreditor']['memberCode'],
                    #                 'memberNameEN': bouncedCheque['bcCreditor']['memberNameEN'],
                    #                 'memberNameAR': bouncedCheque['bcCreditor']['memberNameAR'],
                    #                 'bcChequeNumber': bouncedCheque['bcChequeNumber'],
                    #                 'bcBalance': bouncedCheque['bcBalance'],
                    #                 'bcOutstandingBalance': bouncedCheque['bcOutstandingBalance'],
                    #                 'defaultStatusDescEn': bouncedCheque['bcDefaultStatuses']['defaultStatusDescEn'],
                    #                 'defaultStatusDescAr': bouncedCheque['bcDefaultStatuses']['defaultStatusDescAr'],
                    #                 'defaultStatusCode': bouncedCheque['bcDefaultStatuses']['defaultStatusCode'],
                    #                 'bcSetteledDate': bouncedCheque['bcSetteledDate'],
                    #                 'simah_cheques': rec.id
                    #             })
                    #         except ValueError:
                    #             print(f"Invalid input: '{bouncedCheque}' is not a valid integer.")

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
                    if dic_data and dic_data[0].get('addresses'):
                        for address in dic_data[0]['addresses']:
                            try:
                                obj = rec.simahAddress.create({
                                    'adrsDateLoaded': address.get('adrsDateLoaded'),
                                    'adrsAddressLineFirstDescAr': address.get('adrsAddressLineFirstDescAr'),
                                    'adrsAddressLineFirstDescEn': address.get('adrsAddressLineFirstDescEn'),
                                    'adrsAddressLineSecondDescAr': address.get('adrsAddressLineSecondDescAr'),
                                    'adrsAddressLineSecondDescEn': address.get('adrsAddressLineSecondDescEn'),
                                    'adrsPOBox': address.get('adrsPOBox'),
                                    'adrsPostalCode': address.get('adrsPostalCode'),
                                    'adrsCityDescAr': address.get('adrsCityDescAr'),
                                    'adrsCityDescEn': address.get('adrsCityDescEn'),
                                    # 'addressID': address.get('adrsAddressTypes', {}).get('addressID'),
                                    # 'addressTypeCode': address.get('adrsAddressTypes', {}).get('addressTypeCode'),
                                    # 'addressNameAR': address.get('adrsAddressTypes', {}).get('addressNameAR'),
                                    # 'addressNameEN': address.get('adrsAddressTypes', {}).get('addressNameEN'),
                                    'buildingNumber': address.get('nationalAddress', {}).get('buildingNumber'),
                                    'streetAr': address.get('nationalAddress', {}).get('streetAr'),
                                    'streetEn': address.get('nationalAddress', {}).get('streetEn'),
                                    'districtAr': address.get('nationalAddress', {}).get('districtAr'),
                                    'districtEn': address.get('nationalAddress', {}).get('districtEn'),
                                    'additionalNumber': address.get('nationalAddress', {}).get('additionalNumber'),
                                    'unitNumber': address.get('nationalAddress', {}).get('unitNumber'),
                                    'simah_address': rec.id
                                })
                            except ValueError:
                                print(f"Invalid input: '{address}' is not a valid integer.")
                    else:
                        print("No addresses found or dic_data is None.")
                    # if dic_data[0]['addresses']:
                    #     for address in dic_data[0]['addresses']:
                    #         try:
                    #             obj = rec.simahAddress.create({
                    #                 'adrsDateLoaded': address['adrsDateLoaded'],
                    #                 'adrsAddressLineFirstDescAr': address['adrsAddressLineFirstDescAr'],
                    #                 'adrsAddressLineFirstDescEn': address['adrsAddressLineFirstDescEn'],
                    #                 'adrsAddressLineSecondDescAr': address['adrsAddressLineSecondDescAr'],
                    #                 'adrsAddressLineSecondDescEn': address['adrsAddressLineSecondDescEn'],
                    #                 'adrsPOBox': address['adrsPOBox'],
                    #                 'adrsPostalCode': address['adrsPostalCode'],
                    #                 'adrsCityDescAr': address['adrsCityDescAr'],
                    #                 'adrsCityDescEn': address['adrsCityDescEn'],
                    #                 'addressID': address['adrsAddressTypes']['addressID'],
                    #                 'addressTypeCode': address['adrsAddressTypes']['addressTypeCode'],
                    #                 'addressNameAR': address['adrsAddressTypes']['addressNameAR'],
                    #                 'addressNameEN': address['adrsAddressTypes']['addressNameEN'],
                    #                 'buildingNumber': address['nationalAddress']['buildingNumber'],
                    #                 'streetAr': address['nationalAddress']['streetAr'],
                    #                 'streetEn': address['nationalAddress']['streetEn'],
                    #                 'districtAr': address['nationalAddress']['districtAr'],
                    #                 'districtEn': address['nationalAddress']['districtEn'],
                    #                 'additionalNumber': address['nationalAddress']['additionalNumber'],
                    #                 'unitNumber': address['nationalAddress']['unitNumber'],
                    #                 'simah_address': rec.id
                    #             })
                    #         except ValueError:
                    #             print(f"Invalid input: '{address}' is not a valid integer.")

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

                    # rec.fuel_ava_defaults = dic_data[0]['summaryInfo']['summDefaults']
                    rec.fuel_total_liabilities = dic_data[0]['summaryInfo']['summTotalLiablilites']
                    rec.fuel_total_limits = dic_data[0]['summaryInfo']['summTotalLimits']
                    rec.fuel_total_inquiries = dic_data[0]['summaryInfo']['summPreviousEnquires']
                    rec.fuel_defaults_count = dic_data[0]['summaryInfo']['summDefaults']
                    rec.fuel_defaults_amount = dic_data[0]['summaryInfo']['summTotalDefaults']

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
                                self.fuel_evaluate_mini_range = score['minimumScore']
                                self.fuel_evaluate_max_range = score['maximumScore']
                                self.fuel_evaluate_value = score['score']
                                self.fuel_evaluate_arabic_reasons = score['reasonCodes'][0]['scoreReasonCodeDescAr']
                                self.fuel_evaluate_english_reasons = score['reasonCodes'][0]['scoreReasonCodeDescEn']
                            except ValueError:
                                print(f"Invalid input: '{score}' is not a valid integer.")
                    # disclerText
                    rec.discTextDescAr = dic_data[0].get('disclerText', {}).get('discTextDescAr',
                                                                                'Default Text in Arabic')
                    rec.discTextDescEn = dic_data[0].get('disclerText', {}).get('discTextDescEn',
                                                                                'Default Text in English')
            else:
                raise ValidationError(_('Error : "%s" ') % (dic_re.get('messages')))
        self.calculate_dbr_amount()
        # self._compute_fuel_ava_defaults()
        # self._compute_fuel_credit_instruments()
        # self._compute_last_earliest_loan()
        # self._compute_limit_avar_requested()


class SimahCity(models.Model):
    _name = 'simah.city.api'
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
    _name = 'simah.enquiries.api'
    _description = 'Simah Enquiry'

    simah = fields.Many2one('loan.order', string='Simah Date')
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
    _name = 'credit.instrument.api'
    _description = 'Credit Instrument'

    simah_simah = fields.Many2one('loan.order', string='Simah Instrument')
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
    multi_instalment_details_ids = fields.One2many('multi.instalment.details.api', 'credit_instrument_id',
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

    @api.depends('code', 'creditInstrumentStatusCode')
    def check_write_off_value(self):
        for rec in self:
            _logger.info('Checking code: %s, creditInstrumentStatusCode: %s', rec.code, rec.creditInstrumentStatusCode)
            if rec.code == 'MBL' and rec.creditInstrumentStatusCode == 'W':
                _logger.info('Condition met: Code is MBL and Status is W')
                print('code')  # This should trigger only if the condition is met
            else:
                _logger.info('Condition not met.')

    @api.depends('code', 'creditInstrumentStatusCode', 'ciInstallmentAmount', 'ciLimit',
                 'ciInstallment')
    def sum_total_installmnt(self):
        for rec in self:
            if rec.code != 'ADFL' and 'AQAR' and 'COM' and 'LND' and 'MBL' and 'NET' and 'PE' and 'RCSR' and 'SMS' and 'WAT' and 'HBIL':
                if rec.creditInstrumentStatusCode != 'C':
                    if rec.code == 'MBL' or rec.ciClosingDate != 0:
                        rec.total_installment = 0
                    # elif rec.code == 'CHC':
                    #     rec.credit_value = rec.ciLimit * 0.05
                    #     rec.total_installment = rec.credit_value
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
                elif rec.creditInstrumentStatusCode == 'S':
                    rec.total_installment = 0
                else:
                    rec.total_installment = 0
            else:
                pass


class multiInstalmentDetails(models.Model):
    _name = 'multi.instalment.details.api'
    _description = 'Multi Installment'

    startDate = fields.Char(string='Start Date')
    active = fields.Boolean(default=True)
    instalmentAmount = fields.Float(string='Instalment Amount')
    credit_instrument_id = fields.Many2one('credit.instrument.api', string='Credit Instrument')

    # @api.depends('ciAsOfDate', 'ciNextDueDate')
    # def get_format_date(self):
    #     for rec in self:
    #         ciAsOfDate = convert.Gregorian.fromdate(rec.ciAsOfDate).to_hijri().dmyformat()
    #         ciNextDueDate = convert.Gregorian.fromdate(rec.ciNextDueDate).to_hijri().dmyformat()
    #         print(ciAsOfDate, ciNextDueDate)


class MemberNarratives(models.Model):
    _name = 'simah.narrative.api'
    _description = 'Simah Narrative'

    simah_narr = fields.Many2one('loan.order', string='Simah Narrative')
    active = fields.Boolean(default=True)
    # narrativeTypes
    narrDateLoaded = fields.Char(string='Narrative Date Loaded')
    memberCode = fields.Char(string='Member Code')
    memberNameEN = fields.Char(string='Member Name EN')
    memberNameAR = fields.Char(string='Member Name AR')
    narrativeTypeDescAr = fields.Char(string='narrative Type DescAr')
    narrativeTypeDescEn = fields.Char(string='narrative Type DescEn')
    narrativeTypeCode = fields.Char(string='narrative Type Code')
    narrTextDescAr = fields.Char(string='Text DescAr')
    narrTextDescEn = fields.Char(string='Text DescEn')


class PersonalNarratives(models.Model):
    _name = 'personal.narratives.api'
    _description = 'Personal Narratives'

    simah_id = fields.Many2one('loan.order', string='Personal Narratives')
    active = fields.Boolean(default=True)
    # narrativeTypes
    narrDateLoaded = fields.Char(string='Narrative Date Loaded')
    narrativeTypeDescAr = fields.Char(string='narrative Type DescAr')
    narrativeTypeDescEn = fields.Char(string='narrative Type DescEn')
    narrativeTypeCode = fields.Char(string='narrative Type Code')
    narrTextDescAr = fields.Char(string='Text DescAr')
    narrTextDescEn = fields.Char(string='Text DescEn')


class Addresses(models.Model):
    _name = 'simah.addresses.api'
    _description = 'Simah Address'

    simah_address = fields.Many2one('loan.order', string='Simah Address')

    adrsDateLoaded = fields.Char(string='Date Loaded')
    active = fields.Boolean(default=True)
    # adrsAddressTypes
    addressID = fields.Integer(string='Address ID')
    addressTypeCode = fields.Char(string='Type Code')
    addressNameAR = fields.Char(string='NameAR')
    addressNameEN = fields.Char(string='NameEN')
    adrsAddressLineFirstDescAr = fields.Char(string='Address LineAr')
    adrsAddressLineFirstDescEn = fields.Char(string='Address LineEn')
    adrsAddressLineSecondDescAr = fields.Char(string='Address LineAr')
    adrsAddressLineSecondDescEn = fields.Char(string='Address LineEn')
    adrsPOBox = fields.Char(string='PO Box')
    adrsPostalCode = fields.Char(string='Postal Code')
    adrsCityDescAr = fields.Char(string='City Ar')
    adrsCityDescEn = fields.Char(string='City En')
    # nationalAddress
    buildingNumber = fields.Char(string='Building Number')
    streetAr = fields.Char(string='StreetAr')
    streetEn = fields.Char(string='StreetEn')
    districtAr = fields.Char(string='DistrictAr')
    districtEn = fields.Char(string='DistrictEn')
    additionalNumber = fields.Char(string='Additional Number')
    unitNumber = fields.Char(string='Unit Number')


class PrimaryDefault(models.Model):
    _name = 'simah.default.api'
    _description = 'Simah Default'

    simah_default = fields.Many2one('loan.order', string='Primary Default')
    active = fields.Boolean(default=True)

    # pDefProductTypeDesc
    productId = fields.Char('Product Id')
    code = fields.Char('Code')
    textEn = fields.Char('textEn')
    textAr = fields.Char('textAr')

    pDefAccountNo = fields.Char('pDefAccount No')

    # pDefCreditor
    memberCode = fields.Char('memberCode')
    memberNameEN = fields.Char('memberNameEN')
    memberNameAR = fields.Char('memberNameAR')

    pDefDateLoaded = fields.Char('pDef Date Loaded')
    pDefOriginalAmount = fields.Char('pDef Original Amount')
    pDefOutstandingBalance = fields.Char('pDef Outstanding Balance')

    # pDefaultStatuses
    defaultStatusDescEn = fields.Char('default Status DescEn')
    defaultStatusDescAr = fields.Char('default Status DescAr')
    defaultStatusCode = fields.Char('default Status Code')

    pDefSetteledDate = fields.Char('pDef Setteled Date')


class GuarantorDefault(models.Model):
    _name = 'guarantor.default.api'
    _description = 'Guarantor Default'

    guarantor_default = fields.Many2one('loan.order', string='Guarantor Default')
    active = fields.Boolean(default=True)

    # gDefProductTypeDesc
    productId = fields.Char('Product Id')
    code = fields.Char('Code')
    textEn = fields.Char('textEn')
    textAr = fields.Char('textAr')

    gDefAccountNo = fields.Char('gDefAccount No')

    # gDefCreditor
    memberCode = fields.Char('memberCode')
    memberNameEN = fields.Char('memberNameEN')
    memberNameAR = fields.Char('memberNameAR')

    gDefDateLoaded = fields.Char('gDef Date Loaded')
    gDefOriginalAmount = fields.Char('gDef Original Amount')
    gDefOutstandingBalance = fields.Char('gDef Outstanding Balance')

    # gDefaultStatuses
    defaultStatusDescEn = fields.Char('default Status DescEn')
    defaultStatusDescAr = fields.Char('default Status DescAr')
    defaultStatusCode = fields.Char('default Status Code')

    gDefSetteledDate = fields.Char('gDef Setteled Date')


class BouncedCheque(models.Model):
    _name = 'simah.cheques.api'
    _description = 'Simah Cheques'

    simah_cheques = fields.Many2one('loan.order', string='bounced Cheques')
    active = fields.Boolean(default=True)

    bcCheqDateLoaded = fields.Date('bcCheqDate Loaded')

    # bcProductTypeDesc
    productId = fields.Char('Product Id')
    code = fields.Char('Code')
    textEn = fields.Char('textEn')
    textAr = fields.Char('textAr')

    # bcCreditor
    memberCode = fields.Char('memberCode')
    memberNameEN = fields.Char('memberNameEN')
    memberNameAR = fields.Char('memberNameAR')

    bcChequeNumber = fields.Char('bc ChequeNumber')
    bcBalance = fields.Char('bc Balance')
    bcOutstandingBalance = fields.Char('bcOutstanding Balance')

    # bcDefaultStatuses
    defaultStatusDescEn = fields.Char('defaultStatusDescEn')
    defaultStatusDescAr = fields.Char('defaultStatusDescAr')
    defaultStatusCode = fields.Char('defaultStatusCode')

    bcSetteledDate = fields.Char('bc Setteled Date')


class SimahJudgement(models.Model):
    _name = 'simah.judgement.api'
    _description = 'Simah Judgement'

    simah_judgement = fields.Many2one('loan.order', string='bounced Judgement')
    active = fields.Boolean(default=True)

    executionDate = fields.Char('execution Date')
    resolutionNumber = fields.Char('resolution Number')
    cityNameEn = fields.Char('city NameEn')
    cityNameAr = fields.Char('city NameAr')
    courtNameEn = fields.Char('court NameEn')
    courtNameAr = fields.Char('court NameAr')
    legalCaseNumber = fields.Char('legal Case Number')
    loadedDate = fields.Char('loaded Date')
    originalClaimedAmount = fields.Char('original Claimed Amount')
    outstandingBalance = fields.Char('outstanding Balance')
    settlementDate = fields.Char('settlement Date')
    statusNameEn = fields.Char('status NameEn')
    statusNameAr = fields.Char('status NameAr')
    executionType = fields.Char('execution Type')
    statusCode = fields.Char('status Code')
    cityCode = fields.Char('city Code')


class PublicNotices(models.Model):
    _name = 'public.notices.api'
    _description = 'Public Notices'

    public_notices = fields.Many2one('loan.order', string='Public Notices')
    active = fields.Boolean(default=True)

    dataLoad = fields.Char(string='Data Load')
    noticeType = fields.Char(string='Notice Type')
    publication = fields.Char(string='Publication')
    text = fields.Char(string='Text')


class SimahContacts(models.Model):
    _name = 'simah.contact.api'
    _description = 'Simah Contact'

    simah_contact = fields.Many2one('loan.order', string='Contact')
    active = fields.Boolean(default=True)

    # conNumberTypes
    contactNumberTypeCode = fields.Char(string='Type Code')
    contactNumberTypeDescriptionAr = fields.Char(string='Phone Number Type')
    contactNumberTypeDescriptionEn = fields.Char(string='Type DescriptionEn')
    conCode = fields.Char(string='Code')
    conAreaCode = fields.Char(string='Area Code')
    conPhoneNumber = fields.Char(string='Phone Number')
    conExtension = fields.Char(string='Extension')


class SimahEmployee(models.Model):
    _name = 'simah.employee.api'
    _description = 'Simah Employee'

    simah_employee = fields.Many2one('loan.order', string='Employee')
    active = fields.Boolean(default=True)

    # employers
    empEmployerNameDescAr = fields.Char(string='Employer Name DescAr')
    empEmployerNameDescEn = fields.Char(string='Employer Name DescEn ')
    empOccupationDescAr = fields.Char(string='Occupation DescAr')
    empOccupationDescEn = fields.Char(string='Occupation DescEn')
    empDateOfEmployment = fields.Char(string='Date Of Employment')
    empDateLoaded = fields.Char(string='Date Loaded')
    empIncome = fields.Float(string='Income')
    empTotalIncome = fields.Float(string='Total Income')
    # empAddress
    adrsDateLoaded = fields.Char(string='Date Loaded')
    # adrsAddressTypes
    addressID = fields.Integer(string='Address ID')
    addressTypeCode = fields.Char(string='Address Type')
    addressNameAR = fields.Char(string='Address NameAR')
    addressNameEN = fields.Char(string='Address NameEN')
    adrsAddressLineFirstDescAr = fields.Char(string='Address Line 2 ')
    adrsAddressLineFirstDescEn = fields.Char(string='AddressLine DescEn ')
    adrsAddressLineSecondDescAr = fields.Char(string='Address LineAr')
    adrsAddressLineSecondDescEn = fields.Char(string='Address LineEn')
    adrsPOBox = fields.Integer(string='PO Box')
    adrsPostalCode = fields.Integer(string='Postal Code ')
    adrsCityDescAr = fields.Char(string='City')
    adrsCityDescEn = fields.Char(string='City DescEn')
    # nationalAddress
    buildingNumber = fields.Integer(string='Building Number')
    streetAr = fields.Char(string='StreetAr')
    streetEn = fields.Char(string='StreetEn')
    districtAr = fields.Char(string='Address Line 1')
    districtEn = fields.Char(string='DistrictEn')
    additionalNumber = fields.Integer(string='Additional Number')
    unitNumber = fields.Integer(string='Unit Number')
    # empStatusType
    employerStatusTypeCode = fields.Char(string='Type')
    employerStatusTypeDescAr = fields.Char(string='Status Type DescAr')
    employerStatusTypeDescEn = fields.Char(string='Status Type DescEn')


class SimahScore(models.Model):
    _name = 'simah.score.api'
    _description = 'Simah Score'

    simah_score = fields.Many2one('loan.order', string='Score')
    active = fields.Boolean(default=True)
    score = fields.Float()
    minimumScore = fields.Float('Minimum Score')
    maximumScore = fields.Float('Maximum Score')
    scoreIndex = fields.Float('Score Index')
    error = fields.Char('Error')

    # ScoreCard
    scoreCardCode = fields.Char('Score Card Code')
    scoreCardDescAr = fields.Char('Score Card DescAr')
    scoreCardDescEn = fields.Char('Score Card DescEn')

    # ScoreReason
    scoreReasonCodeName = fields.Char('Score Reason Code Name')
    scoreReasonCodeDescAr = fields.Char('Score Reason Code DescAr')
    scoreReasonCodeDescEn = fields.Char('Score Reason Code DescEn')
    simahScoreCodes = fields.One2many('simah.reason.code.api', 'simah_score_id', string="Simah Score Codes")


class SimahReasonCodes(models.Model):
    _name = 'simah.reason.code.api'
    _description = 'Simah Reason Code'

    scoreReasonCodeName = fields.Char('Score Reason Code Name')
    scoreReasonCodeDescAr = fields.Char('Score Reason Code DescAr')
    scoreReasonCodeDescEn = fields.Char('Score Reason Code DescEn')
    simah_score_id = fields.Many2one('simah.score')
    active = fields.Boolean(default=True)


class SimahExpense(models.Model):
    _name = 'simah.expense.api'
    _description = 'Simah Expenses'

    simah_expense = fields.Many2one('loan.order', string='Expense')

    # expenseResponseModel
    nameEn = fields.Char(string='NameEn')
    nameAr = fields.Char(string='NameAr')
    valueUsedIncaluculation = fields.Float(string='value calculation')
    valueDeclaredByCustomer = fields.Float(string='value By Customer')
    outputValue = fields.Float(string='output Value')
    isVerified = fields.Boolean(string='isVerified')


######################################################### * Loan Installment * ########################################


class loan_installment_line(models.Model):
    _name = "loan.installment"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Loan Installment'

    name = fields.Many2one("res.partner", string="Customer")
    seq_name = fields.Char('Sequence Name')
    i_num = fields.Integer('Installment Number')
    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', string='Company')
    total_amount = fields.Monetary('EMI', compute='get_total_amount', store=True)
    principal_amount = fields.Monetary('Principal Amount')
    interest_amount = fields.Monetary('Interest Amount', store=True)
    descending_installment = fields.Monetary('Desc Installments X', store=True)
    descending_installment_y = fields.Monetary('Desc Installments y', store=True)
    ascending_installment = fields.Monetary('Asce Installments', store=True)
    total_ascending_installment = fields.Monetary('Total Asce Installments', store=True)
    installment_amount = fields.Monetary('Installments', compute='get_installment_amount', store=True, readonly=0)
    installment_amount_early = fields.Monetary('Installment')
    state = fields.Selection([('unpaid', 'Unpaid'), ('paid', 'Paid'), ('partial', 'partial')], string='State',
                             default='unpaid', compute="_compute_amount_paid", store=True)
    installment_account = fields.Many2one("account.account", string="Installment Account")
    interest_account = fields.Many2one("account.account", string="Interest Account")
    disburse_account = fields.Many2one("account.account", string="Disburse Account")
    payment_journal = fields.Many2one("account.journal", string="Payment Journal")
    journal_entry_id = fields.Many2one('account.move', string='Journal Entry', copy=False)
    payment_id = fields.Many2one('account.payment', string='Payment', copy=False)
    # chatter_sms = fields.One2many(related='payment_id.body', string='SMS')
    amount_paid = fields.Monetary(string="Paid Amount", compute="_compute_amount_paid", store=True)
    remaining_amount = fields.Float(string="Remaining Amount", compute="_compute_remaining_amount")
    payment_date = fields.Date('Payment Date')
    currency_id = fields.Many2one('res.currency', string='Currency')
    loan_state = fields.Selection(related='loan_id.state', string='Loan State')
    reschedule_loan_state = fields.Selection(related='reschedule_loan_id.state', string='Loan State')
    loan_record = fields.Integer(related='loan_id.loan_record', string='Loan Record')
    loan_id = fields.Many2one('loan.order', string='Loan', ondelete='cascade')
    reschedule_loan_id = fields.Many2one('loan.order', string='Reschedule Loan', ondelete='cascade')
    installment_type_id = fields.Many2one('loan.order', string='Loan installment type')
    interest_q = fields.Monetary(string='interest quarter')
    identification = fields.Char(related='name.identification_no', string="Identification ID")
    is_late = fields.Boolean(compute='_compute_is_late')
    flag_monthly_move = fields.Boolean()
    installment_due = fields.Monetary(string='Due', compute='get_installment_amount', store=True)
    monthly_move_id = fields.Many2one('account.move', copy=False)
    partial_payment_status = fields.Boolean(
        string="Partial Payment Status",
        compute="_compute_partial_payment_status",
        store=True
    )
    next_installment_id = fields.Many2one(
        'loan.installment',
        string="Next Installment",
        compute="_compute_next_installment_id",
        store=True,
        help="References the next installment in the sequence."
    )

    next_reschedule_installment_id = fields.Many2one(
        'loan.installment',
        string="Next reschedule Installment",
        compute="_compute_next_reschedule_installment_id",
        store=True,
        help="References the next reschedule installment in the sequence."
    )
    sms_sent = fields.Boolean(default=False, string="SMS Sent",
                              help="Indicates if the SMS has been sent for this installment.")

    payment_messages = fields.Text(
        string="Payment Messages",
        compute='_compute_payment_messages',
        store=False  # Set to True if you want to store the value in the database
    )
    is_reschedule = fields.Boolean(string='Is Reschedule', related='loan_id.is_reschedule', required=False,
                                   store=True)
    budget_id = fields.Many2one('crossovered.budget')
    state_arabic = fields.Char(string='Arabic Status', compute='_compute_state_arabic')

    def action_update_state(self):
        for rec in self:
            if rec.amount_paid == 0:
                rec.state = 'unpaid'
            elif rec.amount_paid >= rec.installment_amount:
                rec.state = 'paid'
            else:
                rec.state = 'partial'

    def unpaid_installment(self):
        unpaid_recs = self.filtered(lambda r: r.state != 'unpaid')
        if unpaid_recs:
            for rec in unpaid_recs:
                old_state = rec.state  # Store old state for logging
                old_amount_paid = rec.amount_paid  # Store old amount paid
                old_remaining_amount = rec.remaining_amount  # Store old remaining amount

                rec.write({
                    'state': 'unpaid',
                    'amount_paid': 0,
                    'remaining_amount': rec.installment_amount
                })

                # Log the change in the chatter
                rec.message_post(
                    body=f"Installment state changed from <b>{old_state}</b> to <b>Unpaid</b>.</br>"
                         f"Amount Paid reset from <b>{old_amount_paid}</b> to <b>0</b>.</br>"
                         f"Remaining Amount set to <b>{rec.remaining_amount}</b>.",
                    subtype_xmlid="mail.mt_comment"
                )

        self.loan_id.get_total_interest()


    @api.depends('state')
    def _compute_state_arabic(self):
        for rec in self:
            mapping = {
                'paid': 'مدفوع',
                'partial': 'مدفوع جزى',
                'unpaid': 'غير مدفوع',
            }
            rec.state_arabic = mapping.get(rec.state, '')

    @api.depends('payment_id')  # Ensure 'payment_id' exists and links to account.payment
    def _compute_payment_messages(self):
        for installment in self:
            if installment.payment_id:
                # Retrieve messages from the related account.payment record
                messages = self.env['mail.message'].search([
                    ('res_id', '=', installment.payment_id.id),
                    ('model', '=', 'account.payment')
                ])
                # Combine all message bodies into a single string, cleaned of HTML
                message_bodies = []
                for message in messages:
                    # Clean HTML tags from the message body
                    soup = BeautifulSoup(message.body, 'html.parser')
                    message_bodies.append(soup.get_text(strip=True))
                installment.payment_messages = "\n\n".join(message_bodies)
            else:
                installment.payment_messages = "No related payment messages."

    @api.depends('installment_amount')
    def _compute_partial_payment_status(self):
        for record in self:
            # Set partial_payment_status to True if paid_amount is less than installment
            record.partial_payment_status = 0 < record.installment_amount

    @api.depends('date')
    def _compute_is_late(self):
        for r in self:
            r.is_late = r.date < date.today() and r.state != 'paid'

    @api.depends('principal_amount', 'interest_q')
    def get_total_amount(self):
        for line in self:
            line.total_amount = line.principal_amount + line.interest_q

    def get_account_move_vals(self):
        vals = {
            'date': date.today(),
            'partner_name': self.name.id,
            'identification_id': self.identification,
            'ref': self.seq_name or 'Loan Installment',
            'journal_id': self.payment_journal and self.payment_journal.id or False,
            'company_id': self.company_id and self.company_id.id or False,
        }
        return vals

    def get_partner_lines(self):
        vals = {
            'partner_id': self.name and self.name.id or False,
            'account_id': self.name.property_account_receivable_id and self.name.property_account_receivable_id.id or False,
            'credit': self.installment_amount,
            'name': self.seq_name or '/',
            'date_maturity': date.today(),
        }
        return vals

    @api.depends('loan_id.loan_amount', 'loan_id.interest_amount', 'loan_id.loan_term')
    def get_installment_amount(self):
        for line in self:
            line.installment_amount = line.principal_amount + line.interest_amount
            line.installment_due = line.installment_amount

    def get_interest_lines(self):
        vals = {
            'partner_id': self.name and self.name.id or False,
            'account_id': self.interest_account and self.interest_account.id or False,
            'debit': self.interest_amount,
            'name': self.seq_name or '/',
            'date_maturity': date.today(),

        }
        return vals

    def get_partner_lines_early(self):
        vals = {
            'partner_id': self.name and self.name.id or False,
            'account_id': self.name.property_account_receivable_id and self.name.property_account_receivable_id.id or False,
            'credit': self.installment_amount_early,
            'name': self.seq_name or '/',
            'date_maturity': date.today(),
        }
        return vals

    def get_interest_lines_early(self):
        vals = {
            'partner_id': self.name and self.name.id or False,
            'account_id': self.interest_account and self.interest_account.id or False,
            'debit': 0,
            'name': self.seq_name or '/',
            'date_maturity': date.today(),

        }
        return vals

    def get_installment_lines(self):
        vals = {
            'partner_id': self.name and self.name.id or False,
            'account_id': self.disburse_account and self.disburse_account.id or False,
            'debit': self.principal_amount,
            'name': self.seq_name or '/',
            # 'datepayment_date_maturity': date.today(),
        }
        return vals

    # def set_loan_close(self):
    #     """Check if this is the last unpaid installment and create activities."""
    #     # Fetch all unpaid installments for this loan
    #     unpaid_installments = self.search([
    #         ('loan_id', '=', self.loan_id.id),
    #         ('state', '=', 'unpaid')
    #     ], order='date desc')  # Order by due date to identify the last record
    #
    #     # Log unpaid installments for debugging
    #     _logger.info(f"Unpaid Installments for Loan {self.loan_id.id}: {unpaid_installments}")
    #
    #     # Handle cases where there are no unpaid installments
    #     if not unpaid_installments:
    #         _logger.warning(f"No unpaid installments found for Loan ID {self.loan_id.id}.")
    #         return
    #
    #     # Ensure this record is the last unpaid installment
    #     if self.id != unpaid_installments[0].id:
    #         _logger.info(f"Installment ID {self.id} is not the last unpaid installment.")
    #         return  # Do nothing if it's not the last unpaid installment
    #
    #     # Update loan state and proceed with activity creation
    #     _logger.info(f"Marking Loan {self.loan_id.id} as active and creating activities.")
    #     self.loan_id.state = 'active'
    #     self.installment_type_id.update_loan_status()
    #
    #     # Get user groups for activity assignment
    #     try:
    #         operation_users = self.env.ref('loan.group_customer_operation').users.ids
    #         collection_users = self.env.ref('loan.group_collection').users.ids
    #     except Exception as e:
    #         _logger.error(f"Error fetching user groups: {e}")
    #         return
    #
    #     # Ensure user IDs are selected randomly
    #     activity_object = self.env['mail.activity']
    #     finance_user_id = self.env.user.id
    #
    #     # Create activity for operations group
    #     random_id = finance_user_id
    #     while random_id == finance_user_id:
    #         random_id = random.choice(operation_users)
    #     activity_values = self.activity_request_close(
    #         user_id=random_id,
    #         record_id=self.loan_id.id,
    #         model_name='loan.order',
    #         model_id='loan.model_loan_order'
    #     )
    #     try:
    #         activity_object.create(activity_values)
    #         _logger.info(f"Activity created for Operations Group: {activity_values}")
    #     except Exception as e:
    #         _logger.error(f"Failed to create activity for Operations Group: {e}")
    #
    #     # Create activity for collections group
    #     random_id = finance_user_id
    #     while random_id == finance_user_id:
    #         random_id = random.choice(collection_users)
    #     activity_values = self.activity_request_close(
    #         user_id=random_id,
    #         record_id=self.loan_id.id,
    #         model_name='loan.order',
    #         model_id='loan.model_loan_order'
    #     )
    #     try:
    #         activity_object.create(activity_values)
    #         _logger.info(f"Activity created for Collections Group: {activity_values}")
    #     except Exception as e:
    #         _logger.error(f"Failed to create activity for Collections Group: {e}")
    #
    # def activity_request_close(self, user_id, record_id, model_name, model_id):
    #     """Return a dictionary to create the activity."""
    #     try:
    #         return {
    #             'res_model': model_name,
    #             'res_model_id': self.env.ref(model_id).id,
    #             'res_id': record_id,
    #             'summary': "Close",
    #             'note': "The Request Closed",
    #             'date_deadline': date.today(),
    #             'user_id': user_id,
    #             'activity_type_id': self.env.ref('loan.mail_activity_close').id,
    #         }
    #     except Exception as e:
    #         _logger.error(f"Error creating activity request: {e}")
    #         return {}

    # def unlink(self):
    #     for installment in self:
    #         if installment.loan_id.state not in ['cancel', 'reject'] and not installment._context.get('force_delete'):
    #             installment.loan_id.state == 'draft'
    #             installment.loan_id.installment_ids = [(5, 0, 0)]
    # installment.with_context(force_delete=True).unlink()
    #         raise ValidationError(_('You can not delete Loan Installment.'))
    # return super(loan_installment_line, self).unlink()

    def send_messeage(self, phone, message):
        values = '''{
                                                            "userName": "Fuelfinancesa",
                                                              "numbers": "''' + phone + '''",
                                                              "userSender": "fuelfinance",
                                                              "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                                              "msg": "''' + message + '''"
                                                            }'''

        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        values = values.encode()
        requests.post('https://www.msegat.com/gw/sendsms.php',
                      data=values,
                      headers=headers)
        # requests.post('https://private-anon-6ac4ab1f43-msegat.apiary-proxy.com/gw/sendsms.php',
        #               data=values,
        #               headers=headers)

    def action_paid_reschedule_installment(self, payment_id=None):
        if self.reschedule_loan_id.early_amount > 0 and self.reschedule_loan_id.state == 'active':
            # Validate loan state and required fields
            if self.reschedule_loan_id and self.reschedule_loan_id.state not in ('active', 'early'):
                raise ValidationError(_("Installment pay after loan active !!!"))
            if not self.payment_journal:
                raise ValidationError(_("Please Select Payment Journal !!!"))
            if self.name and not self.name.property_account_receivable_id:
                raise ValidationError(_("Select Customer Receivable Account !!!"))
            # self.state = 'paid'
            self.payment_date = date.today()

            # Check if payment ID is provided
            if payment_id:
                self.payment_id = payment_id
            else:
                # Generate payment if not provided
                self._reschedule_generate_payment()
                self._compute_next_reschedule_installment_id()
                self._compute_amount_paid()
                self._compute_remaining_amount()

            # Update loan status and related fields
            # self.reschedule_loan_id.get_installment()
            self.reschedule_loan_id.get_reschedule_amounts()
            self.reschedule_loan_id.get_first_unpaid_installment_date()
            # Return payment view
            return {
                'name': _('Payment'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': self.payment_id.id,
                'view_mode': 'form',
                'target': 'new',
            }

        # if self.reschedule_loan_id.early_amount > 0 and self.reschedule_loan_id.state == 'active':
        #     if self.reschedule_loan_id and self.reschedule_loan_id.state != 'active' and self.reschedule_loan_id.state != 'early':
        #         raise ValidationError(_("Installment pay after loan active !!!"))
        #
        #     if not self.payment_journal:
        #         raise ValidationError(_("Please Select Payment Journal !!!"))
        #     if self.name and not self.name.property_account_receivable_id:
        #         raise ValidationError(_("Select Customer Receivable Account !!!"))
        #     self.state = 'paid'
        #     self.payment_date = date.today()
        #     if payment_id:
        #         self.payment_id = payment_id
        #     else:
        #         self._generate_reschedule_payment()
        #     # self.set_loan_close()
        #     self.reschedule_loan_id.get_installment()
        #     self.reschedule_loan_id.get_first_unpaid_installment_date()
        #     self.reschedule_loan_id.get_remaining_amount()
        #     # Send Message To Tell Customer To Tell Him The Installment Paid
        #     paid_message = f"""
        #                                 مرحباً,  ({self.name.name})
        #                                   شكراً..لقد تم استلام الدفعة الشهرية بأجمالي مبلغ {self.installment_amount} ريال سعودي
        #                                 ولمزيد من الاستفسارات نسعد بخدمتك علي الرقم الموحد 8001184000
        #                                 خلال اوقات العمل الرسمية من الاحد الي الخميس
        #                                 من الساعة 9 صباحاً الي 5 مساء
        #                                 نشكرك علي اختيارك فيول للتمويل
        #                                 """
        #     if self.name.phone:
        #         self.send_messeage(self.name.phone, paid_message)
        #         self.reschedule_loan_id.message_post(body=paid_message)
        #     return {
        #         'name': _('Payment'),
        #         'type': 'ir.actions.act_window',
        #         'res_model': 'account.payment',
        #         'res_id': self.payment_id.id,
        #         'view_mode': 'form',
        #         'target': 'new',
        #     }

    def action_paid_installment(self, payment_id=None):
        if self.loan_id.early_amount > 0 and self.loan_id.state == 'active':
            # Validate loan state and required fields
            if self.loan_id and self.loan_id.state not in ('active', 'early'):
                raise ValidationError(_("Installment pay after loan active !!!"))
            if not self.payment_journal:
                raise ValidationError(_("Please Select Payment Journal !!!"))
            if self.name and not self.name.property_account_receivable_id:
                raise ValidationError(_("Select Customer Receivable Account !!!"))
            # self.state = 'paid'
            self.payment_date = date.today()

            # Check if payment ID is provided
            if payment_id:
                self.payment_id = payment_id
            else:
                # Generate payment if not provided
                self._generate_payment()
                self._compute_next_installment_id()
                self._compute_amount_paid()
                self._compute_remaining_amount()

            # Update loan status and related fields
            self.loan_id.get_total_interest()
            self.loan_id.get_installment()
            self.loan_id.get_remaining_amount()
            self.loan_id.get_first_unpaid_installment_date()
            # Return payment view
            return {
                'name': _('Payment'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': self.payment_id.id,
                'view_mode': 'form',
                'target': 'new',
            }

    def send_paid_sms(self):
        for record in self:
            if record.name.phone:
                _logger.info(f"Sending SMS for installment {self.id} to {self.name.phone}.")
                paid_message = f"""
                    مرحباً,  ({self.name.name})
                    شكراً..لقد تم استلام الدفعة الشهرية بأجمالي مبلغ {self.amount_paid} ريال سعودي
                    ولمزيد من الاستفسارات نسعد بخدمتك علي الرقم الموحد 8001184000
                    خلال اوقات العمل الرسمية من الاحد الي الخميس
                    من الساعة 9 صباحاً الي 5 مساء
                    نشكرك علي اختيارك فيول للتمويل
                """
                self.send_messeage(self.name.phone, paid_message)
                record.loan_id.message_post(body=paid_message)

    def write(self, vals):
        result = super(loan_installment_line, self).write(vals)
        for record in self:
            old_state = record.state
            new_state = vals.get('state', old_state)

            if old_state != new_state:
                paid_message = ""  # Initialize the variable to avoid errors

                if new_state == 'paid':
                    paid_message = f"""
                        مرحباً,  ({record.name.name})
                        شكراً..لقد تم استلام الدفعة الشهرية بأجمالي مبلغ {record.amount_paid} ريال سعودي
                        ولمزيد من الاستفسارات نسعد بخدمتك علي الرقم الموحد 8001184000
                        خلال اوقات العمل الرسمية من الاحد الي الخميس
                        من الساعة 9 صباحاً الي 5 مساء
                        نشكرك علي اختيارك فيول للتمويل
                    """
                elif new_state == 'partial':
                    paid_message = f"""
                        مرحباً,  ({record.name.name})
                        شكراً..لقد تم استلام الدفعة الشهرية بأجمالي مبلغ {record.amount_paid} ريال سعودي
                        ولمزيد من الاستفسارات نسعد بخدمتك علي الرقم الموحد 8001184000
                        خلال اوقات العمل الرسمية من الاحد الي الخميس
                        من الساعة 9 صباحاً الي 5 مساء
                        نشكرك علي اختيارك فيول للتمويل
                    """
                else:
                    paid_message = f"Installment '{record.name}' is unpaid."

                # Ensure the message is posted only if it has content
                if paid_message:
                    record.message_post(body=paid_message)

        return result

    @api.model
    def update_installment_states(self):
        # Fetch records where the state is 'unpaid' and amount_paid > 0
        installments = self.search([('state', '=', 'unpaid'), ('amount_paid', '>', 0)])
        for installment in installments:
            if installment.amount_paid == installment.installment_amount:
                installment.state = 'paid'
            elif installment.amount_paid < installment.installment_amount:
                installment.state = 'partial'

    def action_early_installment(self):
        interest = self.interest_amount
        principal = self.principal_amount
        installment = self.installment_amount
        installment = installment - interest
        print(installment)
        print(principal)
        account_move_val = self.get_account_move_vals()
        account_move_id = self.env['account.move'].create(account_move_val)
        vals = []
        if account_move_id:
            val = self.get_partner_lines_early()
            vals.append((0, 0, val))
            val = self.get_installment_lines()
            vals.append((0, 0, val))
            val = self.get_interest_lines_early()
            vals.append((0, 0, val))
            account_move_id.line_ids = vals
            self.journal_entry_id = account_move_id and account_move_id.id or False
            self.state = 'paid'
            self.payment_date = date.today()
            # self.set_loan_close()
            self.loan_id.get_first_unpaid_installment_date()
            self.loan_id.get_remaining_amount()
            print(vals)

    @api.depends('payment_id.state', 'payment_id.amount')
    def _compute_state(self):
        for record in self:
            if record.payment_id and record.payment_id.state == 'posted':
                if record.payment_id.amount == record.installment_amount:
                    record.state = 'paid'
                elif 0 < record.payment_id.amount < record.installment_amount:
                    record.state = 'partial'
                else:
                    record.state = 'unpaid'
            else:
                record.state = 'unpaid'

    def _generate_payment(self):
        for r in self:
            # Check if a payment record exists, otherwise initialize one
            payment_name = r.seq_name or f'Loan Installment {r.id}'
            amount_to_pay = r.remaining_amount if r.state == 'partial' else r.installment_amount

            # if is_api_payment:
            #     journal_id = 15
            # else:
            #     journal_id = r.loan_id.loan_type.payment_journal.id

            values = {
                "partner_type": "customer",
                "payment_type": "inbound",
                "partner_id": r.name.id,
                "amount": amount_to_pay,  # Set default to full installment amount
                "date": fields.Date.context_today(self),
                "ref": payment_name,
                "journal_id": r.loan_id.loan_type.payment_journal.id,
            }
            payment_id = self.env['account.payment'].create(values)
            r.payment_id = payment_id

    @api.depends('loan_id.installment_ids')
    def _compute_next_installment_id(self):
        for installment in self:
            installments = installment.loan_id.installment_ids.sorted('date')  # 'date'
            installments_list = list(installments)
            if installment in installments_list:
                index = installments_list.index(installment)
                if index + 1 < len(installments_list):
                    installment.next_installment_id = installments_list[index + 1]
                else:
                    installment.next_installment_id = False
            else:
                installment.next_installment_id = False

    def _reschedule_generate_payment(self):
        for r in self:
            # Check if a payment record exists, otherwise initialize one
            payment_name = r.seq_name or f'Loan Installment {r.id}'
            amount_to_pay = r.remaining_amount if r.state == 'partial' else r.installment_amount
            values = {
                "partner_type": "customer",
                "payment_type": "inbound",
                "partner_id": r.name.id,
                "amount": amount_to_pay,  # Set default to full installment amount
                "date": fields.Date.context_today(self),
                "ref": payment_name,
                "journal_id": r.reschedule_loan_id.loan_type.payment_journal.id,
            }
            payment_id = self.env['account.payment'].create(values)
            r.payment_id = payment_id

    @api.depends('reschedule_loan_id.reschedule_installment_ids')
    def _compute_next_reschedule_installment_id(self):
        for installment in self:
            installments = installment.reschedule_loan_id.reschedule_installment_ids.sorted('date')  # 'date'
            installments_list = list(installments)
            if installment in installments_list:
                index = installments_list.index(installment)
                if index + 1 < len(installments_list):
                    installment.next_reschedule_installment_id = installments_list[index + 1]
                else:
                    installment.next_reschedule_installment_id = False
            else:
                installment.next_reschedule_installment_id = False

    @api.depends('payment_id.amount', 'payment_id.state')
    def _compute_amount_paid(self):
        for record in self:
            remaining_amount = sum(
                payment.amount for payment in record.payment_id
                if payment.state == 'posted' and payment.amount > 0
            )
            current_record = record
            while current_record and remaining_amount > 0:
                due_amount = current_record.installment_amount - current_record.amount_paid
                if remaining_amount >= due_amount:
                    current_record.amount_paid = current_record.installment_amount
                    current_record.state = 'paid'
                    remaining_amount -= due_amount
                else:
                    current_record.amount_paid += remaining_amount
                    current_record.state = 'partial'
                    remaining_amount = 0
                if not record.is_reschedule:
                    current_record = current_record.next_installment_id if remaining_amount > 0 else None
                else:
                    current_record = current_record.next_reschedule_installment_id if remaining_amount > 0 else None
            if remaining_amount > 0:
                next_installment = record.next_installment_id if record.next_installment_id else None
                while next_installment and remaining_amount > 0:
                    next_installment.amount_paid += remaining_amount
                    if next_installment.amount_paid >= next_installment.installment_amount:
                        next_installment.state = 'paid'
                    else:
                        next_installment.state = 'partial'
                    remaining_amount = 0
                    next_installment = next_installment.next_installment_id

    def _compute_remaining_amount(self):
        for record in self:
            # Calculate remaining amount
            record.remaining_amount = record.installment_amount - record.amount_paid
            # Ensure remaining_amount is never negative
            record.remaining_amount = max(record.remaining_amount, 0)

    def _generate_reschedule_payment(self):
        for r in self:
            payment_name = r.seq_name or f'Loan Installment {r.id}'
            values = {
                "partner_type": "customer",
                "payment_type": "inbound",
                "partner_id": r.name.id,
                "amount": r.installment_amount,
                "date": fields.Date.context_today(self),
                "ref": payment_name,
                "journal_id": r.reschedule_loan_id.loan_type.payment_journal.id,
            }
            self.payment_id = self.env['account.payment'].create(values)

    def _generate_monthly_move(self):
        for r in self:
            loan = r.loan_id
            loan_type = loan.loan_type if loan else False

            if not loan or not loan_type:
                print(f'Skipped Record: {r.name} → Loan ID or Loan Type is missing')
                continue

            if r.flag_monthly_move:
                print(f'Skipped Record: {r.name} → Already processed (flag_monthly_move=True)')
                continue

            if loan.state != 'active':
                print(f'Skipped Record: {r.name} → Loan not active (Current State: {loan.state})')
                continue

            # ✅ Determine which interest amount to use
            if loan.is_reschedule:
                amount = sum(loan.reschedule_installment_ids.filtered(
                    lambda i: i.date and i.date.month == r.date.month and i.date.year == r.date.year
                ).mapped('interest_amount'))
                # OR: amount = loan.reschedule_interest_amount if that field is reliable
            else:
                amount = r.interest_amount

            unearned_account = loan_type.unearned_interest_account
            interest_account = loan_type.interest_account

            if not unearned_account:
                print(
                    f'Skipped Record: {r.name} → Missing unearned interest account for loan type "{loan_type.name or "Unknown"}"')
                continue
            if not interest_account:
                print(
                    f'Skipped Record: {r.name} → Missing interest account for loan type "{loan_type.name or "Unknown"}"')
                continue

            # ✅ Create the journal entry
            r.flag_monthly_move = True
            move_values = {
                'date': date.today(),
                'partner_name': r.name.id,
                'identification_id': r.identification,
                'ref': r.seq_name or 'Loan Installment',
                'journal_id': loan_type.payment_journal.id,
                'company_id': r.company_id.id,
            }

            line_name = r.seq_name or '/'

            debit_line = {
                'partner_id': r.name.id,
                'account_id': unearned_account.id,
                'debit': amount,
                'name': line_name,
            }
            credit_line = {
                'partner_id': r.name.id,
                'account_id': interest_account.id,
                'credit': amount,
                'name': line_name,
            }

            move_values['line_ids'] = [
                (0, 0, debit_line),
                (0, 0, credit_line),
            ]

            r.monthly_move_id = self.env['account.move'].create(move_values)
            r.monthly_move_id.action_post()

    def generate_monthly_move(self):
        for r in self:
            # Skip if already processed or loan is not active
            if r.flag_monthly_move or r.loan_id.state != 'active':
                continue

            loan = r.loan_id
            loan_type = loan.loan_type

            # Ensure r.date is valid
            if not r.date:
                raise UserError(f"Installment '{r.name}' has no date set.")

            # ✅ Get the correct interest amount based on reschedule status
            if loan.is_reschedule:
                amount = sum(
                    loan.reschedule_installment_ids.filtered(
                        lambda i: i.date and i.date.month == r.date.month and i.date.year == r.date.year
                    ).mapped('interest_amount')
                )
            else:
                amount = r.interest_amount

            # ✅ Validate accounts
            unearned_account = loan_type.unearned_interest_account
            interest_account = loan_type.interest_account

            if not unearned_account:
                raise UserError(
                    f'Please configure unearned interest account for loan type "{loan_type.name}"'
                )
            if not interest_account:
                raise UserError(
                    f'Please configure interest account for loan type "{loan_type.name}"'
                )

            # ✅ Create the journal entry
            r.flag_monthly_move = True
            move_values = {
                'date': date.today(),
                'partner_name': r.name.id,
                'identification_id': r.identification,
                'ref': r.seq_name or 'Loan Installment',
                'journal_id': loan_type.payment_journal.id,
                'company_id': r.company_id.id,
            }

            line_name = r.seq_name or '/'

            move_values['line_ids'] = [
                (0, 0, {
                    'partner_id': r.name.id,
                    'account_id': unearned_account.id,
                    'debit': amount,
                    'name': line_name,
                }),
                (0, 0, {
                    'partner_id': r.name.id,
                    'account_id': interest_account.id,
                    'credit': amount,
                    'name': line_name,
                }),
            ]

            r.monthly_move_id = self.env['account.move'].create(move_values)
            r.monthly_move_id.action_post()

    @api.model
    def auto_action_monthly_move(self):
        print(' ================> | Server Action Monthly Move Running .......')
        specific_date = fields.Date.from_string('2025-05-27')

        # ---- PROCESSING STAGE ----
        domain = [
            ('date', '=', specific_date),
            ('flag_monthly_move', '=', False),
            ('monthly_move_id', '=', False)
        ]
        records_to_process = self.search(domain)

        skipped_records = self.search([('date', '=', specific_date)])
        excluded_records = skipped_records - records_to_process

        print(f'Total Installments on {specific_date}: {len(skipped_records)}')
        print(f'Records being processed: {len(records_to_process)}')

        for rec in excluded_records:
            print(
                f'Skipped Record: {rec.name}, flag_monthly_move: {rec.flag_monthly_move}, monthly_move_id: {rec.monthly_move_id}')

        if records_to_process:
            print(f'Found {len(records_to_process)} records with date {specific_date}. Processing...')
            try:
                records_to_process._generate_monthly_move()
                print('Monthly move creation completed successfully.')
            except Exception as e:
                print(f'Error during monthly move creation: {e}')
        else:
            print('No records found with date 05/27/2025. Skipping.')

    # ------------------------- | Server Action| -----------------------

    def _cron_monthly_move(self):
        print(' ================> | Cron Monthly Move Running .......')
        fields.Date.today()
        today = fields.Date.from_string(fields.Date.context_today(self))
        if today.day != 27:
            return
        domain = [('date', '=', today), ('flag_monthly_move', '=', False), ('monthly_move_id', '=', False)]
        self.search(domain)._generate_monthly_move()

    # ------------------------- | Send Message [Messgatiy]| -----------------------
    def send_messeage(self, phone, message):
        values = '''{
                                                            "userName": "Fuelfinancesa",
                                                              "numbers": "''' + phone + '''",
                                                              "userSender": "fuelfinance",
                                                              "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                                              "msg": "''' + message + '''"
                                                            }'''

        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        values = values.encode()
        requests.post('https://www.msegat.com/gw/sendsms.php',
                      data=values,
                      headers=headers)


class LoanCalculate(models.Model):
    _name = 'loan.calculate'
    _description = 'Loan Calculate'

    name = fields.Float(string="Loan amount")
    term_year = fields.Integer(string="Loan term in years")
    term_month = fields.Integer(string="Loan term in months")
    liability = fields.Integer(string="Liability")
    interest = fields.Float(string="Interest rate per year")
    principal = fields.Float(string="Total principal paid", compute="_calculate_principal", store=True)
    total_interest = fields.Float(string="Total interest paid", compute="_calculate_interest", store=True)
    monthly_payments = fields.Float(string="Monthly payments", default='1', compute='_calculate_monthly', store=True)

    @api.onchange('term_year')
    def _calculate_year(self):
        for rec in self:
            rec.term_month = rec.term_year * 12

    @api.depends('name', 'term_month')
    def _calculate_principal(self):
        for rec in self:
            if rec.term_month > 1:
                rec.principal = rec.name / rec.term_month

    @api.depends('name')
    def _calculate_interest(self):
        for rec in self:
            rec.total_interest = (rec.name * 0.02)

    @api.depends('total_interest', 'principal')
    def _calculate_monthly(self):
        for rec in self:
            if rec.term_month > 1:
                rec.monthly_payments = rec.principal + rec.total_interest


class HelpdeskCustomer(models.Model):
    _inherit = 'helpdesk.team'
    _description = 'Inherit Helpdesk Team'

    ticket_id = fields.Many2one("loan.order", required=True, string='Ticket')
    message = fields.Text(string="Your file is stored in the directory C:/", readonly=True, store=True)


class LoanTransaction(models.Model):
    _inherit = 'account.move'
    _description = 'Edit Account Move'

    isdown_payment = fields.Boolean('IsDownpayment')
    transaction_channel = fields.Selection([('manual', 'S-SADAD'), ('online', 'V-Virtual Iban')],
                                           string='Transaction Channel', required=False)
    transaction_type = fields.Selection([('confirm', 'Confirmed'), ('cancel', 'Cancelled'), ('revert', 'reverted')],
                                        string='Transaction Status', required=False)
    identification_id = fields.Char(related='partner_name.identification_no', string="Identification ID", store=True)
    partner_name = fields.Many2one("res.partner", store=True, string="Customer")
    transaction_installment = fields.Many2one("loan.installment", store=True, string="Installment Transaction")
    transaction_state = fields.Selection(related='transaction_installment.state', string='Transaction State',
                                         store=True)


class CustomerLiability(models.Model):
    _name = 'customer.liability'
    _description = 'Old Customer Liability'

    liability_type = fields.Many2one('customer.liability.type', string='Liability')
    liability_id = fields.Many2one('res.partner', string='Liability id', ondelete='cascade')
    amount = fields.Float(string='Amount')


class CustomerLiabilityType(models.Model):
    _name = 'customer.liability.type'
    _description = 'Old Customer Liability'

    name = fields.Char(string='Liability')


class VAccount(models.Model):
    _name = 'virtual.account.line'
    _description = 'virtual Account For the Customer'

    name = fields.Char(string='V.Account')
    Customer_name = fields.Many2one('res.partner', string='Customer Name')
    is_select = fields.Boolean(string='is Select')
    iban_num = fields.Char(string="IBAN Number", default='SA', store=True)

    # customer = fields.Char(string='Customer Name', compute='select_customer_name', store=True)

    @api.constrains('name')
    def len_virtual_account(self):
        for rec in self:
            rec.name == 1
            if len(str(rec.name)) != 15:
                raise ValidationError(_('Wrong ! Virtual Account Should be 15 Number '))

    @api.constrains('iban_num')
    def len_iban_number(self):
        for rec in self:
            rec.iban_num == 1
            if len(str(rec.iban_num)) != 24:
                raise ValidationError(_('Wrong ! IBAN NUMBER Should be 22 Number'))

    @api.constrains('name')
    def check_v_account(self):
        name = self.env['virtual.account.line'].search(
            [('name', '=', self.name), ('name', '!=', True),
             ('id', '!=', self.id)])
        if name:
            raise ValidationError(_('Exists ! Already a Virtual Account exists'))

    @api.constrains('iban_num')
    def check_iban_account(self):
        iban_num = self.env['virtual.account.line'].search(
            [('iban_num', '=', self.iban_num), ('iban_num', '!=', True),
             ('id', '!=', self.id)])
        if iban_num:
            raise ValidationError(_('Exists ! Already a Virtual Account exists'))

    # @api.depends('is_select', 'Customer_name', 'customer')
    # def select_customer_name(self):
    #     for rec in self:
    #         if rec.is_select == 'True':
    #             rec.customer = rec.customer_name.name
    #         else:
    #             return False

    # {"contractNumber":"10159","contractStatusCode":"1","updateDate":"2023-08-10T14:36:26.2968656+03:00","sanad":{"id":"f238d54c-024a-4c55-8065-4ffb6617d4dd","status":"approved"}}


class EarlyPayment(models.Model):
    _name = 'early.payment'
    _description = 'Early Payment For the Customer'

    name = fields.Char()
    loan_order = fields.Many2one('loan.order')
    contract_no = fields.Char()
    request_date = fields.Date()
    payment_method = fields.Selection([('bank', 'Bank'), ('sadad', 'Sadad')])
    payment_type = fields.Selection([('fully', 'Fully'), ('partially', 'Partially')])
    payment_amount = fields.Float()
    source_money = fields.Char()
    customer_relation = fields.Char()
    payer_name = fields.Char()
    payer_id = fields.Char()


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    installment_id = fields.Many2one('loan.installment', string="Loan Installment")
    loan_order_id = fields.Many2one('loan.order', string="Loan Order", help="The loan order related to this payment.")

    def send_messeage(self, phone, message):
        values = '''{
                                                            "userName": "Fuelfinancesa",
                                                              "numbers": "''' + phone + '''",
                                                              "userSender": "fuelfinance",
                                                              "apiKey": "3A8DC68B21706A0644A75660AE75553F",
                                                              "msg": "''' + message + '''"
                                                            }'''

        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        values = values.encode()
        requests.post('https://www.msegat.com/gw/sendsms.php',
                      data=values,
                      headers=headers)

    def send_paid_sms(self):
        for record in self:
            if record.partner_id.phone:
                _logger.info(f"Sending SMS for installment {self.id} to {self.partner_id.phone}.")
                paid_message = f"""
                    مرحباً,  ({self.partner_id.name})
                    شكراً..لقد تم استلام الدفعة الشهرية بأجمالي مبلغ {self.amount} ريال سعودي
                    ولمزيد من الاستفسارات نسعد بخدمتك علي الرقم الموحد 8001184000
                    خلال اوقات العمل الرسمية من الاحد الي الخميس
                    من الساعة 9 صباحاً الي 5 مساء
                    نشكرك علي اختيارك فيول للتمويل
                """
                self.send_messeage(self.partner_id.phone, paid_message)
                self.message_post(body=paid_message)
                self.installment_id.message_post(body=paid_message)

    def action_post(self):
        super(AccountPayment, self).action_post()
        # Update the related installment state when payment is posted
        for payment in self:
            if payment.installment_id:
                payment.installment_id._compute_amount_paid()
                payment.send_paid_sms()

    @api.model
    def auto_post_draft_payments(self):
        # Find payments in draft state created more than 1 minute ago
        threshold_time = datetime.now() - timedelta(minutes=1)
        draft_payments = self.search([
            ('state', '=', 'draft'),
            ('create_date', '<=', fields.Datetime.to_string(threshold_time))
        ])
        for payment in draft_payments:
            try:
                payment.action_post()  # Change state to 'posted' using the existing 'post' method
                payment.send_paid_sms()
            except Exception as e:
                # Log the error for debugging purposes
                _logger.error(f"Failed to post payment {payment.id}: {e}")
