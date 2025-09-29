from odoo import api, fields, models, _  # Import Odoo modules for API, fields, models, and translation


class loan_order(models.Model):
    _inherit = 'loan.order'  # Inherit from the existing 'loan.order' model
    _description = "Inherit from Loan module"  # Provide a description for the model extension
    rosom_bill_error = fields.Boolean(string="Rosom Bill Error", default=False, store=True)
    rosom_bill_id = fields.Many2one('rosom.bill',
                                    compute='_compute_rosom_bill_id')  # Define a Many2one field related to 'rosom.bill', computed by '_compute_rosom_bill_id'
    rosom_number = fields.Char('Sadad Number',
                               related='rosom_bill_id.SADADNumber')  # Define a Char field that retrieves the 'SADADNumber' from the related 'rosom.bill'
    invoice = fields.Char(string='Invoice Id',related='rosom_bill_id.InvoiceId')
    @api.depends('rosom_bill_id',
                 'rosom_number')  # Decorator to specify that this method depends on 'rosom_bill_id' and 'rosom_number'
    def remove_rosom_value(self):
        """
        Remove the values of 'rosom_bill_id' and 'rosom_number' fields.
        This method sets these fields to False for all records.
        """
        for rec in self:
            rec.rosom_bill_id = False  # Clear the 'rosom_bill_id' field
            rec.rosom_number = False  # Clear the 'rosom_number' field

    @api.depends('rosom_bill_id',
                 'rosom_number')  # Decorator to specify that this method depends on 'rosom_bill_id' and 'rosom_number'
    def delete_rosom_number(self):
        """
        Placeholder method for future functionality.
        Currently does nothing.
        """
        pass

    @api.depends('name')  # Decorator to specify that this method depends on the 'name' field
    def _compute_rosom_bill_id(self):
        """
        Compute the 'rosom_bill_id' field based on the 'loan_id'.
        This method searches for a 'rosom.bill' record related to the current loan order.
        """
        for r in self:
            r.rosom_bill_id = self.env['rosom.bill'].search([('loan_id', '=', r.id)],
                                                            limit=1)  # Search for the 'rosom.bill' record related to the current loan order

    def _create_rosom(self):
        """
        Create a 'rosom.bill' record if 'rosom_bill_id' is not set.
        Calls 'rosom_create_bill' method to create the bill.
        """
        self.ensure_one()  # Ensure that this method is called on a single record
        # if not self.rosom_bill_id:  # Check if 'rosom_bill_id' is not set
        self.env['rosom.bill'].rosom_create_bill(self)  # Call 'rosom_create_bill' method to create the bill

    def _create_rosom_bills(self):
        self.env['rosom.bill'].rosom_create_bills(self)

    def action_call_done(self):
        """
        Override the 'action_call_done' method from the parent class.
        Currently, it just calls the parent method and returns its result.
        """
        res = super(loan_order, self).action_call_done()  # Call the parent method
        return res  # Return the result of the parent method

    def action_crate_rosom(self):
        """
        Debug method to create a 'rosom.bill' record.
        Prints a debug message and calls '_create_rosom' method.
        """
        print('++++++++++++++++++++++++++++')  # Print a debug message
        self._create_rosom()  # Call the method to create a 'rosom.bill'


    def action_create_multiple_rosom_bills(self):
        """
        Debug method to create a 'rosom.bill' record.
        Prints a debug message and calls '_create_rosom' method.
        """
        print("Number of loans selected: ", len(self))
        self._create_rosom_bills()
