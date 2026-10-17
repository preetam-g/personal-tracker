from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.expenses.models import Expense
from .models import BillShare, GroupMembership, GroupPayment, SharedBill, SharedGroup
from .services import group_balances, simplify_balances


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
        self.assertContains(detail, 'Choose CRED')
        self.assertContains(detail, 'upi://pay?')
        self.assertContains(detail, 'gpay-mark.svg')
        self.assertContains(detail, 'Settle a particular amount')
        self.assertContains(detail, 'Group activity')
        self.assertContains(detail, 'alice</strong> paid <strong>₹100.00</strong> for Dinner')
        self.assertContains(detail, '<details class="group-activity-card">', html=False)
        payment_response = self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '33.33', 'payment_reference': 'TRK123',
        })
        self.assertEqual(payment_response.status_code, 302)
        payment = GroupPayment.objects.get()
        self.assertEqual(payment.status, GroupPayment.Status.PENDING)
        self.assertContains(self.client.get(reverse('groups:detail', args=[self.group.pk])), 'waiting for alice to confirm receipt')
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('-33.33'))
        self.client.force_login(self.alice)
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        payment.refresh_from_db()
        self.assertEqual(payment.status, GroupPayment.Status.CONFIRMED)
        self.assertEqual(group_balances(self.group)[self.bob.pk], Decimal('0.00'))
        self.assertEqual(Expense.objects.count(), 3)

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
        self.assertContains(self.client.get(reverse('groups:detail', args=[self.group.pk])), 'Settle ₹10.00')
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '4.00', 'payment_reference': 'TRKPARTIAL',
        })
        payment = GroupPayment.objects.get()
        page = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertContains(page, 'Settle ₹6.00')
        self.assertContains(page, '₹4.00 from bob to alice — waiting for alice to confirm receipt.')
        self.client.force_login(self.alice)
        self.client.post(reverse('groups:reject_payment', args=[self.group.pk, payment.pk]))
        self.client.force_login(self.bob)
        self.assertContains(self.client.get(reverse('groups:detail', args=[self.group.pk])), 'Settle ₹10.00')

    def test_pending_full_payment_does_not_show_settled_or_duplicate_suggestion(self):
        self.client.force_login(self.alice)
        self.add_bill(amount='20.00')
        self.client.force_login(self.bob)
        payload = {'to_user': self.alice.pk, 'amount': '10.00', 'payment_reference': 'TRK456'}
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload)
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), payload)
        self.assertEqual(GroupPayment.objects.filter(status='pending').count(), 1)
        page = self.client.get(reverse('groups:detail', args=[self.group.pk]))
        self.assertNotContains(page, 'Everyone is settled.')
        self.assertNotContains(page, 'Settle ₹10.00')

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

    def test_only_receiver_can_confirm_pending_payment(self):
        self.client.force_login(self.alice)
        self.add_bill(amount='20.00')
        self.client.force_login(self.bob)
        self.client.post(reverse('groups:add_payment', args=[self.group.pk]), {
            'to_user': self.alice.pk, 'amount': '10.00', 'payment_reference': 'TRKRECEIVER',
        })
        payment = GroupPayment.objects.get()
        self.client.post(reverse('groups:confirm_payment', args=[self.group.pk, payment.pk]))
        payment.refresh_from_db()
        self.assertEqual(payment.status, GroupPayment.Status.PENDING)
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
            'to_user': self.alice.pk, 'amount': '10.00', 'payment_reference': 'TRKEDIT',
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
        self.client.post(edit_url, {'amount': '11.00'})
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
