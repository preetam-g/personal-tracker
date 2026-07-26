from django.forms import ModelForm

from apps.habits.models import Habit


class HabitForm(ModelForm):

    class Meta:
        model = Habit
        fields = (
            'name',
            'default_target_value',
            'default_unit',
        )
        labels = {
            'name' : 'Name*',
            'default_target_value' : 'Target Value*',
            'default_unit' : 'Unit*',
        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user')
        if not self.user: raise Exception('User is required')

        super().__init__(*args, **kwargs)