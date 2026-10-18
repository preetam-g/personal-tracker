from decimal import Decimal
from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.expenses.models import ExpenseCategory
from .models import SharedGroup, SharedBill
from .services import claim_payment, create_bill, update_bill


class SharedGroupForm(forms.ModelForm):
    class Meta:
        model = SharedGroup
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Enter a group name.')
        return name


class AddMemberForm(forms.Form):
    username = forms.CharField(max_length=150, label='Registered username')

    def __init__(self, *args, group, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        user = get_user_model().objects.filter(username__iexact=username).first()
        if user is None:
            raise forms.ValidationError('No account has that username. Ask them to sign up first.')
        if self.group.members.filter(pk=user.pk).exists():
            raise forms.ValidationError('That person is already in the group.')
        self.member = user
        return username


class SharedBillForm(forms.ModelForm):
    split_method = forms.ChoiceField(
        choices=[('equal', 'Equally'), ('percentage', 'By percentage'), ('amount', 'By amount')],
        initial='equal', widget=forms.RadioSelect,
    )

    class Meta:
        model = SharedBill
        fields = ['title', 'amount', 'date', 'paid_by', 'category']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}
        labels = {'paid_by': 'Paid by', 'amount': 'Total amount (INR)'}

    def __init__(self, *args, group, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group
        self.members = list(group.members.order_by('username'))
        existing_shares = {
            share.user_id: share for share in self.instance.shares.all()
        } if self.instance.pk else {}
        self.fields['paid_by'].queryset = group.members.order_by('username')
        if self.instance.pk:
            self.fields['paid_by'].disabled = True
            self.fields['split_method'].initial = 'amount'
        self.fields['category'].queryset = ExpenseCategory.objects.only_global()
        self.fields['category'].empty_label = 'Uncategorized'
        self.fields['date'].initial = timezone.localdate()
        self.fields['date'].widget.attrs['max'] = timezone.localdate().isoformat()
        method = self.data.get('split_method', 'amount' if self.instance.pk else 'equal') if self.is_bound else ('amount' if self.instance.pk else 'equal')
        equal = 10000 // len(self.members) if self.members else 0
        leftover = 10000 - equal * len(self.members)
        for index, member in enumerate(self.members):
            self.fields[f'include_{member.pk}'] = forms.BooleanField(
                required=False, initial=member.pk in existing_shares if self.instance.pk else True,
                label=member.username,
            )
            percent_field = forms.DecimalField(
                label=f'{member.username} (%)', max_digits=5, decimal_places=2,
                min_value=0, max_value=100, required=False,
                widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            )
            if not self.is_bound:
                percent_field.initial = existing_shares[member.pk].percentage if member.pk in existing_shares else Decimal(equal + (leftover if index == 0 else 0)) / 100
            percent_field.disabled = method != 'percentage'
            self.fields[f'percent_{member.pk}'] = percent_field
            amount_field = forms.DecimalField(
                label=f'{member.username} (INR)', max_digits=12, decimal_places=2,
                min_value=0, required=False,
                widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            )
            amount_field.disabled = method != 'amount'
            if not self.is_bound and member.pk in existing_shares:
                amount_field.initial = existing_shares[member.pk].amount
            self.fields[f'amount_{member.pk}'] = amount_field
        self.split_rows = [
            {
                'member': member,
                'included': self[f'include_{member.pk}'],
                'percentage': self[f'percent_{member.pk}'],
                'amount': self[f'amount_{member.pk}'],
            }
            for member in self.members
        ]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('date') and cleaned['date'] > timezone.localdate():
            self.add_error('date', 'A bill cannot be dated in the future.')
        amount = cleaned.get('amount')
        if amount is not None and amount <= 0:
            self.add_error('amount', 'Enter a positive amount.')
        selected = [member for member in self.members if cleaned.get(f'include_{member.pk}')]
        if not selected:
            raise forms.ValidationError('Select at least one person for this bill.')
        method = cleaned.get('split_method')
        self.percentages = None
        self.amounts = None
        if method == 'equal' and amount and amount > 0:
            cents = int(amount * 100)
            if cents < len(selected):
                raise forms.ValidationError('The bill needs at least ₹0.01 for each selected person.')
            each, extra = divmod(cents, len(selected))
            self.amounts = {
                member.pk: Decimal(each + (index < extra)) / 100
                for index, member in enumerate(selected)
            }
        elif method == 'percentage':
            self.percentages = {}
            for member in selected:
                share = cleaned.get(f'percent_{member.pk}')
                if share is None or share <= 0:
                    self.add_error(f'percent_{member.pk}', 'Enter a percentage above 0, or untick this person.')
                else:
                    self.percentages[member.pk] = share
            if not self.errors and sum(self.percentages.values(), Decimal('0')) != Decimal('100'):
                raise forms.ValidationError('Selected percentages must add up to 100%.')
        elif method == 'amount':
            self.amounts = {}
            for member in selected:
                share = cleaned.get(f'amount_{member.pk}')
                if share is None or share <= 0:
                    self.add_error(f'amount_{member.pk}', 'Enter an amount above ₹0, or untick this person.')
                else:
                    self.amounts[member.pk] = share
            if not self.errors and amount is not None and sum(self.amounts.values(), Decimal('0.00')) != amount:
                raise forms.ValidationError('Selected amounts must add up to the bill total.')
        return cleaned

    def save(self, *, created_by):
        if self.instance.pk:
            return update_bill(
                bill=self.instance, editor=created_by,
                title=self.cleaned_data['title'], amount=self.cleaned_data['amount'],
                date=self.cleaned_data['date'], category=self.cleaned_data['category'],
                percentages=self.percentages, amounts=self.amounts,
            )
        return create_bill(
            group=self.group, title=self.cleaned_data['title'],
            amount=self.cleaned_data['amount'], date=self.cleaned_data['date'],
            paid_by=self.cleaned_data['paid_by'], created_by=created_by,
            category=self.cleaned_data['category'],
            percentages=self.percentages, amounts=self.amounts,
        )


class GroupPaymentForm(forms.Form):
    to_user = forms.ModelChoiceField(queryset=get_user_model().objects.none())
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    payment_reference = forms.CharField(max_length=64, widget=forms.HiddenInput)

    def __init__(self, *args, group, sender, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group
        self.sender = sender
        self.fields['to_user'].queryset = group.members.exclude(pk=sender.pk)

    def save(self):
        return claim_payment(
            group=self.group, from_user=self.sender,
            to_user=self.cleaned_data['to_user'], amount=self.cleaned_data['amount'],
            reference=self.cleaned_data['payment_reference'],
        )


class PaymentAmountEditForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
    )
