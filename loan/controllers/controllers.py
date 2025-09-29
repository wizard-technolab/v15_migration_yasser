# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json


# class CUSTOMERID(http.Controller):
#     @http.route('/api/check', methods=["GET"], auth="none", csrf=False)
#     def check(self, **kw):
#         return "Hello, world"


class API(http.Controller):
    @http.route('/web/session/authenticate', type='json', auth="none", csrf=False)
    def check(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info()

    @http.route('/get_loan', type='json', auth="user", csrf=False)
    def get_loan(self):
        print('Welcome')
        loan_order = request.env['loan.order'].search([])
        orders = []
        for rec in loan_order:
            vals = {
                'id': rec.id,
                'name': rec.name,
            }
            orders.append(vals)
        date = {'status': 200, 'response': orders, 'message': 'Success'}
        return date

