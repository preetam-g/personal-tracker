from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile
from django.forms import ModelForm


class SignupForm(UserCreationForm):

    class Meta:
        model = UserProfile
        fields = ["username", "email"]


class LoginForm(AuthenticationForm):
    pass


class UserUpdateForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ["first_name", "last_name", "username", "email"]

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True