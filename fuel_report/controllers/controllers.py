# -*- coding: utf-8 -*-
# from odoo import http


# class FuelReports(http.Controller):
#     @http.route('/fuel_reports/fuel_reports', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fuel_reports/fuel_reports/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fuel_reports.listing', {
#             'root': '/fuel_reports/fuel_reports',
#             'objects': http.request.env['fuel_reports.fuel_reports'].search([]),
#         })

#     @http.route('/fuel_reports/fuel_reports/objects/<model("fuel_reports.fuel_reports"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fuel_reports.object', {
#             'object': obj
#         })
