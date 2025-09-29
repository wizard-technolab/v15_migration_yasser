from datetime import datetime, date  # Import datetime and date for handling dates and times
from odoo import api, fields, models, _  # Import Odoo API components for defining models, fields, and translations
from odoo.exceptions import UserError, AccessDenied  # Import exceptions for handling errors and access control


class NafaesPurchaseOrder(models.Model):
    _name = "nafaes.purchase.order"  # Define the model name for this Odoo model
    _inherit = ["nafaes.api.mixin", "mail.thread",
                "mail.activity.mixin"]  # Inherit from API mixin and mail mixins for extended functionalities
    _description = "Nafaes Purchase Order"  # Provide a description for the model
    _rec_name = 'partner_id'  # Set the field used as the display name for records of this model
    _order = 'id desc'  # Set the default ordering for records by descending order of the ID

    partner_id = fields.Many2one('res.partner', readonly=True, states={'draft': [
        ('readonly', False)]})  # Many2one field linking to the 'res.partner' model, editable only in draft state
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.ref(
        'base.SAR'))  # Many2one field for currency, defaulting to 'SAR' currency
    amount = fields.Monetary(readonly=True, states={
        'draft': [('readonly', False)]})  # Monetary field for the amount, editable only in draft state
    date = fields.Date(default=lambda self: fields.Date.today(), readonly=True, states={
        'draft': [('readonly', False)]})  # Date field, defaulting to today's date and editable only in draft state

    # API fields
    uuid_po = fields.Char('UUID PO', readonly=True,
                          tracking=True)  # Char field for storing UUID for purchase order, readonly and tracked
    uuid_to = fields.Char('UUID TO', readonly=True,
                          tracking=True)  # Char field for storing UUID for transfer order, readonly and tracked
    uuid_so = fields.Char('UUID SO', readonly=True,
                          tracking=True)  # Char field for storing UUID for sales order, readonly and tracked
    purchaser = fields.Char(default='Fuel Finance Company')  # Char field for the purchaser, default value provided
    currency = fields.Char(
        related='currency_id.name')  # Char field to display the name of the currency related to 'currency_id'
    valueDate = fields.Char(readonly=True)  # Char field for value date, readonly
    counterPartyAccount = fields.Char(string='Counter Party Account', readonly=True, states={
        'draft': [('readonly', False)]})  # Char field for counterparty account, editable only in draft state
    counterPartyName = fields.Char(string='Counter Party Name', readonly=True, states={
        'draft': [('readonly', False)]})  # Char field for counterparty name, editable only in draft state
    counterPartyTelephone = fields.Char('Counter Party Telephone', readonly=True, states={
        'draft': [('readonly', False)]})  # Char field for counterparty telephone, editable only in draft state
    referenceNo = fields.Char('Nafaes Reference', readonly=True)  # Char field for Nafaes reference number, readonly
    state = fields.Selection([
        ('draft', 'Draft'),  # State indicating the order is in draft stage
        ('waiting_po', 'Waiting PO'),  # State indicating the order is waiting for a PO
        ('po', 'PO'),  # State indicating the order is in PO stage
        ('waiting_to', 'Waiting TO'),  # State indicating the order is waiting for a TO
        ('to', 'TO'),  # State indicating the order is in TO stage
        ('waiting_so', 'Waiting SO'),  # State indicating the order is waiting for a SO
        ('so', 'SO'),  # State indicating the order is in SO stage
        ('co', 'Canceled'),  # State indicating the order has been canceled
    ], default='draft', tracking=True)  # Default state is 'draft' and the state is tracked
    api_log_ids = fields.One2many('nafaes.api.log',
                                  compute='_compute_api_log_ids')  # One2many field to link API logs related to this purchase order
    api_error = fields.Char(readonly=True)  # Char field to store API error messages, readonly
    error_invisible = fields.Boolean(
        compute='_compute_error_invisible')  # Boolean field to determine if error message should be invisible
    order_result_ids = fields.One2many('nafaes.order.result',
                                       'purchase_order_id')  # One2many field to link order results related to this purchase order

    # Fields related to the order result
    order_result_id = fields.Many2one('nafaes.order.result',
                                      compute='_compute_order_result_id')  # Many2one field to link the primary order result
    transactionReference = fields.Char('Reference',
                                       related='order_result_id.transactionReference')  # Char field for transaction reference from the order result
    commodityName = fields.Char(
        related='order_result_id.commodityName')  # Char field for commodity name from the order result
    result_amount = fields.Monetary(
        related='order_result_id.amount')  # Monetary field for the amount from the order result
    unit = fields.Char(related='order_result_id.unit')  # Char field for unit from the order result
    executingUnit = fields.Char(
        related='order_result_id.executingUnit')  # Char field for executing unit from the order result
    quantity = fields.Char(related='order_result_id.quantity')  # Char field for quantity from the order result
    commission = fields.Char(related='order_result_id.commission')  # Char field for commission from the order result
    comm_currency_id = fields.Many2one(
        related='order_result_id.comm_currency_id')  # Many2one field for commission currency from the order result
    certificateNo = fields.Char('Certificate No',
                                related='order_result_id.certificateNo')  # Char field for certificate number from the order result
    attribute1 = fields.Char(related='order_result_id.attribute1')  # Char field for attribute1 from the order result
    attribute2 = fields.Char(related='order_result_id.attribute2')  # Char field for attribute2 from the order result
    attribute3 = fields.Char(related='order_result_id.attribute3')  # Char field for attribute3 from the order result
    result_date = fields.Datetime(string='Execution Date',
                                  related='order_result_id.date')  # Datetime field for execution date from the order result
    loan_ids = fields.One2many('loan.order',
                               'nafaes_order_id')  # One2many field to link loan orders related to this purchase order

    po_user_id = fields.Many2one('res.users', 'Purchased by')  # Many2one field for the user who purchased the order
    so_user_id = fields.Many2one('res.users', 'Sold by')  # Many2one field for the user who sold the order

    def _compute_api_log_ids(self):
        """Compute the API log IDs related to this purchase order."""
        for r in self:
            r.api_log_ids = self.env['nafaes.api.log'].search([('res_id', '=', r.id), (
            'res_model', '=', r._name)])  # Search for API logs related to the current purchase order

    def _compute_order_result_id(self):
        """Compute the order result ID related to this purchase order."""
        for r in self:
            r.order_result_id = r.order_result_ids and r.order_result_ids[
                0] or r.order_result_ids  # Set the first order result if available

    @api.depends('api_error')
    def _compute_error_invisible(self):
        """Compute if the error message should be invisible."""
        for r in self:
            r.error_invisible = not bool(
                r.api_error)  # Set the error_invisible field based on the presence of api_error

    def get_partner_mobile(self, partner):
        """Retrieve the mobile number of the partner."""
        res = ''  # Initialize result as an empty string
        if self.partner_id:  # Check if partner_id is set
            phone = self.partner_id.phone  # Retrieve the phone number of the partner
            if phone:  # If phone number is present
                phone = phone.replace(' ', '')  # Remove spaces from phone number
                res = phone[-10:]  # Extract the last 10 digits of the phone number
        return res  # Return the extracted mobile number

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """Update counterparty fields when the partner changes."""
        if self.partner_id:  # Check if partner_id is set
            date_prefix = date.today().strftime('%Y%m%d')  # Get today's date as a prefix
            self.counterPartyTelephone = self.get_partner_mobile(
                self.partner_id)  # Set counterPartyTelephone using get_partner_mobile method
            self.counterPartyAccount = f'{date_prefix}{self.partner_id.id}'  # Set counterPartyAccount using date_prefix and partner_id
            self.counterPartyName = f'{date_prefix}{self.partner_id.id}'  # Set counterPartyName using date_prefix and partner_id

    def handle_api_response(self, response, success_values, set_reference=False):
        """Handle the response from the API."""
        values = success_values  # Initialize values with success_values
        self.ensure_one()  # Ensure that only one record is processed
        if response['status'] == 'success':  # Check if the API response status is success
            if set_reference:  # If set_reference is True
                values.update({
                    'referenceNo': response['response'][0]['referenceNo'],  # Update referenceNo with response data
                })
            values.update({
                'api_error': False,  # Clear any previous API error
            })
        else:
            error_message = ', '.join(response['header']['errorMessages'])  # Join error messages from response
            for loan_id in self.loan_ids:  # Iterate over related loan orders
                responsible_user = self.so_user_id or self.po_user_id  # Get the responsible user (sold by or purchased by)
                loan_id.activity_schedule_nafaes_error(responsible_user,
                                                       error_message)  # Schedule an error activity for the loan order
            values = {  # Update values with error information
                'api_error': error_message,  # Set api_error with the error message
            }
        self.write(values)  # Write the updated values to the record

    def action_refresh_commodities(self):
        """Refresh the list of commodities."""
        self.env[
            'nafaes.commodity'].action_refresh_commodities()  # Call action_refresh_commodities on the 'nafaes.commodity' model

    def action_submit(self):
        """Submit the purchase order."""
        self.ensure_one()  # Ensure that only one record is processed
        self.po_user_id = self.env.user  # Set the po_user_id to the current user
        if self.state not in ['draft']:  # Check if the state is not 'draft'
            raise UserError('Invalid Operation, Nafaes order is not draft')  # Raise an error if the state is invalid
        if not self.date:  # Check if date is not set
            raise UserError('Please select a date')  # Raise an error if no date is provided
        if not self.amount:  # Check if amount is not set
            raise UserError('Please enter amount')  # Raise an error if no amount is provided
        self.valueDate = self.date.strftime("%Y%m%d")  # Set valueDate with the formatted date
        if self.referenceNo:  # Check if referenceNo is already set
            raise UserError(
                f'PO already has reference {self.referenceNo}')  # Raise an error if referenceNo is already present
        response = self.nafaes_purchase_order(order_id=self)  # Call nafaes_purchase_order method to get response
        success_values = {
            'state': 'waiting_po',  # Set state to 'waiting_po' if the API call is successful
        }
        self.handle_api_response(response, success_values, set_reference=True)  # Handle the API response

    def action_transfer(self):
        """Transfer the purchase order."""
        self.ensure_one()  # Ensure that only one record is processed
        if self.state not in ['po']:  # Check if the state is not 'po'
            raise UserError('Invalid Operation, Nafaes order is not in PO')  # Raise an error if the state is invalid
        response = self.nafaes_transfer(self)  # Call nafaes_transfer method to get response
        success_values = {
            'state': 'waiting_to',  # Set state to 'waiting_to' if the API call is successful
        }
        self.handle_api_response(response, success_values)  # Handle the API response

    def action_sell(self):
        """Sell the purchase order."""
        self.ensure_one()  # Ensure that only one record is processed
        if self.state not in ['to']:  # Check if the state is not 'to'
            raise UserError('Invalid Operation, Nafaes order is not in TO')  # Raise an error if the state is invalid
        response = self.nafaes_sell(order_id=self)  # Call nafaes_sell method to get response
        self.so_user_id = self.env.user  # Set the so_user_id to the current user
        success_values = {
            'state': 'waiting_so',  # Set state to 'waiting_so' if the API call is successful
        }
        self.handle_api_response(response, success_values)  # Handle the API response

    def action_cancel(self):
        """Cancel the purchase order."""
        for record in self:
            record.ensure_one()  # Ensure single record processing
            response = record.nafaes_cancel(order_id=record)  # Call nafaes_cancel method to get response
            success_values = {
                'state': 'co',  # Set state to 'co' if the API call is successful
            }
            record.handle_api_response(response, success_values)  # Handle the API response

    def _check_manual_rights(self):
        """Check if the user has manual rights to perform an operation."""
        if not self.user_has_groups('base.group_system'):  # Check if the user does not have the system admin group
            raise AccessDenied()  # Raise an AccessDenied exception if user lacks rights

    def action_order_result(self):
        """Get the order result from the API."""
        self.nafaes_order_result(self)  # Call nafaes_order_result method to get the result

    def action_manual_co(self):
        """Manually cancel the purchase order."""
        self._check_manual_rights()  # Check if the user has manual rights
        self.state = 'co'  # Set state to 'co' to indicate cancellation

    def action_draft(self):
        """Set the purchase order state to draft."""
        self.ensure_one()  # Ensure that only one record is processed
        self.state = 'draft'  # Set state to 'draft'
