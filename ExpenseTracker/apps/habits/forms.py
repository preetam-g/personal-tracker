from django.forms import ModelForm, DateInput
from django.utils import timezone

from apps.habits.models import Habit, HabitPlan


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


class HabitPlanForm(ModelForm):

    class Meta:
        model = HabitPlan
        fields = (
            'habit',
            'start_date',
            'end_date',
            'target_value',
            'unit',
        )
        labels = {
            'habit' : 'Habit*',
            'start_date' : 'Start Date*',
            'target_value' : 'Target Value*',
            'unit' : 'Unit*',
        }
        widgets = {
            "start_date": DateInput(attrs={"type": "date"}),
            "end_date": DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user')
        if not self.user: raise Exception('User is required')

        super().__init__(*args, **kwargs)

        self.fields['habit'].queryset = Habit.objects.active().all_for_user(user=self.user)

        today = timezone.localdate().strftime('%Y-%m-%d')
        self.fields['start_date'].widget.attrs['min'] = today
        self.fields['start_date'].initial = today

        self.habit_defaults = {
            habit.pk: {
                "target": str(habit.default_target_value),
                "unit": habit.default_unit,
            }
            for habit in self.fields["habit"].queryset
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            self.add_error(
                "end_date",
                "End date cannot be before start date.",
            )

        return cleaned_data