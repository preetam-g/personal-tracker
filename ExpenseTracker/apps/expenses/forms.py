from django import forms
from .models import Expense, ExpenseCategory, ExpenseType
from django.utils import timezone

from .utils import SortChoices

from apps.base.utils import TimeFrame
from apps.base.forms import CategoryTypeValidationForm


class ExpenseForm(forms.ModelForm):

    class Meta:
        model = Expense
        fields = ['date', 'amount', 'category', 'type', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'amount': 'Amount*',
            'date': 'Date*',
        }

    # frontend
    def __init__(self, *args, **kwargs): # frontend

        self.user = kwargs.pop('user', None)
        if not self.user: raise Exception('User is required')

        super().__init__(*args, **kwargs)

        # date
        today = timezone.localdate().strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs['max'] = today
        self.fields['date'].initial = today

        # note
        note_max_len = self.Meta.model._meta.get_field('note').max_length
        if note_max_len:
            self.fields['note'].widget.attrs['maxlength'] = str(note_max_len)
            self.fields['note'].widget.attrs['rows'] = str(note_max_len//10 + 1)

        # categories, types
        self.fields['category'].queryset = ExpenseCategory.objects.user_items(self.user)
        self.fields['type'].queryset = ExpenseType.objects.user_items(self.user)

    # backend
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
        queryset=ExpenseCategory.objects.only_global(),
        required=False,
        label="Category",
        empty_label="All Categories",
    )

    type = forms.ModelChoiceField(
        queryset=ExpenseType.objects.only_global(),
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

        user = kwargs.pop('user', None)
        if not user: raise Exception('User is required')

        super().__init__(*args, **kwargs)

        today = timezone.localtime().strftime('%Y-%m-%d')

        self.fields['start_date'].widget.attrs['max'] = today
        self.fields['end_date'].widget.attrs['max'] = today

        if user:
            self.fields['category'].queryset = ExpenseCategory.objects.user_items(user)
            self.fields['type'].queryset = ExpenseType.objects.user_items(user)

    def clean(self):
        start = self.cleaned_data.get('start_date')
        end = self.cleaned_data.get('end_date')

        if start and end and start > end:
            raise forms.ValidationError("Start date can't be after end date!")

        return self.cleaned_data


class DashboardForm(forms.Form):
    timeFrame = forms.ChoiceField(
        choices=TimeFrame,
        required=False,
        initial=TimeFrame.SEVEN_DAYS,
        label="Timeframe",
        widget=forms.Select(attrs={
            'onchange': 'this.form.submit()'
        })
    )


class ExpenseCategoryForm(CategoryTypeValidationForm):

    class Meta:
        model = ExpenseCategory
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = "New Category"


class ExpenseTypeForm(CategoryTypeValidationForm):

    class Meta:
        model = ExpenseType
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = "New Type"