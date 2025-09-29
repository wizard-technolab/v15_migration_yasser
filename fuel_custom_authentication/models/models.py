# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class fuel_custom_authentication(models.Model):
#     _name = 'fuel_custom_authentication.fuel_custom_authentication'
#     _description = 'fuel_custom_authentication.fuel_custom_authentication'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
