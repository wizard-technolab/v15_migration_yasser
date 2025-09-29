# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from email.mime import application
from re import template
from tempfile import tempdir
from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request


class PortalExpression(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'application_count' in counters:
            application_count = request.env['crm.lead'].search_count(self._get_application_domain()) \
                if request.env['crm.lead'].check_access_rights('read', raise_exception=False) else 0
            values['application_count'] = application_count
        return values

    # ------------------------------------------------------------
    # My Applications of desire
    # ------------------------------------------------------------

    def _application_get_page_view_values(self, application, access_token, **kwargs):
        values = {
            'page_name': 'application',
            'application': application,
        }
        return self._get_page_view_values(application, access_token, values, 'my_applications_history', False, **kwargs)

    def _get_application_domain(self):
        return []

    @http.route(['/my/application', '/my/application/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_applications(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        ApplicationObject = request.env['crm.lead']

        domain = self._get_application_domain()

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
        application_count = ApplicationObject.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/application",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=application_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        applications = ApplicationObject.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_applications_history'] = applications.ids[:100]

        values.update({
            'date': date_begin,
            'applications': applications,
            'page_name': 'applications',
            'pager': pager,
            'default_url': '/my/application',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby':filterby,
        })
        return request.render("website_portal_custom.portal_my_applications", values)

    @http.route(['/my/application/<int:application_id>'], type='http', auth="public", website=True)
    def portal_my_application_detail(self, application_id, access_token=None, report_type=None, download=False, **kw):
        try:
            application_sudo = self._document_check_access('crm.lead', application_id, access_token)
            print("\n\n application_sudo: ",application_sudo,"\n\n")
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=application_sudo, report_type=report_type, report_ref='partner_reports.medical_services_financing_request_action', download=download)

        values = self._application_get_page_view_values(application_sudo, access_token, **kw)
        return request.render("website_portal_custom.portal_application_page", values)

    @http.route(['/printonsuccess/<int:application_id>/<string:model>/<int:template>'], type='http', auth="public", website=True)
    def print_every_succes(self, application_id, model, template, access_token=None, report_type='pdf', download=True, **kw):
        try:
            application_sudo = self._document_check_access(model, application_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            if template == 1:
                return self._show_report(model=application_sudo, report_type=report_type, report_ref='partner_reports.expression_of_desire_form_action', download=download)
            elif template == 2:
                return self._show_report(model=application_sudo, report_type=report_type, report_ref='partner_reports.medical_services_financing_request_action', download=download)
            elif template == 3:
                return self._show_report(model=application_sudo, report_type=report_type, report_ref='partner_reports.health_declaration_action', download=download)
            else:
                return self._show_report(model=application_sudo, report_type=report_type, report_ref='partner_reports.quotation_form_action', download=download)

        values = self._application_get_page_view_values(application_sudo, access_token, **kw)
        return request.render("website_portal_custom.portal_application_page", values)


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
