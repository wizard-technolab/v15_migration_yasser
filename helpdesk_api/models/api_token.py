import hashlib  # Import the hashlib module for generating hash values
import logging  # Import the logging module for logging purposes
import os  # Import the os module for accessing operating system functionalities
from datetime import datetime, timedelta  # Import datetime and timedelta for date and time manipulation
from odoo import api, fields, models  # Import required Odoo modules
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT  # Import the default server datetime format from Odoo tools

# Set up logging
_logger = logging.getLogger(__name__)

# Placeholder for token expiry configuration (can be taken from configuration parameters)
token_expiry_date_in = "helpdesk_api.access_token_token_expiry_date_in"


def random_token(length=80, prefix="access_token"):
    """
    Generate a random token string with a specified length and prefix.

    :param length: Length of the random bytes to generate.
    :param prefix: Prefix to prepend to the token.
    :return: Randomly generated token string.
    """
    rbytes = os.urandom(length)  # Generate random bytes
    return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))  # Return the token string with prefix and SHA-1 hash


class APIAccessToken(models.Model):
    _name = "api.access_token"  # Define the model name
    _description = "API Access Token"  # Description of the model

    token = fields.Char("Access Token", required=True)  # Define the 'token' field
    user_id = fields.Many2one("res.users", string="User", required=True)  # Define the 'user_id' field as a many-to-one relation
    token_expiry_date = fields.Datetime(string="Token Expiry Date", required=True)  # Define the 'token_expiry_date' field
    scope = fields.Char(string="Scope")  # Define the 'scope' field

    def find_or_create_token(self, user_id=None, create=False):
        """
        Find an existing token or create a new one if requested.

        :param user_id: User ID for which to find or create the token.
        :param create: Boolean flag indicating whether to create a new token if not found.
        :return: The access token string.
        """
        if not user_id:
            user_id = self.env.user.id  # Use the current user's ID if not provided

        # Search for the latest token for the given user
        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None  # Invalidate the token if it has expired

        if not access_token and create:
            # Generate a new token if none found and creation is requested
            token_expiry_date = datetime.now() + timedelta(days=720)  # Set expiry date to 720 days from now
            vals = {
                "user_id": user_id,
                "scope": "userinfo",
                "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": random_token(),
            }
            access_token = self.env["api.access_token"].sudo().create(vals)  # Create the new token record

        if not access_token:
            return None  # Return None if no token found and creation not requested
        return access_token.token  # Return the token string

    def is_valid(self, scopes=None):
        """
        Check if the access token is valid.

        :param scopes: An iterable containing the scopes to check or None.
        :return: Boolean indicating if the token is valid.
        """
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)  # Check if the token has expired and if the scopes are allowed

    def has_expired(self):
        """
        Check if the token has expired.

        :return: Boolean indicating if the token has expired.
        """
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.token_expiry_date)  # Compare current date with expiry date

    def _allow_scopes(self, scopes):
        """
        Check if the provided scopes are allowed.

        :param scopes: An iterable containing the scopes to check.
        :return: Boolean indicating if the scopes are allowed.
        """
        self.ensure_one()
        if not scopes:
            return True  # Allow all scopes if none provided

        provided_scopes = set(self.scope.split())  # Split and convert the stored scopes into a set
        resource_scopes = set(scopes)  # Convert the provided scopes into a set

        return resource_scopes.issubset(provided_scopes)  # Check if provided scopes are a subset of the stored scopes


class Users(models.Model):
    _inherit = "res.users"  # Extend the 'res.users' model
    _description = 'User Table'

    def sum_numbers(self, x, y):
        """
        Sum two numbers.

        :param x: First number.
        :param y: Second number.
        :return: Sum of x and y.
        """
        return x + y

    token_ids = fields.One2many("api.access_token", "user_id", string="Access Tokens")  # Define a one-to-many relation for access tokens
