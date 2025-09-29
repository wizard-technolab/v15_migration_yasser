from odoo import api, models, fields
import requests
from datetime import datetime, date, timedelta
import json
import time
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SMS(models.Model):
    _name = 'collection.sms'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Collection SMS module'

    name = fields.Many2one("loan.order", string='Customer', domain=[('state', '=', 'active')],
                           context={'display_seq_only': True})
    # loan_seq_num = fields.Char(related='name.seq_num')
    customer_ids = fields.Many2many("loan.order", string='Customers', domain=[('state', '=', 'active')], tracking=True,
                                    context={'display_seq_only': True})
    massage = fields.Many2one("massage.template", string='Massage')
    status = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')], default='draft', tracking=True)

    def action_send_massage(self):
        config = self.env['collection.configuration'].search([], limit=1)
        if not config:
            raise ValueError("⚠️ No SMS configuration found in 'collection.configuration'.")

        for rec in self:
            phone = rec.name.phone_customer
            if not phone:
                rec.message_post(body="⚠️ No phone number found for the customer.")
                continue

            sms = rec.massage.text
            payload = {
                "userName": config.userName,
                "numbers": phone,
                "userSender": config.userSender,
                "apiKey": config.apiKey,
                "msg": sms
            }

            headers = {
                'Content-Type': config.headers or 'application/json;charset=UTF-8'
            }

            try:
                response = requests.post(
                    url=config.url,
                    data=json.dumps(payload),
                    headers=headers,
                    timeout=60
                )

                config.response = response.text  # save raw response
                # ✅ Mark as sent
                rec.status = 'sent'
                send_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                rec.message_post(
                    body=f"📤 SMS Massage sent successfully to {phone} at {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}",
                    subject="SMS Massage Sent",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                # 🔁 Log also in related loan.order
                rec.name.message_post(
                    body=(
                        f"📤 SMS Sent\n"
                        f"🕒 Time: {send_time}\n"
                        f"👤 Sender: {self.env.user.name}\n"
                        f"📩 Message:\n{sms}"
                    ),
                    subject="SMS Notification",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )

            except Exception as e:
                rec.message_post(
                    body=f"❌ SMS sending failed: {str(e)}",
                    subject="SMS Sending Error",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )

    def action_send_massages(self):
        config = self.env['collection.configuration'].search([], limit=1)
        if not config:
            raise ValueError("⚠️ No SMS configuration found in 'collection.configuration'.")

        for rec in self:
            if not rec.customer_ids:
                rec.message_post(body="⚠️ No customers selected.")
                continue

            success_customers = []
            failed_customers = []

            send_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sms = rec.massage.text

            for customer in rec.customer_ids:
                phone = customer.phone_customer
                if not phone:
                    failed_customers.append(f"{customer.display_name} (No phone)")
                    continue
                payload = {
                    "userName": config.userName,
                    "numbers": phone,
                    "userSender": config.userSender,
                    "apiKey": config.apiKey,
                    "msg": sms
                }

                headers = {
                    'Content-Type': config.headers or 'application/json;charset=UTF-8'
                }

                try:
                    response = requests.post(
                        url=config.url,
                        data=json.dumps(payload),
                        headers=headers,
                        timeout=60
                    )
                    config.response = response.text
                    success_customers.append(customer.display_name)

                    customer.message_post(
                        body=(
                            f"📤 SMS Sent\n"
                            f"🕒 Time: {send_time}\n"
                            f"👤 Sender: {self.env.user.name}\n"
                            f"📩 Message:\n{sms}"
                        ),
                        subject="SMS Notification",
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )

                except Exception as e:
                    failed_customers.append(f"{customer.display_name} (Error: {str(e)})")

            if success_customers:
                rec.status = 'sent'
                rec.message_post(
                    body=f"✅ SMS sent to: {', '.join(success_customers)}",
                    subject="Multi SMS Sent",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )

            if failed_customers:
                rec.message_post(
                    body=f"❌ Failed to send SMS to: {', '.join(failed_customers)}",
                    subject="Multi SMS Failed",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )


class Configuration(models.Model):
    _name = 'collection.configuration'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Collection Configuration'

    userName = fields.Char(string='User Name', required=True)
    userSender = fields.Char(string='User Sender', required=True)
    apiKey = fields.Char(string='API Key', required=True)
    headers = fields.Char(string='Header', required=True)
    url = fields.Char(string='Base URL', required=True)
    response = fields.Text(string='Response', required=False)


class Template(models.Model):
    _name = 'massage.template'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Massage Template'

    name = fields.Char(string='Template Name', required=True)
    text = fields.Text(string='Text', required=True)


class CollectionCall(models.Model):
    _name = 'collection.call'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'Collection Call Setting'

    name = fields.Char(string='Call Result Name', required=True)
    payment_date = fields.Datetime(string='Payment Date')
    additional_phone = fields.Char(string='Additional Phone')
    comment = fields.Text(string='Comment', copy=False)
    loan_id = fields.Many2one('loan.order', string="Loan")


class CollectionCallLine(models.Model):
    _name = 'collection.call.line'
    _description = 'Collection Call Line'

    loan_id = fields.Many2one('loan.order', string="Loan")
    call_result_id = fields.Many2one('collection.call', string='Call Result', required=True)
    payment_date = fields.Datetime(string='Payment Date')
    additional_phone = fields.Char(string='Additional Phone', required=False)
    comment = fields.Text(string='Comment', copy=False)
    create_date = fields.Datetime(string="Created On", readonly=True)
    collector_user_id = fields.Many2one(
        'res.users',
        string='Collector',
        default=lambda self: self.env.user,
        readonly=True
    )

    @api.model
    def write(self, vals):
        if 'create_date' in self._fields and self.create_date:
            raise ValidationError("You cannot modify a line after it has been created.")
        return super(CollectionCallLine, self).write(vals)
