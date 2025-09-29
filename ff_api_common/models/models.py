import logging  # Import the logging module for logging purposes
from odoo import api, fields, models, _  # Import necessary modules from Odoo

# Set up the logger for this module
_logger = logging.getLogger(__name__)


class fuel_api_log(models.AbstractModel):
    """
    An abstract model for logging API requests and responses.
    This model is abstract for security reasons, so each API log should be accessible only by its users.
    """
    _name = "ff.api.log"
    _description = "Fuel Api Log"
    _order = "id desc"

    # Fields to store request and response data
    request = fields.Char(readonly=True, help="A json dump of the request, use json.dumps(request_dict)")
    response = fields.Char(readonly=True, help="A json dump of the response, use json.dumps(request_dict)")

    # URL of the API endpoint
    url = fields.Char('URL', readonly=True)

    # Type of API request (e.g., Auth, CreateOrder, CancelRequest, etc.)
    type = fields.Selection([], help='This represents the endpoint, e.g: Auth, CreateOrder, CancelRequest, ..etc')

    # Model and record ID related to the API request
    res_model = fields.Char('Model', help='The model which the request is related to, e.g: sale.order')
    res_id = fields.Many2oneReference(string='Record ID', help="ID of the target record in the database",
                                      model_field='res_model')

    # Computed field to store a reference combining model and record ID
    reference = fields.Char(string='Reference', compute='_compute_reference')

    @api.depends('res_model', 'res_id')
    def _compute_reference(self):
        """
        Compute the reference field which combines the res_model and res_id.
        """
        for res in self:
            res.reference = "%s,%s" % (res.res_model, res.res_id)

    def create_log(self, values):
        """
        Create a log entry with the provided values.
        A new cursor is used to avoid issues if the current transaction gets rolled back.
        """
        with self.pool.cursor() as new_cr:
            # Create a new cursor to ensure the log entry is not affected by rollbacks
            return self.with_env(self.env(cr=new_cr)).sudo().create(values)

    def update_log(self, values):
        """
        Update a log entry with the provided values.
        A new cursor is used to avoid issues if the current transaction gets rolled back.
        """
        self.ensure_one()
        with self.pool.cursor() as new_cr:
            # Create a new cursor to ensure the log entry update is not affected by rollbacks
            log_id = self.with_env(self.env(cr=new_cr)).sudo()
            log_id.write(values)
