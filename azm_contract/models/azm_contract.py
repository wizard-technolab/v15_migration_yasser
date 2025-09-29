# -*- coding: utf-8 -*-
# Import necessary modules and classes from Odoo
from odoo import api, models, fields, _

# Define a new Odoo model class named 'azm.contract'
class azm_contract(models.Model):
    # Specify the model name for the Odoo ORM
    _name = 'azm.contract'
    _description = 'Contract Model'

    customer_date = fields.Many2one('loan.order', required=True, string='Customer Data')
    # Define a field named 'customer_date' in the 'azm.contract' model
    # The field is of type Many2one, which creates a many-to-one relationship with another model
    # The 'loan.order' model is the target model for this relationship
    # 'required=True' means this field is mandatory when creating or editing records
    # 'string' specifies the label for the field in the Odoo interface