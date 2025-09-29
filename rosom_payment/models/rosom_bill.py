import logging
import random
from datetime import datetime
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)  # Configure logger for this module


class rosom_bill(models.Model):
    _name = "rosom.bill"  # Define the model name
    _inherit = ["rosom.api.mixin",
                "mail.thread"]  # Inherit from 'rosom.api.mixin' and 'mail.thread' for additional functionality
    _description = "Rosom Bill"  # Provide a description for the model
    _order = "id desc"  # Default ordering of records by ID in descending order
    _rec_name = 'SADADNumber'  # Default display name of the record

    # SQL constraint to ensure that 'InvoiceId' is unique
    _sql_constraints = [
        ('unique_InvoiceId', 'unique(InvoiceId)', 'Duplicate InvoiceId')
    ]

    company_id = fields.Many2one('res.company', default=lambda
        self: self.env.user.company_id)  # Many2one relationship with 'res.company', default to current user's company
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.ref(
        'base.SAR'))  # Many2one relationship with 'res.currency', default to Saudi Riyal
    loan_id = fields.Many2one('loan.order', tracking=True,domain=[('state', '=', 'active')])  # Many2one relationship with 'loan.order', tracking changes
    loan_ref = fields.Char(related='loan_id.seq_num')  # Char field related to 'seq_num' of 'loan.order'

    InvoiceId = fields.Char(string='InvoiceId', tracking=True)  # Char field for Invoice ID
    InvoiceStatus = fields.Char(string='InvoiceStatus', tracking=True)  # Char field for Invoice Status
    DisplayInfo = fields.Char(string='DisplayInfo', tracking=True)  # Char field for Display Info
    AmountDue = fields.Monetary(string='AmountDue', tracking=True,
                                currency_field='currency_id')  # Monetary field for Amount Due, with currency field reference
    MinPartialAmount = fields.Monetary(string='MinPartialAmount', tracking=True,
                                       currency_field='currency_id')  # Monetary field for Minimum Partial Amount
    CreateDate = fields.Datetime(string='CreateDate', tracking=True)  # Datetime field for Create Date
    ExpiryDate = fields.Datetime(string='ExpiryDate', tracking=True)  # Datetime field for Expiry Date
    SADADNumber = fields.Char(string='SADADNumber', tracking=True)  # Char field for SADAD Number

    payment_ids = fields.One2many('rosom.payment', 'bill_id')  # One2many relationship with 'rosom.payment'
    log_ids = fields.One2many('rosom.api.log',
                              compute='_compute_log_ids')  # One2many relationship with 'rosom.api.log', computed by '_compute_log_ids'

    # SQL constraint to ensure that 'SADADNumber' is unique
    _sql_constraints = [
        ('unique_SADADNumber', 'unique(SADADNumber)', 'Duplicate SADAD Number')
    ]

    @api.depends('loan_id')  # Specify that this method depends on the 'loan_id' field
    def _compute_log_ids(self):
        """
        Compute the 'log_ids' field based on related 'rosom.api.log' records.
        Searches for logs where the 'res_id' matches the current record's ID and 'res_model' matches the model name.
        """
        for r in self:
            r.log_ids = self.env['rosom.api.log'].search([('res_id', '=', r.id), ('res_model', '=', r._name)])


class rosom_payment(models.Model):
    _name = "rosom.payment"  # Define the model name
    _inherit = 'mail.thread'  # Inherit from 'mail.thread' for activity tracking
    _description = "Rosom Payment"  # Provide a description for the model
    _order = "PaymentDate"  # Default ordering of records by Payment Date
    _rec_name = 'PaymentId'  # Default display name of the record

    # SQL constraint to ensure that 'PaymentId' is unique
    _sql_constraints = [
        ('unique_payment_id', 'unique(PaymentId)', 'Duplicate PaymentId')
    ]

    bill_id = fields.Many2one('rosom.bill')  # Many2one relationship with 'rosom.bill'
    loan_id = fields.Many2one(related='bill_id.loan_id')  # Many2one relationship with 'loan_id' of related 'rosom.bill'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.ref(
        'base.SAR'))  # Many2one relationship with 'res.currency', default to Saudi Riyal
    MerchantId = fields.Char(string='MerchantId', tracking=True)  # Char field for Merchant ID
    InvoiceId = fields.Char(string='InvoiceId', tracking=True)  # Char field for Invoice ID
    PaymentId = fields.Integer(string='PaymentId', tracking=True)  # Integer field for Payment ID
    SADADTransactionId = fields.Char(string='SADADTransactionId', tracking=True)  # Char field for SADAD Transaction ID
    BankTransactionId = fields.Char(string='BankTransactionId', tracking=True)  # Char field for Bank Transaction ID
    PaidAmount = fields.Monetary(string='PaidAmount', tracking=True,
                                 currency_field='currency_id')  # Monetary field for Paid Amount
    PaymentDate = fields.Datetime(string='PaymentDate', tracking=True)  # Datetime field for Payment Date
    SADADNumber = fields.Char(string='SADADNumber', tracking=True)  # Char field for SADAD Number
    BankName = fields.Char(string='BankName', tracking=True)  # Char field for Bank Name
    DistrictCode = fields.Char(string='DistrictCode', tracking=True)  # Char field for District Code
    BranchCode = fields.Char(string='BranchCode', tracking=True)  # Char field for Branch Code
    AccessChannel = fields.Char(string='AccessChannel', tracking=True)  # Char field for Access Channel
    PmtMethod = fields.Char(string='PmtMethod', tracking=True)  # Char field for Payment Method
    PmtType = fields.Char(string='PmtType', tracking=True)  # Char field for Payment Type
    ServiceType = fields.Char(string='ServiceType', tracking=True)  # Char field for Service Type
    payment_id_char = fields.Char('PaymentId',
                                  compute='_compute_payment_id_char')  # Char field for Payment ID as a string, computed by '_compute_payment_id_char'
    @api.depends('PaymentId')  # Specify that this method depends on the 'PaymentId' field
    def _compute_payment_id_char(self):
        """
        Compute the 'payment_id_char' field from the 'PaymentId' field.
        Converts 'PaymentId' to a string representation.
        """
        for r in self:
            r.payment_id_char = str(r.PaymentId)  # Set 'payment_id_char' to the string representation of 'PaymentId'

    def post_create(self,is_reschedule=False):
        """
        Perform additional actions after the record is created.
        Updates installment payment statuses based on PaidAmount.
        """
        self.ensure_one()
        activity_object = self.env['mail.activity']
        # Determine field names dynamically based on is_reschedule
        installment_field = 'reschedule_installment_ids' if is_reschedule else 'installment_ids'
        loan_field = 'reschedule_loan_id' if is_reschedule else 'loan_id'

        # Fetch all related installments ordered by sequence
        installments = getattr(self, loan_field).mapped(installment_field).sorted(key=lambda x: x.date)
        remaining_paid_amount = self.PaidAmount  # Amount available for payments
        paymendate = self.PaymentDate
        print(installments,"***************",remaining_paid_amount)
        for installment in installments:
            if remaining_paid_amount <= 0:
                break

            due_amount = round(installment.installment_amount - (
                        installment.amount_paid or 0) ,2)
            if remaining_paid_amount >= due_amount:
                installment.write({
                    'amount_paid': installment.installment_amount,
                    'remaining_amount': 0,
                    'state': 'paid',
                    'payment_date': paymendate,
                })
                remaining_paid_amount -= due_amount
            elif remaining_paid_amount < due_amount:
                # Partial payment case
                installment.write({
                    'amount_paid': (installment.amount_paid or 0) + remaining_paid_amount,
                    'remaining_amount': due_amount - remaining_paid_amount,
                    'state': 'partial',  
                    'payment_date': paymendate,
                })
                remaining_paid_amount = 0  # All paid amount is allocated
                break  # Stop after partial payment
            # else:
            #     # Full payment case: pay the full installment and move to the next
            #     installment.write({
            #         'amount_paid': installment.installment_amount,
            #         'remaining_amount': 0,
            #         'state': 'paid',  # Mark installment as fully paid
            #     })
            #     if not installment.payment_date:
            #         print("no date in payment date ")
            #         installment.write({'payment_date':paymendate})
            #     remaining_paid_amount -= due_amount  # Deduct paid amount from remaining

        # If there's still a significant amount difference, create a mail activity
        first_installment = installments[0] if installments else None
        diff = abs(self.PaidAmount - (first_installment.installment_amount if first_installment else 0))

        if diff >= 1:
            users = self.env.ref('loan.group_accounting_move').users.ids
            user_id = self.env.user.id
            random_id = user_id
            while random_id == user_id:
                random_id = random.choice(users)

            activity_values = {
                'res_model': getattr(self, loan_field)._name,
                'res_model_id': self.env.ref('loan.model_loan_order').id,
                'res_id': getattr(self, loan_field).id,
                'summary': "Check Amount",
                'note': "Please check the amount of the payment.",
                'date_deadline': datetime.today(),
                'user_id': random_id,
                'activity_type_id': self.env.ref('loan.mail_activity_amount_difference').id,
            }

            # _logger.info('#activity_values')
            # _logger.info(activity_values)

            activity_object.create(activity_values)

    # 02/02/2025 last edit
    # def post_create(self, is_reschedule=False):
    #     """
    #     Perform additional actions after the record is created.
    #     Creates a mail activity if the difference between PaidAmount and the installment amount is significant.
    #     """
    #     self.ensure_one()  # Ensure this method is called on a single record
    #     activity_object = self.env['mail.activity']  # Get the 'mail.activity' model
    #
    #     # Dynamically determine the field names based on the is_reschedule flag
    #     installment_field = 'reschedule_installment_ids' if is_reschedule else 'installment_ids'
    #     loan_field = 'reschedule_loan_id' if is_reschedule else 'loan_id'
    #
    #     # Get the related installments and calculate the difference
    #     first_installment_id = getattr(self, loan_field).mapped(installment_field)  # Get all related installments
    #     first_installment_id = first_installment_id and first_installment_id[
    #         0] or first_installment_id  # Get the first installment if it exists
    #     diff = abs(self.PaidAmount - (first_installment_id.installment_amount or 0))  # Calculate the difference
    #
    #     if diff >= 1:  # If the difference is 1 or more
    #         # Get users from the 'loan.group_accounting_move' group
    #         users = self.env.ref('loan.group_accounting_move').users.ids
    #         user_id = self.env.user.id  # Get the current user's ID
    #         random_id = user_id
    #         while random_id == user_id:  # Ensure a different user ID is selected
    #             random_id = random.choice(users)
    #
    #         # Prepare activity values
    #         activity_values = {
    #             'res_model': getattr(self, loan_field)._name,  # Model of the related record
    #             'res_model_id': self.env.ref('loan.model_loan_order').id,  # ID of the related model
    #             'res_id': getattr(self, loan_field).id,  # ID of the related record
    #             'summary': "Check Amount",  # Summary of the activity
    #             'note': "Please check the amount of the payment.",  # Note for the activity
    #             'date_deadline': datetime.today(),  # Deadline for the activity
    #             'user_id': random_id,  # User assigned to the activity
    #             'activity_type_id': self.env.ref('loan.mail_activity_amount_difference').id,  # Activity type ID
    #         }
    #
    #         # Log activity values for debugging
    #         _logger.info('#activity_values')
    #         _logger.info(activity_values)
    #
    #         # Create the mail activity
    #         self.env['mail.activity'].create(activity_values)

    # old code
    # def post_create(self):
    #     """
    #     Perform additional actions after the record is created.
    #     Creates a mail activity if the difference between PaidAmount and the installment amount is significant.
    #     """
    #     self.ensure_one()  # Ensure this method is called on a single record
    #     activity_object = self.env['mail.activity']  # Get the 'mail.activity' model
    #     first_installment_id = self.loan_id.installment_ids  # Get the installment IDs related to the loan
    #     first_installment_id = first_installment_id and first_installment_id[
    #         0] or first_installment_id  # Get the first installment if it exists
    #     diff = abs(self.PaidAmount - (
    #             first_installment_id.installment_amount or 0))  # Calculate the difference between PaidAmount and installment amount
    #     if diff >= 1:  # If the difference is 1 or more
    #         users = self.env.ref(
    #             'loan.group_accounting_move').users.ids  # Get user IDs from the 'loan.group_accounting_move' group
    #         user_id = self.env.user.id  # Get the current user's ID
    #         random_id = user_id
    #         while random_id == user_id:  # Ensure a different user ID is selected
    #             random_id = random.choice(users)
    #         activity_values = {
    #             'res_model': self.loan_id._name,  # Model of the related record
    #             'res_model_id': self.env.ref('loan.model_loan_order').id,  # ID of the related model
    #             'res_id': self.loan_id.id,  # ID of the related record
    #             'summary': "Check Amount",  # Summary of the activity
    #             'note': "Please check the amount of the payment.",  # Note for the activity
    #             'date_deadline': datetime.today(),  # Deadline for the activity
    #             'user_id': random_id,  # User assigned to the activity
    #             'activity_type_id': self.env.ref('loan.mail_activity_amount_difference').id,  # Activity type ID
    #         }
    #         _logger.info('#activity_values')  # Log the activity values
    #         _logger.info(activity_values)  # Log the activity values
    #         self.env['mail.activity'].create(activity_values)  # Create the mail activity
