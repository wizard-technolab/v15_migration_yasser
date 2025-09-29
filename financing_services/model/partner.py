# # -*- coding: utf-8 -*-

# from decimal import Clamped
# from email.policy import default
# from statistics import mode
# from odoo import models, fields, api
# import datetime

# class ResPartner(models.Model):
#     _inherit = 'res.partner'

#     def print_report(self,res_id, model):
#         """
#             print report pdf for created record
#         """
#         record = self.env[model].search([('id','=',res_id)])
#         if record.id:
#             get = record.get_portal_url(report_type='pdf', download=True)
#             access_tocken_str = get.split('&report_type')
#             access_tocken = access_tocken_str[0].split('=')[1]
#             print("\n\n access_tocken_str:",access_tocken_str,"\n\n")
#             print("\n\n access_tocken:",access_tocken,"\n\n")
            
#             # application_sudo = self._document_check_access(model, res_id, access_token)
#             return self._show_report(model=record, report_type='pdf', report_ref='partner_reports.medical_services_financing_request_action', download=True)
