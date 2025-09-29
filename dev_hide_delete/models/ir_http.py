# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Devintelle Software Solutions (<http://devintelle.com>).
#
##############################################################################

from odoo import models


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(Http, self).session_info()
        result.update({
            'is_show_delete_button': True if (self.env.user.has_group(
                'dev_hide_delete.group_display_delete_action')) else False
        })
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
