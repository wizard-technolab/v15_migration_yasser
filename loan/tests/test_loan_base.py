from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestLoanCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestLoanCommon, cls).setUpClass()

        user_group_internal = cls.env.ref('base.group_user')
        user_group_loan_user = cls.env.ref('loan.group_use_loan_user')
        user_group_loan_manager = cls.env.ref('loan.group_use_loan_admin')
        user_group_loan_super_manager = cls.env.ref('loan.group_use_loan_super_admin')
        user_group_contact_creation = cls.env.ref('base.group_partner_manager')
        user_group_type_user = cls.env.ref('loan.group_use_alon_user_type')

        user_group_settings = cls.env.ref('base.group_system')

        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Abbas Hamid',
            'email': 'abbas.hamid@agrolait.com'
        })

        # Test users to use through the various tests
        Users = cls.env['res.users'].with_context({'no_reset_password': True})
        cls.user_loan_admin = Users.create({
            'name': 'Mohammed Ali',
            'login': 'mo.ali',
            'email': 'm.a@example.com',
            'signature': 'SignBert',
            'notification_type': 'email',
            'groups_id': [
                (6, 0, [
                    user_group_loan_manager.id,
                    user_group_internal.id,
                    user_group_loan_super_manager.id,
                    user_group_settings.id,
                    user_group_contact_creation.id,
                    user_group_type_user.id,
                ])
            ],
        })
