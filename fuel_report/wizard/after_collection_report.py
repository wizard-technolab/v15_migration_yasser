import datetime
from io import BytesIO
from datetime import datetime, timedelta, date
import xlsxwriter
from odoo import models, fields, api
import base64


class AfterCollectionReport(models.TransientModel):
    _name = 'after.collection.report'
    _description = 'After Collection Report'

    def after_collection_excel_report(self):
        # Create a BytesIO object to hold the Excel workbook in memory
        excel_buffer = BytesIO()

        # Create a new Excel workbook
        workbook = xlsxwriter.Workbook(excel_buffer)

        sheet = workbook.add_worksheet('Collection Report - 1')

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

        reschedule_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'align': 'center',
            'font_size': 10,
            'bold': False,
            'bg_color': 'yellow',  # Light blue color
        })
        # Write headers and content
        headers = [
            "رقم الهوية",
            "رقم العقد",
            "اسم العميل",
            "رقم الجوال",
            "الجنسية",
            "جنس",
            "عمر العميل",
            "القطاع",
            "جهة العميل",
            "المسمى الوظيفي",
            "المنطقة",
            "المدينة",
            "نوع العميل",
            "صافي الدخل",
            "الالتزام الكلي",
            "نتيجة المخاطر SIMAH",
            "درجة مخاطر العميل",
            "أصل التمويل",
            "مبلغ الربح",
            "مدة العقد",
            "القسط الشهري",
            "نوع التمويل",
            "تاريخ الموافقة",
            "شهر الصرف",
            "تاريخ الصرف",
            "تاريخ اول قسط",
            "تاريخ اخر قسط",
            "تاريخ الاستحقاق الحالي",
            "تاريخ اخر سداد",
            "اجمالي المبالغ المدفوعة",
            "مبلغ اخر سداد",
            "اجمالي المتأخرات",
            "BKT",
            "عدد ايام التأخير",
            "رأس المال المتبقي",
            "الارباح المتبقية",
            "اجمالي المبلغ المتبقي",
            "حالة العقد",
            "اسم المحصل",
        ]

        # Write headers with title format
        for col, header in enumerate(headers):
            sheet.write(0, col, header, title_format)

        today = datetime.now()
        current_month_due_date = today.replace(day=27)

        # Start of the current month
        first_day_of_current_month = today.replace(day=1)

        if today.month == 12:  # Handle December to January transition
            next_month_start = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month_start = today.replace(month=today.month + 1, day=1)

        if next_month_start.month == 12:  # Handle December to January transition
            after_next_month_start = next_month_start.replace(year=next_month_start.year + 1, month=1, day=1)
        else:
            after_next_month_start = next_month_start.replace(month=next_month_start.month + 1, day=1)

        # Search for active loans with overdue amounts and a first unpaid installment date before the current month
        loan_data = self.env['loan.order'].search([
            ('state', '=', 'active'),
            ('late_installment', '>', 0),  # Ensure there are overdue amounts
            '|',  # Combine conditions using OR
            ('first_unpaid_installment', '<', first_day_of_current_month),  # Before the current month
            '&',  # Include the following conditions together
            ('first_unpaid_installment', '>=', next_month_start),  # In or after the next month
            ('first_unpaid_installment', '<', after_next_month_start),  # But before the month after the next
        ])

        # loan_data = self.env['loan.order'].search([
        #     ('state', '=', 'active'),
        #     ('late_installment', '>', 0),  # Ensure there are overdue amounts
        #     # Exclude loans with first unpaid installment in the current month
        # ])
        # '|',
        # ('last_paid_installment_date', '<', current_month_due_date),  # Overdue before the current 27th
        # ('first_unpaid_installment', '<', current_month_due_date),  # Check for overdue installments before 27th
        # ('first_unpaid_installment', '<', first_day_of_current_month)
        # Process the loan data
        for customer in loan_data:
            if customer.late_installment > 0:  # Only process if late_installment is greater than 0
                print(f"Name: {customer.name.name}")
                print(f"Remaining Amount: {customer.remaining_amount}")
                print(f"First Unpaid Installment: {customer.first_unpaid_installment}")
                print(f"Last Paid Installment Date: {customer.last_paid_installment_date}")
                print("=" * 50)

        # , ('is_Closed', '=', False), ('is_Stumbled', '=', False)

        # ===================================== | Content | ==================================

        # ------------------------------- | ID Number | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            slice_sequence = f'{order.identification_id}'
            # new_sequence_format = f'{slice_sequence[1]}{slice_sequence[2]}{slice_sequence[3]}'
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 0, f'{slice_sequence}', row_format)

        # # ------------------------------- | Application Number  | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 1, order.seq_num, row_format)
        #
        # # ------------------------------- | Customer Name | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 2, order.name.name, row_format)
        #
        # # ------------------------------- |Phone number  | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 3, order.phone_customer, row_format)
        #
        # # ------------------------------- | Nationality  | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 4, 'SAU', row_format)
        #
        # # ------------------------------- | Gender  | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 5, order.name.gender_elm, row_format)
        #
        # # ------------------------------- | Age  | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 6, order.name.age, row_format)
        #
        # # ------------------------------- | Sector  | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 7, order.name.sectors, row_format)
        #
        # # ------------------------------- | Employer | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 8, order.name.employer, row_format)
        #
        # # ------------------------------- | Position | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 9, order.name.position, row_format)
        #
        # # ------------------------------- | Regin | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.name.region:
                selection_dict = dict(order.name.fields_get(allfields=['region'])['region']['selection'])
                region_label = selection_dict.get(order.name.region)
                sheet.write(row, 10, region_label, row_format)
            else:
                sheet.write(row, 10, "No Region", row_format)

        #
        # # ------------------------------- | City | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.name.elm_res_partner.elm_city:
                sheet.write(row, 11, order.name.elm_res_partner.elm_city, row_format)
            elif order.name.elm_address_line_ids:
                # If elm_city is not available, check elm_address_line_ids
                city_name = order.name.elm_address_line_ids[0].city if order.name.elm_address_line_ids else ""
                sheet.write(row, 11, city_name, row_format)
            else:
                # If both fields are unavailable, write an empty string
                sheet.write(row, 11, '', row_format)

        #
        # # ------------------------------- | Customer Type | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 12, 'فرد', row_format)
        #
        # # ------------------------------- | Net Salary | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 13, order.name.salary_rate, row_format)
        #
        # # ------------------------------- | All Liabilities  | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 14, order.name.number_liability, row_format)

        # # ------------------------------- | Simah Risk | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 15, order.name.risk, row_format)
        #
        # # ------------------------------- | Simah Score | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.simahScore:
                simah_score = order.simahScore[0]  # Take the first record
                sheet.write(row, 16, simah_score.score, row_format)
            # sheet.write(row, 16, order.simahScore.score, content_format)
        #
        # # ------------------------------- | Loan Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                sheet.write(row, 17, order.reschedule_loan_amount, row_format)
            else:
                sheet.write(row, 17, order.loan_amount, row_format)
        #
        # # ------------------------------- | Interest Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                sheet.write(row, 18, order.reschedule_interest_amount, row_format)
            else:
                sheet.write(row, 18, order.interest_amount, row_format)
        #
        # # ------------------------------- | Loan Term | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                sheet.write(row, 19, order.reschedule_loan_term, row_format)
            else:
                sheet.write(row, 19, order.loan_term, row_format)
        # # ------------------------------- | Installment Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                sheet.write(row, 20, '{:.2f}'.format(order.reschedule_installment_amount), row_format)
            else:
                sheet.write(row, 20, '{:.2f}'.format(order.installment_month), row_format)
        # # ------------------------------- | Loan Type | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 21, order.loan_type.name, row_format)
        #
        # # ------------------------------- | Approve Date | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if isinstance(order.approve_date, date):  # Check if approve_date is a date object
                sheet.write(row, 22, order.approve_date.strftime('%d/%m/%Y'), row_format)
            else:
                sheet.write(row, 22, '', row_format)

        #
        # # ------------------------------- | Month of Disburse | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if isinstance(order.disbursement_date, date):  # Check if disbursement_date is a date object
                sheet.write(row, 23, order.disbursement_date.strftime('%m/%Y'), row_format)
            else:
                sheet.write(row, 23, '', row_format)
        #
        # # ------------------------------- | Disbursement Date| ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if isinstance(order.disbursement_date, date):  # Check if disbursement_date is a date object
                sheet.write(row, 24, order.disbursement_date.strftime('%d/%m/%Y'), row_format)
            else:
                sheet.write(row, 24, '', row_format)
        #
        # # ------------------------------- | Start Installment Date | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                if isinstance(order.reschedule_installment_start_date,
                              date):  # Check if installment_start_date is a date object
                    sheet.write(row, 25, order.reschedule_installment_start_date.strftime('%d/%m/%Y'), row_format)
                else:
                    sheet.write(row, 25, '', row_format)
            else:
                if isinstance(order.installment_start_date, date):  # Check if installment_start_date is a date object
                    sheet.write(row, 25, order.installment_start_date.strftime('%d/%m/%Y'), row_format)
                else:
                    sheet.write(row, 25, '', row_format)
        #
        # # ------------------------------- | Last Installment Date | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                if isinstance(order.reschedule_installment_end_date,
                              date):  # Check if installment_end_date is a date object
                    sheet.write(row, 26, order.reschedule_installment_end_date.strftime('%d/%m/%Y'), row_format)
                else:
                    sheet.write(row, 26, '', row_format)
            else:
                if isinstance(order.installment_end_date, date):  # Check if installment_end_date is a date object
                    sheet.write(row, 26, order.installment_end_date.strftime('%d/%m/%Y'), row_format)
                else:
                    sheet.write(row, 26, '', row_format)
        #
        # # ------------------------------- | Now Installment Date | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            # Check if 'first_unpaid_installment' is already a date object
            if isinstance(order.first_unpaid_installment, date):
                sheet.write(row, 27, order.first_unpaid_installment.strftime('%d/%m/%Y'), row_format)
            else:
                # Debugging: Print the installments and their states
                print(
                    f"Order: {order.id}, Installments: {[{'state': inst.state, 'date': inst.date} for inst in order.installment_ids]}")

                # Find the first unpaid installment manually
                first_unpaid_installment = next(
                    (installment for installment in order.installment_ids if installment.state != 'paid'),
                    None
                )
                if first_unpaid_installment:
                    # Access the 'due_date' attribute and format it
                    if hasattr(first_unpaid_installment, 'date') and isinstance(first_unpaid_installment.date,
                                                                                date):
                        sheet.write(row, 27, first_unpaid_installment.date.strftime('%d/%m/%Y'), row_format)
                    else:
                        # Handle case where 'due_date' is missing or invalid
                        print(f"Invalid date for unpaid installment: {first_unpaid_installment}")
                        sheet.write(row, 27, '', row_format)
                else:
                    # If no unpaid installments are found, write an empty string
                    print(f"No unpaid installments found for order: {order.id}")
                    sheet.write(row, 27, '', row_format)
        #
        # # ------------------------------- |  Last Payment Date | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.last_paid_installment_date:  # Check if the field is not False or None
                sheet.write(row, 28, order.last_paid_installment_date.strftime('%d/%m/%Y'), row_format)
            else:
                sheet.write(row, 28, '', row_format)


        #
        # # ------------------------------- |  Paid Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                sheet.write(row, 29, order.reschedule_paid_amount, row_format)
            else:
                sheet.write(row, 29, order.paid_amount, row_format)

        # # ------------------------------- |  Last Payment Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 30, order.last_paid_installment_amount, row_format)

        # # ------------------------------- |  Late Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                sheet.write(row, 31, order.reschedule_late_amount, row_format)
            else:
                sheet.write(row, 31, order.late_amount, row_format)

        # # ------------------------------- |  BKT | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 32, order.bkt, row_format)

        # # ------------------------------- |  Days Of Late | ------------------------------
        # for row, order in enumerate(loan_data, start=1):
        #         sheet.write(row, 33, order.days_since_first_unpaid, content_format)
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            # Check if bkt is less than or equal to 0
            if order.bkt <= 0:
                days_since_first_unpaid = 0
            else:
                days_since_first_unpaid = order.days_since_first_unpaid

            # Write the value to the sheet
            sheet.write(row, 33, days_since_first_unpaid, row_format)

        # # ------------------------------- |  Remaining Loan Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                sheet.write(row, 34, order.reschedule_remaining_principle_amount, row_format)
            else:
                sheet.write(row, 34, order.remaining_principle, row_format)

        # # ------------------------------- |  Remaining Interest Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                sheet.write(row, 35, order.reschedule_remaining_interest_amount, row_format)
            else:
                sheet.write(row, 35, order.remaining_interest, row_format)

        # # ------------------------------- |  Remaining Total Amount | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            if order.is_reschedule:
                sheet.write(row, 36, order.reschedule_remaining_total_amount, row_format)
            else:
                sheet.write(row, 36, order.remaining_amount, row_format)

        # # ------------------------------- |  Status of Loan | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            row_format = reschedule_format if order.is_reschedule else content_format
            sheet.write(row, 37, order.state, row_format)

        # # ------------------------------- |  Collection User | ------------------------------
        for row, order in enumerate(loan_data, start=1):
            pass
            # sheet.write(row, 38, order.user.name, content_format)

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
            "document_frame": "Collection Report - 1"
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
