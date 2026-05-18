from django.contrib import admin

from apps.base.admin import SoftDeleteAdmin
from apps.ledger.models import Transaction, Contact

class ContactAdmin(SoftDeleteAdmin):

    list_display = ('name', 'user',)
    list_filter = ('user',)


class TransactionAdmin(SoftDeleteAdmin):
    pass

# Register your models here.
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Contact, ContactAdmin)