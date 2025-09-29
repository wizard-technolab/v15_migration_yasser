# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Session
from .connection_info import Connection


class CustomLoginController(http.Controller):
    prefix_url = Connection.prefix_url

    @http.route(f'/{prefix_url}/login', type='json', auth='none', methods=['POST'], csrf=False)
    def custom_login(self, **kwargs):
        username = kwargs.get('username')
        password = kwargs.get('password')

        if not username or not password:
            return {'error': 'Missing username or password'}

        # Authenticate the user
        uid = request.session.authenticate(request.session.db, username, password)

        if uid:
            return {'session_id': request.session.sid}
        else:
            return {'error': 'Invalid username or password'}


