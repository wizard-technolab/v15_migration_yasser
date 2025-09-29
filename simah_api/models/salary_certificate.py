# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
import requests
from odoo.exceptions import ValidationError


class SalaryCertificate(models.Model):
    _name = 'salary.certificate'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Salary Certificate'

    # Define fields for the salary certificate model
    name = fields.Many2one('res.partner', string='Client')  # Link to the res.partner model
    id_number = fields.Char(related='name.identification_no', string='ID')  # ID number from related partner
    private_sector_ids = fields.One2many('private.sector', 'salary_certificate_id')  # Link to private.sector records

    def action_salary_certificate_data(self):
        '''Fetch salary certificate data from an external API and create private sector records.'''
        url = 'https://fuelfinance.sa/api/simah/reports/salary-certificate'  # API endpoint URL
        headers = {
            'Content-Type': 'application/json'  # Set content type to JSON
        }

        for rec in self:
            national_id = rec.id_number  # Retrieve the ID number
            data = {"national_id": int(national_id)}  # Prepare the data for API request

            # Make a POST request to the API with the provided ID number
            response = requests.post(url, json=data, headers=headers, verify=False)
            dic_re = response.json()  # Parse the response as JSON

            if response.status_code == 200:
                dic_data = dic_re.get('data')  # Extract data from the response
                if dic_data['privateSector']:
                    # Loop through each private sector entry and create corresponding records
                    for privatesector in dic_data['privateSector']['employmentStatusInfo']:
                        rec.private_sector_ids.create({
                            'fullName': privatesector['fullName'],
                            'basicWage': privatesector['basicWage'],
                            'housingAllowance': privatesector['housingAllowance'],
                            'otherAllowance': privatesector['otherAllowance'],
                            'fullWage': privatesector['fullWage'],
                            'dateOfJoining': privatesector['dateOfJoining'],
                            'employerName': privatesector['employerName'],
                            'workingMonths': privatesector['workingMonths'],
                            'employmentStatus': privatesector['employmentStatus'],
                            'salaryStartingDate': privatesector['salaryStartingDate'],
                            'establishmentActivity': privatesector['establishmentActivity'],
                            'commercialRegistrationNumber': privatesector['commercialRegistrationNumber'],
                            'legalEntity': privatesector['legalEntity'],
                            'dateOfBirth': privatesector['dateOfBirth'],
                            'nationality': privatesector['nationality'],
                            'gosinumber': privatesector['gosinumber'],
                            'nationalUnifiedNo': privatesector['nationalUnifiedNo'],
                            'salary_certificate_id': rec.id  # Link back to the current salary certificate
                        })
            else:
                # Raise an error if the API response is not successful
                raise ValidationError(_('Error : "%s" ') % (dic_re.get('messages')))


class PrivateSector(models.Model):
    _name = 'private.sector'
    _description = 'Private Sector'

    # Define fields for the private sector model
    salary_certificate_id = fields.Many2one('salary.certificate')  # Link to the salary certificate
    fullName = fields.Char('Full Name')  # Employee's full name
    basicWage = fields.Float('Basic Wage')  # Employee's basic wage
    housingAllowance = fields.Float('Housing Allowance')  # Employee's housing allowance
    otherAllowance = fields.Float('Other Allowance')  # Employee's other allowances
    fullWage = fields.Float('Full Wage')  # Employee's total wage
    employerName = fields.Char('Employer Name')  # Employer's name
    dateOfJoining = fields.Char('Date Of Joining')  # Date when the employee joined
    workingMonths = fields.Char('Working Months')  # Number of months the employee has worked
    employmentStatus = fields.Char('Employment Status')  # Employment status of the employee
    salaryStartingDate = fields.Char('Salary Starting Date')  # Date when salary started
    establishmentActivity = fields.Char('Establishment Activity')  # Activity of the establishment
    commercialRegistrationNumber = fields.Char('Commercial Registration Number')  # Commercial registration number
    legalEntity = fields.Char('Legal Entity')  # Type of legal entity
    dateOfBirth = fields.Char('Date Of Birth')  # Employee's date of birth
    nationality = fields.Char('Nationality')  # Employee's nationality
    gosinumber = fields.Char('Gosi Number')  # GOSI number
    nationalUnifiedNo = fields.Char('National Unified No')  # National Unified Number