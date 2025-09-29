# **************************************************************************************
#
#
#       ---------------| This Controller Content On  Call APi |---------------------
#                           "Call Api For Call To Customer"
#
# **************************************************************************************
import datetime
from odoo import http


class CallApiController(http.Controller):
    @http.route(['/api/v2/receive_client_data'], type="json", auth="public", method=['POST'])
    def receive_client_data(self, **data):
        phone = data.get('phone')
        status = data.get('status')
        decision = data.get('decision')
        try:
            if phone and status and decision:
                loan_order = http.request.env['loan.order'].sudo().search(
                    [('name.phone', '=', phone), ('state', '=', 'approve')], limit=1)
                if loan_order:

                    # ------------------- | If decision == 'accepted' Change Loan Order State To By Nafaes
                    if decision == 'accepted':
                        loan_order.send_notification_to_user('group_customer_operation', "Customer Call Approve"
                                                             , "Customer Approved and Call")
                        loan_order.action_call_done()

                    # ------------------- | ElIf decision == 'rejected' Change Loan Order State To Cancel
                    elif decision == 'rejected':
                        loan_order.action_confirmation_call_cancel()
                        loan_order.send_notification_to_user('group_sales_cancel', "Canceled By Customer"
                                                             , "Canceled By Customer")

                    # ------------------- | Else  Change Loan Order State To Pending
                    else:
                        loan_order.send_notification_to_user('group_sales_cancel', "Customer Pending"
                                                             , "Customer Pending")
                        loan_order.name.action_pending()
                        loan_order.write({'state': 'pending'})

                    # ------------------- | Add a message to the chatter of the loan order
                    message_body = (
                        f"بيانات الاتصال بالعميل   :"
                        f" رقم الجوال : {phone}\n"
                        f"| الحاله: {status}\n"
                        f"| القرار: {decision}\n"
                        f"| الوقت والتاريخ: {datetime.datetime.today().date()} "
                        f"{datetime.datetime.today().time().strftime('%H:%M:%S')}"
                    )
                    loan_order.message_post(body=message_body)

                    return {"success": True, 'status_code': 200, "message": "Customer Data Added Successfully"}
                else:
                    return {"success": False, 'status_code': 404, "message": "Loan Order Not Found"}
            else:
                return {"success": False, 'status_code': 400, "message": "Required Fields Not Found"}
        except Exception as e:
            return {"success": False, 'status_code': 500, "message": e}
