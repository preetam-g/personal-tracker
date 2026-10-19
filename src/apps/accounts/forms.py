from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, PasswordChangeForm
from django import forms

UserModel = get_user_model()


class SignupForm(UserCreationForm):

    class Meta:
        model = UserModel
        fields = ["username", "email"]


class LoginForm(AuthenticationForm):
    pass


class UpdateUserForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ["first_name", "last_name", "username", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True


class UPIIdForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ['upi_id']
        labels = {'upi_id': 'Your UPI ID'}
        widgets = {'upi_id': forms.TextInput(attrs={'placeholder': 'yourname@bank', 'autocomplete': 'off'})}

    def clean_upi_id(self):
        upi_id = self.cleaned_data['upi_id'].strip().lower()
        return upi_id
