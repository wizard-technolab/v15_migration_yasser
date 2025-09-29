# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class PurchaseOffer(models.Model):
    _inherit = 'purchase.order'
    _description = 'Purchase Offer'

    state = fields.Selection(selection_add=[('acceptance', 'Sale Acceptance'), ('done',)])

    customer_name = fields.Char(name='Customer Name')
    customer_id = fields.Char(name='Customer ID')
    customer_phone = fields.Char(name='Phone no')
    is_medical = fields.Boolean(name='is medical')
    age = fields.Char(name='Age')
    section_name = fields.Char(name='Section Name')
    supplier_id = fields.Char(name='Supplier id')
    supplier_name = fields.Char(name='Supplier Name')


