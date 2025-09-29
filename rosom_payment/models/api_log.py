import json  # Import JSON module for handling JSON data
import logging  # Import logging module for logging messages
from odoo import api, fields, models, _  # Import Odoo modules for API, fields, models, and translation
from odoo.exceptions import UserError  # Import UserError for handling user-specific exceptions

_logger = logging.getLogger(__name__)  # Create a logger object for this module


class rosom_api_log(models.Model):
    _name = "rosom.api.log"  # Define the model name
    _inherit = "ff.api.log"  # Inherit from the 'ff.api.log' model to extend its functionality
    _description = "Rosom Api Log"  # Provide a description for the model

    # Add new selection options to the existing 'type' field
    type = fields.Selection(selection_add=[
        ('auth', 'Auth'),  # Selection option for authentication logs
        ('webhook', 'Webhook'),  # Selection option for webhook logs
        ('multi_bill', 'Create Multiple Bills'),  # Selection option for creating multiple bills logs
    ])

    def action_retry_webhook(self):
        """
        Retry the webhook request if the log type is 'webhook'.

        This method ensures that the current record is of type 'webhook' and then
        reprocesses the request by calling 'handle_request' method on 'rosom.api.mixin'.
        """
        self.ensure_one()  # Ensure that only one record is processed
        if self.type != 'webhook':  # Check if the log type is not 'webhook'
            raise UserError('Not a webhook request')  # Raise an error if it's not a webhook request
        # Reprocess the webhook request
        self.env['rosom.api.mixin'].handle_request(
            json.loads(self.request),  # Load and parse the request data from JSON
            '<manual retry>',  # Provide a description for the retry
            enable_log=False  # Disable logging for this retry operation
        )
    def highlight_errors_in_response(self, response_data):
        print("++++++++++++++++++++++")
        if isinstance(response_data, list):
            highlighted = ""
            for item in response_data:
                code = item.get("Status", {}).get("Code", 0)
                color = "red" if code != 0 else "black"
                item_str = json.dumps(item, indent=2, ensure_ascii=False)
                highlighted += f'<pre style="color:{color}">{item_str}</pre>\n'
            return highlighted
        return json.dumps(response_data, indent=2, ensure_ascii=False)
