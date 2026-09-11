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