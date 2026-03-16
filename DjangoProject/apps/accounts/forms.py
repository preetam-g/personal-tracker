from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile
from django.forms import ModelForm


class SignupForm(UserCreationForm):

    class Meta:
        model = UserProfile
        fields = ["username", "email"]


class LoginForm(AuthenticationForm):
    pass


class UpdateUserForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ["first_name", "last_name"]