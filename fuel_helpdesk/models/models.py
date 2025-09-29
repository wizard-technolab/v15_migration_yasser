# -*- coding: utf-8 -*-
from importlib.resources import _

from odoo import models, fields, api

from odoo15.odoo.exceptions import UserError, AccessError, ValidationError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def submit_action(self):
        if not self.user_id:
            raise UserError('The Assign User Is Required')

        # Get the user group using its external ID
        user_group = self.env.ref('fuel_helpdesk.group_helpdesk_user')

        # Get the users belonging to the specified user group
        group_users = user_group.users

        # Schedule activity for each user in the specified user group
        for user in group_users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary='New Ticket Submitted',
                note='Please Review The Ticket And Take Necessary Action'
            )
        # Chatter Customer Message
        chatter_customer_message = """
            <div>
                Ticket Submitted <br/>
                The reference of ticket is - {sequence_num}.
                <br/>
                <div style="text-align: center; padding: 16px 0px 16px 0px;">
                    <a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff;
                     border-radius: 5px; font-size:13px;"
                       href="{ticket_portal_url}">View the ticket
                    </a>
                    <br/>
                    <br/>
                </div>
            </div>
        """.format(
            customer_name=self.sudo().partner_id.name or 'Madam/Sir',
            ticket_portal_url=self.get_portal_url(),
            ticket_name=self.name or '',
            team_name=self.team_id.name or 'Helpdesk',
            sequence_num=self.sequence_num or ''
        )

        # Send Message In Chatter Off Partner
        self.partner_id.message_post(
            body=chatter_customer_message,
            subtype_id=self.env.ref('mail.mt_note').id
        )

        # Chatter Ticket Message
        message = (
            "A new ticket has been submitted.<br/>"
        ).format(self.id)
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=self.user_id.id,
            summary='New Ticket Submitted',
            note=message
        )

    @api.model
    def create(self, vals):
        """Override create method to trigger initial notification."""
        ticket = super(HelpdeskTicket, self).create(vals)
        ticket._send_initial_notification()
        return ticket

    @api.model
    def _send_initial_notification(self):
        """Send an initial notification when a new ticket is created."""
        if self.user_id:
            self.message_subscribe([self.user_id.partner_id.id])
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.user_id.id,
                note='New ticket: Please review the ticket and take necessary action.'
            )

    @api.model
    def _send_followup_notifications(self):
        """Send follow-up notifications based on the ticket's age and status."""
        tickets = self.search([('stage_id.name', '=', 'New')])
        for ticket in tickets:
            days_open = (fields.Date.today() - ticket.create_date.date()).days
            if days_open == 1 and ticket.user_id:
                # Send activity notification to the current user assigned to the ticket
                self._schedule_activity(ticket, ticket.user_id,
                                        'No action has been taken on the ticket after one day. Please follow up.')

            elif days_open == 2:
                # Send notification to the Customer Care Manager group
                customer_care_user_group = self.env.ref('fuel_helpdesk.group_customer_care_manager')
                for user in customer_care_user_group.users:
                    self._schedule_activity(ticket, user,
                                            'No action has been taken on the ticket after two days. Please follow up.')

            elif days_open >= 3:
                # Send notification to the General Manager group
                customer_care_manager_group = self.env.ref('fuel_helpdesk.group_help_desk_general_manager')
                for user in customer_care_manager_group.users:
                    self._schedule_activity(ticket, user,
                                            'No action has been taken on the ticket after three or more days. Please '
                                            'follow up.')

    def _schedule_activity(self, ticket, user, note):
        """Helper method to schedule an activity for a user."""
        if user:
            ticket.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                note=note
            )
