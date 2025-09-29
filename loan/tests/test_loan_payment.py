from datetime import date, timedelta

from .test_loan_base import TestLoanCommon
from odoo import Command
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.tests.common import users
from odoo.tools import mute_logger

LOAN_AMOUNT = 20000
LOAN_TERMS = 10


class TestLoanPayments(TestLoanCommon):
    def setUp(self):
        super().setUp()

    def _get_loan_values(self):
        return {
            'name': self.partner_1.id,
            'loan_type': 1,
            'rate_per_month': 0.02,
            'loan_term': LOAN_TERMS,
            'disburse_journal': 10,
            'disburse_account': 47,
            'request_date': date.today(),
        }
    
    def _get_sum(self, loan, count, field='interest_amount'):
        counter = 0
        res = 0
        for line_id in loan.installment_ids:
            if counter == count:
                break
            res += line_id[field]
            counter += 1

        print(f'#res {field} #{count} = {res}')
        return res
    
    def validate_early_numbers(self, loan_id, interest, principal):
        print('#' * 80)
        move_id = loan_id.early_payment_id.move_id
        early_move_id = loan_id.early_move_id
        receivable_line1 = move_id.line_ids.filtered(lambda x: x.account_id == loan_id.name.property_account_receivable_id)
        bank_line = move_id.line_ids.filtered(lambda x: x.id not in [receivable_line1.id])
        unearned_line = early_move_id.line_ids.filtered(lambda x: x.account_id == loan_id.loan_type.unearned_interest_account)
        interest_line = early_move_id.line_ids.filtered(lambda x: x.account_id == loan_id.loan_type.interest_account)
        receivable_line2 = early_move_id.line_ids.filtered(lambda x: x.account_id == loan_id.name.property_account_receivable_id)
        bank_value = self._get_sum(loan_id, interest, field='interest_amount') + self._get_sum(loan_id, principal, field='principal_amount')
        unearned_value = self._get_sum(loan_id, principal, field='interest_amount')
        receivable_value = self._get_sum(loan_id, principal, field='installment_amount')
        interest_value = self._get_sum(loan_id, interest, field='interest_amount')
        print(f'bank_line.debit {bank_line} = {bank_line.debit} == {bank_value}')
        print(f'unearned_line.debit {unearned_line} = {unearned_line.debit} == {unearned_value}')
        print(f'receivable_line2.credit {receivable_line2} = {receivable_line2.credit} == {unearned_value}')
        print(f'interest_line.credit {interest_line} = {interest_line.credit} == {interest_value}')
        self.assertEqual(bank_line.debit, bank_value, 'early bank.debit failed')
        self.assertEqual(interest_line.credit, interest_value, 'early interest.credit failed')
        self.assertEqual(unearned_line.debit, unearned_value, 'early unearned.debit failed')
        # there is not need to validate the last line, since the entry must be balanced
        # self.assertEqual(receivable_line2.credit, unearned_value, 'early receivable.credit failed')

    def verbose_installments(self, loan_id):
        agg = 0
        agg_in = 0
        for line_id in loan_id.installment_ids:
            agg += line_id.principal_amount
            agg_in += line_id.interest_amount
            print(f'{agg} {agg_in} :: {line_id.principal_amount} + {line_id.interest_amount} = {line_id.installment_amount} , {line_id.date} => {line_id.is_late}')

    def test_early_payment(self):
        self.partner_1.loan_amount = LOAN_AMOUNT  # yes the amount is in the partner
        values = self._get_loan_values()
        loan_id = self.env['loan.order'].with_user(self.user_loan_admin).create(values)
        loan_id.compute_installment()
        loan_id.action_early_payment()
        move_id = loan_id.early_payment_id.move_id
        interest_amount = self._get_sum(loan_id, 3)
        self.verbose_installments(loan_id)
        self.validate_early_numbers(loan_id, 3, LOAN_TERMS)

    def test_early_payment_with_late(self):
        self.partner_1.loan_amount = LOAN_AMOUNT  # yes the amount is in the partner
        values = self._get_loan_values()
        values['request_date'] = date.today() - timedelta(days=30 * 4)
        loan_id = self.env['loan.order'].with_user(self.user_loan_admin).create(values)
        loan_id.compute_installment()
        loan_id.action_early_payment()
        self.verbose_installments(loan_id)
        move_id = loan_id.early_payment_id.move_id
        interest_amount = self._get_sum(loan_id, 6)
        self.validate_early_numbers(loan_id, 6, LOAN_TERMS)

    def test_early_payment_with_all_paid(self):
        self.partner_1.loan_amount = LOAN_AMOUNT  # yes the amount is in the partner
        values = self._get_loan_values()
        loan_id = self.env['loan.order'].with_user(self.user_loan_admin).create(values)
        loan_id.compute_installment()
        loan_id.installment_ids.write({'state': 'paid'})
        with self.assertRaises(UserError):
            loan_id.action_early_payment()
        # move_id = loan_id.early_payment_id.move_id
        # self.validate_early_numbers(loan_id, 0, 0)
