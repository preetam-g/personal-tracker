from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models.functions import Coalesce
from django.db.models import Sum, Q, F, DecimalField, Manager
from django.utils import timezone

from .utils import TransactionType

from datetime import timedelta, time, datetime
from decimal import Decimal


class TransactionManager(Manager):

    def base_for_user(self, user:AbstractBaseUser):
        return self.get_queryset().filter(user=user)

    def all_for_user(self, user:AbstractBaseUser):
        return (
            self.base_for_user(user)
            .select_related('contact')
        )

    def filtered_for_user(self, user:AbstractBaseUser, filter_form: dict):

        qs = self.all_for_user(user)

        start_date = filter_form.get('start_date')
        if start_date:
            start_date = timezone.make_aware(datetime.combine(start_date, time.min))
            qs = qs.filter(date__gte=start_date)

        end_date = filter_form.get('end_date')
        if end_date:
            end_date = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min))
            qs = qs.filter(date__lt=end_date)

        return qs

    def get_contacts_summary(self, user:AbstractBaseUser, filter_form:dict) -> dict:

        qs = self.filtered_for_user(user, filter_form).order_by()

        aggregates = list(
            qs.values(
                'contact',
                contact_name=F('contact__name'),
            )
            .annotate(
                sent=Coalesce(
                    Sum('amount', filter=Q(type=TransactionType.MONEY_SENT)),
                    Decimal('0.00'),
                    output_field=DecimalField(),
                ),
                received=Coalesce(
                    Sum('amount', filter=Q(type=TransactionType.MONEY_RECEIVED)),
                    Decimal('0.00'),
                    output_field=DecimalField(),
                ),
            )
            .annotate(
                balance=F('sent') - F('received')
            )
        )

        total_stats = {
            'owed': round(
                sum(
                    item['balance']
                    for item in aggregates
                    if item['balance'] > 0
            ), 2),

            'owe': round(
                abs(sum(
                    item['balance']
                    for item in aggregates
                    if item['balance'] < 0
            )), 2),

            'net_balance': round(
                sum(
                    item['balance']
                    for item in aggregates
            ), 2),
        }

        return {
            'stats': total_stats,
            'contacts_info': aggregates,
        }


class ContactManager(Manager):

    def for_user(self, user:AbstractBaseUser):
        return self.get_queryset().filter(user=user)