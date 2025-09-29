from odoo import http
from odoo.http import request


class MainPage(http.Controller):
    @http.route('/calculation', type='http', auth='public', website=True)
    def calculator(self, **kw):
        monthly_payments = http.request.env['loan.calculate'].search([])
        values = {
            'monthly_payments': monthly_payments,
        }

        return http.request.render('website_menu.menu_data', values)

    @http.route('/calculate-result', type='http', methods=['POST'], auth='public', website=True)
    def calculator_result(self, **kw):
        cal_val = request.env['loan.calculate'].sudo().create(kw)
        # cal_val = request.env['loan.calculate'].search([])
        print("calculate")
        values = {
            'docs': cal_val,
        }
        # cal_val = request.env['loan.calculate'].sudo().create(kw)
        print(cal_val.monthly_payments)
        # request.env['loan.calculate'].sudo().create(kw)
        return request.render('website_menu.result_data', values)

# /<model("loan.calculate"):calculate>/
