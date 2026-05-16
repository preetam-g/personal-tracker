from django.contrib import admin

from apps.base.admin import SoftDeleteAdmin
from apps.ledger.models import Transaction, Contact

class ContactAdmin(SoftDeleteAdmin):

    list_display = ('name', 'owner',)
    list_filter = ('owner',)


class TransactionAdmin(SoftDeleteAdmin):
    pass

# Register your models here.
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Contact, ContactAdmin)