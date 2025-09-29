# -*- coding: utf-8 -*-
# from odoo import http


# class FuelHide(http.Controller):
#     @http.route('/fuel_hide/fuel_hide', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fuel_hide/fuel_hide/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fuel_hide.listing', {
#             'root': '/fuel_hide/fuel_hide',
#             'objects': http.request.env['fuel_hide.fuel_hide'].search([]),
#         })

#     @http.route('/fuel_hide/fuel_hide/objects/<model("fuel_hide.fuel_hide"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fuel_hide.object', {
#             'object': obj
#         })
