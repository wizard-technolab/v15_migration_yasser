# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details.

import hashlib  # Import hashlib for generating secure hash values
import logging  # Import logging for logging messages
import os  # Import os for generating random bytes
from datetime import datetime, timedelta  # Import datetime and timedelta for handling dates and times
from odoo import api, fields, models  # Import core Odoo modules
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT  # Import default date-time format for Odoo

# Set up a logger specifically for this module
_logger = logging.getLogger(__name__)

# Define the key used to retrieve the token expiry duration from configuration
token_expiry_date_in = "project_api.access_token_token_expiry_date_in"

def random_token(length=40, prefix="access_token"):
    """
    Generate a random token string.

    :param length: Length of the random bytes for the token. Default is 40 bytes.
    :param prefix: Prefix to prepend to the token. Default is "access_token".
    :return: A string that combines the prefix with a SHA-1 hash of random bytes.
    """
    rbytes = os.urandom(length)  # Generate `length` bytes of cryptographically secure random data.
    return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))  # Format the token with a prefix and SHA-1 hash.

class APIAccessToken(models.Model):
    _name = "api.access_token"  # Define the model name used in Odoo.
    _description = "API Access Token"  # Provide a description of the model.

    # Define fields for the model
    token = fields.Char("Access Token", required=True)  # Field to store the access token string. It is required.
    user_id = fields.Many2one("res.users", string="User", required=True)  # Field linking to the `res.users` model. It is required.
    token_expiry_date = fields.Datetime(string="Token Expiry Date", required=True)  # Field for the token's expiry date. It is required.
    scope = fields.Char(string="Scope")  # Field for the token's scope (e.g., "userinfo").

    def find_or_create_token(self, user_id=None, create=False):
        """
        Find an existing token for a user or create a new one if needed.

        :param user_id: The ID of the user for whom to find or create the token. Defaults to the current user's ID if None.
        :param create: Boolean flag indicating whether to create a new token if none is found.
        :return: The token string if found or created, otherwise None.
        """
        if not user_id:
            user_id = self.env.user.id  # If no user ID is provided, use the ID of the currently logged-in user.

        # Search for the most recent token for the specified user
        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token:
            access_token = access_token[0]  # Retrieve the most recent token.
            if access_token.has_expired():
                access_token = None  # If the token has expired, set it to None.

        if not access_token and create:
            # If no token exists and creation is allowed, create a new token
            # token_expiry_date = datetime.now() + timedelta(seconds=int(self.env.ref(token_expiry_date_in).sudo().value))
            token_expiry_date = datetime.now() + timedelta(days=1)  # Set the expiry date to 1 day from now.
            vals = {
                "user_id": user_id,  # Set the user ID for the new token.
                "scope": "userinfo",  # Define the scope of the new token.
                "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),  # Format the expiry date.
                "token": random_token(),  # Generate a new random token.
            }
            access_token = self.env["api.access_token"].sudo().create(vals)  # Create the new token record.

        if not access_token:
            return None  # If no token is available, return None.

        return access_token.token  # Return the token string.

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.

        :param scopes: An iterable of scopes to check against. If None, all scopes are considered valid.
        :return: True if the token is valid and has the required scopes; False otherwise.
        """
        self.ensure_one()  # Ensure that the method is called on a single record.
        return not self.has_expired() and self._allow_scopes(scopes)  # Check if the token is not expired and includes the required scopes.

    def has_expired(self):
        """
        Checks if the token has expired.

        :return: True if the current date and time is past the token's expiry date; False otherwise.
        """
        self.ensure_one()  # Ensure that the method is called on a single record.
        return datetime.now() > fields.Datetime.from_string(self.token_expiry_date)  # Compare current time with the expiry date.

    def _allow_scopes(self, scopes):
        """
        Checks if the token has the required scopes.

        :param scopes: An iterable of required scopes.
        :return: True if the token's scopes include all the required scopes; False otherwise.
        """
        self.ensure_one()  # Ensure that the method is called on a single record.
        if not scopes:
            return True  # If no specific scopes are required, return True.

        provided_scopes = set(self.scope.split())  # Convert the token's scopes to a set of strings.
        resource_scopes = set(scopes)  # Convert the required scopes to a set of strings.

        return resource_scopes.issubset(provided_scopes)  # Check if the required scopes are a subset of the token's scopes.

class Users(models.Model):
    _inherit = "res.users"  # Inherit from the existing `res.users` model to extend its functionality.

    def sum_numbers(self, x, y):
        """
        Sums two numbers.

        :param x: The first number.
        :param y: The second number.
        :return: The sum of x and y.
        """
        return x + y  # Return the result of adding x and y.

    # Define a one-to-many relationship with the `api.access_token` model
    token_ids = fields.One2many("api.access_token", "user_id", string="Access Tokens")  # Field to manage multiple access tokens related to a user.
