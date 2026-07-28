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
        today = timezone.localdate()
        today_str = today.isoformat()

        if not self.instance.pk:
            # New goal
            self.fields['start_date'].initial = today
            self.fields['start_date'].widget.attrs['min'] = today_str
            self.fields['habit'].help_text = (
                "Selecting a habit fills its default target and unit, which you can adjust."
            )

        elif self.instance.end_date and self.instance.end_date < today:
            # Ended goal - nothing can be changed
            for field in self.fields.values():
                field.disabled = True
            self.fields['habit'].help_text = (
                "This goal has ended and can no longer be edited."
            )

        elif self.instance.start_date <= today:
            # # Ongoing goal — only the end date can be changed
            immutable_fields = ('habit', 'target_value', 'unit', 'start_date')
            for field_name in immutable_fields:
                self.fields[field_name].disabled = True

            self.fields['habit'].help_text = (
                "This goal has already started. Only the end date can be changed."
            )

            self.fields['end_date'].widget.attrs['min'] = today_str
            self.fields['end_date'].help_text = (
                "You can extend or shorten the goal, but it cannot end before today."
            )

        else:
            # Future goal — dates can be changed, but not into the past
            self.fields['start_date'].widget.attrs['min'] = today_str
            self.fields['habit'].help_text = (
                "Changing the habit will update the target and unit to its defaults."
            )

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
        today = timezone.localdate()

        if start_date and start_date < today:
            if not self.instance.pk or start_date != self.instance.start_date:
                self.add_error(
                    'start_date',
                    'Start date cannot be before today.',
                )

        if start_date and end_date and end_date < start_date:
            self.add_error(
                'end_date',
                'End date cannot be before start date.',
            )

        if (
                self.instance.pk
                and self.instance.start_date <= today
                and end_date
                and end_date < today
        ):
            self.add_error(
                'end_date',
                'An active goal cannot end before today.',
            )

        return cleaned_data