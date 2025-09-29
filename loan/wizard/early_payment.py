# # -*- coding: utf-8 -*-
# from odoo import api, fields, models, _
# from datetime import datetime, date
#
#
# class EarlyPayment(models.TransientModel):
#     _name = "early.payment"
#     _description = 'Loan Request'
#
#     name = fields.Char(string='Name')
#     installment = fields.Many2one('loan.installment', string='Name')
#     early_seq_name = fields.Char(related='installment.seq_name', string='Sequence Name')
#     early_name = fields.Many2one(related='installment.name', string='Name')
#     early_date = fields.Date(related='installment.date', string='Date')
#     # early_payment_date = fields.Date(related='installment.payment_date ', string='Date Payment')
#     early_principal_amount = fields.Monetary(related='installment.principal_amount', string='principal_amount')
#     early_interest_amount = fields.Monetary(related='installment.interest_amount', string='interest_amount')
#     early_installment_amount = fields.Monetary(related='installment.installment_amount', string='installment_amount')
#     currency_id = fields.Many2one('res.currency', string='Currency')
