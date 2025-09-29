from odoo import http
from odoo.http import request
#from odoo15.odoo import fields

class CollectionDashboardController(http.Controller):
    @http.route('/collection/dashboard', type='http', auth='user', website=True)
    def collection_dashboard(self, **kw):
        data = request.env['collection.collection'].get_dashboard_data()
        return request.render('collection.CollectionDashboardMain', {'data': data})

# class CollectionDashboard(http.Controller):
#
#     @http.route('/collection/dashboard', auth='user', type='http', website=True)
#     def collection_dashboard(self, **kw):
#         Collection = request.env['collection.collection']
#         Loan = request.env['loan.order']
#         Users = request.env['res.users'].search([])
#
#         all_loans = Loan.search([('state', '=', 'active')])
#         total_active = len(all_loans)
#         urgent_loans = all_loans.filtered(lambda r: r.bkt >= 3)
#         total_urgent = len(urgent_loans)
#
#         # SLA failed if installment due date < today and not paid
#         late_loans = all_loans.filtered(lambda r: any(i.due_date < fields.Date.today() and i.state != 'paid' for i in r.installment_ids))
#         total_late = len(late_loans)
#
#         # Per-user collections
#         per_user = {}
#         for user in Users:
#             collections = Collection.search([('assigned_user_id', '=', user.id)])
#             unassigned = Collection.search([('assigned_user_id', '=', False)])
#             per_user[user] = {
#                 'collections': collections,
#                 'sla_issues': collections.filtered(lambda c: c.loan_id.bkt >= 3),
#                 'unassigned': unassigned
#             }
#
#         return request.render('collection.collection_dashboard_template', {
#             'total_active': total_active,
#             'total_urgent': total_urgent,
#             'total_late': total_late,
#             'per_user': per_user,
#         })
