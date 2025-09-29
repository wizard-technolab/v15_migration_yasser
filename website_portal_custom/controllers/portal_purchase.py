# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from collections import OrderedDict
from datetime import datetime

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, Response
from odoo.tools import image_process
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.purchase.controllers import portal

class CustomerPortal(portal.CustomerPortal):

    def _render_portal(self, template, page, date_begin, date_end, sortby, filterby, domain, searchbar_filters, default_filter, url, history, page_name, key):
        print("\n\n\nhere we go again \n\n\n")
        values = self._prepare_portal_layout_values()
        PurchaseOrder = request.env['purchase.order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
            'amount_total': {'label': _('Total'), 'order': 'amount_total desc, id desc'},
        }
        # default sort
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if searchbar_filters:
            # default filter
            if not filterby:
                filterby = default_filter
            domain += searchbar_filters[filterby]['domain']

        # count for pager
        domain = [('state','not in',['x'])]
        count = PurchaseOrder.search_count(domain)

        # make pager
        pager = portal_pager(
            url=url,
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=count,
            page=page,
            step=self._items_per_page
        )

        # search the purchase orders to display, according to the pager data
        orders = PurchaseOrder.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        print("\n Domain: ",domain,"\n")
        request.session[history] = orders.ids[:100]

        values.update({
            'date': date_begin,
            key: orders,
            'page_name': page_name,
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': url,
        })
        return request.render(template, values)
