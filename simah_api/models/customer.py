# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Create Customer'

    # Define additional fields for the res.partner model
    first_name = fields.Char()  # Field for the first name
    second_name = fields.Char()  # Field for the second name
    third_name = fields.Char()  # Field for the third name
    family_name = fields.Char()  # Field for the family name
    simah_amount = fields.Float()  # Field for the Simah amount
    english_name = fields.Char()  # Field for the English name

    @api.onchange('name')
    def action_split(self):
        '''Splits the 'name' field into individual name components.'''
        for rec in self:
            if rec.name == '':
                # Split the 'name' field into components based on spaces
                char = rec.name.split()
                print(char)  # Print the split name components for debugging

                # Assign split components to respective fields
                rec.first_name = char[0] if len(char) > 0 else ''
                rec.second_name = char[1] if len(char) > 1 else ''
                rec.third_name = char[2] if len(char) > 2 else ''
                rec.family_name = char[3] if len(char) > 3 else ''
            else:
                # If 'name' is empty, do nothing
                return False