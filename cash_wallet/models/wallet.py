# -*- coding: utf-8 -*-
from odoo import api, models, fields, _  # Import necessary Odoo modules and functions


class CashWallet(models.Model):  # Define a new model class inheriting from Odoo's models.Model
    _name = 'cash.wallet'  # Set the internal name of the model, used for database and references
    _description = 'Cash wallet'  # Set the description of the model, which appears in the user interface

    label = fields.Char(string="Label")  # Define a Char field named 'label' with a user-friendly string "Label"
