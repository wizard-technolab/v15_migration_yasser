# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request


class PortalExpression(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'health_count' in counters:
            health_count = request.env['health.declaration'].search_count(self._get_expression_domain()) \
                if request.env['health.declaration'].check_access_rights('read', raise_exception=False) else 0
            values['health_count'] = health_count
        return values

    # ------------------------------------------------------------
    # My Health Declaration
    # ------------------------------------------------------------

    def _health_declaration_get_page_view_values(self, health_declaration, access_token, **kwargs):
        values = {
            'page_name': 'health_declaration',
            'health_declaration': health_declaration,
        }
        return self._get_page_view_values(health_declaration, access_token, values, 'my_health_declarations_history', False, **kwargs)

    def _get_health_declarations_domain(self):
        return []

    @http.route(['/my/health_declaration', '/my/health_declaration/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_health_declarations(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        HealthDeclaration = request.env['health.declaration']

        domain = self._get_health_declarations_domain()

        searchbar_sortings = {
            'name': {'label': _('Customer Name'), 'order': 'name desc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
        }

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        health_count = HealthDeclaration.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/health_declaration",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=health_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        health_declarations = HealthDeclaration.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_health_declarations_history'] = health_declarations.ids[:100]

        values.update({
            'date': date_begin,
            'health_declarations': health_declarations,
            'page_name': 'health_declarations',
            'pager': pager,
            'default_url': '/my/health_declaration',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby':filterby,
        })
        return request.render("website_portal_custom.portal_my_health_declarations", values)

    @http.route(['/my/health_declaration/<int:health_declaration_id>'], type='http', auth="public", website=True)
    def portal_my_health_declaration_detail(self, health_declaration_id, access_token=None, report_type=None, download=False, **kw):
        try:
            health_declaration_sudo = self._document_check_access('health.declaration', health_declaration_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=health_declaration_sudo, report_type=report_type, report_ref='partner_reports.health_declaration_action', download=download)

        values = self._health_declaration_get_page_view_values(health_declaration_sudo, access_token, **kw)
        return request.render("website_portal_custom.portal_health_declaration_page", values)

    # ------------------------------------------------------------
    # My Home
    # ------------------------------------------------------------

    def details_form_validate(self, data):
        error, error_message = super(PortalExpression, self).details_form_validate(data)
        # prevent VAT/name change if invoices exist
        partner = request.env['res.users'].browse(request.uid).partner_id
        if not partner.can_edit_vat():
            if 'vat' in data and (data['vat'] or False) != (partner.vat or False):
                error['vat'] = 'error'
                error_message.append(_('Changing VAT number is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'name' in data and (data['name'] or False) != (partner.name or False):
                error['name'] = 'error'
                error_message.append(_('Changing your name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'company_name' in data and (data['company_name'] or False) != (partner.company_name or False):
                error['company_name'] = 'error'
                error_message.append(_('Changing your company name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
        return error, error_message
