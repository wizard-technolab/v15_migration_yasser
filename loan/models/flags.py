# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class LoanFlag(models.Model):
    _inherit = 'account.analytic.account'
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Loan Flag'

    flag_obj = fields.Many2one('loan.order', string="Related Loan")
    loan_ids = fields.One2many('loan.order', 'account_analytic')
    customer_count = fields.Integer(compute='_compute_customer_count')
    total_balance = fields.Float(compute='_compute_total_loan', string="Total Balance")
    total_loan = fields.Float(compute='_compute_total_loan', string="Total Receivable")
    total_loan_amount = fields.Float(compute='_compute_loan_amount', string="Loan Amount")
    total_loan_interest = fields.Float(compute='_compute_loan_interest', string="Loan interest")
    total_paid_interest = fields.Float(compute='_compute_interest_paid', string="Paid interest")
    total_paid_principal = fields.Float(compute='_compute_principal_paid', string="Paid Principal")

    def get_customer(self):
        self.ensure_one()
        return {
            'name': _('Customer Data'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.order',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [('account_analytic', '=', self.name)],
            'context': "{'create': False}"
        }

    def _compute_customer_count(self):
        for record in self:
            record.customer_count = self.env['loan.order'].search_count(
                [('account_analytic', '=', self.name)])

    def _compute_total_balance(self):
        for record in self:
            balance = sum(
                self.env['crossovered.budget.lines'].search([('analytic_account_id', '=', record.id)]).mapped(
                    'planned_amount'))
            record.total_balance = balance

    def _compute_total_loan(self):
        for record in self:
            total_amount = sum(
                self.env['loan.order'].search([('account_analytic', '=', record.id)]).mapped('loan_sum'))
            record.total_loan = total_amount
            record.update({
                'total_balance': record.total_planned_amount - total_amount,
            })
            print(record.total_balance)

    def _compute_loan_amount(self):
        for record in self:
            total_amount = sum(
                self.env['loan.order'].search([('account_analytic', '=', record.id)]).mapped('loan_amount'))
            record.total_loan_amount = total_amount

    def _compute_loan_interest(self):
        for record in self:
            total_amount = sum(
                self.env['loan.order'].search([('account_analytic', '=', record.id)]).mapped('interest_amount'))
            record.total_loan_interest = total_amount

    def _compute_interest_paid(self):
        for record in self:
            total_amount = sum(self.env['loan.installment'].search(
                [('loan_id.account_analytic', '=', record.id), ('state', '=', 'paid')]).mapped('interest_amount'))
            record.total_paid_interest = total_amount

    def _compute_principal_paid(self):
        for record in self:
            total_amount = sum(self.env['loan.installment'].search(
                [('loan_id.account_analytic', '=', record.id), ('state', '=', 'paid')]).mapped('principal_amount'))
            record.total_paid_principal = total_amount

    def get_total_loans(self):
        action = self.env.ref('loan.request_action').read()[0]
        action['domain'] = [('account_analytic', '=', self.id)]
        return action

    def get_total_balance(self):
        action = self.env.ref('account_budget.act_account_analytic_account_cb_lines').read()[0]
        action['domain'] = [('analytic_account_id', '=', self.id)]
        return action


class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Crossovered Budget'

    paid_installments_ids = fields.One2many('loan.installment', 'budget_id', string='Paid Installments')
    loan_order_count = fields.Integer(compute="_compute_loan_order_count", string="Loan Orders")
    loan_principle_due = fields.Float(compute='_compute_loan_principle_due', string="Total Principle Due")
    loan_interest_due = fields.Float(compute='_compute_loan_interest_due', string="Total Interest Due")
    loan_principle_paid = fields.Float(compute='_compute_loan_principle_paid', string="Total Principle Paid")
    loan_interest_paid = fields.Float(compute='_compute_loan_interest_paid', string="Total Interest Paid")
    total_installment_paid = fields.Float(compute='_compute_loan_installment_paid', string="Total Installment Paid")
    total_interest_paid = fields.Float(compute='_compute_total_interest_paid', string="Total Interest Paid")
    installment_paid_count = fields.Integer(
        string='Paid Installments Count',
        compute='_compute_installment_paid_count',
        store=False
    )
    installment_unpaid_count = fields.Integer(
        string='UnPaid Installments Count',
        compute='_compute_installment_unpaid_count',
        store=False
    )
    total_planned_amount = fields.Monetary(
        string='Total Planned Amount',
        compute='_compute_total_planned_amount',
        store=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('crossovered_budget_line.planned_amount')
    def _compute_total_planned_amount(self):
        for record in self:
            record.total_planned_amount = sum(record.crossovered_budget_line.mapped('planned_amount'))

    def get_total_active_loans(self):
        action = self.env.ref('loan.request_action').read()[0]
        action['domain'] = [('account_analytic_line', '=', self.id)]
        return action

    def action_view_paid_installments(self):
        self.ensure_one()
        analytic_ids = self.crossovered_budget_line.mapped('analytic_account_id').ids
        domain = [
            ('loan_id.account_analytic', 'in', analytic_ids),
            ('state', '=', 'paid'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        return {
            'name': 'Paid Installments',
            'type': 'ir.actions.act_window',
            'res_model': 'loan.installment',
            'view_mode': 'tree',
            'domain': domain,
            'context': {
                **self.env.context,
                'analytic_ids': analytic_ids,
                'date_from': self.date_from,
                'date_to': self.date_to,
            },
        }

    def action_view_unpaid_installments(self):
        self.ensure_one()
        analytic_ids = self.crossovered_budget_line.mapped('analytic_account_id').ids
        domain = [
            ('loan_id.account_analytic', 'in', analytic_ids),
            ('state', '=', 'unpaid'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        return {
            'name': 'Paid Installments',
            'type': 'ir.actions.act_window',
            'res_model': 'loan.installment',
            'view_mode': 'tree',
            'domain': domain,
            'context': self.env.context,
        }

    ############################## Total Customers ######################################
    def _compute_loan_order_count(self):
        for record in self:
            budget_lines = self.env['crossovered.budget.lines'].search([
                ('crossovered_budget_id', '=', record.id)
            ])
            loan_orders = self.env['loan.order'].search([
                ('account_analytic_line', 'in', budget_lines.ids)
            ])
            record.loan_order_count = len(loan_orders)

    def action_view_loan_orders(self):
        self.ensure_one()
        budget_lines = self.env['crossovered.budget.lines'].search([
            ('crossovered_budget_id', '=', self.id)
        ])
        return {
            'name': 'Loan Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'loan.order',
            'domain': [('account_analytic_line', 'in', budget_lines.ids)],
            'context': {'default_account_budget_ids': [(6, 0, [self.id])]},
        }

    ############################## Total Principle Due ######################################
    @api.depends('crossovered_budget_line', 'date_from', 'date_to')
    def _compute_loan_principle_due(self):
        for record in self:
            total_amount = 0
            if record.date_from and record.date_to:
                analytic_ids = record.crossovered_budget_line.mapped('analytic_account_id').ids
                if analytic_ids:
                    # Search for loan installments that match those accounts and the date range
                    installments = self.env['loan.installment'].search([
                        ('loan_id.account_analytic', 'in', analytic_ids),
                        ('state', '=', 'unpaid'),
                        ('date', '>=', record.date_from),
                        ('date', '<=', record.date_to),
                    ])
                    total_amount = sum(installments.mapped('principal_amount'))

            record.loan_principle_due = total_amount

    ############################## Total Interest Due ######################################
    @api.depends('crossovered_budget_line', 'date_from', 'date_to')
    def _compute_loan_interest_due(self):
        for record in self:
            total_amount = 0
            if record.date_from and record.date_to:
                analytic_ids = record.crossovered_budget_line.mapped('analytic_account_id').ids
                if analytic_ids:
                    # Search for loan installments that match those accounts and the date range
                    installments = self.env['loan.installment'].search([
                        ('loan_id.account_analytic', 'in', analytic_ids),
                        ('state', '=', 'unpaid'),
                        ('date', '>=', record.date_from),
                        ('date', '<=', record.date_to),
                    ])
                    total_amount = sum(installments.mapped('interest_amount'))

            record.loan_interest_due = total_amount

    ############################## Total Interest Paid ######################################
    def _compute_loan_interest_paid(self):
        for record in self:
            total_amount = 0
            if record.date_from and record.date_to:
                analytic_ids = record.crossovered_budget_line.mapped('analytic_account_id').ids
                if analytic_ids:
                    # Search for loan installments that match those accounts and the date range
                    installments = self.env['loan.installment'].search([
                        ('loan_id.account_analytic', 'in', analytic_ids),
                        ('state', '=', 'paid'),
                        ('date', '>=', record.date_from),
                        ('date', '<=', record.date_to),
                    ])
                    total_amount = sum(installments.mapped('interest_amount'))

            record.loan_interest_paid = total_amount

    ############################## Total Principal Paid ######################################
    def _compute_loan_principle_paid(self):
        for record in self:
            total_amount = 0
            if record.date_from and record.date_to:
                analytic_ids = record.crossovered_budget_line.mapped('analytic_account_id').ids
                if analytic_ids:
                    # Search for loan installments that match those accounts and the date range
                    installments = self.env['loan.installment'].search([
                        ('loan_id.account_analytic', 'in', analytic_ids),
                        ('state', '=', 'paid'),
                        ('date', '>=', record.date_from),
                        ('date', '<=', record.date_to),
                    ])
                    total_amount = sum(installments.mapped('principal_amount'))

            record.loan_principle_paid = total_amount

    ############################## Total Installment Paid ######################################
    @api.depends('loan_principle_paid', 'loan_interest_paid')
    def _compute_loan_installment_paid(self):
        for record in self:
            record.total_installment_paid = record.loan_principle_paid + record.loan_interest_paid

    ############################## Total Interest Paid ######################################
    @api.depends('loan_interest_due', 'loan_interest_paid')
    def _compute_total_interest_paid(self):
        for record in self:
            record.total_interest_paid = record.loan_interest_due + record.loan_interest_paid

    ############################## Number Installment Paid ######################################
    def _compute_installment_paid_count(self):
        for record in self:
            count = 0
            if record.date_from and record.date_to:
                analytic_ids = record.crossovered_budget_line.mapped('analytic_account_id').ids
                if analytic_ids:
                    installments = self.env['loan.installment'].search([
                        ('loan_id.account_analytic', 'in', analytic_ids),
                        ('state', '=', 'paid'),
                        ('date', '>=', record.date_from),
                        ('date', '<=', record.date_to),
                    ])
                    count = len(installments)
            record.installment_paid_count = count

    ############################## Number Installment UnPaid ######################################
    def _compute_installment_unpaid_count(self):
        for record in self:
            count = 0
            if record.date_from and record.date_to:
                analytic_ids = record.crossovered_budget_line.mapped('analytic_account_id').ids
                if analytic_ids:
                    installments = self.env['loan.installment'].search([
                        ('loan_id.account_analytic', 'in', analytic_ids),
                        ('state', '=', 'unpaid'),
                        ('date', '>=', record.date_from),
                        ('date', '<=', record.date_to),
                    ])
                    count = len(installments)
            record.installment_unpaid_count = count


class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Crossovered Budget Lines'

    loan_order_budget = fields.Many2one("loan.order", string="Related Loan")
    expenses = fields.Selection(
        [('it_cost', 'IT Subscription Cost'), ('digital_cost', 'Digital Contracting Cost'),
         ('web_cost', 'Web Registration Cost'), ('collection_cost', 'Collection Cost'), ('admin_fees', 'Admin Fees'),
         ('sales_com', 'Sales Commition'), ('fuel_cost', 'Fuel Cost(30%)'), ('dividing_cost', 'Dividing Cost'),
         ('other_cost', 'Other Cost')], string='Expenses', store=True)
    amount_expenses = fields.Float(string='Exp Amount')
    net_cash_flow = fields.Float(string='Net Cash Flow', compute='_compute_net_cash_flow', store=True)
    net_profit = fields.Float(string='Net Profit', compute='_compute_net_profit_flow', store=True)

    @api.depends('amount_expenses', 'crossovered_budget_id.total_installment_paid')
    def _compute_net_cash_flow(self):
        for record in self:
            if not record.amount_expenses:
                record.net_cash_flow = 0.0
            else:
                total_paid = record.crossovered_budget_id.total_installment_paid or 0.0
                record.net_cash_flow = total_paid - record.amount_expenses

    @api.depends('amount_expenses', 'crossovered_budget_id.total_interest_paid')
    def _compute_net_profit_flow(self):
        for record in self:
            if not record.amount_expenses:
                record.net_profit = 0.0
            else:
                total_interest = record.crossovered_budget_id.total_interest_paid or 0.0
                record.net_profit = total_interest - record.amount_expenses
