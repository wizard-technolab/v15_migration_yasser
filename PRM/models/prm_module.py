# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class PrmLead(models.Model):
    # _name = 'prm.lead.new'
    _inherit = 'crm.lead'
    _description = 'Partner management'

    name = fields.Char(string='Cosmetic')
    commission = fields.Float(string='Discount')
    discount = fields.Float(string='To')
    partner_id = fields.Many2one(
        'res.partner', string='Name')


class Editbutton(models.Model):
    _inherit = "crm.iap.lead.mining.request"

    # email_from = fields.Char(
    #     'Email', tracking=40, index=True,
    #     compute='_compute_email_from', inverse='_inverse_email_from', readonly=False, store=True)

# @api.depends('make_visible')
# def get_user(self, ):
#     user_crnt = self._uid
#     res_user = self.env['res.users'].search([('id', '=', self._uid)])
#     if res_user.has_group('crm.lead.group_name'):
#         self.make_visible = False
#         else:
#         self.make_visible = True
