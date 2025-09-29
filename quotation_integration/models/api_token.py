import hashlib  # Import hashlib for generating cryptographic hash functions
import logging  # Import logging for logging messages
import os  # Import os for operating system functionalities
from datetime import datetime, timedelta  # Import datetime and timedelta for date and time operations
from odoo import api, fields, models  # Import Odoo components for models and fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT  # Import default datetime format used by Odoo

_logger = logging.getLogger(__name__)  # Create a logger for this module

# Define a configuration key for token expiry date
token_expiry_date_in = "helpdesk_api.access_token_token_expiry_date_in"


def random_token(length=80, prefix="access_token"):
    """
    Generates a random token with a specified length and prefix.

    :param length: Length of the token
    :param prefix: Prefix to be added to the token
    :return: A unique token string
    """
    rbytes = os.urandom(length)  # Generate random bytes
    return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))  # Return the token with prefix


class APIAccessToken(models.Model):
    _name = "api.access_token"  # Model name
    _description = "API Access Token"  # Description of the model

    token = fields.Char("Access Token", required=True)  # Token field
    user_id = fields.Many2one("res.users", string="User", required=True)  # User associated with the token
    token_expiry_date = fields.Datetime(string="Token Expiry Date", required=True)  # Expiry date of the token
    scope = fields.Char(string="Scope")  # Scope of the token

    def find_or_create_token(self, user_id=None, create=False):
        """
        Finds an existing token for a user or creates a new one if requested.

        :param user_id: ID of the user for whom the token is created or found
        :param create: Boolean indicating whether to create a new token if not found
        :return: The token string or None if not found and create is False
        """
        if not user_id:
            user_id = self.env.user.id  # Use the current user ID if none provided

        # Search for an existing token for the user
        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None  # Invalidate expired token
        if not access_token and create:
            token_expiry_date = datetime.now() + timedelta(days=720)  # Set expiry date for 720 days from now
            vals = {
                "user_id": user_id,
                "scope": "userinfo",  # Default scope
                "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),  # Format expiry date
                "token": random_token(),  # Generate a new token
            }
            access_token = self.env["api.access_token"].sudo().create(vals)  # Create new token
        if not access_token:
            return None  # Return None if no valid token found or created
        return access_token.token  # Return the token string

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.

        :param scopes: An iterable containing the scopes to check or None
        :return: True if the token is valid, otherwise False
        """
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)  # Check expiry and scope validity

    def has_expired(self):
        """Checks if the token has expired."""
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(
            self.token_expiry_date)  # Compare current time with expiry date

    def _allow_scopes(self, scopes):
        """
        Checks if the token has the required scopes.

        :param scopes: A set of required scopes
        :return: True if the token includes all required scopes, otherwise False
        """
        self.ensure_one()
        if not scopes:
            return True  # If no scopes provided, allow all

        provided_scopes = set(self.scope.split())  # Convert scope string to a set
        resource_scopes = set(scopes)  # Convert required scopes to a set

        return resource_scopes.issubset(provided_scopes)  # Check if all required scopes are included in provided scopes


class Users(models.Model):
    _inherit = "res.users"  # Inherit from Odoo's res.users model
    _description = "Table of user"  # Description of the model

    def sum_numbers(self, x, y):
        """
        Example method to sum two numbers.

        :param x: First number
        :param y: Second number
        :return: Sum of x and y
        """
        return x + y

    token_ids = fields.One2many("api.access_token", "user_id",
                                string="Access Tokens")  # Relationship with API access tokens
