from datetime import datetime, time
from decimal import Decimal

from django.db import migrations
from django.utils import timezone


def backfill_group_bill_expenses(apps, schema_editor):
    Expense = apps.get_model('expenses', 'Expense')
    BillShare = apps.get_model('ledger', 'BillShare')
    Currency = apps.get_model('forex', 'Currency')
    alias = schema_editor.connection.alias
    inr = Currency.objects.using(alias).get(code='INR')

    for share in BillShare.objects.using(alias).select_related('bill__group').filter(amount__gt=0).iterator():
        bill = share.bill
        Expense.objects.using(alias).get_or_create(
            group_bill_share_id=share.pk,
            defaults={
                'user_id': share.user_id,
                'date': timezone.make_aware(datetime.combine(bill.date, time(12, 0))),
                'amount': share.amount,
                'amount_entered': share.amount,
                'currency_id': inr.pk,
                'exchange_rate': Decimal('1'),
                'category_id': bill.category_id,
                'note': f'Group: {bill.group.name} / {bill.title}'[:50],
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ('expenses', '0018_expense_group_bill_share'),
        ('ledger', '0013_grouppayment_confirmed_at_grouppayment_payee_upi_id_and_more'),
    ]

    operations = [migrations.RunPython(backfill_group_bill_expenses, migrations.RunPython.noop)]
