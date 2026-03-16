from django import forms
from apps.expenses.models import Expense
from django.utils import timezone

class ExpenseForm(forms.ModelForm):

    class Meta:

        model = Expense
        fields = ['date', 'amount', 'note', 'category', 'type']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs): # frontend blocking for dates
        super().__init__(*args, **kwargs)

        today = timezone.now().date().strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs['max'] = today

    def clean_date(self): # backend validation for dates

        submitted_date = self.cleaned_data['date']

        if hasattr(submitted_date, 'date'):
            submitted_date = submitted_date.date()

        if submitted_date > timezone.now().date():
            raise forms.ValidationError('You cannot log an expense for a future date!')

        return self.cleaned_data['date']