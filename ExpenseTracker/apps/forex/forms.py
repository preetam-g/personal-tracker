from django import forms

from apps.accounts.models import UserPreference


class ForexFeaturesForm(forms.ModelForm):

    class Meta:
        model = UserPreference
        fields = ['preferred_currency', 'show_advanced_currency_features']
        widgets = {
            'show_advanced_currency_features': forms.CheckboxInput(),
            'preferred_currency': forms.Select(
                attrs={'class': 'tom-select'}
            ),
        }
        labels = {
            'show_advanced_currency_features': 'Show forex features',
            'preferred_currency': 'Preferred currency',
        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user')
        if not self.user:
            raise ValueError('User is required')

        super().__init__(*args, **kwargs)