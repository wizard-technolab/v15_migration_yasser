import json
import logging
from datetime import datetime, timedelta

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ApiLog(models.Model):
    _name = 'kw.api.log'
    _description = 'API log'
    _order = 'create_date DESC'

    name = fields.Char(
        string='URL', )
    json = fields.Text()

    post = fields.Text()

    headers = fields.Text()

    error = fields.Text()

    response = fields.Text()

    ip = fields.Char()

    method = fields.Char()

    code = fields.Char()

    login = fields.Char()

    @staticmethod
    def try_convert2formatted_json(val):
        try:
            val = json.dumps(json.loads(val), indent=2, ensure_ascii=False)
        except Exception as e:
            _logger.debug(e)
        return val

    @api.model
    def create(self, vals_list):
        for x in ['json', 'post', 'response']:
            vals_list[x] = self.try_convert2formatted_json(vals_list.get(x))
        return super().create(vals_list)

    def write(self, vals_list):
        for x in ['json', 'post', 'response']:
            if x in vals_list:
                vals_list[x] = self.try_convert2formatted_json(
                    vals_list.get(x))
        return super().write(vals_list)

    @api.model
    def call_clear_logs(self):
        del_date = datetime.now() - timedelta(
            days=int(self.env['ir.config_parameter'].sudo(
            ).get_param(key='kw_api.kw_api_log_storage_days') or 1))
        self.sudo().search([('create_date', '<', del_date), ]).unlink()
