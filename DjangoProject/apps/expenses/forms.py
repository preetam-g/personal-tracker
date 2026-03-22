from email.policy import default

from django import forms
from .models import Expense, ExpenseCategory, ExpenseType
from django.utils import timezone
from .utils import SortChoices, TimeFrame

class ExpenseForm(forms.ModelForm):

    class Meta:

        model = Expense
        fields = ['date', 'amount', 'note', 'category', 'type']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    # frontend
    def __init__(self, *args, **kwargs): # frontend
        super().__init__(*args, **kwargs)

        today = timezone.now().date().strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs['max'] = today

        note_max_len = self.Meta.model._meta.get_field('note').max_length

        if note_max_len:
            self.fields['note'].widget.attrs['maxlength'] = str(note_max_len)
            self.fields['note'].widget.attrs['rows'] = str(note_max_len/10 + 1)

    # backend
    def clean_date(self):

        submitted_date = self.cleaned_data['date']

        if hasattr(submitted_date, 'date'):
            submitted_date = submitted_date.date()

        if submitted_date > timezone.now().date():
            raise forms.ValidationError('You cannot log an expense for a future date!')

        return self.cleaned_data['date']

    def clean_note(self):
        note = self.cleaned_data.get('note', '')
        max_len = self.Meta.model._meta.get_field('note').max_length

        if note and len(note) > max_len:
            raise forms.ValidationError(f'Keep it short! Notes cannot exceed {max_len} characters.')

        return note


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

    type = forms.ModelChoiceField(
        queryset=ExpenseType.objects.all(),
        required=False,
        label="Type",
        empty_label="All Types",
    )

    sort_by = forms.ChoiceField(
        choices=SortChoices,
        required=False,
        label="Sort By",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = timezone.now().date().strftime('%Y-%m-%d')
        self.fields['start_date'].widget.attrs['max'] = today
        self.fields['end_date'].widget.attrs['max'] = today


class DashboardForm(forms.Form):
    timeFrame = forms.ChoiceField(
        choices=TimeFrame,
        required=False,
        initial=TimeFrame.THIS_MONTH,
        label="Timeframe",
    )