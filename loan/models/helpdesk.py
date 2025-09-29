from odoo import api, models, fields, _


class HelpdeskCustom(models.Model):
    _inherit = 'helpdesk.ticket'
    _description = 'Inherit Helpdesk Team'


    # ticket_id = fields.Many2one("loan.order", required=True, string='Ticket')
    # message = fields.Text(string="Your file is stored in the directory C:/", readonly=True, store=True)