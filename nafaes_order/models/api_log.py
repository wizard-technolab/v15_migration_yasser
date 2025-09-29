import json  # Import JSON module for handling JSON data
import logging  # Import logging module for logging errors and information
from odoo import api, fields, models, _  # Import necessary classes and functions from Odoo
from odoo.exceptions import UserError  # Import UserError exception from Odoo
from .api_mixin import NAFAES_TOKEN  # Import NAFAES_TOKEN from the api_mixin module

_logger = logging.getLogger(__name__)  # Initialize the logger

class NafaesApiLog(models.Model):  # Define a new model class for Nafaes API logs
    _name = "nafaes.api.log"  # Set the model name
    _description = "Nafaes Api Log"  # Set the model description
    _order = "id desc"  # Set the default order for records
    _rec_name = 'create_date'  # Set the default record name to creation date

    request = fields.Char(readonly=True)  # Define a read-only Char field for storing the request data
    response = fields.Char(readonly=True)  # Define a read-only Char field for storing the response data
    header = fields.Char(readonly=True)  # Define a read-only Char field for storing the header data
    partner_id = fields.Many2one('res.partner', readonly=True)  # Define a Many2one field for the partner, read-only
    url = fields.Char('URL', readonly=True)  # Define a read-only Char field for the URL
    response_status = fields.Integer()  # Define an Integer field for the response status
    type = fields.Selection([  # Define a selection field for the type of API log
        ('auth', 'Auth'),
        ('po', 'Purchase Order'),
        ('to', 'Transfer Order'),
        ('so', 'Sale Order'),
        ('co', 'Cancel Order'),
        ('result', 'Order Result'),
        ('get_commodities', 'Get Commodities'),
        ('webhook', 'Webhook'),
    ])
    res_model = fields.Char('Model', help='The model which the request is related to, e.g: sale.order')  # Define a Char field for the related model
    res_id = fields.Many2oneReference(string='Record ID', help="ID of the target record in the database", model_field='res_model')  # Define a Many2oneReference field for the record ID
    note = fields.Text()  # Define a Text field for additional notes

    reference = fields.Char(string='Reference', compute='_compute_reference')  # Define a computed Char field for the reference

    @api.depends('res_model', 'res_id')  # Set dependencies for the computed field
    def _compute_reference(self):
        for res in self:  # Iterate through records
            res.reference = "%s,%s" % (res.res_model, res.res_id)  # Compute the reference field value

    res_ids = fields.Char('Resource IDs')  # Define a Char field for resource IDs

    def action_retry_webhook(self):  # Define a method to retry a webhook
        self.ensure_one()  # Ensure a single record is selected
        if self.type != 'webhook':  # Check if the type is not 'webhook'
            raise UserError('Not a webhook')  # Raise a UserError if not a webhook
        payload = json.loads(self.request)  # Load the request data as JSON
        self.env['nafaes.order.result'].handle_request(payload, '<manual retry>', NAFAES_TOKEN, enable_log=True)  # Call the handle_request method on the nafaes.order.result model

    def create_log(self, values):  # Define a method to create a log entry
        with self.pool.cursor() as new_cr:  # Open a new cursor
            # Create a new log entry with sudo permissions using the new cursor
            return self.with_env(self.env(cr=new_cr)).sudo().create(values)

    def update_log(self, values):  # Define a method to update a log entry
        self.ensure_one()  # Ensure a single record is selected
        with self.pool.cursor() as new_cr:  # Open a new cursor
            # Update the log entry with sudo permissions using the new cursor
            log_id = self.with_env(self.env(cr=new_cr)).sudo()
            log_id.write(values)
