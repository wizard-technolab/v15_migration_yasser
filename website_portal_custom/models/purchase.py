# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import random
from pyexpat import model
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    email_formatted = fields.Char(
        'Formatted Email',
        help='Format email address "Name <email@domain>"')

    def action_acceptance(self):
        """
            change state to acceptance
        """
        for rec in self:
            rec.write({'state': 'acceptance'})

    def change_state(self, order):
        """
            change the state of purchase order and return a get_portal_url
        """
        url = order.get_portal_url()
        url = url.split('?')
        new_url = url[0] + '/accept?' + url[1]
        return new_url

    def send_to_clinic(self):
        """
            send the email to the clinic
        """
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        template = self.env.ref('website_portal_custom.mail_template_sent_to_clinic', raise_if_not_found=False)
        port_url = self.get_portal_url()
        base_url = base_url + port_url
        ctx = dict(self._context)
        ctx.update({
            'base_url': base_url,
            # 'model': self._name,
            # 'action_id': action_id,
        })
        template.sudo().with_context(ctx).send_mail(self.id, force_send=True)
        self.button_confirm()

    def create_activity(self):
        users = self.env.ref('purchase.group_purchase_user').users.ids
        user_id = self.env.user.id
        random_id = user_id
        while random_id == user_id:
            random_id = random.choice(users)
        activity_object = self.env['mail.activity']
        activity_values = self.get_activity_data(random_id, self.id, 'purchase.order', 'purchase.model_purchase_order')
        activity_id = activity_object.sudo().create(activity_values)

    def get_activity_data(self, user_id, record_id, model_name, model_id):
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
