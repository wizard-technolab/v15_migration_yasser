from datetime import date
from odoo import models, fields, api


class LoanOrderInherit(models.Model):
    _inherit = 'loan.order'

    is_Closed = fields.Boolean(string='Is Closed')
    is_Stumbled = fields.Boolean(string='Is Stumbled')
    late_installment = fields.Float(string='Late Installment', compute='_compute_late_amount', store=False)

    @api.depends('installment_ids.state', 'installment_ids.date', 'installment_ids.installment_amount')
    def _compute_late_amount(self):
        for record in self:
            late_sum = 0
            today = date.today()
            for installment in record.installment_ids:
                if installment.state == 'unpaid':
                    # Calculate the difference in months, considering the year
                    installment_month_diff = (today.year - installment.date.year) * 12 + (
                                today.month - installment.date.month)
                    # If the installment date is before the current month
                    if installment_month_diff > 0:
                        late_sum += installment.remaining_amount
            # Assign the total late sum
            record.late_installment = late_sum