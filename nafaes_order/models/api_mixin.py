import os  # Importing OS module for environment variables
import uuid  # Importing UUID module for generating unique identifiers
import requests  # Importing Requests module for making HTTP requests
import json  # Importing JSON module for handling JSON data
import datetime  # Importing Datetime module for date and time manipulation
import logging  # Importing Logging module for logging errors and information
from odoo import api, fields, models, registry, _, SUPERUSER_ID  # Importing necessary classes and functions from Odoo
from odoo.exceptions import UserError  # Importing UserError exception from Odoo

_logger = logging.getLogger(__name__)  # Initializing the logger

WEBHOOK_PATH = '/NafaesWebhook'  # Defining a constant for the webhook path
NAFAES_TOKEN = 'hQirnWKFBH%hHD3234fad$$hh'  # Defining a constant for the Nafaes token
TOKEN_KEY = 'nafaes.token'  # Defining a constant for the token key
TOKEN_EXPIRY_KEY = 'nafaes.token.expiry'  # Defining a constant for the token expiry key


class NafaesApiMixin(models.AbstractModel):  # Defining a new abstract model class for Nafaes API mixin
    _name = "nafaes.api.mixin"  # Setting the model name
    _description = "Nafaes Api Mixin"  # Setting the model description

    def get_base_url(self):  # Method to get the base URL from environment variables
        return os.getenv('NAFAES_URL', 'https://testapi.nafaes.com')  # Default to test URL if not set

    def get_common_headers(self, is_json=True):  # Method to get common headers for API requests
        content_type = 'application/json'  # Default content type
        if not is_json:  # If not JSON, set content type to form-urlencoded
            content_type = 'application/x-www-form-urlencoded'
        return {
            'Accept': 'application/json',  # Set accept header
            'Content-Type': content_type  # Set content type header
        }

    def _call_auth(self):  # Method to call the authentication API
        url = f'{self.get_base_url()}/oauth/token'  # Construct the authentication URL
        username = os.getenv('NAFAES_USERNAME', 'APINIG1120')  # Get username from environment variables
        password = os.getenv('NAFAES_PASSWORD', 'qs$9p3dfjb')  # Get password from environment variables
        client_id = os.getenv('NAFAES_CLIENT_ID', 'FFCSUD6432')  # Get client ID from environment variables
        client_secret = os.getenv('NAFAES_CLIENT_SECRET', 'hw3$mfjc4z')  # Get client secret from environment variables
        payload = f'grant_type=password&username={username}&password={password}&client_id={client_id}&client_secret={client_secret}'  # Construct the payload
        payload_to_log = payload.replace(username, '*' * 10)  # Mask the username in the payload
        payload_to_log = payload_to_log.replace(password, '*' * 10)  # Mask the password in the payload
        payload_to_log = payload_to_log.replace(client_id, '*' * 10)  # Mask the client ID in the payload
        payload_to_log = payload_to_log.replace(client_secret, '*' * 10)  # Mask the client secret in the payload
        headers = self.get_common_headers(is_json=False)  # Get common headers for form data
        log_values = {
            'request': payload_to_log,  # Log the masked payload
            'partner_id': False,  # No partner ID
            'url': url,  # Log the URL
            'type': 'auth',  # Log the type as authentication
        }
        log_obj = self.env['nafaes.api.log']  # Get the log object
        log_id = log_obj.create_log(log_values)  # Create a log entry
        response = requests.request("POST", url, headers=headers, data=payload)  # Send the POST request
        self._log_response(log_id, response)  # Log the response
        response = response.json()  # Parse the JSON response
        access_token = response.get('access_token', '')  # Get the access token
        expires_in_seconds = response.get('expires_in', 0)  # Get the expiry time
        nafaes_token_expiry = datetime.datetime.now() + datetime.timedelta(
            seconds=expires_in_seconds)  # Calculate the expiry date
        param_obj = self.env['ir.config_parameter'].sudo()  # Get the parameter object
        if access_token:  # If access token is available
            param_obj.set_param(TOKEN_EXPIRY_KEY, nafaes_token_expiry.isoformat())  # Set the token expiry parameter
            param_obj.set_param(TOKEN_KEY, access_token)  # Set the token parameter

        return access_token  # Return the access token

    def auth(self, try_old=True):  # Method to authenticate and get the token
        param_obj = self.env['ir.config_parameter'].sudo()  # Get the parameter object
        existing_token = param_obj.get_param(TOKEN_KEY)  # Get the existing token
        existing_token_expiry = param_obj.get_param(TOKEN_EXPIRY_KEY)  # Get the token expiry date
        use_old = False  # Initialize the flag to use old token
        if existing_token and existing_token_expiry and try_old:  # If existing token and expiry date are available
            expiry_date = datetime.datetime.fromisoformat(existing_token_expiry)  # Parse the expiry date
            expiry_date = expiry_date - datetime.timedelta(seconds=60 * 5)  # Subtract 5 minutes from expiry date
            if expiry_date > datetime.datetime.now():  # If token is still valid
                use_old = True  # Set the flag to use old token
        if use_old:  # If using old token
            access_token = existing_token  # Set access token to existing token
        else:  # If not using old token
            access_token = self._call_auth()  # Call authentication method to get new token

        return {
            'Authorization': f'Bearer {access_token}',  # Return the authorization header with access token
        }

    def get_language(self):  # Method to get the language setting
        arabic = "1"  # Define Arabic language code
        language = self.env['ir.config_parameter'].sudo().get_param('nafaes.language',
                                                                    arabic)  # Get the language parameter
        return language  # Return the language

    def _log_response(self, log_id, response):  # Method to log the response
        try:
            response_to_log = json.dumps(response.json())  # Try to parse and log the JSON response
        except Exception:
            response_to_log = response.text  # If JSON parsing fails, log the response text

        log_id.update_log({
            'response_status': response.status_code,  # Log the response status code
            'response': response_to_log,  # Log the response data
        })

    def nafaes_call_api(self, url, data, log_values={}, retry=True):  # Method to call the Nafaes API
        headers = self.get_common_headers()  # Get common headers
        auth_header = self.auth()  # Get the authentication header
        headers.update(auth_header)  # Update headers with authentication header
        log_values.update({
            'request': data,  # Update log values with request data
            'url': url,  # Update log values with URL
        })
        log_obj = self.env['nafaes.api.log']  # Get the log object
        log_id = log_obj.create_log(log_values)  # Create a log entry

        response = requests.request("POST", url, headers=headers, data=data)  # Send the POST request
        self._log_response(log_id, response)  # Log the response

        if response.status_code == 401 and retry:  # If response status is 401 (Unauthorized) and retry is True
            self.auth(try_old=False)  # Call authentication method with try_old as False
            return self.nafaes_call_api(url, data, retry=False)  # Retry the API call with retry as False

        return response.json()  # Return the JSON response

    def nafaes_get_available_commodities(self):  # Method to get available commodities from Nafaes
        url = f'{self.get_base_url()}/api/v2/avaliablecommoditieswithsource'  # Construct the URL

        payload = json.dumps({  # Construct the JSON payload
            "request": {
                "amount": "2000",
                "currency": "SAR",
                "lng": self.get_language(),
            }
        })
        log_values = {
            'partner_id': False,  # No partner ID
            'type': 'get_commodities',  # Set log type as get commodities
        }
        response = self.nafaes_call_api(url, payload, log_values)  # Call the API with payload and log values

    def get_webhook_url(self):  # Method to get the webhook URL
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url',
                                                                    'https://fuelfinance.sa')  # Get the base URL from parameters
        if base_url.startswith('http:'):  # If base URL starts with http
            base_url = base_url[:4] + 's' + base_url[4:]  # Change it to https

        webhook_path = '/NafaesWebhook'  # Define the webhook path
        return f'{base_url}{webhook_path}?secretKey={NAFAES_TOKEN}'  # Return the full webhook URL

    def nafaes_purchase_order(self, order_id):  # Method to create a purchase order
        url = f'{self.get_base_url()}/api/v2/purchaseorder'  # Construct the URL

        self.uuid_po = str(uuid.uuid4())  # Generate a UUID for the purchase order
        payload = json.dumps({  # Construct the JSON payload
            "header": {
                "uuid": self.uuid_po,
            },
            "push": {
                "callBackUrl": self.get_webhook_url(),
                "dataType": "json"
            },
            "request": [
                {
                    "commodityCode": 'PAC',
                    "purchaser": order_id.purchaser,
                    "currency": order_id.currency,
                    "purchaseAmount": order_id.amount,
                    "valueDate": order_id.valueDate,
                    "counterPartyAccount": order_id.counterPartyAccount,
                    "counterPartyName": order_id.counterPartyName,
                    "counterPartyTelephone": order_id.counterPartyTelephone,
                    "transactionType": "managed",
                    "lng": self.get_language(),
                }
            ]
        })

        log_values = {
            'partner_id': order_id.partner_id.id,  # Set partner ID
            'type': 'po',  # Set log type as purchase order
            'res_id': order_id.id,  # Set resource ID
            'res_model': order_id._name,  # Set resource model
        }

        response = self.nafaes_call_api(url, payload, log_values)  # Call the API with payload and log values
        return response  # Return the response

    def nafaes_transfer(self, order_id):  # Method to create a transfer order
        url = f'{self.get_base_url()}/api/v2/transferorder'  # Construct the URL

        self.uuid_to = str(uuid.uuid4())  # Generate a UUID for the transfer order
        payload = json.dumps({  # Construct the JSON payload
            "header": {
                "uuid": self.uuid_to,
            },
            "push": {
                "callBackUrl": self.get_webhook_url(),
                "dataType": "json"
            },
            "request": [
                {
                    "referenceNo": self.referenceNo,
                    "orderType": "TO",
                    "lng": self.get_language()
                }
            ]
        })

        log_values = {
            'partner_id': order_id.partner_id.id,  # Set partner ID
            'type': 'to',  # Set log type as transfer order
            'res_id': order_id.id,  # Set resource ID
            'res_model': order_id._name,  # Set resource model
        }
        response = self.nafaes_call_api(url, payload, log_values)  # Call the API with payload and log values

        return response  # Return the response

    def nafaes_sell(self, order_id):  # Method to create a sale order
        url = f'{self.get_base_url()}/api/v2/saleorder'  # Construct the URL

        self.uuid_so = str(uuid.uuid4())  # Generate a UUID for the sale order
        payload = json.dumps({  # Construct the JSON payload
            "header": {
                "uuid": self.uuid_so,
            },
            "push": {
                "callBackUrl": self.get_webhook_url(),
                "dataType": "json"
            },
            "request": [
                {
                    "referenceNo": order_id.referenceNo,
                    "orderType": "SO",
                    "lng": self.get_language()
                }
            ]
        })

        log_values = {
            'partner_id': order_id.partner_id.id,  # Set partner ID
            'type': 'so',  # Set log type as sale order
            'res_id': order_id.id,  # Set resource ID
            'res_model': order_id._name,  # Set resource model
        }
        response = self.nafaes_call_api(url, payload, log_values)  # Call the API with payload and log values

        return response  # Return the response

    def nafaes_cancel(self, order_id):  # Method to cancel an order
        url = f'{self.get_base_url()}/api/v2/cancelorder'  # Construct the URL

        payload = json.dumps({  # Construct the JSON payload
            "header": {
                "uuid": str(uuid.uuid4()),
            },
            "request": {
                "referenceNo": order_id.referenceNo,
                "orderType": "CO",
                "lng": self.get_language()
            }
        })

        log_values = {
            'partner_id': order_id.partner_id.id,  # Set partner ID
            'type': 'co',  # Set log type as cancel order
            'res_id': order_id.id,  # Set resource ID
            'res_model': order_id._name,  # Set resource model
        }
        response = self.nafaes_call_api(url, payload, log_values)  # Call the API with payload and log values

        return response  # Return the response

    def nafaes_order_result(self, order_id):  # Method to get the order result (long polling)
        url = f'{self.get_base_url()}/api/v2/orderresult'  # Construct the URL

        if order_id.state not in ['waiting_po', 'waiting_to', 'waiting_so']:  # If order state is not waiting
            raise UserError('Order is not in a waiting state')  # Raise an error

        if order_id.state in ['draft', 'waiting_po', 'po']:  # If order state is draft or waiting for purchase order
            uuid_value = order_id.uuid_po  # Set UUID to purchase order UUID
            orderType = 'PO'  # Set order type to purchase order
        if order_id.state in ['waiting_to', 'to']:  # If order state is waiting for transfer order
            uuid_value = order_id.uuid_to  # Set UUID to transfer order UUID
            orderType = 'TO'  # Set order type to transfer order
        if order_id.state in ['waiting_so', 'so']:  # If order state is waiting for sale order
            uuid_value = order_id.uuid_so  # Set UUID to sale order UUID
            orderType = 'SO'  # Set order type to sale order

        payload = json.dumps({  # Construct the JSON payload
            "header": {
                "uuid": uuid_value,
            },
            "request": [
                {
                    "referenceNo": order_id.referenceNo or '',
                    "orderType": orderType,
                    "lng": self.get_language()
                }
            ]
        })

        log_values = {
            'partner_id': order_id.partner_id.id,  # Set partner ID
            'type': 'result',  # Set log type as order result
            'res_id': order_id.id,  # Set resource ID
            'res_model': order_id._name,  # Set resource model
        }

        response = self.nafaes_call_api(url, payload, log_values)  # Call the API with payload and log values
        self.env['nafaes.order.result'].handle_request(response, url, NAFAES_TOKEN, enable_log=False,
                                                       data_key='response')  # Handle the response
# import os
# import uuid
# import requests
# import json
# import datetime
# import logging
# from odoo import api, fields, models, registry, _, SUPERUSER_ID
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
#
# WEBHOOK_PATH = '/NafaesWebhook'
# NAFAES_TOKEN = 'hQirnWKFBH%hHD3234fad$$hh'
# TOKEN_KEY = 'nafaes.token'
# TOKEN_EXPIRY_KEY = 'nafaes.token.expiry'
#
#
# class nafaes_api_mixin(models.AbstractModel):
#     _name = "nafaes.api.mixin"
#     _description = "Nafaes Api Mixin"
#
#     def get_base_url(self):
#         return os.getenv('NAFAES_URL', 'https://testapi.nafaes.com')
#
#     def get_common_headers(self, is_json=True):
#         content_type = 'application/json'
#         if not is_json:
#             content_type = 'application/x-www-form-urlencoded'
#         return {
#             'Accept': 'application/json',
#             'Content-Type': content_type
#         }
#
#     def _call_auth(self):
#         url = f'{self.get_base_url()}/oauth/token'
#         username = os.getenv('NAFAES_USERNAME', 'APINIG1120')
#         password = os.getenv('NAFAES_PASSWORD', 'qs$9p3dfjb')
#         client_id = os.getenv('NAFAES_CLIENT_ID', 'FFCSUD6432')
#         client_secret = os.getenv('NAFAES_CLIENT_SECRET', 'hw3$mfjc4z')
#         payload = f'grant_type=password&username={username}&password={password}&client_id={client_id}&client_secret={client_secret}'
#         payload_to_log = f'grant_type=password&username={username}&password={password}&client_id={client_id}&client_secret={client_secret}'
#         payload_to_log = payload_to_log.replace(username, '*' * 10)
#         payload_to_log = payload_to_log.replace(password, '*' * 10)
#         payload_to_log = payload_to_log.replace(client_id, '*' * 10)
#         payload_to_log = payload_to_log.replace(client_secret, '*' * 10)
#         headers = self.get_common_headers(is_json=False)
#         log_values = {
#             'request': payload_to_log,
#             'partner_id': False,
#             'url': url,
#             'type': 'auth',
#         }
#         log_obj = self.env['nafaes.api.log']
#         log_id = log_obj.create_log(log_values)
#         response = requests.request("POST", url, headers=headers, data=payload)
#         self._log_response(log_id, response)
#         response = response.json()
#         access_token = response.get('access_token', '')
#         expires_in_seconds = response.get('expires_in', 0)
#         nafaes_token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in_seconds)
#         param_obj = self.env['ir.config_parameter'].sudo()
#         if access_token:
#             param_obj.set_param(TOKEN_EXPIRY_KEY, nafaes_token_expiry.isoformat())
#             param_obj.set_param(TOKEN_KEY, access_token)
#
#         return access_token
#
#     def auth(self, try_old=True):
#         param_obj = self.env['ir.config_parameter'].sudo()
#         existing_token = param_obj.get_param(TOKEN_KEY)
#         existing_token_expiry = param_obj.get_param(TOKEN_EXPIRY_KEY)
#         use_old = False
#         if existing_token and existing_token_expiry and try_old:
#             expiry_date = datetime.datetime.fromisoformat(existing_token_expiry)
#             expiry_date = expiry_date - datetime.timedelta(seconds=60 * 5)
#             if expiry_date > datetime.datetime.now():
#                 use_old = True
#         if use_old:
#             access_token = existing_token
#         else:
#             access_token = self._call_auth()
#
#         return {
#             'Authorization': f'Bearer {access_token}',
#         }
#
#     def get_language(self):
#         arabic = "1"
#         # english = "2"
#         language = self.env['ir.config_parameter'].sudo().get_param('nafaes.language', arabic)
#         return language
#
#     def _log_response(self, log_id, response):
#         try:
#             response_to_log = json.dumps(response.json())
#         except Exception:
#             response_to_log = response.text
#
#         log_id.update_log({
#             'response_status': response.status_code,
#             'response': response_to_log,
#         })
#
#     def nafaes_call_api(self, url, data, log_values={}, retry=True):
#         # this method handles unexpectedly expired auth token, by retrying once with a new token
#         headers = self.get_common_headers()
#         # auth
#         auth_header = self.auth()
#         headers.update(auth_header)
#         # log
#         log_values.update({
#             'request': data,
#             'url': url,
#         })
#         log_obj = self.env['nafaes.api.log']
#         log_id = log_obj.create_log(log_values)
#
#         # send the request
#         response = requests.request("POST", url, headers=headers, data=data)
#
#         self._log_response(log_id, response)
#
#         if response.status_code == 401 and retry:
#             # here we know the auth token is not valid
#             self.auth(try_old=False)
#             return self.nafaes_call_api(url, data, retry=False)
#
#         return response.json()
#
#     def nafaes_get_available_commodities(self):
#         url = f'{self.get_base_url()}/api/v2/avaliablecommoditieswithsource'
#
#         payload = json.dumps({
#             "request": {
#                 "amount": "2000",
#                 "currency": "SAR",
#                 "lng": self.get_language(),
#             }
#         })
#         log_values = {
#             'partner_id': False,
#             'type': 'get_commodities',
#         }
#         response = self.nafaes_call_api(url, payload, log_values)
#
#     def get_webhook_url(self):
#         base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'https://fuelfinance.sa')
#         if base_url.startswith('http:'):
#             base_url = base_url[:4] + 's' + base_url[4:]
#
#         webhook_path = '/NafaesWebhook'
#         return f'{base_url}{webhook_path}?secretKey={NAFAES_TOKEN}'
#
#     def nafaes_purchase_order(self, order_id):
#         url = f'{self.get_base_url()}/api/v2/purchaseorder'
#
#         self.uuid_po = str(uuid.uuid4())
#         payload = json.dumps({
#             "header": {
#                 "uuid": self.uuid_po,
#             },
#             "push": {
#                 "callBackUrl": self.get_webhook_url(),
#                 "dataType": "json"
#             },
#             "request": [
#                 {
#                     "commodityCode": 'PAC',
#                     "purchaser": order_id.purchaser,
#                     "currency": order_id.currency,
#                     "purchaseAmount": order_id.amount,
#                     "valueDate": order_id.valueDate,
#                     "counterPartyAccount": order_id.counterPartyAccount,
#                     "counterPartyName": order_id.counterPartyName,
#                     "counterPartyTelephone": order_id.counterPartyTelephone,
#                     "transactionType": "managed",
#                     "lng": self.get_language(),
#                 }
#             ]
#         })
#
#         log_values = {
#             'partner_id': order_id.partner_id.id,
#             'type': 'po',
#             'res_id': order_id.id,
#             'res_model': order_id._name,
#         }
#
#         response = self.nafaes_call_api(url, payload, log_values)
#         return response
#
#     def nafaes_transfer(self, order_id):
#         url = f'{self.get_base_url()}/api/v2/transferorder'
#
#         self.uuid_to = str(uuid.uuid4())
#         payload = json.dumps({
#             "header": {
#                 "uuid": self.uuid_to,
#             },
#             "push": {
#                 "callBackUrl": self.get_webhook_url(),
#                 "dataType": "json"
#             },
#             "request": [
#                 {
#                     "referenceNo": self.referenceNo,
#                     "orderType": "TO",
#                     "lng": self.get_language()
#                 }
#             ]
#         })
#
#         log_values = {
#             'partner_id': order_id.partner_id.id,
#             'type': 'to',
#             'res_id': order_id.id,
#             'res_model': order_id._name,
#         }
#         response = self.nafaes_call_api(url, payload, log_values)
#
#         return response
#
#     def nafaes_sell(self, order_id):
#         url = f'{self.get_base_url()}/api/v2/saleorder'
#
#         self.uuid_so = str(uuid.uuid4())
#         payload = json.dumps({
#             "header": {
#                 "uuid": self.uuid_so,
#             },
#             "push": {
#                 "callBackUrl": self.get_webhook_url(),
#                 "dataType": "json"
#             },
#             "request": [
#                 {
#                     "referenceNo": order_id.referenceNo,
#                     "orderType": "SO",
#                     "lng": self.get_language()
#                 }
#             ]
#         })
#
#         log_values = {
#             'partner_id': order_id.partner_id.id,
#             'type': 'so',
#             'res_id': order_id.id,
#             'res_model': order_id._name,
#         }
#         response = self.nafaes_call_api(url, payload, log_values)
#
#         return response
#
#     def nafaes_cancel(self, order_id):
#         url = f'{self.get_base_url()}/api/v2/cancelorder'
#
#         payload = json.dumps({
#             "header": {
#                 "uuid": str(uuid.uuid4()),
#             },
#             "request": {
#                 "referenceNo": order_id.referenceNo,
#                 "orderType": "CO",
#                 "lng": self.get_language()
#             }
#         })
#
#         log_values = {
#             'partner_id': order_id.partner_id.id,
#             'type': 'co',
#             'res_id': order_id.id,
#             'res_model': order_id._name,
#         }
#         response = self.nafaes_call_api(url, payload, log_values)
#
#         return response
#
#     def nafaes_order_result(self, order_id):
#         # aka "long polling" as defined by Nafaes docs
#         url = f'{self.get_base_url()}/api/v2/orderresult'
#
#         if order_id.state not in ['waiting_po', 'waiting_to', 'waiting_so']:
#             raise UserError('Order is not in a waiting state')
#
#         if order_id.state in ['draft', 'waiting_po', 'po']:
#             uuid_value = order_id.uuid_po
#             orderType = 'PO'
#         if order_id.state in ['waiting_to', 'to']:
#             uuid_value = order_id.uuid_to
#             orderType = 'TO'
#         if order_id.state in ['waiting_so', 'so']:
#             uuid_value = order_id.uuid_so
#             orderType = 'SO'
#
#         payload = json.dumps({
#             "header": {
#                 "uuid": uuid_value,
#             },
#             "request": [
#                 {
#                     "referenceNo": order_id.referenceNo or '',
#                     "orderType": orderType,
#                     "lng": self.get_language()
#                 }
#             ]
#         })
#
#         log_values = {
#             'partner_id': order_id.partner_id.id,
#             'type': 'result',
#             'res_id': order_id.id,
#             'res_model': order_id._name,
#         }
#
#         response = self.nafaes_call_api(url, payload, log_values)
#         # response here should be the same as the webhook request body
#         self.env['nafaes.order.result'].handle_request(response, url, NAFAES_TOKEN, enable_log=False,
#                                                        data_key='response')
