import json  # Importing JSON module for handling JSON data
from datetime import datetime  # Importing Datetime module for date and time manipulation
from odoo import api, fields, models, _  # Importing necessary classes and functions from Odoo
from odoo.exceptions import UserError, AccessDenied  # Importing exceptions from Odoo

from .api_mixin import NAFAES_TOKEN  # Importing the NAFAES_TOKEN from api_mixin


class NafaesOrderResult(models.Model):
    _name = "nafaes.order.result"  # Defining the model name
    _description = "Nafaes Order Result"  # Setting the model description
    _order = "id desc"  # Setting the default order for records
    rec_name = "transactionReference"  # Setting the display name for records

    purchase_order_id = fields.Many2one('nafaes.purchase.order',
                                        readonly=True)  # Defining a Many2one field for purchase order
    transactionReference = fields.Char('Transaction Reference',
                                       readonly=True)  # Defining a Char field for transaction reference
    orderType = fields.Char('Order Type', readonly=True)  # Defining a Char field for order type
    commodityName = fields.Char('Commodity Name', readonly=True)  # Defining a Char field for commodity name
    beneficiary = fields.Char(readonly=True)  # Defining a Char field for beneficiary
    currency_id = fields.Many2one('res.currency', readonly=True)  # Defining a Many2one field for currency
    amount = fields.Monetary(readonly=True)  # Defining a Monetary field for amount
    executionDate = fields.Char(readonly=True)  # Defining a Char field for execution date
    executionTime = fields.Char(readonly=True)  # Defining a Char field for execution time
    unit = fields.Char(readonly=True)  # Defining a Char field for unit
    executingUnit = fields.Char(readonly=True)  # Defining a Char field for executing unit
    quantity = fields.Char(readonly=True)  # Defining a Char field for quantity
    commission = fields.Char(currency_field='comm_currency_id', readonly=True)  # Defining a Char field for commission
    comm_currency_id = fields.Many2one('res.currency',
                                       readonly=True)  # Defining a Many2one field for commission currency
    secretToken = fields.Char(readonly=True)  # Defining a Char field for secret token
    certificateNo = fields.Char(readonly=True)  # Defining a Char field for certificate number
    attribute1 = fields.Char(readonly=True)  # Defining a Char field for attribute 1
    attribute2 = fields.Char(readonly=True)  # Defining a Char field for attribute 2
    attribute3 = fields.Char(readonly=True)  # Defining a Char field for attribute 3
    date = fields.Datetime('Execution Date', readonly=True)  # Defining a Datetime field for execution date
    json = fields.Char(readonly=True)  # Defining a Char field for JSON data

    def handle_request(self, payload, path, secretKey, enable_log=True, log_values={}, data_key='request'):
        """Handles the incoming request payload, validates the secret key, processes the payload, and logs the results."""

        log_id = log_obj = self.env['nafaes.api.log']  # Initializing the log object

        if enable_log:  # If logging is enabled
            log_values.update({
                'request': json.dumps(payload),  # Log the request payload
                'url': path,  # Log the request URL
                'type': 'webhook',  # Log the request type as webhook
            })
            log_id = log_obj.create_log(log_values)  # Create a log entry

        if secretKey != NAFAES_TOKEN:  # If the secret key does not match
            return False, log_id  # Return False and the log ID

        env_obj = self  # Set the current environment object
        order_ids = env_obj.env['nafaes.purchase.order']  # Initialize the order IDs

        for item in payload[data_key]:  # Iterate over each item in the payload
            currency_id = env_obj.env['res.currency'].search(
                [('name', '=', item.get('currency', ''))])  # Get the currency ID
            comm_currency_id = env_obj.env['res.currency'].search(
                [('name', '=', item.get('commCurrency', ''))])  # Get the commission currency ID

            referenceNo = item.get('transactionReference', '')  # Get the transaction reference number
            request_uuid = payload.get('header', {}).get('uuid', '')  # Get the request UUID
            domain = [
                '|',
                ('uuid_po', '=', request_uuid),
                '|',
                ('uuid_to', '=', request_uuid),
                ('uuid_so', '=', request_uuid),
            ]  # Define the domain for searching purchase orders
            order_id = env_obj.env['nafaes.purchase.order'].search(domain)  # Search for the purchase order
            if order_id:
                order_ids += order_id  # Add the order ID to the order IDs
            else:
                raise UserError(f'Order not found with domain {domain}')  # Raise an error if no order is found

            date_value = False  # Initialize the date value
            try:
                date_value = datetime.strptime(f'{item.get("executionDate", "")} {item.get("executionTime", "")}',
                                               '%Y%m%d %H%M%S')  # Parse the execution date and time
            except Exception:
                pass  # Ignore the exception

            values = {
                'purchase_order_id': order_id.id,  # Set the purchase order ID
                "transactionReference": referenceNo,  # Set the transaction reference
                "orderType": item.get('orderType', ''),  # Set the order type
                "commodityName": item.get('commodityName', ''),  # Set the commodity name
                "beneficiary": item.get('beneficiary', ''),  # Set the beneficiary
                "currency_id": currency_id.id,  # Set the currency ID
                "amount": float(item.get('amount', '0')),  # Set the amount
                "executionDate": item.get('executionDate', ''),  # Set the execution date
                "executionTime": item.get('executionTime', ''),  # Set the execution time
                "unit": item.get('unit', ''),  # Set the unit
                "executingUnit": item.get('executingUnit', ''),  # Set the executing unit
                "quantity": float(item.get('quantity', '0')),  # Set the quantity
                "commission": float(item.get('commission', '0')),  # Set the commission
                "comm_currency_id": comm_currency_id.id,  # Set the commission currency ID
                "secretToken": item.get('secretToken', ''),  # Set the secret token
                "certificateNo": item.get('certificateNo', ''),  # Set the certificate number
                "attribute1": item.get('attribute1', ''),  # Set attribute 1
                "attribute2": item.get('attribute2', ''),  # Set attribute 2
                "attribute3": item.get('attribute3', ''),  # Set attribute 3
                "date": date_value,  # Set the date value
                "json": json.dumps(payload),  # Set the JSON payload
            }

            orderType = values['orderType'].lower() or ''  # Get the order type in lowercase
            if orderType == 'po' and order_id.state == 'waiting_po':  # If order type is purchase order and state is waiting
                order_id.state = orderType  # Update the state
            if orderType == 'to' and order_id.state == 'waiting_to':  # If order type is transfer order and state is waiting
                order_id.state = orderType  # Update the state
            if orderType == 'so' and order_id.state == 'waiting_so':  # If order type is sale order and state is waiting
                order_id.state = orderType  # Update the state

            if orderType == 'so' and order_id:  # If order type is sale order and order ID exists
                for loan_id in order_id.loan_ids:  # Iterate over loan IDs
                    loan_id.activity_schedule_nafaes_sell(order_id.so_user_id)  # Schedule the sale activity

            env_obj.sudo().create(values)  # Create the order result
            # if order_id.state == 'po' and orderType == 'po':  # If state is purchase order and order type is purchase order
            #     try:
            #         order_id.action_transfer()  # Call the action_transfer method
            #     except Exception:
            #         # We can retry later
            #         pass

        first_order_id = env_obj.env['nafaes.purchase.order']  # Initialize the first order ID
        if order_ids:
            first_order_id = order_ids[0]  # Set the first order ID

        if log_id and enable_log:  # If log ID exists and logging is enabled
            log_id.update_log({
                'partner_id': first_order_id.partner_id.id,  # Update log with partner ID
                'res_id': first_order_id.id,  # Update log with resource ID
                'res_model': first_order_id._name,  # Update log with resource model
                'res_ids': str(order_ids.ids),  # Update log with resource IDs
            })

        return True, log_id  # Return True and the log ID
