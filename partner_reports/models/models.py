# -*- coding: utf-8 -*-

from decimal import Clamped
from email.policy import default
from statistics import mode
from odoo import models, fields, api
import datetime


class PartnerReports(models.Model):
    _name = 'partner.reports'


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    seq = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('crm.lead.seq'))
    application_date = fields.Date(default=datetime.date.today())


class Partner(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(translate=True)
    guarantor_id = fields.Many2one('res.partner')

    # def get_en_ar_name(self, partner, lang):
    #     """
    #         get the name in both arabic and english
    #     """
    #     Envals = partner.with_context({'lang': 'en_US'}).name.split()
    #     Arvals = partner.with_context({'lang': 'ar_AA'}).name.split()
    #
    #     if lang == 'ar':
    #         return Arvals
    #     if lang == 'en':
    #         return Envals

    def get_age(self, partner):
        """
            get the age of the partner
        """
        today = datetime.date.today()
        birthdate = partner.birth_of_date
        age = ''
        if birthdate:
            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        print("...........", age)
        return age

    def get_divided_date(self, recieved_date):
        """
            get day, month and year
        """
        print("\n\n,,,,,,,,,,,,,,,,,", recieved_date)
        if recieved_date:
            return [recieved_date.year, recieved_date.month, recieved_date.day]
        else:
            return [0, 0, 0]
