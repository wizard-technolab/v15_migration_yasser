from odoo import models, fields, api, _
from datetime import date


class CreditReport(models.TransientModel):
    _name = 'credit.report'
    _description = 'Credit Report Wizard'

    partner_name = fields.Many2one("res.partner", string='Name')
    loan_request_id = fields.Many2one("loan.order", string='Loan ID')
    loan_request_from = fields.Date(string='From')
    loan_request_to = fields.Date(string='To')
    # user_id = fields.Many2many("res.users", string='Credit User')
    user_id = fields.Many2one("res.users", string='Credit User')
    status = fields.Selection([('draft', 'Draft'), ('review done', 'Credit V')], string='Status')
    note = fields.Char(string='Note')

    def action_partner_print(self):
        domain = []
        # loan_request_id = self.loan_request_id
        # if loan_request_id:
        #     domain += [('loan_request_id', '=', loan_request_id.id)]
        #
        # loan_request_from = self.loan_request_from
        # if loan_request_from:
        #     domain += [('request_date', '>=', loan_request_from)]
        #
        # loan_request_to = self.loan_request_to
        # if loan_request_to:
        #     domain += [('request_date', '<=', loan_request_to)]
        #
        # records = self.env['loan.order'].search_read([domain])
        # print('Test', records)
        data = {
            'model': 'loan.order',
            'form_data': self.read()[0]
        }
        select_credit = data['form_data']['user_id'][0]
        loans = self.env['loan.order'].search([('user_id', '=', select_credit)])
        print('loans', loans)
        data['docs'] = loans
        return self.env.ref('loan.action_credit_report').report_action(self, data=data)
