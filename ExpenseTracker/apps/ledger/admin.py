from django.contrib import admin

from apps.ledger.models import Transaction, Contact

class ContactAdmin(admin.ModelAdmin):

    list_display = ('name', 'user',)
    list_filter = ('user',)


class TransactionAdmin(admin.ModelAdmin):
    pass

admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Contact, ContactAdmin)