from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        user = super().create(vals)
        group_agent = self.env.ref('collection.group_collection_agent')
        if group_agent in user.groups_id:
            existing = self.env['collection.collection'].search([('assigned_user_id', '=', user.id)], limit=1)
            if not existing:
                self.env['collection.collection'].create({
                    'assigned_user_id': user.id,
                })
        return user

    def write(self, vals):
        res = super().write(vals)
        group_agent = self.env.ref('collection.group_collection_agent')
        for user in self:
            if group_agent in user.groups_id:
                existing = self.env['collection.collection'].search([('assigned_user_id', '=', user.id)], limit=1)
                if not existing:
                    self.env['collection.collection'].create({
                        'assigned_user_id': user.id,
                    })
        return res
