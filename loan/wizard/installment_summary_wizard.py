import datetime

from odoo import api, fields, models, _


class InstallmentSummaryWizard(models.TransientModel):
    _name = "installment.report.wizard"
    _description = 'Installment Loan Request'

    @api.model
    def default_get(self, fields):
        res = super(InstallmentSummaryWizard, self).default_get(fields)
        res['early_date'] = datetime.date.today()
        res['early_name'] = self.env.context.get('active_id')
        res['early_loan_amount'] = self.env.context.get('active_id')
        # res['early_loan_amount'] = self.env['loan.order'].browse(self.env.context.get('active_id'))
        return res

    # start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today())
    # end_date = fields.Date(string='End Date', required=True)
    # group_id = fields.Selection([('loan', 'Loan'), ('name', 'Name')], string='Group By', required=True)
    # filter_name = fields.Many2one("loan.order", string="Name")
    # filter_loan = fields.Many2one("loan.order", string="Loan")
    currency_id = fields.Many2one("res.currency", string="Currency", required=True)
    # early_id = fields.Many2one('loan.order', string='Early Loan')
    early_name = fields.Many2one('loan.order', string='Customer')
    early_date = fields.Date(string='Date')
    early_loan_amount = fields.Monetary(related='early_name.loan_amount', currency_field="currency_id",
                                        string="Loan Amount")
    early_interest_amount = fields.Monetary(related='early_name.interest_amount', currency_field="currency_id",
                                            string="Interest Amount", compute="remaining_early")
    early_paid_amount = fields.Monetary(related='early_name.paid_amount', currency_field="currency_id",
                                        string="Paid Amount")
    early_remaining_amount = fields.Monetary(related='early_name.remaining_amount', currency_field="currency_id",
                                             string="Remaining Amount")

    def action_early(self):
        return

# def action_print_report(self):
#     data = {}
#     for rec in self:
#         if rec.early_name:
#             data.update({'early_name': rec.early_name})
#         # if rec.end_date:
#         #     data.update({'end': rec.end_date})
#         # if rec.filter_name:
#         #     data.update({'name': rec.filter_name.name.name})
#
#     return self.env.ref('loan.action_installment_report').report_action(self, data=data)
