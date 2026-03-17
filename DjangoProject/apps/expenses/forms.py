from email.policy import default

from django import forms
from .models import Expense, ExpenseCategory, ExpenseType
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


class ExpenseFilterForm(forms.Form):

    start_date = forms.DateField(
        required=False,
        label="Start Date",
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    end_date = forms.DateField(
        required=False,
        label="End Date",
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.all(), # later filter based on user
        required=False,
        label="Category",
        empty_label="All Categories",
    )

    # type = forms.ModelChoiceField(
    #     queryset=ExpenseType.objects.all(),
    #     required=False,
    #     label="Type",
    #     empty_label="All Types",
    # )

    SORT_CHOICES = [
        ('-date', 'Newest First'),
        ('date', 'Oldest First'),
        ('-amount', 'Highest Amount'),
        ('amount', 'Lowest Amount'),
    ]

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        label="Sort By",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = timezone.now().date().strftime('%Y-%m-%d')
        self.fields['start_date'].widget.attrs['max'] = today
        self.fields['end_date'].widget.attrs['max'] = today