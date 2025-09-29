# from asyncio import exceptions
from odoo.exceptions import ValidationError, UserError
from telnetlib import STATUS
import time
import json
from odoo import http
from odoo.http import request
import requests
import base64
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class CalculaterAPI(http.Controller):
    @http.route('/api/calculator', type='http', auth='public', website=True, csrf=False, methods=['PUT'])
    def calculate_form(self, **kw):
        print("::: DATA Calculate :::")
        print(kw)
        CalculaterObject = request.env['loan.calculate']
        values = self._calculate_monthly(**kw)
        record = CalculaterObject.sudo().create(values)
        if record.id:
            result = {'message': '', 'status': True, 'record_id': record.id}
            return json.dumps(result)

