from django import forms

from apps.accounts.models import UserPreference


class ForexFeaturesForm(forms.ModelForm):

    class Meta:
        model = UserPreference
        fields = [
            'preferred_currency',
        ]
        widgets = {
            'preferred_currency': forms.Select(
                attrs={'class': 'tom-select'}
            ),
        }
        labels = {
            'preferred_currency': 'Preferred currency',
        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user')
        if not self.user:
            raise ValueError('User is required')

        super().__init__(*args, **kwargs)