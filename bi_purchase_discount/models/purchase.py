# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Discount %')

    def _prepare_compute_all_values(self):
        
        discount = (self.price_unit * self.discount * self.product_qty)/100
        self.ensure_one()
        return {
            'price_unit': self.price_unit - discount,
            'currency': self.order_id.currency_id,
            'quantity': self.product_qty,
            'product': self.product_id,
            'partner': self.order_id.partner_id,
        }

    def _prepare_account_move_line(self, move=False):
        result = super(purchase_order_line, self)._prepare_account_move_line()
        if result:
            result.update({
                'discount' : self.discount,
            })
        return result 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
