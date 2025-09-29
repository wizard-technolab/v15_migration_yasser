from itertools import product
import time
import json
from odoo import http
from odoo.http import request
import requests
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class FinanceWebsiteController(http.Controller):

    @http.route('/form1', type='http', auth='public', website=True, csrf=True)
    def form1_page(self, **kw):
        return http.request.render("financing_services.form1")

    @http.route('/form2', type='http', auth='public', website=True, csrf=True)
    def form2_page(self, **kw):
        return http.request.render("financing_services.form2")

    @http.route('/form3', type='http', auth='public', website=True, csrf=True)
    def form3_page(self, **kw):
        return http.request.render("financing_services.form3")

    @http.route('/form4', type='http', auth='public', website=True, csrf=True)
    def form4_page(self, **kw):
        return http.request.render("financing_services.form4")

    @http.route('/web/get_products', type="json", auth="public", website=True, csrf=True)
    def get_products(self, **kw):
        """
            get the product for the quotations,
            return json {}.
        """
        products = request.env['product.product'].sudo().search([])
        data = []
        for product in products:
            data.append({
                'id': product.id,
                'name': product.name,
                'default_code': product.default_code,
            })
        clinic = {}
        if request.env.user.partner_id.parent_id.id:
            clinic = {
                'clinic_name': request.env.user.partner_id.parent_id.name,
                'applicant_name': request.env.user.partner_id.name,
                'clinic_email': request.env.user.partner_id.parent_id.email,
                'clinic_phone': request.env.user.partner_id.parent_id.phone,
                # 'contract_name': request.env.user.partner_id.parent_id.vat,
                # 'contract_date': request.env.user.partner_id.parent_id.birth_of_date,
                # 'contract_date_month': request.env.user.partner_id.parent_id.hijri_birth_date_month,
                # 'contract_date_year': request.env.user.partner_id.parent_id.hijri_birth_date_year,
                'clinic_user_id': request.env.user.id,
            }
        else:
            clinic = {
                'clinic_name': request.env.user.partner_id.name,
                'applicant_name': request.env.user.partner_id.name,
                'clinic_email': request.env.user.partner_id.email,
                'clinic_phone': request.env.user.partner_id.phone,
                # 'contract_name': request.env.user.partner_id.parent_id.vat,
                # 'contract_date': request.env.user.partner_id.parent_id.birth_of_date,
                'contract_date_month': request.env.user.partner_id.parent_id.hijri_birth_date_month,
                'contract_date_year': request.env.user.partner_id.parent_id.hijri_birth_date_year,
                'clinic_user_id': request.env.user.id,
            }
        return {'products': data, 'clinic': clinic}
