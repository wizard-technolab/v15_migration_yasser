# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import json
import re

from psycopg2 import IntegrityError
from werkzeug.exceptions import BadRequest

from odoo import http, SUPERUSER_ID, _
from odoo.http import request
from odoo.tools import plaintext2html
from odoo.exceptions import ValidationError, UserError
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.website.controllers import form

class WebsiteForm(form.WebsiteForm):

    def _handle_website_form(self, model_name, **kwargs):
        """
            Inherit the action function and add the partner creation
            within actions, then return the same value of inherited function.
            return json obj;
        """
        res = super(WebsiteForm, self)._handle_website_form(model_name, **kwargs)
        if not request.session.uid and request.validate_csrf(kwargs.get('csrf_token')):
            self.validate_partner_data(**kwargs)
            vals = self.prepare_partner_data(**kwargs)
            partner_obj = request.env['res.partner']
            partner_id = partner_obj.sudo().create(vals)
        return res

    def prepare_partner_data(self, **kwargs):
        """
            prepare partner data and return dict{} of vals;
        """
        vals = {
            'name': kwargs.get('name'),
            'phone': kwargs.get('phone'),
            'email': kwargs.get('email_from'),
        }
        return vals

    def validate_partner_data(self, **kwargs):
        """
            Validate the partner data before generating the partner;
        """
        phone_message = _("Phone number must start with 0 and equal to 10 digits")
        name_message = _("Your Name must contain only Characters")
        try:
            # check if it's a number parseble
            x = int(kwargs.get('phone'))
            # check phone number
            if self.isvalid(kwargs.get('phone'),False) and len(kwargs.get('phone')) == 10:
                pass
            else:
                raise ValidationError(phone_message)
            # check name
            if self.isvalid(kwargs.get('name'),True):
                pass
            else:
                raise ValidationError(name_message)
        except (ValidationError, ValueError, UserError) as e:
            raise ValidationError(phone_message)
            error = e.args[0]

    def isvalid(self,string,is_name):
        if is_name == False:
            pattern = re.compile('(0)\d{9}')
            match = pattern.match(string,is_name)
            return match
        else:
            pattern = re.compile('\D')
            match = pattern.match(string,is_name)
            return match
