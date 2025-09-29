import datetime
from io import BytesIO

import xlsxwriter
from odoo import models, fields, api
import base64


class SimahReport(models.TransientModel):
    _name = 'simah.report'
    _description = 'SIMAH Report'

    def generate_excel_report(self):
        # Create a BytesIO object to hold the Excel workbook in memory
        excel_buffer = BytesIO()

        # Create a new Excel workbook
        workbook = xlsxwriter.Workbook(excel_buffer)

        sheet = workbook.add_worksheet('Simah Report')

        # Define title format
        title_format = workbook.add_format({
            'bold': False,
            'valign': 'vcenter',
            'align': 'center',
            'font_size': 10,
            'bg_color': 'yellow',  # Yellow background color
        })

        # Define Abbreviations format
        abbreviations_format = workbook.add_format({
            'bold': False,
            'valign': 'vcenter',
            'align': 'left',
            'font_size': 10,
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
            "Credit Instrument Number",
            "Issue Date",
            "Product Type",
            "Product Limit / Original Amount",
            "Salary Assignment Flag",
            "Product Expiry Date",
            "Product Status",
            "Instalment Amount",
            "Average Instalment Amount",
            "Payment Frequency",
            "Tenure",
            "Security Type",
            "Down Payment",
            "Balloon Payment",
            "Dispensed Amount",
            "Max Instalment Amount",
            "Sub Product Type",
            "Total leasing amount",
            "Reason For Closure Code",
            "Factoring Flag",
            "Installment Start date",
            "Installment amount",
            "Installment Start date",
            "Installment amount",
            "Installment Start date",
            "Installment amount",
            "Installment Start date",
            "Installment amount",
            "Installment Start date",
            "Installment amount",
            "Contract Number",
            "First Installment date",
            "Cost Rate",
            "Amount Rate",
            "Fixed Rate",
            "Number of credit instrument holders",
            "Cycle ID",
            "Last Payment Date",
            "Last Amount Paid",
            "Payment Status",
            "Outstanding balance",
            "Past Due balance",
            "As of Date",
            "Next payment Date",
            "Prefer Method of payment",
            "Number of paid Instalment",
            "Early Payoff",
            "Number of unpaid Instalment",
            "Amount paid to 3rd party",
            "Right of Withdrawal Code",
            "APR percentage",
            "Termination Procedure Code",
            "Ownership Change Code",
            "Amount of ownership as per the law",
            "Admin & Notarial Fees",
            "Payment Type",
            "Amount of pending future installments",
            "Amount of unpaid installments",
            "ID type",
            "Consumer ID",
            "ID Expiration Date",
            "National ID / Iqama issuing place",
            "Marital status",
            "Nationality code",
            "Family Name - Arabic",
            "First Name - Arabic",
            "CNM2A",
            "CNM3A",
            "Full Name - Arabic",
            "Family name - English",
            "First name - English",
            "CNM2E",
            "CNM3E",
            "Full Name - English",
            "Date Of Birth",
            "Gender",
            "Number of Dependence",
            "Applicant Type",
            "Percentage Allocation",
            "Applicant Outstanding Balance",
            "Applicant Limit",
            "Applicant Last Amount Paid",
            "Applicant Instalment Amount",
            "Applicant Last Payment Date",
            "Applicant Next Due Date",
            "Applicant Past Due Balance",
            "Applicant Payment Status",
            "Building Number",
            "Street English",
            "Street Arabic",
            "District English",
            "District Arabic",
            "Additional Number",
            "Until Number",
            "Building Number",
            "Street English",
            "Street Arabic",
            "District English",
            "District Arabic",
            "Additional Number",
            "Unit Number",
            "Other income",
        ]

        abbreviations = [
            "AREF",
            "AOPN",
            "APRD",
            "ALMT",
            "ASAL",
            "AEXP",
            "APST",
            "AINST",
            "AVINST",
            "AFRQ",
            "ATNR",
            "ASEC",
            "ADWNP",
            "ABPAY",
            "ADAMT",
            "AMAX",
            "ASP",
            "ATLEAMT",
            "ACLSRESON",
            "AFACTORING",
            "STRTINSDT1",
            "INSAMT1",
            "STRTINSDT2",
            "INSAMT2",
            "STRTINSDT3",
            "INSAMT3",
            "STRTINSDT4",
            "INSAMT4",
            "STRTINSDT5",
            "INSAMT5",
            "CONTRACTNO",
            "FRSTINSDT",
            "CSTRATE",
            "AMTRATE",
            "FIXRATE",
            "ACON",
            "ACYCID",
            "ALSPD",
            "ALSTAM",
            "AACS",
            "ACUB",
            "AODB",
            "AASOF",
            "ANXPD",
            "PMETHPAY",
            "PNOPI",
            "PECCC",
            "PNOUI",
            "PAPTP",
            "PDRW",
            "PAPR",
            "PDTP",
            "PDOC",
            "PDOWN",
            "PDAF",
            "PAYTYPE",
            "AMTPNDFINS",
            "AMTUNPINS",
            "CID1",
            "CID2",
            "CID3",
            "CID4",
            "CMAR",
            "CNAT",
            "CNMFA",
            "CNM1A",
            "CNM2A",
            "CNM3A",
            "CNMUA",
            "CNMFE",
            "CNM1E",
            "CNM2E",
            "CNM3E",
            "CNMUE",
            "CDOB",
            "CGND",
            "CINOI",
            "CAPL",
            "CPER",
            "COUTBAL",
            "CAPPLIMIT",
            "CLAP",
            "CINSTAMT",
            "CPLD",
            "CNDDATE",
            "CPDB",
            "CPAYSTS",
            "CADBNUM",
            "CADBSTR",
            "CADBSTRU",
            "CADDIS",
            "CADDISU",
            "CADADNU",
            "CADUNTNUM",
            "EADBNUM",
            "EADBSTR",
            "EADBSTRU",
            "EADDIS",
            "EADDISU",
            "EADADNU",
            "EADUNTNUM",
            "EITHI",
        ]

        # Write headers with title format
        for col, header in enumerate(headers):
            sheet.write(0, col, header, title_format)

        # Write abbreviations below corresponding headers
        for col, abbr in enumerate(abbreviations):
            sheet.write(1, col, abbr, abbreviations_format)

        loan_data = self.env['loan.order'].search(
            [('state', '=', 'active'), ('is_Closed', '=', False), ('is_Stumbled', '=', False)])


        # ===================================== | Content | ==================================

        # ------------------------------- | Credit Instrument Number | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            slice_sequence = f'{order.seq_num}'.split('/')
            new_sequence_format = f'{slice_sequence[1]}{slice_sequence[2]}{slice_sequence[3]}'
            sheet.write(row, 0, f'{new_sequence_format}', content_format)

        # ------------------------------- | Issue Date  | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            # sheet.write(row, 1, order.approve_date.strftime('%d/%m/%Y'), content_format)
            if order.approve_date:
                sheet.write(row, 1, order.approve_date.strftime('%d/%m/%Y'), content_format)
            else:
                sheet.write(row, 1, '', content_format)

        # ------------------------------- | Product Type  | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            if order.is_reschedule:
                sheet.write(row, 2, 'RPLN', content_format)
            else:
                sheet.write(row, 2, order.loan_type.product_type.upper(), content_format)

        # ------------------------------- | Product Limit / Original Amount  | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 3, order.loan_amount_positive, content_format)

        # ------------------------------- | Salary Assignment Flag  | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 4, 'N', content_format)

        # ------------------------------- | Product Expiry Date  | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            if order.is_reschedule:
                sheet.write(row, 5, order.reschedule_installment_end_date.strftime('%d/%m/%Y'), content_format)
            else:
                sheet.write(row, 5, order.installment_end_date.strftime('%d/%m/%Y'), content_format)

        # ------------------------------- | Product Status  | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            total_installments = len(order.installment_ids)
            paid_installments = sum(
                1 for installment in order.installment_ids if installment.state == 'paid')
            if total_installments == paid_installments:
                sheet.write(row, 6, "C", content_format)
            else:
                unpaid_count = 0
                for installment in order.installment_ids:
                    if installment.date < datetime.datetime.now().date() and installment.state != 'paid':
                        unpaid_count += 1
                print(total_installments, "LLLLLLLLLLLLLLLLLLLLL", unpaid_count)
                if unpaid_count > 6:
                    sheet.write(row, 6, "W", content_format)
                else:
                    sheet.write(row, 6, order.product_status, content_format)

        # ------------------------------- | Installment Amount  | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            if order.is_reschedule:
                sheet.write(row, 7, '{:.2f}'.format(order.reschedule_installment_amount), content_format)
            else:
                sheet.write(row, 7, '{:.2f}'.format(order.installment_month), content_format)

        # ------------------------------- | Average Instalment Amount | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            if order.is_reschedule:
                sheet.write(row, 8, '{:.2f}'.format(order.reschedule_installment_amount),content_format)
            else:
                sheet.write(row, 8, '{:.2f}'.format(order.installment_month),content_format)

        # ------------------------------- | Payment Frequency | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 9, 'M', content_format)

        # ------------------------------- | Tenure | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            if order.is_reschedule:
                sheet.write(row, 10, order.reschedule_loan_term, content_format)
            else:
                sheet.write(row, 10, order.loan_term, content_format)

        # ------------------------------- | Security Type | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 11, 'NO', content_format)

        # ------------------------------- | Down Payment | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 12, '0', content_format)

        # ------------------------------- | Balloon Payment | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 13, '0', content_format)

        # ------------------------------- | Dispensed Amount | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 14, '0', content_format)

        # ------------------------------- | Max Instalment Amount | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 15, '0', content_format)

        # ------------------------------- | Sub Product Type | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 16,
                        dict(self.env['loan.type']._fields['sub_product'].selection).get(order.loan_type.sub_product),
                        content_format)

        # ------------------------------- | Cycle ID | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            today_date = f'{datetime.date.today()}'.split('-')
            cycle_id_date_format = f'{today_date[0]}{today_date[1]}{today_date[2]}'
            sheet.write(row, 36, cycle_id_date_format, content_format)

        # ------------------------------- | Payment Status | ------------------------------
        # Function to check if dates are consecutive
        # def are_dates_consecutive(dates):
        #     return all(date == prev_date + datetime.timedelta(days=1) for prev_date, date in zip(dates, dates[1:]))
        #
        # def are_dates_consecutive_and_paid(installments):
        #     # Extract and sort dates of paid installments
        #     paid_dates = sorted(installment['date'] for installment in installments if installment['state'] == 'paid')
        #
        #     # Check if each date is one day after the previous date
        #     return all(
        #         paid_dates[i] == paid_dates[i - 1] + datetime.timedelta(days=1) for i in range(1, len(paid_dates)))

        for row, order in enumerate(loan_data, start=2):
            
            if order.is_reschedule:
                total_installments = len(order.reschedule_installment_ids)
                paid_installments = sum(1 for installment in order.reschedule_installment_ids if installment.state == 'paid')

                # Check if all installments are paid
                if total_installments == paid_installments:
                    order.is_Closed = True
                    sheet.write(row, 39, "C", content_format)
                else:
                    unpaid_overdue_count = 0
                    # installment_dates = [installment.date for installment in order.installment_ids if
                    #                      installment.state == 'paid']

                    # Check if payment is regular
                    if order.reschedule_late_amount == 0:
                        sheet.write(row, 39, "0", content_format)  # Regular payment
                    else:
                        # Check if installment is overdue and unpaid
                        for installment in order.reschedule_installment_ids:
                            if installment.date < datetime.datetime.now().date() and installment.state != 'paid':
                                unpaid_overdue_count += 1
                        # Check If Stumbled
                        if unpaid_overdue_count > 6:
                            sheet.write(row, 39, "W", content_format)
                            order.is_Stumbled = True
                        else:
                            # Write the total count of unpaid installments
                            sheet.write(row, 39, unpaid_overdue_count, content_format)

#if it not reschedule
            else:
                total_installments = len(order.installment_ids)
                paid_installments = sum(1 for installment in order.installment_ids if installment.state == 'paid')

                # Check if all installments are paid
                if total_installments == paid_installments:
                    order.is_Closed = True
                    sheet.write(row, 39, "C", content_format)
                else:
                    unpaid_overdue_count = 0
                    # installment_dates = [installment.date for installment in order.installment_ids if
                    #                      installment.state == 'paid']

                    # Check if payment is regular
                    if order.late_amount == 0:
                        sheet.write(row, 39, "0", content_format)  # Regular payment
                    else:
                        # Check if installment is overdue and unpaid
                        for installment in order.installment_ids:
                            if installment.date < datetime.datetime.now().date() and installment.state != 'paid':
                                unpaid_overdue_count += 1
                        # Check If Stumbled
                        if unpaid_overdue_count > 6:
                            sheet.write(row, 39, "W", content_format)
                            order.is_Stumbled = True
                        else:
                            # Write the total count of unpaid installments
                            sheet.write(row, 39, unpaid_overdue_count, content_format)
        # ------------------------------- | Outstanding balance | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            if order.is_reschedule:
                sheet.write(row, 40, '{:.2f}'.format(order.reschedule_remaining_total_amount), content_format)
            else:
                sheet.write(row, 40, '{:.2f}'.format(order.remaining_amount), content_format)

        # ------------------------------- | Past Due balance | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            if order.is_reschedule:
                sheet.write(row, 41, '{:.2f}'.format(order.reschedule_late_amount), content_format)
            else:
                unpaid_overdue_count = 0
                for installment in order.installment_ids:
                    if installment.date < datetime.datetime.now().date() and installment.state != 'paid':
                        unpaid_overdue_count += 1
                # Check If Stumbled
                if unpaid_overdue_count > 6:
                    sheet.write(row, 41, '{:.2f}'.format(order.remaining_amount), content_format)
                else:
                    sheet.write(row, 41, '{:.2f}'.format(order.late_amount), content_format)


        # ------------------------------- | As of Date | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            today_date = datetime.date.today()
            sheet.write(row, 42, today_date.strftime('%d/%m/%Y'), content_format)

        # ------------------------------- | ID type | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 58, 'T', content_format)

        # ------------------------------- | Consumer ID | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 59, order.identification_id, content_format)

        # ------------------------------- | Nationality code | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 63, 'SAU', content_format)

        # ------------------------------- | Full Name - Arabic  | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 68, order.name.name, content_format)

        # ------------------------------- |  Gender | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 75, order.gender_loan, content_format)

        # ------------------------------- |  Applicant Type | ------------------------------
        for row, order in enumerate(loan_data, start=2):
            sheet.write(row, 77, order.applicant_type, content_format)

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
            "document_frame": "Simah Report"
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
