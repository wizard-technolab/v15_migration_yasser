# -*- coding: utf-8 -*-
# from odoo import http


# class PartnerReports(http.Controller):
#     @http.route('/partner_reports/partner_reports', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/partner_reports/partner_reports/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('partner_reports.listing', {
#             'root': '/partner_reports/partner_reports',
#             'objects': http.request.env['partner_reports.partner_reports'].search([]),
#         })

#     @http.route('/partner_reports/partner_reports/objects/<model("partner_reports.partner_reports"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('partner_reports.object', {
#             'object': obj
#         })
