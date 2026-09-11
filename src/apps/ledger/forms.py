from django import forms
from django.utils import timezone

from apps.base.utils import TimeFrame
from apps.ledger.models import Transaction, Contact


class TransactionForm(forms.ModelForm):

    class Meta:
        model = Transaction
        fields = ['contact', 'date', 'amount', 'type', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'date': 'Date*',
            'amount': 'Amount*',
            'contact': 'Contact*',
            'type': 'Type*',
        }

    def __init__(self, *args, user, **kwargs):

        self.user = user
        super().__init__(*args, **kwargs)

        today = timezone.localdate().strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs['max'] = today
        self.fields['date'].initial = today

        note_max_len = self.Meta.model._meta.get_field('note').max_length
        if note_max_len:
            self.fields['note'].widget.attrs['maxlength'] = str(note_max_len)
            self.fields['note'].widget.attrs['rows'] = str(note_max_len//30 + 1)

        self.fields['contact'].queryset = Contact.objects.for_user(self.user)

    def clean_date(self):

        submitted_date = self.cleaned_data['date']
        current_date = timezone.localtime()

        if submitted_date > current_date:
            raise forms.ValidationError('You cannot log an expense for a future date!')

        return self.cleaned_data['date']

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')

        return amount


class ContactForm(forms.ModelForm):

    class Meta:
        model = Contact
        fields = ['name']

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if not self.instance.pk:
            self.instance.user = self.user


class LedgerSummaryDefaultsForm(forms.Form):

    timeframe_home = forms.ChoiceField(
        choices=TimeFrame,
        initial=TimeFrame.THIRTY_DAYS,
        required=False,
        label="Timeframe (Home Page)",
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        defaults = self.user.preferences.get_ledger_preferences(
            "ledger_defaults",
            {},
        )

        self.initial.update(defaults)


class LedgerHomeForm(forms.Form):

    timeframe = forms.ChoiceField(
        choices=TimeFrame,
        initial=TimeFrame.SEVEN_DAYS,
        required=False,
        label=None,
        widget=forms.Select(attrs={
            'onchange': 'this.form.submit()'
        })
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if not self.is_bound:
            defaults = self.user.preferences.get_ledger_preferences(
                'ledger_defaults',
                {}
            )

            self.initial['timeframe'] = defaults.get(
                'timeframe_home',
                TimeFrame.SEVEN_DAYS,
            )