# -*- coding: utf-8 -*-

from dataclasses import field
from email.policy import default
import random
from datetime import datetime, timedelta
import string
from odoo import models, fields, api, _


class CrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'portal.mixin', 'mail.thread', 'mail.activity.mixin']

    def _compute_access_url(self):
        super(CrmLead, self)._compute_access_url()
        for record in self:
            record.access_url = '/my/application/%s' % (record.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return _('Funding Application-%s') % (self.name)


class Quotation(models.Model):
    _name = 'hospital.quotation'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'seq'
    _description = 'Hospital Quotation'
    _order = "id desc"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')
    ])
    # seq = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('hospital.quotation.seq'))
    seq = fields.Char(string='Sequence')

    contract_name = fields.Char()
    contract_date = fields.Date()

    department_name = fields.Char(string='Department Name')
    clinic_name = fields.Char(string='Clinic Name')
    doctor_name = fields.Char(string='Doctor Name')

    # customer_name = fields.Many2one("res.partner", required=True, string='Customer Name')
    product_ids = fields.One2many('hospital.quotation.line', 'quotation_id')

    service = fields.Char(string="Service")
    patient_id = fields.Char(string="Patient Id")
    patient_name = fields.Char(string="Patient Name")
    service_amount = fields.Float(compute="_get_service_amount")

    email = fields.Char()
    phone = fields.Char()
    name = fields.Char()
    description = fields.Text()
    # clinic_user_id = fields.Many2one('res.users', default=lambda self: self.create_uid.id)
    clinic_user_id = fields.Char()
    activity_user_id = fields.Many2one('res.users')

    customer_id = fields.Char("Customer ID")
    customer_name = fields.Char("Customer Name")
    customer_phone = fields.Char("Customer phone")
    customer_amount = fields.Float("Amount")

    def _get_service_amount(self):
        for rec in self:
            amount = 0
            for line in rec.product_ids:
                amount += line.amount
            rec.service_amount = amount

    def _compute_access_url(self):
        super(Quotation, self)._compute_access_url()
        for record in self:
            record.access_url = '/my/quotations/%s' % (record.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return _('Hospital Quotation-%s') % (self.seq)

    def action_approve(self):
        """
            change document state and create a purchase order
        """
        for rec in self:
            purchase_data = {
                'partner_id': rec.create_uid.partner_id.id,
                'date_approve': datetime.now(),
                'user_id': rec.create_uid.id,
            }
            data = []
            for product in rec.product_ids:
                data.append((0, 0, {
                    'product_id': product.product_id.id,
                    'price_unit': product.amount,
                }))
            purchase_data.update({
                'order_line': data
            })
            purchase_order = self.env['purchase.order'].create(purchase_data)
            users = self.env.ref('purchase.group_purchase_user').users.ids
            user_id = self.env.user.id
            # random_id = user_id
            # while random_id == user_id:
            # index = random.randrange(len(users))
            # random_id = users[index]
            activity_object = self.env['mail.activity']
            activity_values = self.create_activity(rec.activity_user_id.id, purchase_order.id, 'purchase.order',
                                                   'purchase.model_purchase_order')
            activity_id = activity_object.create(activity_values)
            rec.write({'state': 'approved'})

    def create_activity(self, user_id, record_id, model_name, model_id):
        """
            return a dictionary to create the activity
        """
        return {
            'res_model': model_name,
            'res_model_id': self.env.ref(model_id).id,
            'res_id': record_id,
            'summary': "My Summary",
            'note': "my note",
            'date_deadline': datetime.today(),
            'user_id': user_id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
        }


class QuotationLines(models.Model):
    _name = 'hospital.quotation.line'

    quotation_id = fields.Many2one('hospital.quotation')
    product_id = fields.Char()
    # product_id = fields.Many2one('product.product')
    amount = fields.Float()
    quantity = fields.Integer(default=1)
    price = fields.Float(default=1)

    @api.onchange('quantity', 'price')
    def get_amount(self):
        """
            amount = price * quantity
        """
        self.amount = self.price * self.quantity


class ExpressionOfDesire(models.Model):
    _name = 'expression.of.desire'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Expression of desire'

    name = fields.Char()
    id_number = fields.Char()
    phone_number = fields.Char()
    # don't know if it a selection or what so for now it's just a string
    loan_type = fields.Char()
    service_provider = fields.Char()
    service_amount = fields.Float()
    actual_beneficiary = fields.Char()

    def _compute_access_url(self):
        super(ExpressionOfDesire, self)._compute_access_url()
        for record in self:
            record.access_url = '/my/expression_of_desire/%s' % (record.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return _('Expression of desire-%s') % (self.name)


class HealthDeclaration(models.Model):
    _name = 'health.declaration'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Health Declaration Form for customer'

    name = fields.Char("Full Name", size=70)
    weight = fields.Float()
    Height = fields.Float()
    birth_date = fields.Date()
    place_of_birth = fields.Char(size=60)
    martial_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
    ])
    work_nature = fields.Selection([
        ('civilian', 'Civilian'),
        ('military', 'Military'),
        ('other', 'Other'),
    ])
    other_work_nature = fields.Char()
    address = fields.Char()
    loan_amount = fields.Float()
    loan_period = fields.Integer()
    phone = fields.Char()
    # 
    unable_to_work_now_flag = fields.Boolean("Are you unable to work now ?")
    unable_to_work_now_text = fields.Text()
    # 
    unable_to_work_thirty_days_flag = fields.Boolean(
        "Have you been unable to work for 30 consecutive days during the last five years?")
    unable_to_work_thirty_days_text = fields.Text()
    # 
    suffered_accident_serious_damage_flag = fields.Boolean("Have you suffered any accident caused you serious damage")
    suffered_accident_serious_damage_text = fields.Text()
    # 
    disability_total_or_partial_flag = fields.Boolean(
        "Do you have any disability , total disability or partial disability?")
    disability_total_or_partial_text = fields.Text()
    # 
    treatment_fourteen_days_past_two_years_flag = fields.Boolean(
        "Have you taken any treatment or medication for more than 14 consecutive days during the past (2) years to treat a disease (leg for, blood pressure, diabetes, cholesterol, or other diesels")
    treatment_fourteen_days_past_two_years_text = fields.Text()
    # 
    heart_failure_flag = fields.Boolean("Heart Failure")
    # 
    diabetes_seven_kinds_flag = fields.Boolean("Diabetes of any kind 7")
    # 
    cancer_flag = fields.Boolean("Any kind of cancer disease?")
    # 
    hepatitis_flag = fields.Boolean("Hepatitis?")
    # 
    reheumatic_fever_umatoid_arthrits_flag = fields.Boolean("Rheumatic fever and the umatoid arthritis?")
    # 
    chronic_diseases_flag = fields.Boolean(
        "Have you been diagnosed with any of the following chronic diseases limited to: Autism, Benign Tumor, Cancer, Heart Diseases, Chronic Hepatitis C, Gallstones, Kidney failure, Urinary tract stones, thyroid goiter, Cysts, fibroid uterus, Hernias, autoimmune diseases or Multiple sclerosis.")
    # 
    high_cholestrerol_flag = fields.Boolean("High cholesterol?")
    # 
    athma_bronchitis_flag = fields.Boolean("Asthma, bronchitis or other chest problems?")
    # 
    difficult_digestion_colon_flag = fields.Boolean(
        "Difficulty digestion with or without ulceration and inflammation In the colon?")
    # 
    thyroid_anemia_flag = fields.Boolean("Thyroid, anemia, bloated glands?")
    # 
    long_medical_condition_flag = fields.Boolean("Has/Had long medical condition?")
    # 
    hiv_aids_flag = fields.Boolean("HIV/ AIDS, AIDS?")
    # 
    psychiatric_illness_flag = fields.Boolean("Any psychiatric illness?")

    def _compute_access_url(self):
        super(HealthDeclaration, self)._compute_access_url()
        for record in self:
            record.access_url = '/my/health_declaration/%s' % (record.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return _('Health Declaration-%s') % (self.name)
