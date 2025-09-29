# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    state = fields.Selection(
        selection_add=[('accounting_manager', 'Manager'),
                       ('approved', 'Approved'),
                       ('rejected', 'Rejected')],
        ondelete={'project_manager': 'set default', 'accounting_manager': 'set default', 'vp': 'set default',
                  'approved': 'set default',
                  'rejected': 'set default'})


class AccountPayment(models.Model):
    _inherit = "account.payment"
    _inherits = {'account.move': 'move_id'}

    @api.model
    def _get_account_manager_id(self):
        account_manager_id = self.env.company.account_manager_id
        return account_manager_id

    def transfer_accounting_manager(self):
        if self.state == 'draft':
            self.sudo().write({
                'state': 'accounting_manager',
            })
            user = self.env.company.account_manager_id
            self.activity_schedule(
                'Payment Approve', user_id=user.id)

    def transfer_approved(self):
        if self.state == 'accounting_manager':
            user_id = self.env.company.account_manager_id
            self.sudo().activity_done(user_id.id)
            self.sudo().write({
                'state': 'approved',
            })

    def reject_transfer(self):
        self.sudo().write({
            'state': 'rejected'
        })

    def activity_done(self, u_id):
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', 'account.payment'),
            ('res_id', '=', self.id),
            ('user_id', '=', u_id)])
        for rec in activity:
            if rec:
                rec.sudo().action_done()
