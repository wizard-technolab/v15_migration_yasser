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
        if 'expression_count' in counters:
            expression_count = request.env['expression.of.desire'].search_count(self._get_expression_domain()) \
                if request.env['expression.of.desire'].check_access_rights('read', raise_exception=False) else 0
            values['expression_count'] = expression_count
        return values

    # ------------------------------------------------------------
    # My Expressions of desire
    # ------------------------------------------------------------

    def _expression_get_page_view_values(self, expression, access_token, **kwargs):
        values = {
            'page_name': 'expression',
            'expression': expression,
        }
        return self._get_page_view_values(expression, access_token, values, 'my_expressions_history', False, **kwargs)

    def _get_expression_domain(self):
        return []

    @http.route(['/my/expression_of_desire', '/my/expression_of_desire/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_expressions(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        ExpressionOfdesire = request.env['expression.of.desire']

        domain = self._get_expression_domain()

        searchbar_sortings = {
            'name': {'label': _('Customer Name'), 'order': 'name desc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
        }
        # default filter by value
        # if not filterby:
        #     filterby = 'all'
        # domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        expression_count = ExpressionOfdesire.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/expression_of_desire",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=expression_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        expressions = ExpressionOfdesire.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_expressions_history'] = expressions.ids[:100]

        values.update({
            'date': date_begin,
            'expressions': expressions,
            'page_name': 'expressions',
            'pager': pager,
            'default_url': '/my/expression_of_desire',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby':filterby,
        })
        return request.render("website_portal_custom.portal_my_expressions", values)

    @http.route(['/my/expression_of_desire/<int:expression_id>'], type='http', auth="public", website=True)
    def portal_my_expression_detail(self, expression_id, access_token=None, report_type=None, download=False, **kw):
        print("\n\n\n this is it\n\n\n\n")
        try:
            expression_sudo = self._document_check_access('expression.of.desire', expression_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=expression_sudo, report_type=report_type, report_ref='partner_reports.expression_of_desire_form_action', download=download)

        values = self._expression_get_page_view_values(expression_sudo, access_token, **kw)
        return request.render("website_portal_custom.portal_expression_pagee", values)

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
