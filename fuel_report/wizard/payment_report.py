import datetime
from io import BytesIO

import xlsxwriter
from odoo import models, fields, api
import base64


class PaymentReport(models.TransientModel):
    _name = 'payment.report'
    _description = 'Payment Report'

    def payment_excel_report(self):
        # Get the current month and year
        today = datetime.date.today()
        current_month_start = today.replace(day=1)
        next_month_start = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)  # First day of the next month

        # Create a BytesIO object to hold the Excel workbook in memory
        excel_buffer = BytesIO()

        # Create a new Excel workbook
        workbook = xlsxwriter.Workbook(excel_buffer)

        sheet = workbook.add_worksheet('Payment Report')

        # Define title format
        title_format = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'align': 'center',
            'font_size': 10,
            'bg_color': 'yellow',  # Yellow background color
        })

        # Define content format
        content_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'align': 'center',
            'font_size': 10,
            'bold': False,
        })

        # Write headers and content
        headers = [
            "رقم التسلسل",
            "رقم العقد",
            "اسم العميل",
            "المبلغ المدفوع",
            "تاريخ السداد",
            "البكت إثناء السداد",
            "حالة السداد",
        ]

        for col, header in enumerate(headers):
            sheet.write(0, col, header, title_format)

        # Filter loan orders by payment date within the current month
        loan_data = self.env['loan.order'].search(
            [('state', '=', 'active'),
             ('last_paid_installment_date', '>=', current_month_start),
             ('last_paid_installment_date', '<', next_month_start)])

        # #------------------------------- | NO | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            sheet.write(row, 0, row, content_format)
            sheet.write(row, 1, f'{order.identification_id}', content_format)

        # # ------------------------------- | Application Number  | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            sheet.write(row, 1, order.seq_num, content_format)

        # # ------------------------------- | Customer Name | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            sheet.write(row, 2, order.name.name, content_format)

        # # ------------------------------- | Paid Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            sheet.write(row, 3, order.last_paid_installment_amount, content_format)

        # # ------------------------------- | Payment Date | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            if isinstance(order.last_paid_installment_date,
                          datetime.date):  # Check if last_paid_installment_date is a date object
                sheet.write(row, 4, order.last_paid_installment_date.strftime('%d/%m/%Y'), content_format)
            else:
                sheet.write(row, 4, '', content_format)

        # # ------------------------------- | BKT | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            sheet.write(row, 5, order.bkt + 1, content_format)

        # # ------------------------------- | Status | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            sheet.write(row, 6, order.state, content_format)

            # ===================================== | End Content Area| ==================================

        # Set column width and row height
        for col in range(len(headers)):
            sheet.set_column(col, col, 27)  # Set column width to 20

        # Close workbook
        workbook.close()

        # Reset the buffer position to the beginning
        excel_buffer.seek(0)

        # Read and encode the generated Excel file from the buffer
        ex_report = base64.b64encode(excel_buffer.getvalue())

        # Create the report record
        excel_report_id = self.env['save.ex.report.wizard'].create({
            "file_name": ex_report,
            "document_frame": "Payment Report"
        })

        # Return action to download the report
        return {
            'res_id': excel_report_id.id,
            'name': 'Files to Download',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'save.ex.report.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
