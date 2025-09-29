
from odoo import models
from odoo.http import request
from odoo.http import ALLOWED_DEBUG_MODES
from odoo.tools.misc import str2bool


class IrHttpInherit(models.AbstractModel):
    _inherit="ir.http"

    @classmethod
    def _handle_debug(cls):
        if 'debug' in request.httprequest.args:
            debug_mode = []
            user_id = request.context.get('uid', False)
            for debug in request.httprequest.args['debug'].split(','):
                if debug not in ALLOWED_DEBUG_MODES:
                    debug = '1' if str2bool(debug, debug) else ''
                debug_mode.append(debug)
            debug_mode = ','.join(debug_mode)

            user = request.env['res.users'].sudo().browse(user_id)
            if not user.has_group('as_manage_odoo_debug_mode.debug_mode_option_group'):
                request.session.debug= ''
            else:
                if debug_mode != request.session.debug:
                    request.session.debug = debug_mode
