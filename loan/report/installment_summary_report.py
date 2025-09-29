# from odoo import api, fields, models, _
#
#
# class LoanReport(models.AbstractModel):
#     _name = 'report.loan.installment_summary_template'
#     _description = 'Proforma Report'
#
#     @api.model
#     def _get_report_values(self, docids, data=None):
#         start_date = data['start']
#         end_date = data['end']
#         filter_name = data['name']
#
#         domain = []
#         installments = []
#
#         if start_date:
#             domain += [('request_date', '>=', start_date)]
#
#         if end_date:
#             domain += [('request_date', '<=', end_date)]
#
#         # if filter_name:
#         #     domain += [('request_loan', 'in', filter_name)]
#         print(data)
#         installment = self.env['loan.order'].sudo().search(domain)
#
#         return {
#             'doc_ids': docids,
#             'doc_model': 'installment.report.wizard',
#             'docs': installment,
#         }
