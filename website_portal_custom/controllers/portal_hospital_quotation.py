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
import werkzeug.wrappers



def alternative_json_response(self, result=None, error=None):
    # sauce for this method: https://stackoverflow.com/a/71262562
    if isinstance(result, werkzeug.wrappers.Response):
        # this is what we expect in the helpdesk api
        return result

    mime = 'application/json'
    if result is None:
        result = DEFAULT_ERROR_RESPONSE
    body = json.dumps(result, default=date_utils.json_default, separators=(',', '"'))

    return Response(
        body, status=error and error.pop('http_status', 200) or 200,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )


class PortalQuotation(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'quotation_count' in counters:
            quotation_count = request.env['hospital.quotation'].search_count(self._get_quotation_domain()) \
                if request.env['hospital.quotation'].check_access_rights('read', raise_exception=False) else 0
            values['quotation_count'] = quotation_count
        return values

    # ------------------------------------------------------------
    # My Applications of desire
    # ------------------------------------------------------------

    def _quotation_get_page_view_values(self, quotation, access_token, **kwargs):
        values = {
            'page_name': 'quotation',
            'quotation': quotation,
        }
        return self._get_page_view_values(quotation, access_token, values, 'my_quotation_history', False, **kwargs)

    def _get_quotation_domain(self):
        domain = []
        if request.env.user.share == False:
            domain = []
        else:
            domain = [('create_uid','=',request.env.user.id)]
        return domain

    def _validate_ticket(self, values):
        # Phone : mandatory ( 10 digits)
        # Email : mandatory ( email format)
        sequence = values.get('sequence', '')
        team_id = values.get('team_id', '')
        phone = values.get('partner_phone', '')
        email = values.get('partner_email', '')
        if len(phone) != 10:
            return False, invalid_response('validation', f'Phone number must be 10 digits', 400)
        if phone[0: 2] != '05':
            return False, invalid_response('validation', f'Phone number must start with "05"', 400)
        if not tools.single_email_re.match(email):
            return False, invalid_response('validation', f'Invalid email', 400)
        return True, None

    """
            second request [Route / POST]
                create the Ticket and lead in HelpDesk **
                     if the token or params not right then wrong [403] or internal server error [500] **
                        if the token and params right then success and create the customer date and lead [200] **
    """
    # @validate_token
    @http.route("/api/ticket/create", methods=["POST"], type="json", auth="public", csrf=False)
    def create_ticket(self, **post):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        user_id = request.uid
        user_obj = request.env['res.users'].browse(user_id)
        payload = request.jsonrequest
        required_keys = ['partner_email', 'partner_phone','sequence','team_id']
        allowed_keys = ['name', 'partner_name', 'description'] + required_keys
        values = dict()
        for key in required_keys:
            if key not in payload:
                return invalid_response('validation', f'Missing required key "{key}"', 400)
        for value in payload:
            if value in allowed_keys:
                values[value] = payload[value]
        ticket_valid, ticket_error_response = self._validate_ticket(values)
        if not ticket_valid:
            return ticket_error_response

        new_ticket_obj = request.env['helpdesk.ticket'].sudo().create(values)
        print(new_ticket_obj.id)
        if new_ticket_obj:
            result = {'message': 'success', 'status': True, 'record_id': new_ticket_obj.id}
            try:
                return valid_response(
                    [{'result': result, "message [200]": "Customer created successfully"}],
                    status=200)
            except Exception as e:
                info = "The field is not valid {}".format((e))
                error = "invalid_params"
                _logger.error(info)
                return invalid_response("wrong", error, 403)

    @http.route(['/my/quotations', '/my/quotations/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_quotations(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        QuotationObject = request.env['hospital.quotation']

        domain = self._get_quotation_domain()

        searchbar_sortings = {
            'name': {'label': _('Customer Name'), 'order': 'id desc'},
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
        quotation_count = QuotationObject.sudo().search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/quotations",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=20
        )
        # content according to pager and archive selected
        quotations = QuotationObject.search(domain, order=order, limit=20, offset=pager['offset'])
        request.session['my_quotation_history'] = quotations.ids[:100]

        values.update({
            'date': date_begin,
            'quotations': quotations,
            'page_name': 'quotations',
            'pager': pager,
            'default_url': '/my/quotations',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby':filterby,
        })
        return request.render("website_portal_custom.portal_my_quotations", values)

    @http.route(['/my/quotations/<int:quotation_id>'], type='http', auth="public", website=True)
    def portal_my_quotation_detail(self, quotation_id, access_token=None, report_type=None, download=False, **kw):
        try:
            quotation_sudo = self._document_check_access('hospital.quotation', quotation_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=quotation_sudo, report_type=report_type, report_ref='partner_reports.quotation_form_action', download=download)

        values = self._quotation_get_page_view_values(quotation_sudo, access_token, **kw)
        return request.render("website_portal_custom.portal_quotation_page", values)
    
    @http.route(['/my/purchase/<int:order_id>/accept'], type='http', auth="public", website=True)
    def portal_accept_rfq_to_po(self, order_id, access_token=None, **kw):
        """
            make the rfq to purchase order
        """
        if order_id:
            purchase_order_id = request.env['purchase.order'].search([('id','=',order_id)],limit=1)
            if purchase_order_id.id:
                # purchase_order_id.sudo().button_confirm()
                purchase_order_id.sudo().action_acceptance()
                purchase_order_id.sudo().create_activity()
                return request.redirect(purchase_order_id.get_portal_url())
