from datetime import datetime
from odoo import api, models, fields, _
import logging
from odoo.exceptions import ValidationError, UserError
import random

_logger = logging.getLogger(__name__)


class Collection(models.Model):
    _name = 'collection.collection'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'mail.composer.mixin']
    _description = 'collection module'

    loan_id = fields.Many2one('loan.order', string="Loan Order", domain="[('state', '=', 'active')]", tracking=True,
                              required=False)
    loan_ids = fields.One2many('loan.order', 'collection_id', string="Loan Orders")

    name = fields.Many2one('res.partner', related='loan_id.name', store=True)
    loan_seq_num = fields.Char(related='loan_id.seq_num', store=True)
    loan_installment_month = fields.Float(related='loan_id.installment_month', store=True)
    loan_bkt = fields.Integer(string="BKT", compute="_compute_loan_bkt", store=True)
    loan_days_since_first_unpaid = fields.Integer(string="Days", related='loan_id.days_since_first_unpaid', store=True)
    loan_state = fields.Selection(related='loan_id.state', store=True)
    assigned_user_id = fields.Many2one('res.users', string='Assigned To', tracking=True)
    is_summary = fields.Boolean(string="Is Summary", default=False, store=False)
    collector_user_id = fields.Many2one(
        'res.users',
        string="Collector User",
        tracking=True,
    )
    # domain = lambda self: [("groups_id", "in", self.env.ref("collection.group_collection_agent").id)]
    total_unpaid_loan_amount = fields.Monetary(
        string="Total unpaid loan amount",
        compute='compute_total_unpaid_loan_amount',
        store=False,
        currency_field='currency_id'
    )
    total_unpaid_installments = fields.Monetary(
        string="Total unpaid installment",
        compute='compute_total_unpaid_loan_amount',
        store=False,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    _sql_constraints = [
        ('unique_assigned_user', 'unique(assigned_user_id)', 'لا يمكن إنشاء أكثر من بطاقة لنفس المحصل.')
    ]

    @api.depends('loan_ids')
    def _compute_loan_bkt(self):
        for rec in self:
            rec.loan_bkt = len(rec.loan_ids.filtered(lambda l: l.state == 'active'))

    @api.depends('loan_ids.remaining_amount', 'loan_ids.late_amount')
    def compute_total_unpaid_loan_amount(self):
        for record in self:
            active_loans = record.loan_ids.filtered(lambda l: l.state == 'active')
            record.total_unpaid_loan_amount = sum(loan.remaining_amount or 0.0 for loan in active_loans)
            record.total_unpaid_installments = sum(loan.late_amount or 0.0 for loan in active_loans)
            _logger.warning(f"🧪 collector_user_id: {record.collector_user_id}, loan_ids: {record.loan_ids.ids}")

    # @api.depends('collector_user_id')
    # def compute_total_unpaid_loan_amount(self):
    #     Loan = self.env['loan.order']
    #     for record in self:
    #         domain = [('state', '=', 'active')]
    #         if record.collector_user_id:
    #             domain.append(('collector_user_id', '=', record.collector_user_id.id))
    #
    #         loans = Loan.search(domain)
    #         record.total_unpaid_loan_amount = sum(loan.remaining_amount or 0.0 for loan in loans)
    #         record.total_unpaid_installments = sum(loan.late_amount or 0.0 for loan in loans)
    #         _logger.info(
    #             f"💡 Collector: {record.collector_user_id.name}, Loans found: {len(loans)}, Total: {record.total_unpaid_loan_amount}")

    def get_summary_card(self):
        Loan = self.env['loan.order']
        Collection = self.env['collection.collection']

        # Fetch all active loans
        loans = Loan.search([('state', '=', 'active')])
        customers = loans.mapped('name')

        # Calculate summary values for all loans
        unpaid_loan_total = sum(loan.remaining_amount or 0.0 for loan in loans)
        unpaid_total_installments = sum(loan.late_amount or 0.0 for loan in loans)

        # Summary card (main dashboard card)
        summary_card = {
            'id': -1,
            'name': f"إجمالي الطلبات: {len(loans)} | العملاء: {len(set(customers))}",
            'loan_seq_num': '',
            'loan_installment_month': 0,
            'loan_bkt': len(loans),
            'loan_days_since_first_unpaid': 0,
            'loan_state': False,
            'assigned_user_id': False,
            'is_summary': True,
            'total_unpaid_loan_amount': unpaid_loan_total,
            'total_unpaid_installments': unpaid_total_installments,
        }

        # # Get users that already have collection cards
        # existing_user_ids = set(
        #     Collection.search([]).mapped('assigned_user_id').filtered(lambda u: u).ids
        # )
        #
        # # Get all users in the collector group
        # all_collectors = self.env.ref("collection.group_collection_agent").users
        # virtual_cards = []
        #
        # for user in all_collectors:
        #     # Skip users who already have a real card
        #     if user.id in existing_user_ids:
        #         continue
        #
        #     # 🔽🔽🔽 NEW: Fetch active loans assigned to this collector
        #     user_loans = Loan.search([
        #         ('state', '=', 'active'),
        #         ('collector_user_id', '=', user.id)
        #     ])
        #
        #     total_loan_amount = sum(loan.remaining_amount or 0.0 for loan in user_loans)
        #     total_late_amount = sum(loan.late_amount or 0.0 for loan in user_loans)
        #
        #     _logger.info(f"🧪 Current user ID: {user.id}")
        #     _logger.info(f"🧪 Records in user_loans: {user_loans}")
        #     _logger.info(f"🧪 Records in total_loan_amount: {total_loan_amount}")
        #     _logger.info(f"🧪 Records in total_late_amount: {total_late_amount}")
        #
        #     # Create virtual card for collector
        #     virtual_cards.append({
        #         'id': f"virtual_{user.id}",
        #         'display_name': f"محصل: {user.name}",
        #         'is_summary': False,
        #         'is_virtual': True,
        #         'assigned_user_id': (user.id, user.name),
        #         'loan_bkt': len(user_loans),
        #         'total_unpaid_loan_amount': total_loan_amount,  # ✅ now correctly calculated
        #         'total_unpaid_installments': total_late_amount,  # ✅ now correctly calculated
        #     })

        return [summary_card]

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        required_fields = [
            'id',
            'name',
            'loan_seq_num',
            'loan_installment_month',
            'loan_bkt',
            'loan_days_since_first_unpaid',
            'loan_state',
            'assigned_user_id',
            'total_unpaid_loan_amount',
            'total_unpaid_installments',
            'is_summary',
        ]
        fields = fields or []
        for f in required_fields:
            if f not in fields:
                fields.append(f)

        user = self.env.user

        domain = domain or []
        # if not user.has_group('collection.group_collection_admin'):
        #     domain.append(('assigned_user_id', '=', user.id))

        records = super().search_read(domain, fields, offset, limit, order)

        virtual_cards = self.get_summary_card()

        existing_user_ids = {rec['assigned_user_id'][0] for rec in records if rec.get('assigned_user_id')}
        filtered_virtuals = [
            card for card in virtual_cards
            if not card.get('assigned_user_id') or card['assigned_user_id'][0] not in existing_user_ids
        ]

        clean_virtuals = []
        for card in filtered_virtuals:
            clean_card = {}
            for field in fields:
                clean_card[field] = card.get(field, False)
            clean_virtuals.append(clean_card)
        # _logger.info(f"🧪 Records in DB: {records}")
        # _logger.info(f"🧪 Virtual cards: {virtual_cards}")
        # _logger.info(f"🧪 Virtual cards: {clean_virtuals}")
        return clean_virtuals + records

    @api.model
    def sync_active_loans(self):
        active_loans = self.env['loan.order'].search([('state', '=', 'active')])
        for loan in active_loans:
            collector_user = loan.collector_user_id

            if not collector_user:
                continue

            if loan.collection_id:
                continue

            existing_card = self.search([('assigned_user_id', '=', collector_user.id)], limit=1)
            if existing_card:
                if loan.collection_id != existing_card:
                    loan.collection_id = existing_card.id
            else:
                new_card = self.create({
                    'assigned_user_id': collector_user.id,
                    'loan_ids': [(4, loan.id)],
                })
                loan.collection_id = new_card.id

    @api.model
    def action_do_something(self):
        _logger.info(f"Action triggered on record {self.id}")
        return True

    @api.model
    def get_dashboard_data(self):
        _logger.info("Fetching dashboard data...")  # Log to confirm the method is being called.

        # Late Installments
        late_orders = self.env['loan.order'].sudo().search_count([('installment_ids.state', '=', 'unpaid')])
        _logger.info(f"Late Orders: {late_orders}")

        # Active Loans
        active_customers = self.env['loan.order'].sudo().search_count([('state', '=', 'active')])
        _logger.info(f"Active Customers: {active_customers}")

        # (users in group_collection_manager)
        group = self.env.ref('collection.group_sms_admin').sudo()
        collectors = len(group.users) if group else 0
        _logger.info(f"Collectors: {collectors}")

        start_date = datetime.today().replace(day=1)
        today = fields.Date.today()
        amount_paid = sum(self.env['loan.installment'].sudo().search([
            ('state', '=', 'paid'),
            ('payment_date', '>=', start_date),
            ('payment_date', '<=', today)
        ]).mapped('amount_paid'))
        _logger.info(f"Amount Paid: {amount_paid}")

        return {
            'cards': [
                {'title': 'الطلبات المتأخرة', 'count': late_orders, 'action_id': 'collection.action_late_orders'},
                {'title': 'العملاء النشطين', 'count': active_customers,
                 'action_id': 'collection.action_active_customers'},
                {'title': 'عدد المحصلين', 'count': collectors, 'action_id': 'collection.action_collectors'},
                {'title': 'المبلغ المحصل', 'count': amount_paid, 'action_id': 'collection.action_paid_summary'},
            ]
        }

    def action_open_collector_loans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'طلبات هذا المحصل',
            'res_model': 'loan.order',
            'view_mode': 'tree,form',
            'domain': [
                ('state', '=', 'active'),
                ('collector_user_id', '=', self.assigned_user_id.id)
            ],
            'context': {
                'search_default_active_loans': 1,
            },
            'target': 'current',
        }


class CollectionTransferWizard(models.TransientModel):
    _name = 'collection.transfer.wizard'
    _description = 'Transfer Loans to Multiple Agents'

    user_ids = fields.Many2many(
        'res.users',
        string="Collectors",
        domain=lambda self: [("groups_id", "in", self.env.ref("collection.group_collection_agent").id)],
        required=True
    )

    def action_transfer(self):
        loan_model = self.env['loan.order']
        active_ids = self.env.context.get('active_ids', [])
        loans = loan_model.browse(active_ids)

        collectors = self.user_ids
        if not collectors or not loans:
            raise UserError("⚠️ يرجى تحديد المحصلين والطلبات.")

        total_amount = sum(loans.mapped('loan_amount'))
        collector_buckets = {
            collector.id: {'collector': collector, 'loans': [], 'amount': 0.0}
            for collector in collectors
        }

        shuffled_loans = list(loans)
        random.shuffle(shuffled_loans)

        for loan in shuffled_loans:
            best_fit = min(collector_buckets.values(), key=lambda b: b['amount'])
            best_fit['loans'].append(loan)
            best_fit['amount'] += loan.loan_amount or 0.0

        for bucket in collector_buckets.values():
            collector = bucket['collector']
            assigned_loans = bucket['loans']

            collection = self.env['collection.collection'].search([
                ('assigned_user_id', '=', collector.id)
            ], limit=1)

            if not collection:
                collection = self.create_new_collection(collector)

            for loan in assigned_loans:
                loan.transfer_loan_to_collection(collection)

        return {'type': 'ir.actions.act_window_close'}

    def create_new_collection(self, user):
        existing = self.env['collection.collection'].search([
            ('assigned_user_id', '=', user.id)
        ], limit=1)
        if existing:
            return existing
        return self.env['collection.collection'].create({
            'assigned_user_id': user.id
        })


class LoanOrder(models.Model):
    _inherit = 'loan.order'
    _order = 'latest_payment_sortable desc'

    collection_id = fields.Many2one('collection.collection', string="Collection")
    collection_line_ids = fields.One2many(
        comodel_name='collection.call.line',
        inverse_name='loan_id',
        string='Collection Lines'
    )
    collection_call_id = fields.Many2one('collection.call', string="Collection Call")
    collector_user_id = fields.Many2one(
        'res.users',
        string="Collector User",
        tracking=True
    )
    # domain = lambda self: [("groups_id", "in", self.env.ref("collection.group_collection_agent").id)],
    latest_payment_date = fields.Datetime(
        string="Expected Payment Date",
        compute="_compute_latest_payment_date",
        store=True
    )
    latest_payment_sortable = fields.Datetime(
        string="Sortable Payment Date",
        compute="_compute_latest_payment_sortable",
        store=True
    )

    @api.depends('collection_line_ids.payment_date')
    def _compute_latest_payment_date(self):
        for record in self:
            payment_dates = [payment_date for payment_date in record.collection_line_ids.mapped('payment_date') if
                             isinstance(payment_date, datetime)]
            if payment_dates:
                record.latest_payment_date = max(payment_dates)
            else:
                record.latest_payment_date = False

    @api.depends('latest_payment_date')
    def _compute_latest_payment_sortable(self):
        for record in self:
            record.latest_payment_sortable = record.latest_payment_date or datetime(1, 1, 1)

    @api.model
    def action_create_payment_date_activities(self):
        today = fields.Date.today()
        loan_orders = self.search([])

        for loan in loan_orders:
            if not loan.latest_payment_date or not loan.collector_user_id:
                continue

            if loan.latest_payment_date.date() == today:
                existing_activity = self.env['mail.activity'].search([
                    ('res_model', '=', 'loan.order'),
                    ('res_id', '=', loan.id),
                    ('user_id', '=', loan.collector_user_id.id),
                    ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
                    ('summary', '=', 'Payment Date Follow-up'),
                ])

                if not existing_activity:
                    self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'res_model_id': self.env['ir.model']._get_id('loan.order'),
                        'res_id': loan.id,
                        'user_id': loan.collector_user_id.id,
                        'date_deadline': today,
                        'summary': 'Payment Date Follow-up',
                        'note': f"Follow up on today's payment date: {loan.latest_payment_date.strftime('%Y-%m-%d')}"
                    })
    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get('display_seq_only'):
                name = record.seq_num or 'No Ref'
            else:
                name = record.name.name if record.name else 'No Name'
            result.append((record.id, name))
        return result

    def transfer_loan_to_collection(self, new_collection):
        self.collection_id = new_collection.id
        self.collector_user_id = new_collection.assigned_user_id.id

        if self.id not in new_collection.loan_ids.ids:
            new_collection.loan_ids = [(4, self.id)]

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._ensure_collection_binding()
        return record

    def write(self, vals):
        res = super().write(vals)
        if 'collector_user_id' in vals:
            self._ensure_collection_binding()
        return res

    def _ensure_collection_binding(self):
        for rec in self:
            if rec.collector_user_id:
                collection = self.env['collection.collection'].search([
                    ('assigned_user_id', '=', rec.collector_user_id.id)
                ], limit=1)

                if not collection:
                    collection = self.env['collection.collection'].create({
                        'assigned_user_id': rec.collector_user_id.id,
                        'loan_ids': [(4, rec.id)],
                    })
                else:
                    if rec.id not in collection.loan_ids.ids:
                        collection.loan_ids = [(4, rec.id)]

                rec.collection_id = collection.id
