from django.db import migrations


def set_group_bill_share_type_upi(apps, schema_editor):
    Expense = apps.get_model('expenses', 'Expense')
    ExpenseType = apps.get_model('expenses', 'ExpenseType')
    alias = schema_editor.connection.alias
    upi_type, _ = ExpenseType.objects.using(alias).get_or_create(name='UPI', user=None)
    Expense.objects.using(alias).filter(group_bill_share__isnull=False).update(type_id=upi_type.pk)


class Migration(migrations.Migration):
    dependencies = [('expenses', '0019_backfill_group_bill_share_expenses')]

    operations = [migrations.RunPython(set_group_bill_share_type_upi, migrations.RunPython.noop)]
