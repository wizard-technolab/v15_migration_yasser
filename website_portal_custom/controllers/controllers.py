# -*- coding: utf-8 -*-
# from odoo import http


# class WebsitePortalCustom(http.Controller):
#     @http.route('/website_portal_custom/website_portal_custom', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/website_portal_custom/website_portal_custom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('website_portal_custom.listing', {
#             'root': '/website_portal_custom/website_portal_custom',
#             'objects': http.request.env['website_portal_custom.website_portal_custom'].search([]),
#         })

#     @http.route('/website_portal_custom/website_portal_custom/objects/<model("website_portal_custom.website_portal_custom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('website_portal_custom.object', {
#             'object': obj
#         })
