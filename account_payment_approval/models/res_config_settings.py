from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'
    payment_approval = fields.Boolean('Payment Approval')
    account_manager_id = fields.Many2one('res.users', string="Manager")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_approval = fields.Boolean('Payment Approval', readonly=False, related='company_id.payment_approval')
    account_manager_id = fields.Many2one('res.users', readonly=False, string="Manager",
                                         related='company_id.account_manager_id')
