from django import forms
from django.utils import timezone
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

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)
        if not self.user: raise Exception('User is required')

        super().__init__(*args, **kwargs)

        today = timezone.localdate().strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs['max'] = today
        self.fields['date'].initial = today

        note_max_len = self.Meta.model._meta.get_field('note').max_length
        if note_max_len:
            self.fields['note'].widget.attrs['maxlength'] = str(note_max_len)
            self.fields['note'].widget.attrs['rows'] = str(note_max_len // 10 + 1)

        self.fields['contact'].queryset = Contact.objects.all() # all for user

    def clean_date(self):

        submitted_date = self.cleaned_data['date']
        current_date = timezone.localtime()

        if submitted_date > current_date:
            raise forms.ValidationError('You cannot log an expense for a future date!')

        return self.cleaned_data['date']

    def clean_note(self):
        note = self.cleaned_data.get('note', '')
        max_len = self.Meta.model._meta.get_field('note').max_length

        if note and len(note) > max_len:
            raise forms.ValidationError(f'Keep it short! Notes cannot exceed {max_len} characters.')

        return note

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')

        return amount