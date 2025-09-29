from odoo import models, api, fields

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    asset_code = fields.Char(
        string='Asset Code',
        readonly=True,
        copy=False
    )

    @api.model
    def create(self, vals):
        if not vals.get('asset_code'):
            vals['asset_code'] = self.env['ir.sequence'].next_by_code('account.asset') or '/'
        return super(AccountAsset, self).create(vals)
