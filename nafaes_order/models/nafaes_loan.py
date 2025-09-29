import json  # Import json for handling JSON data
import logging  # Import logging for logging messages
from odoo import api, fields, models, _  # Import Odoo components for defining models, fields, and translations
from odoo.exceptions import UserError  # Import UserError for raising user-related errors
import datetime  # Import datetime for handling dates and times

_logger = logging.getLogger(__name__)  # Create a logger for this module

class loan_order(models.Model):
    _inherit = "loan.order"  # Inherit from the 'loan.order' model
    _description = 'Inherit From Loan Order'  # Description of the inherited model

    # Fields related to 'nafaes.purchase.order'
    nafaes_order_id = fields.Many2one('nafaes.purchase.order')  # Many2one field linking to 'nafaes.purchase.order'

    nafaes_api_error = fields.Char(related='nafaes_order_id.api_error')  # Char field for API error from the related 'nafaes_order_id'
    nafaes_error_invisible = fields.Boolean(related='nafaes_order_id.error_invisible')  # Boolean field for error visibility from the related 'nafaes_order_id'
    nafaes_state = fields.Selection(related='nafaes_order_id.state')  # Selection field for state from the related 'nafaes_order_id'
    nafaes_uuid_po = fields.Char(related='nafaes_order_id.uuid_po')  # Char field for UUID PO from the related 'nafaes_order_id'
    nafaes_uuid_to = fields.Char(related='nafaes_order_id.uuid_to')  # Char field for UUID TO from the related 'nafaes_order_id'
    nafaes_uuid_so = fields.Char(related='nafaes_order_id.uuid_so')  # Char field for UUID SO from the related 'nafaes_order_id'
    nafaes_referenceNo = fields.Char(related='nafaes_order_id.referenceNo')  # Char field for reference number from the related 'nafaes_order_id'
    nafaes_transactionReference = fields.Char(related='nafaes_order_id.transactionReference')  # Char field for transaction reference from the related 'nafaes_order_id'
    nafaes_commodityName = fields.Char(related='nafaes_order_id.commodityName')  # Char field for commodity name from the related 'nafaes_order_id'
    nafaes_result_amount = fields.Monetary(related='nafaes_order_id.result_amount')  # Monetary field for result amount from the related 'nafaes_order_id'
    nafaes_unit = fields.Char(related='nafaes_order_id.unit')  # Char field for unit from the related 'nafaes_order_id'
    nafaes_executingUnit = fields.Char(related='nafaes_order_id.executingUnit')  # Char field for executing unit from the related 'nafaes_order_id'
    nafaes_quantity = fields.Char(related='nafaes_order_id.quantity')  # Char field for quantity from the related 'nafaes_order_id'
    nafaes_commission = fields.Char(related='nafaes_order_id.commission')  # Char field for commission from the related 'nafaes_order_id'
    nafaes_comm_currency_id = fields.Many2one(related='nafaes_order_id.comm_currency_id')  # Many2one field for commission currency from the related 'nafaes_order_id'
    nafaes_certificateNo = fields.Char(related='nafaes_order_id.certificateNo')  # Char field for certificate number from the related 'nafaes_order_id'
    nafaes_attribute1 = fields.Char(related='nafaes_order_id.attribute1')  # Char field for attribute1 from the related 'nafaes_order_id'
    nafaes_attribute2 = fields.Char(related='nafaes_order_id.attribute2')  # Char field for attribute2 from the related 'nafaes_order_id'
    nafaes_attribute3 = fields.Char(related='nafaes_order_id.attribute3')  # Char field for attribute3 from the related 'nafaes_order_id'
    nafaes_result_date = fields.Datetime(related='nafaes_order_id.result_date')  # Datetime field for result date from the related 'nafaes_order_id'

    nafaes_purchaser = fields.Char(related='nafaes_order_id.purchaser')  # Char field for purchaser from the related 'nafaes_order_id'
    nafaes_currency = fields.Char(related='nafaes_order_id.currency')  # Char field for currency from the related 'nafaes_order_id'
    nafaes_valueDate = fields.Char(related='nafaes_order_id.valueDate')  # Char field for value date from the related 'nafaes_order_id'

    nafaes_po_user_id = fields.Many2one(related='nafaes_order_id.po_user_id')  # Many2one field for PO user from the related 'nafaes_order_id'
    nafaes_so_user_id = fields.Many2one(related='nafaes_order_id.so_user_id')  # Many2one field for SO user from the related 'nafaes_order_id'

    def _create_nafaes_order(self):
        """Create a new Nafaes purchase order and submit it."""
        self.ensure_one()  # Ensure that only one record is processed
        nafaes_obj = self.env['nafaes.purchase.order']  # Get the 'nafaes.purchase.order' model
        date_prefix = datetime.date.today().strftime('%Y%m')  # Get the current date in 'YYYYMM' format
        self.nafaes_order_id = nafaes_obj.create({
            'partner_id': self.name.id,  # Set partner_id using the current record's name ID
            'amount': self.loan_amount - self.down_payment_loan,  # Calculate the amount as loan_amount minus down_payment_loan
            # NOTE: nafaes API does not accept old dates here, not even yesterday's date
            'date': fields.Date.today(),  # Set the date to today's date
            'counterPartyTelephone': nafaes_obj.get_partner_mobile(self.name),  # Set counterPartyTelephone using the get_partner_mobile method
            'counterPartyAccount': f'{date_prefix}{self.id}',  # Set counterPartyAccount with date_prefix and current record ID
            'counterPartyName': f'{date_prefix}{self.id}',  # Set counterPartyName with date_prefix and current record ID
        })
        self.nafaes_order_id.action_submit()  # Submit the created Nafaes purchase order

    def action_call_done(self):
        """Override the action_call_done method to handle specific loan types."""
        self.ensure_one()  # Ensure only one record is processed
        _logger.info(f"Calling action_call_done for Loan ID {self.id}")
        if self.loan_type.id in [2, 3]:  # Check if the loan_type ID is 2
            # self.ensure_one()  # Ensure that only one record is processed
            res = super(loan_order, self).action_call_done()  # Call the superclass method
            self.message_post(subject='An item was purchased from Nafaes')  # Post a message indicating that an item was purchased from Nafaes
            if not self.nafaes_order_id:  # Check if nafaes_order_id is not set
                self._create_nafaes_order()  # Create a Nafaes order if not already present
            return res  # Return the result from the superclass method
        elif self.loan_type.id == 1:  # Check if the loan_type ID is 1
            print('ignore Nafaes API')  # Print a message indicating that Nafaes API is ignored
            self.send_po_status()  # Call send_po_status method
            self.message_post(subject='The purchase order has been sent to supplier')  # Post a message indicating that the purchase order was sent to the supplier
            self.ensure_one()  # Ensure that only one record is processed
            res = super(loan_order, self).action_call_done()  # Call the superclass method
        else:
            _logger.info("No action for Loan ID {self.id}")
            return super(loan_order, self).action_call_done()


    def action_nafaes_recreate(self):
        """Recreate the Nafaes order if there is an API error."""
        if self.nafaes_order_id.api_error:  # Check if there is an API error
            self._create_nafaes_order()  # Recreate the Nafaes order
        else:
            raise UserError("Nafaes order should not be retried")  # Raise an error if the Nafaes order should not be retried

    def action_nafaes(self):
        """Handle Nafaes actions."""
        res = super(loan_order, self).action_nafaes()  # Call the superclass method
        if self.nafaes_order_id:  # Check if nafaes_order_id is set
            self.nafaes_order_id.action_sell()  # Call action_sell on the related Nafaes order
        return res  # Return the result from the superclass method

    def activity_schedule_nafaes_error(self, user_id, error_message):
        """Schedule an activity to handle Nafaes errors."""
        self.activity_schedule(
            'nafaes_order.mail_activity_nafaes_issue',  # Activity type for Nafaes issue
            summary=_("Nafaes Issue"),  # Summary of the activity
            user_id=user_id.id,  # User assigned to the activity
            date_deadline=datetime.datetime.today(),  # Set deadline to today's date
            note=error_message  # Note containing the error message
        )

    def activity_schedule_nafaes_sell(self, user_id):
        """Schedule an activity to handle Nafaes sell."""
        self.activity_schedule(
            'nafaes_order.mail_activity_nafaes_sell',  # Activity type for Nafaes sell
            summary=_("Nafaes Order Sold"),  # Summary of the activity
            user_id=user_id.id,  # User assigned to the activity
            date_deadline=datetime.datetime.today(),  # Set deadline to today's date
            note=_('Nafaes order has been sold'),  # Note indicating that the Nafaes order has been sold
        )
