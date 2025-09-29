import hashlib  # Importing hashlib to create secure hash tokens
import logging  # Importing logging to log messages
import os  # Importing os to generate random bytes
from datetime import datetime, timedelta  # Importing datetime and timedelta to handle dates and times
from odoo import api, fields, models  # Importing necessary modules from Odoo
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT  # Importing default date-time format from Odoo tools

_logger = logging.getLogger(__name__)  # Setting up logging for this module

# Configuration for token expiry date setting
token_expiry_date_in = "helpdesk_api.access_token_token_expiry_date_in"


def random_token(length=80, prefix="access_token"):
    """
    Generate a random token.
    :param length: The length of the random bytes to generate
    :param prefix: The prefix to use for the token
    :return: A string representing the token
    """
    rbytes = os.urandom(length)  # Generating random bytes
    return "{}_{}".format(prefix,
                          str(hashlib.sha1(rbytes).hexdigest()))  # Returning the token with prefix and hashed value


class APIAccessToken(models.Model):
    _name = "api.access_token"  # Model name in Odoo
    _description = "API Access Token"  # Description of the model

    token = fields.Char("Access Token", required=True)  # Token field (required)
    user_id = fields.Many2one("res.users", string="User", required=True)  # User field as a Many2one relation (required)
    token_expiry_date = fields.Datetime(string="Token Expiry Date", required=True)  # Token expiry date field (required)
    scope = fields.Char(string="Scope")  # Scope field to define the access scope of the token

    def find_or_create_token(self, user_id=None, create=False):
        """
        Find or create a token for the given user.
        :param user_id: The ID of the user for whom the token is to be created
        :param create: Boolean indicating whether to create a new token if none exists
        :return: The token string or None if not found/created
        """
        if not user_id:
            user_id = self.env.user.id  # Use current user's ID if none is provided

        # Search for the latest token for the given user
        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token:
            access_token = access_token[0]  # Get the first token found
            if access_token.has_expired():
                access_token = None  # Invalidate the token if it has expired
        if not access_token and create:
            # Set the token expiry date to 720 days from now
            token_expiry_date = datetime.now() + timedelta(days=720)
            vals = {
                "user_id": user_id,
                "scope": "userinfo",  # Default scope
                "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                # Expiry date formatted
                "token": random_token(),  # Generate a random token
            }
            access_token = self.env["api.access_token"].sudo().create(vals)  # Create a new token
        if not access_token:
            return None  # Return None if no token found or created
        return access_token.token  # Return the token string

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.
        :param scopes: An iterable containing the scopes to check or None
        :return: Boolean indicating whether the token is valid
        """
        self.ensure_one()  # Ensure the record is singleton
        return not self.has_expired() and self._allow_scopes(scopes)  # Check expiry and allowed scopes

    def has_expired(self):
        """
        Check if the token has expired.
        :return: Boolean indicating whether the token has expired
        """
        self.ensure_one()  # Ensure the record is singleton
        return datetime.now() > fields.Datetime.from_string(
            self.token_expiry_date)  # Compare current date with expiry date

    def _allow_scopes(self, scopes):
        """
        Check if the token allows the required scopes.
        :param scopes: The required scopes
        :return: Boolean indicating whether the scopes are allowed
        """
        self.ensure_one()  # Ensure the record is singleton
        if not scopes:
            return True  # Allow if no specific scopes are required

        provided_scopes = set(self.scope.split())  # Split and convert the scope string to a set
        resource_scopes = set(scopes)  # Convert the required scopes to a set

        return resource_scopes.issubset(provided_scopes)  # Check if required scopes are a subset of provided scopes


class Users(models.Model):
    _inherit = "res.users"  # Inheriting the existing res.users model
    _description = 'Users Table'

    def sum_numbers(self, x, y):
        """
        Sum two numbers.
        :param x: The first number
        :param y: The second number
        :return: The sum of x and y
        """
        return x + y  # Return the sum

    token_ids = fields.One2many("api.access_token", "user_id",
                                string="Access Tokens")  # One2many relation to access tokens
