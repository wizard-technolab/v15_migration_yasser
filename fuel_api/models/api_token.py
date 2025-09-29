import hashlib  # Module for hashing algorithms
import logging  # Module for logging
import os  # Module for interacting with the operating system
from datetime import datetime, timedelta  # Modules for working with dates and times
from odoo import api, fields, models  # Odoo specific modules
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT  # Default datetime format for Odoo

_logger = logging.getLogger(__name__)  # Setting up a logger for this module

# Configuration value for token expiry date
token_expiry_date_in = "fuel_api.access_token_token_expiry_date_in"

def random_token(length=80, prefix="access_token"):
    """
    Generates a random token using the os.urandom function and hashlib.sha1 for hashing.
    :param length: Length of the random bytes to generate
    :param prefix: Prefix to add to the generated token
    :return: A string with the format 'prefix_sha1_hashed_value'
    """
    rbytes = os.urandom(length)  # Generate random bytes
    return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))  # Create token with prefix and hashed value

class APIAccessToken(models.Model):
    _name = "api.access_token"  # Model name
    _description = "API Access Token"  # Model description

    token = fields.Char("Access Token", required=True)  # Token field
    user_id = fields.Many2one("res.users", string="User", required=True)  # Related user
    token_expiry_date = fields.Datetime(string="Token Expiry Date", required=True)  # Expiry date of the token
    scope = fields.Char(string="Scope")  # Scope of the token

    def find_or_create_token(self, user_id=None, create=False):
        """
        Finds an existing valid token or creates a new one if none exist or the existing one has expired.
        :param user_id: User ID for which the token is to be created or found
        :param create: Boolean indicating if a new token should be created if none is found
        :return: Token string if found or created, otherwise None
        """
        if not user_id:
            user_id = self.env.user.id  # Use the current user's ID if none is provided

        # Search for the most recent token for the given user
        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():  # Check if the token has expired
                access_token = None

        if not access_token and create:
            # Calculate the expiry date (default to 720 days if no configuration is found)
            token_expiry_date = datetime.now() + timedelta(days=720)
            vals = {
                "user_id": user_id,
                "scope": "userinfo",
                "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": random_token(),
            }
            access_token = self.env["api.access_token"].sudo().create(vals)  # Create a new token

        if not access_token:
            return None
        return access_token.token  # Return the token string

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.
        :param scopes: An iterable containing the scopes to check or None
        :return: Boolean indicating if the token is valid
        """
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)

    def has_expired(self):
        """
        Checks if the token has expired.
        :return: Boolean indicating if the token has expired
        """
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.token_expiry_date)

    def _allow_scopes(self, scopes):
        """
        Checks if the token allows the specified scopes.
        :param scopes: A list of scopes to check
        :return: Boolean indicating if all specified scopes are allowed
        """
        self.ensure_one()
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)  # Check if all requested scopes are allowed

class Users(models.Model):
    _inherit = "res.users"  # Extending the res.users model
    _description = 'user Table'

    def sum_numbers(self, x, y):
        """
        Example method to sum two numbers.
        :param x: First number
        :param y: Second number
        :return: Sum of x and y
        """
        return x + y

    token_ids = fields.One2many("api.access_token", "user_id", string="Access Tokens")  # One2many relation to access tokens
