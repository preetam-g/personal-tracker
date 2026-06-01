from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, PasswordChangeForm
from django import forms

from .models import UserProfile

from apps.expenses import (
    models as expenses_models,
)

from apps.base.utils import TimeFrame


class SignupForm(UserCreationForm):

    class Meta:
        model = UserProfile
        fields = ["username", "email"]


class LoginForm(AuthenticationForm):
    pass


class UpdateUserForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["first_name", "last_name", "username", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True


class ExpenseFilterDefaultsForm(forms.Form):

    timeframe = forms.ChoiceField(
        choices=TimeFrame,
        required=False,
        initial=TimeFrame.SEVEN_DAYS,
        label="Timeframe",
    )

    category = forms.ModelChoiceField(
        queryset=expenses_models.ExpenseCategory.objects.only_global(),
        required=False,
        label="Category",
        empty_label="All Categories",
    )

    type = forms.ModelChoiceField(
        queryset=expenses_models.ExpenseType.objects.only_global(),
        required=False,
        label="Type",
        empty_label="All Types",
    )

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)
        if not self.user:
            raise Exception('User is required')

        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = expenses_models.ExpenseCategory.objects.user_items(self.user)
        self.fields['type'].queryset = expenses_models.ExpenseType.objects.user_items(self.user)