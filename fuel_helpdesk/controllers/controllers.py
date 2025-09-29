# -*- coding: utf-8 -*-
# from odoo import http


# class FuelHelpdesk(http.Controller):
#     @http.route('/fuel_helpdesk/fuel_helpdesk', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fuel_helpdesk/fuel_helpdesk/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fuel_helpdesk.listing', {
#             'root': '/fuel_helpdesk/fuel_helpdesk',
#             'objects': http.request.env['fuel_helpdesk.fuel_helpdesk'].search([]),
#         })

#     @http.route('/fuel_helpdesk/fuel_helpdesk/objects/<model("fuel_helpdesk.fuel_helpdesk"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fuel_helpdesk.object', {
#             'object': obj
#         })
