# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details.
import requests  # Import the `requests` library for making HTTP requests
from odoo import api, models, fields, _  # Import core Odoo modules for model creation and field definitions


class AmlManagement(models.Model):
    _name = 'aml.aml'  # Define the model name used in Odoo
    _description = 'compliance Management'  # Provide a description of the model

    # Define fields for the model with their respective attributes
    label = fields.Char(string="Label")  # A character field to store a label
    name = fields.Char(string="Name")  # A character field to store the name
    iq_number = fields.Char(string="ID")  # A character field to store an identification number
    date = fields.Date(string="Date")  # A date field to store a date value
    phone = fields.Char(string="Phone")  # A character field to store a phone number
    national = fields.Selection(
        [('saudi', 'Saudi'), ('foreigner', 'Foreigner')],  # Define selection options for nationality
        index=True  # Index the field to optimize search performance
    )
    document = fields.Binary(string="Attachment")  # A binary field to store file attachments
    customer_id = fields.Integer(string="Customer ID")  # An integer field to store a customer ID
    alert_id = fields.Integer(string="Alert ID")  # An integer field to store an alert ID
    status_id = fields.Integer(string="Status ID")  # An integer field to store a status ID
    match_info = fields.Char(string="Match information")  # A character field to store match information
    Message = fields.Char(string="Message")  # A character field to store a message
    aml_id = fields.Many2one(
        'loan.order',  # Define a many-to-one relationship with the 'loan.order' model
        string="aml id"  # Set the label for this field
    )

    def check_api(self):
        """
        Function to make an API request to a predefined endpoint.

        This function demonstrates how to make a GET request to a local API and print the response.
        """
        param = ["hadeel", "admin", "123"]  # Define a list of parameters (not used in the request currently)

        # Make a GET request to the specified API endpoint with hardcoded query parameters
        rest = requests.request('GET', 'http://localhost:8015/api/login2?db=odoo&login=admin&password=123')

        # Print the raw response from the API request (response object)
        # Uncomment the line below if you want to see the raw response data
        # print("___________", rest)

        # Print the response object to the console
        print(">>>>>>>>>>>>>>>>>>>", rest)
