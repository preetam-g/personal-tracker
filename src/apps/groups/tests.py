from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.expenses.models import Expense
from .models import BillShare, GroupMembership, GroupPayment, SharedBill, SharedGroup
from .services import group_balances, simplify_balances
from .settlement_tokens import payment_token


class SharedGroupsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.alice = users.objects.create_user('alice', password='test-password-123')
        cls.bob = users.objects.create_user('bob', password='test-password-123')
        cls.cara = users.objects.create_user('cara', password='test-password-123')
        cls.outsider = users.objects.create_user('outsider', password='test-password-123')
        cls.alice.upi_id = 'alice@okaxis'
        cls.alice.save(update_fields=['upi_id'])
        cls.group = SharedGroup.objects.create(name='Trip', created_by=cls.alice)
        for user in (cls.alice, cls.bob, cls.cara):
            GroupMembership.objects.create(group=cls.group, user=user)

    def destination_token(self, reference):
        return payment_token(self.group, self.bob, self.alice, Decimal('999999.00'), reference)

    def issued_payment(self):
        self.client.force_login(self.alice)
        self.add_bill(amount='20.00')
        self.client.force_login(self.bob)
        suggestion = self.client.get(reverse('groups:detail', args=[self.group.pk])).context['suggestions'][0]
        return suggestion, {
            'to_user': self.alice.pk, 'amount': '10.00',
            'payment_reference': suggestion['reference'],
            'destination_token': suggestion['destination_token'], 'payment_completed': 'on',
        }

    def add_bill(self, *, title='Dinner', amount='100.00', split_method='equal', paid_by=None, participants=None, extra=None):
        participants = participants or (self.alice, self.bob)
        payload = {
            'title': title, 'amount': amount, 'date': '2026-10-13',
            'paid_by': (paid_by or self.alice).pk, 'split_method': split_method,
        }
        payload.update({f'include_{user.pk}': 'on' for user in participants})
        payload.update(extra or {})
        return self.client.post(reverse('groups:add_bill', args=[self.group.pk]), payload)

    def test_navigation_and_existing_group_data_use_groups_app(self):
        self.client.force_login(self.alice)
        page = self.client.get(reverse('groups:home'))
        self.assertContains(page, reverse('groups:detail', args=[self.group.pk]))
        self.assertContains(page, 'Groups')
        self.assertContains(self.client.get(reverse('groups:detail', args=[self.group.pk])), 'Trip')
        self.assertEqual(SharedGroup._meta.app_label, 'groups')
        self.assertEqual(SharedGroup._meta.db_table, 'ledger_sharedgroup')

    def test_percentage_bill_rounding_expense_upi_and_payment_confirmation(self):
        self.client.force_login(self.bob)
        response = self.add_bill(
            split_method='percentage', participants=(self.alice, self.bob, self.cara),
            extra={f'percent_{self.alice.pk}': '33.34', f'percent_{self.bob.pk}': '33.33', f'percent_{self.cara.pk}': '33.33'},
        )
        self.assertEqual(response.status_code, 302)
        bill = SharedBill.objects.get(title='Dinner')
        self.assertEqual(dict(bill.shares.values_list('user_id', 'amount')), {
            self.alice.pk: Decimal('33.34'), self.bob.pk: Decimal('33.33'), self.cara.pk: Decimal('33.33'),
        })
        self.assertEqual(set(Expense.objects.filter(group_bill_share__bill=bill).values_list('type__name', flat=True)), {'UPI'})
        self.assertEqual(group_balances(self.group)[self.alice.pk], Decimal('66.66'))
        detail = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertContains(detail, 'To receive ₹66.66')
        self.assertContains(detail, 'To pay ₹33.33')
        self.assertContains(detail, 'Pay the receiver directly in your UPI app.')
        self.assertNotContains(detail, 'ToroPay')
        self.assertNotContains(detail, 'upi://pay?')
        self.assertContains(detail, 'Settle a particular amount')
        self.assertContains(detail, 'Group activity')
        self.assertContains(detail, 'bob</strong> added a bill of <strong>₹100.00</strong> for Dinner')
        self.assertContains(detail, '<details class="group-activity-card"', html=False)
        payment_response = self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '33.33', 'payment_reference': 'TRK123', 'destination_token': self.destination_token('TRK123'), 'payment_completed': 'on',
        })
        self.assertEqual(payment_response.status_code, 302)
        payment = GroupPayment.objects.get()
        self.assertEqual(payment.status, GroupPayment.Status.AUTO_APPROVED)
        self.assertContains(self.client.get(reverse('groups:detail', args=[self.group.pk])), 'Automatically approved')
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('0.00'))
        self.client.force_login(self.alice)
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        payment.refresh_from_db()
        self.assertEqual(payment.status, GroupPayment.Status.CONFIRMED)
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('0.00'))
        self.assertEqual(Expense.objects.count(), 3)

    def test_manual_settlement_keeps_receiver_and_records_nothing_on_open(self):
        suggestion, _ = self.issued_payment()
        self.assertEqual(suggestion['receiver'].pk, self.alice.pk)
        page = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertContains(page, 'Copy amount')
        self.assertContains(page, 'data-settlement-form')
        self.assertNotContains(page, 'ToroPay')
        self.assertNotContains(page, 'data-payment-link')
        self.assertFalse(GroupPayment.objects.exists())
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('-10.00'))

    def test_only_explicit_paid_claim_creates_settlement_activity_with_correct_status(self):
        self.client.force_login(self.alice)
        self.add_bill(amount='20.00')
        self.client.force_login(self.bob)
        detail_url = reverse('groups:detail', args=[self.group.pk])
        for _ in range(2):
            page = self.client.get(detail_url)
            self.assertTrue(page.context['suggestions'])
            self.assertEqual([event['kind'] for event in page.context['activity']], ['bill'])
            self.assertNotContains(page, 'to settle up.')
        self.client.get(reverse('groups:add_payment', args=[self.group.pk]))
        self.assertFalse(GroupPayment.objects.exists())
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '4.00', 'payment_reference': 'TRKSTATUS', 'destination_token': self.destination_token('TRKSTATUS'), 'payment_completed': 'on',
        })
        payment = GroupPayment.objects.get()
        page = self.client.get(detail_url)
        self.assertContains(page, 'Automatically approved')
        self.assertContains(page, 'as paid to alice — automatically approved.')
        self.client.force_login(self.alice)
        self.client.post(reverse('groups:reject_payment', args=[self.group.pk, payment.pk]))
        page = self.client.get(detail_url)
        self.assertContains(page, 'rejected bob’s payment claim')
        self.assertNotContains(page, 'to settle up.')
        self.client.force_login(self.bob)
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '10.00', 'payment_reference': 'TRKCONFIRM', 'destination_token': self.destination_token('TRKCONFIRM'), 'payment_completed': 'on',
        })
        pending = GroupPayment.objects.get(status=GroupPayment.Status.AUTO_APPROVED)
        self.client.force_login(self.alice)
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, pending.pk]))
        page = self.client.get(detail_url)
        self.assertContains(page, 'to alice to settle up.')
        self.assertContains(page, 'Receiver confirmed')
        self.assertEqual(Expense.objects.count(), 2)

    def test_equal_split_only_selected_members_and_every_paisa(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.add_bill(title='Snacks', amount='10.01', paid_by=self.bob, participants=(self.alice, self.cara)).status_code, 302)
        bill = SharedBill.objects.get(title='Snacks')
        self.assertEqual(dict(bill.shares.values_list('user_id', 'amount')), {
            self.alice.pk: Decimal('5.01'), self.cara.pk: Decimal('5.00'),
        })
        self.assertEqual(sum(bill.shares.values_list('percentage', flat=True)), Decimal('100.00'))

    def test_amount_split_checks_total(self):
        self.client.force_login(self.cara)
        payload = {f'amount_{self.alice.pk}': '3.34', f'amount_{self.bob.pk}': '6.66'}
        invalid = self.add_bill(title='Tickets', amount='10.01', split_method='amount', extra=payload)
        self.assertContains(invalid, 'Selected amounts must add up to the bill total.')
        self.assertFalse(SharedBill.objects.exists())
        payload[f'amount_{self.bob.pk}'] = '6.67'
        self.assertEqual(self.add_bill(title='Tickets', amount='10.01', split_method='amount', extra=payload).status_code, 302)
        self.assertEqual(sum(SharedBill.objects.get(title='Tickets').shares.values_list('amount', flat=True)), Decimal('10.01'))

    def test_partial_payment_recalculates_remaining_then_reject_restores_it(self):
        self.client.force_login(self.alice)
        self.add_bill(title='Cab', amount='20.00')
        self.client.force_login(self.bob)
        self.assertContains(self.client.get(reverse('groups:detail', args=[self.group.pk])), 'Settle up')
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '4.00', 'payment_reference': 'TRKPARTIAL', 'destination_token': self.destination_token('TRKPARTIAL'), 'payment_completed': 'on',
        })
        payment = GroupPayment.objects.get()
        page = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertEqual(page.context['suggestions'][0]['amount'], Decimal('6.00'))
        self.assertContains(page, 'Automatically approved')
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('-6.00'))
        self.client.force_login(self.alice)
        self.client.post(reverse('groups:reject_payment', args=[self.group.pk, payment.pk]))
        self.client.force_login(self.bob)
        self.assertContains(self.client.get(reverse('groups:detail', args=[self.group.pk])), 'Settle up')

    def test_autoapproved_full_payment_is_recorded_once_without_duplicate_suggestion(self):
        self.client.force_login(self.alice)
        self.add_bill(amount='20.00')
        self.client.force_login(self.bob)
        payload = {'to_user': self.alice.pk, 'amount': '10.00', 'payment_reference': 'TRK456', 'destination_token': self.destination_token('TRK456'), 'payment_completed': 'on'}
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload)
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload)
        self.assertEqual(GroupPayment.objects.filter(status=GroupPayment.Status.AUTO_APPROVED).count(), 1)
        page = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertFalse(page.context['suggestions'])
        self.assertContains(page, 'Everyone is settled.')
        self.assertNotContains(page, 'Settle up')

    def test_group_access_and_member_management_are_scoped(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(reverse('groups:detail', args=[self.group.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('groups:add_bill', args=[self.group.pk]), {}).status_code, 404)
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse('groups:add_member', args=[self.group.pk])).status_code, 403)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse('groups:add_member', args=[self.group.pk]), {'username': self.outsider.username}).status_code, 302)
        self.assertTrue(self.group.members.filter(pk=self.outsider.pk).exists())

    def test_new_group_includes_creator_and_legacy_route_still_opens(self):
        self.client.force_login(self.outsider)
        response = self.client.post(reverse('groups:create'), {'name': 'Housemates'})
        self.assertEqual(response.status_code, 302)
        group = SharedGroup.objects.get(name='Housemates')
        self.assertEqual(list(group.members.values_list('pk', flat=True)), [self.outsider.pk])
        self.assertEqual(self.client.get(reverse('ledger:group_detail', args=[group.pk])).status_code, 200)

    def test_invalid_percentage_and_nonmember_payer_do_not_create_bill(self):
        self.client.force_login(self.alice)
        payload = {f'percent_{self.alice.pk}': '60', f'percent_{self.bob.pk}': '30'}
        self.assertEqual(self.add_bill(split_method='percentage', extra=payload).status_code, 200)
        self.assertFalse(SharedBill.objects.exists())
        payload[f'percent_{self.bob.pk}'] = '40'
        self.assertEqual(self.add_bill(split_method='percentage', paid_by=self.outsider, extra=payload).status_code, 200)
        self.assertFalse(SharedBill.objects.exists())

    def test_only_receiver_can_explicitly_confirm_autoapproved_payment(self):
        self.client.force_login(self.alice)
        self.add_bill(amount='20.00')
        self.client.force_login(self.bob)
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '10.00', 'payment_reference': 'TRKRECEIVER', 'destination_token': self.destination_token('TRKRECEIVER'), 'payment_completed': 'on',
        })
        payment = GroupPayment.objects.get()
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        payment.refresh_from_db()
        self.assertEqual(payment.status, GroupPayment.Status.AUTO_APPROVED)
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(reverse('groups:detail', args=[self.group.pk])), 'Confirm received')
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        payment.refresh_from_db()
        self.assertEqual(payment.status, GroupPayment.Status.CONFIRMED)

    def test_exact_simplification_uses_minimum_two_transfers(self):
        transfers = simplify_balances({
            self.alice.pk: Decimal('-8.00'), self.bob.pk: Decimal('-7.00'),
            self.cara.pk: Decimal('7.00'), self.outsider.pk: Decimal('8.00'),
        })
        self.assertEqual(len(transfers), 2)
        self.assertEqual(sum((item['amount'] for item in transfers), Decimal('0.00')), Decimal('15.00'))

    def test_bill_removal_deletes_linked_personal_expenses(self):
        self.client.force_login(self.alice)
        self.add_bill(title='Tea', amount='8.00')
        bill = SharedBill.objects.get(title='Tea')
        expense = Expense.objects.get(user=self.bob, group_bill_share__bill=bill)
        self.client.force_login(self.bob)
        self.client.post(reverse('expenses:delete', args=[expense.pk]))
        self.assertTrue(Expense.objects.filter(pk=expense.pk).exists())
        self.client.force_login(self.alice)
        self.client.post(reverse('groups:delete_bill', args=[self.group.pk, bill.pk]))
        self.assertFalse(Expense.objects.filter(group_bill_share__bill_id=bill.pk).exists())

    def test_only_bill_payer_sees_and_can_use_edit_delete(self):
        self.client.force_login(self.bob)
        self.add_bill(title='Hotel', amount='30.00', paid_by=self.alice)
        bill = SharedBill.objects.get(title='Hotel')
        detail = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertNotContains(detail, reverse('groups:edit_bill', args=[self.group.pk, bill.pk]))
        self.assertNotContains(detail, reverse('groups:delete_bill', args=[self.group.pk, bill.pk]))
        self.assertEqual(self.client.get(reverse('groups:edit_bill', args=[self.group.pk, bill.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('groups:edit_bill', args=[self.group.pk, bill.pk]), {}).status_code, 403)
        self.assertEqual(self.client.post(reverse('groups:delete_bill', args=[self.group.pk, bill.pk])).status_code, 403)
        self.client.force_login(self.alice)
        detail = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertContains(detail, reverse('groups:edit_bill', args=[self.group.pk, bill.pk]))
        self.assertContains(detail, reverse('groups:delete_bill', args=[self.group.pk, bill.pk]))

    def test_bill_edit_updates_shares_and_linked_expenses_without_changing_payer(self):
        self.client.force_login(self.bob)
        self.add_bill(title='Hotel', amount='30.00', paid_by=self.alice, participants=(self.alice, self.bob, self.cara))
        bill = SharedBill.objects.get(title='Hotel')
        alice_expense = Expense.objects.get(group_bill_share__bill=bill, user=self.alice)
        self.client.force_login(self.alice)
        edit_url = reverse('groups:edit_bill', args=[self.group.pk, bill.pk])
        page = self.client.get(edit_url)
        self.assertContains(page, 'Edit bill')
        self.assertEqual(page.context['form']['split_method'].value(), 'amount')
        response = self.client.post(edit_url, {
            'title': 'Hotel revised', 'amount': '60.00', 'date': '2026-10-13',
            'paid_by': self.bob.pk, 'split_method': 'amount',
            f'include_{self.alice.pk}': 'on', f'include_{self.bob.pk}': 'on',
            f'amount_{self.alice.pk}': '20.00', f'amount_{self.bob.pk}': '40.00',
        })
        self.assertEqual(response.status_code, 302)
        bill.refresh_from_db()
        self.assertEqual(bill.paid_by_id, self.alice.pk)
        self.assertEqual(bill.title, 'Hotel revised')
        self.assertEqual(dict(bill.shares.values_list('user_id', 'amount')), {
            self.alice.pk: Decimal('20.00'), self.bob.pk: Decimal('40.00'),
        })
        alice_expense.refresh_from_db()
        self.assertEqual(alice_expense.amount_entered, Decimal('20.00'))
        self.assertEqual(Expense.objects.filter(group_bill_share__bill=bill).count(), 2)

    def test_only_payment_receiver_can_edit_confirm_and_delete(self):
        self.client.force_login(self.alice)
        self.add_bill(title='Cab', amount='20.00')
        self.client.force_login(self.bob)
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '10.00', 'payment_reference': 'TRKEDIT', 'destination_token': self.destination_token('TRKEDIT'), 'payment_completed': 'on',
        })
        payment = GroupPayment.objects.get()
        edit_url = reverse('groups:edit_payment', args=[self.group.pk, payment.pk])
        delete_url = reverse('groups:delete_payment', args=[self.group.pk, payment.pk])
        detail = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertNotContains(detail, edit_url)
        self.assertNotContains(detail, delete_url)
        self.assertEqual(self.client.post(edit_url, {'amount': '4.00'}).status_code, 403)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.client.force_login(self.alice)
        detail = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertContains(detail, edit_url)
        self.assertContains(detail, delete_url)
        self.assertContains(detail, 'Confirm received')
        self.client.post(edit_url, {'amount': '-1.00'})
        payment.refresh_from_db()
        self.assertEqual(payment.amount, Decimal('10.00'))
        self.client.post(edit_url, {'amount': '4.00'})
        payment.refresh_from_db()
        self.assertEqual(payment.amount, Decimal('4.00'))
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        payment.refresh_from_db()
        self.assertEqual(payment.status, GroupPayment.Status.CONFIRMED)
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('-6.00'))
        self.client.post(edit_url, {'amount': '5.00'})
        payment.refresh_from_db()
        self.assertEqual(payment.amount, Decimal('5.00'))
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('-5.00'))
        self.client.post(delete_url)
        self.assertFalse(GroupPayment.objects.filter(pk=payment.pk).exists())
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('-10.00'))

    def test_simplification_clears_balances(self):
        balances = {number: Decimal('-1.00') for number in range(12)}
        balances[12] = Decimal('12.00')
        transfers = simplify_balances(balances)
        for item in transfers:
            balances[item['from_user_id']] += item['amount']
            balances[item['to_user_id']] -= item['amount']
        self.assertTrue(all(amount == 0 for amount in balances.values()))

    def test_6000_paid_then_new_bill_leaves_only_200_and_receiver_can_correct_or_reject(self):
        self.client.force_login(self.alice)
        self.add_bill(title='Original', amount='12000.00')
        self.client.force_login(self.bob)
        payload = {'to_user': self.alice.pk, 'amount': '6000.00', 'payment_reference': 'TRK6000', 'destination_token': self.destination_token('TRK6000'), 'payment_completed': 'on'}
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload)
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('0.00'))
        self.add_bill(title='New bill', amount='400.00', paid_by=self.bob)
        detail_url = reverse('groups:detail', args=[self.group.pk])
        page = self.client.get(detail_url)
        suggestion = page.context['suggestions'][0]
        self.assertEqual((suggestion['sender'].pk, suggestion['receiver'].pk, suggestion['amount']),
                         (self.alice.pk, self.bob.pk, Decimal('200.00')))
        # Retrying the original submission after new bills must not count it twice.
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload)
        self.assertEqual(GroupPayment.objects.count(), 1)
        self.client.force_login(self.alice)
        payment = GroupPayment.objects.get()
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        self.assertEqual(group_balances(self.group)[self.alice.pk], Decimal('-200.00'))
        suggestion = self.client.get(detail_url).context['suggestions'][0]
        self.assertEqual((suggestion['sender'].pk, suggestion['receiver'].pk, suggestion['amount']),
                         (self.alice.pk, self.bob.pk, Decimal('200.00')))
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        self.assertEqual(group_balances(self.group)[self.alice.pk], Decimal('-200.00'))
        self.client.post(reverse('groups:edit_payment', args=[self.group.pk, payment.pk]), {'amount': '5800.00'})
        self.assertTrue(all(value == 0 for value in group_balances(self.group).values()))
        self.client.post(reverse('groups:reject_payment', args=[self.group.pk, payment.pk]))
        self.assertEqual(group_balances(self.group)[self.alice.pk], Decimal('5800.00'))
        self.assertNotContains(self.client.get(detail_url), 'Receiver confirmed')
        self.client.post(reverse('groups:reject_payment', args=[self.group.pk, payment.pk]))
        self.assertEqual(group_balances(self.group)[self.alice.pk], Decimal('5800.00'))
        self.assertEqual(Expense.objects.count(), 4)  # No duplicate settlement expense.

    def test_ajax_payment_actions_and_revision_are_available_for_live_refresh(self):
        self.client.force_login(self.alice)
        self.add_bill(amount='20.00')
        self.client.force_login(self.bob)
        detail_url = reverse('groups:detail', args=[self.group.pk])
        initial = self.client.get(detail_url).context['revision']
        self.assertEqual(self.client.get(detail_url).context['revision'], initial)
        response = self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '4.00', 'payment_reference': 'TRKAJAX', 'destination_token': self.destination_token('TRKAJAX'), 'payment_completed': 'on',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(response.json()['ok'])
        payment = GroupPayment.objects.get()
        page = self.client.get(detail_url)
        self.assertNotEqual(page.context['revision'], initial)
        self.assertEqual(page.context['suggestions'][0]['amount'], Decimal('6.00'))
        forbidden = self.client.post(reverse('groups:reject_payment', args=[self.group.pk, payment.pk]),
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(forbidden.status_code, 400)
        self.client.force_login(self.alice)
        edited = self.client.post(reverse('groups:edit_payment', args=[self.group.pk, payment.pk]),
                                  {'amount': '3.00'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(edited.json()['ok'])
        rejected = self.client.post(reverse('groups:reject_payment', args=[self.group.pk, payment.pk]),
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(rejected.json()['ok'])
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('-10.00'))

    def test_migration_counts_existing_pending_claims_once(self):
        from importlib import import_module
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection

        self.client.force_login(self.alice)
        self.add_bill(amount='12000.00')
        payment = GroupPayment.objects.create(group=self.group, from_user=self.bob, to_user=self.alice,
            created_by=self.bob, amount=Decimal('6000.00'), status=GroupPayment.Status.PENDING)
        migrate = import_module('apps.groups.migrations.0002_alter_grouppayment_status').approve_existing_claims
        migrate(apps, SimpleNamespace(connection=connection))
        migrate(apps, SimpleNamespace(connection=connection))
        payment.refresh_from_db()
        self.assertEqual(payment.status, GroupPayment.Status.AUTO_APPROVED)
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('0.00'))

    def test_different_website_and_payment_names_do_not_change_destination(self):
        self.alice.first_name = 'Website Alice'
        self.alice.upi_account_name = 'Alice Kumar'
        self.alice.save(update_fields=['first_name', 'upi_account_name'])
        suggestion, payload = self.issued_payment()
        self.assertEqual(suggestion['receiver'].pk, self.alice.pk)
        response = self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(response.json()['ok'])
        payment = GroupPayment.objects.get()
        self.assertEqual((payment.to_user_id, payment.payee_upi_id, payment.payee_name),
                         (self.alice.pk, 'alice@okaxis', 'Alice Kumar'))
        self.assertEqual(payment.status, GroupPayment.Status.AUTO_APPROVED)
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('0.00'))

    def test_changed_upi_preserves_original_claim_destination(self):
        old, payload = self.issued_payment()
        self.alice.upi_id = 'new.alice@oksbi'
        self.alice.upi_account_name = 'New Bank Name'
        self.alice.save(update_fields=['upi_id', 'upi_account_name'])
        # A payer can still report a transfer already made using the issued snapshot.
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload)
        payment = GroupPayment.objects.get()
        self.assertEqual(payment.payee_upi_id, 'alice@okaxis')
        self.client.force_login(self.alice)
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        payment.refresh_from_db()
        self.assertEqual(payment.payee_upi_id, 'alice@okaxis')
        self.assertEqual(payment.to_user_id, self.alice.pk)
        self.assertContains(self.client.get(reverse('groups:detail', args=[self.group.pk])), 'alice@okaxis')

    def test_tampered_receiver_reference_amount_or_token_cannot_claim_payment(self):
        _, payload = self.issued_payment()
        url = reverse('groups:add_payment', args=[self.group.pk])
        for changes in (
            {'to_user': self.cara.pk}, {'payment_reference': 'another-reference'},
            {'amount': '10.01'}, {'amount': 'NaN'}, {'amount': '0'}, {'amount': '-1'},
            {'amount': '1.001'}, {'destination_token': payload['destination_token'] + 'x'},
            {'destination_token': ''}, {'payment_completed': ''},
        ):
            with self.subTest(changes=list(changes)):
                response = self.client.post(url, payload | changes, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(response.status_code, 400)
                self.assertFalse(GroupPayment.objects.exists())
        with patch('django.core.signing.time.time', return_value=9999999999):
            response = self.client.post(url, payload, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(GroupPayment.objects.exists())

    def test_return_cancel_and_app_fallback_do_not_record_or_confirm_payment(self):
        _, payload = self.issued_payment()
        detail = reverse('groups:detail', args=[self.group.pk])
        for params in ({'upi_fallback': str(self.alice.pk), 'upi_amount': '10.00'}, {'status': 'SUCCESS'}, {}):
            self.assertEqual(self.client.get(detail, params).status_code, 200)
        self.assertFalse(GroupPayment.objects.exists())
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload)
        self.client.get(detail, {'status': 'SUCCESS'})
        self.assertEqual(GroupPayment.objects.get().status, GroupPayment.Status.AUTO_APPROVED)
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('0.00'))

    def test_paid_claims_apply_immediately_and_new_bills_remain_available(self):
        _, payload = self.issued_payment()
        url = reverse('groups:add_payment', args=[self.group.pk])
        self.client.post(url, payload)
        other = payload | {'payment_reference': 'other', 'destination_token': self.destination_token('other')}
        self.assertEqual(self.client.post(url, other, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 400)
        self.assertEqual(self.add_bill(title='New while pending', amount='400.00', paid_by=self.bob).status_code, 302)
        self.assertEqual(GroupPayment.objects.count(), 1)
        self.client.post(url, payload)  # Retry remains idempotent even after the new bill.
        self.assertEqual(GroupPayment.objects.count(), 1)
        self.assertTrue(self.client.get(reverse('groups:detail', args=[self.group.pk])).context['suggestions'])
        self.client.force_login(self.alice)
        payment = GroupPayment.objects.get()
        confirm = reverse('groups:confirm_payment', args=[self.group.pk, payment.pk])
        self.client.post(confirm)
        balance = group_balances(self.group)
        self.client.post(confirm)
        self.assertEqual(group_balances(self.group), balance)
        self.assertEqual(GroupPayment.objects.count(), 1)

    def test_missing_upi_still_allows_reporting_and_confirming_direct_transfer(self):
        self.alice.upi_id = ''
        self.alice.save(update_fields=['upi_id'])
        _, payload = self.issued_payment()
        page = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertContains(page, 'data-settlement-form')
        self.assertNotContains(page, 'data-toropay-checkout')
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload)
        payment = GroupPayment.objects.get()
        self.assertEqual(payment.status, GroupPayment.Status.AUTO_APPROVED)
        self.client.force_login(self.alice)
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('0.00'))

    def test_existing_pending_claim_migration_applies_each_payment_once(self):
        from importlib import import_module
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection
        self.client.force_login(self.alice)
        self.add_bill(amount='20.00')
        payment = GroupPayment.objects.create(group=self.group, from_user=self.bob, to_user=self.alice,
            created_by=self.bob, amount=Decimal('10.00'), status=GroupPayment.Status.PENDING)
        migrate = import_module('apps.groups.migrations.0006_alter_grouppayment_status').approve_recorded_claims
        migrate(apps, SimpleNamespace(connection=connection))
        migrate(apps, SimpleNamespace(connection=connection))
        payment.refresh_from_db()
        self.assertEqual(payment.status, GroupPayment.Status.AUTO_APPROVED)
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('0.00'))

    def test_paid_button_is_the_single_confirmation_action(self):
        self.issued_payment()
        page = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertContains(page, '<input type="hidden" name="payment_completed" value="on">', html=True)
        self.assertNotContains(page, 'My UPI app shows this payment succeeded.')
        self.assertContains(page, 'I’ve paid — update balances')
        self.assertFalse(GroupPayment.objects.exists())
