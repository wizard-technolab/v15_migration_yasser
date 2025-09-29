from collections import defaultdict
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class DailyReportWizard(models.TransientModel):
    _name = 'daily.report.wizard'
    _description = 'Daily Report Wizard'

    date_start = fields.Date(string="Start Date", required=True, default=fields.Date.today)
    date_end = fields.Date(string="End Date", required=True, default=fields.Date.today)
    module_type = fields.Selection([('all', 'All'), ('loan', 'Loan'), ('crm', 'CRM')], string="Module Type",
                                   default='all')

    def generate_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
                'module_type': self.module_type,
            },
        }
        return self.env.ref('fuel_report.action_daily_report').report_action(self, data=data)


class DailyReport(models.AbstractModel):
    _name = 'report.fuel_report.report_daily_template'
    _description = 'Daily Report'

    def _get_report_values(self, docids, data=None):
        # Extract start and end dates from the form data and convert them to datetime.date objects
        start_date = datetime.strptime(data['form']['date_start'], "%Y-%m-%d").date()
        end_date = datetime.strptime(data['form']['date_end'], "%Y-%m-%d").date()
        module_type = data['form'].get('module_type')

        # Calculate start and end dates for the previous week
        previous_week_start = start_date - timedelta(days=start_date.weekday() + 7)
        previous_week_end = previous_week_start + timedelta(days=6)

        # Calculate start and end dates for the previous month
        previous_month_start = start_date.replace(day=1) - timedelta(days=1)
        previous_month_end = previous_month_start.replace(day=1)

        # Initialize dictionaries to store request counts for each day of the week
        salesperson_data = defaultdict(lambda: defaultdict(int))
        credit_user_data = defaultdict(lambda: defaultdict(int))
        status_data = defaultdict(lambda: defaultdict(int))
        total_loan_amount_by_status = defaultdict(lambda: defaultdict(float))

        # Define all days of the week
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Get CRM leads and loan orders within the specified date range
        leads = self.env['crm.lead'].search([
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date),
        ])
        orders = self.env['loan.order'].search([
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date),
        ])

        # If there are no leads or orders, raise an AccessError indicating no data
        if not leads and not orders:
            raise ValidationError(_('No data available for the selected date range.'))

        # Count CRM leads by salesperson for each day of the week
        for lead in leads:
            day_of_week = lead.create_date.strftime('%A')
            salesperson_data[lead.user_id.name][day_of_week] += 1

        # Count loan orders by credit user for each day of the week
        for order in orders:
            day_of_week = order.create_date.strftime('%A')
            credit_user_data[order.credit_user.name][day_of_week] += 1

            # Count orders by status for each day of the week
            status_display_name = dict(self.env['loan.order']._fields['state'].selection).get(order.state)
            status_data[status_display_name][day_of_week] += 1

            # Accumulate loan amount for each status and each day of the week
            total_loan_amount_by_status[status_display_name][day_of_week] += order.loan_amount

        # Fill in missing days with zero counts for each salesperson, credit user, and status
        for data_dict in [salesperson_data, credit_user_data, status_data]:
            for person_or_status in data_dict:
                for day in days_of_week:
                    if day not in data_dict[person_or_status]:
                        data_dict[person_or_status][day] = 0

        # Calculate total requests for the previous week and previous month for each salesperson and credit user
        for person_data in [salesperson_data, credit_user_data]:
            for person in person_data:
                previous_week_total = sum(person_data[person][day] for day in person_data[person] if
                                          previous_week_start <= datetime.strptime(day, '%A').date() <= previous_week_end)
                previous_month_total = sum(person_data[person][day] for day in person_data[person] if
                                           previous_month_start <= datetime.strptime(day, '%A').date() <= previous_month_end)

                person_data[person]['Previous Week Total'] = previous_week_total
                person_data[person]['Previous Month Total'] = previous_month_total

        # Calculate total orders for each status for the previous week and previous month
        for status_counts in status_data.values():
            previous_week_total = sum(status_counts[day] for day in status_counts if
                                      previous_week_start <= datetime.strptime(day, '%A').date() <= previous_week_end)
            previous_month_total = sum(status_counts[day] for day in status_counts if
                                       previous_month_start <= datetime.strptime(day, '%A').date() <= previous_month_end)

            status_counts['Previous Week Total'] = previous_week_total
            status_counts['Previous Month Total'] = previous_month_total

        # Add total loan amount for each loan status for the previous week and previous month
        previous_week_total_amount = 0.0
        previous_month_total_amount = 0.0
        for status, amount_by_day in total_loan_amount_by_status.items():
            # Calculate total amount for the previous week
            previous_week_total_amount += sum(amount_by_day[day] for day in amount_by_day if
                                               previous_week_start <= datetime.strptime(day, '%A').date() <= previous_week_end)
            # Calculate total amount for the previous month
            previous_month_total_amount += sum(amount_by_day[day] for day in amount_by_day if
                                                previous_month_start <= datetime.strptime(day, '%A').date() <= previous_month_end)

            # Add total amounts to the status_data dictionary
            status_data[status]['Previous Week Total Amount'] = round(previous_week_total_amount, 4)
            status_data[status]['Previous Month Total Amount'] = round(previous_month_total_amount, 4)

        # Initialize total_amount_by_day with all days of the week and initial values of 0.0
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        total_amount_by_day = {day: 0.0 for day in days_of_week}

        # Loop through each status and day to calculate the total amount
        for status, status_amounts in total_loan_amount_by_status.items():
            for day, amount in status_amounts.items():
                # Add the amount for the current status and day to the total amount for the day
                total_amount_by_day[day] += amount

        # Include the "Previous Week Total Amount" and "Previous Month Total Amount" in total_amount_by_day
        total_amount_by_day['Previous Week Total Amount'] = round(previous_week_total_amount, 4)
        total_amount_by_day['Previous Month Total Amount'] = round(previous_month_total_amount, 4)

        # Print the updated total_amount_by_day dictionary

        # Loop through each status and day to calculate the total orders
        total_counts_by_day = {}
        for status, status_counts in status_data.items():
            for day, count in status_counts.items():
                # Initialize the count for the current day if it's not already initialized
                if day not in total_counts_by_day:
                    total_counts_by_day[day] = 0
                # Add the count for the current status and day to the total count for the day
                total_counts_by_day[day] += count
        return {
            'doc_ids': docids,
            'doc_model': 'daily.report.wizard',
            'start_date': start_date,
            'end_date': end_date,
            'salesperson_data': salesperson_data,
            'credit_user_data': credit_user_data,
            'status_data': status_data,
            'total_loan_amount_by_status': total_loan_amount_by_status,
            'total_counts_by_day': total_counts_by_day,  # Include the total counts by day
            'total_amount_by_day': total_amount_by_day,
            'module_type': module_type,
        }