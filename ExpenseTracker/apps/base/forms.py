from django import forms
from django.db.models import Q


class CategoryTypeValidationForm(forms.ModelForm):
    """
    Reusable form to enforce uniqueness per user (+ optional global)
    This is used for Expense Category and Expense Type Models.
    """
    unique_fields = ['name']  # override in child if needed
    include_global = True     # check global (user=None)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if not self.user:
            raise Exception("User not specified")

        filters = Q()
        # build dynamic filters for multiple fields
        for field in self.unique_fields:
            value = cleaned_data.get(field)
            if value:
                filters &= Q(**{f"{field}__iexact": value})

        if not filters:
            return cleaned_data

        qs = self._meta.model.objects.filter(filters)

        # user scope
        if self.include_global:
            qs = qs.filter(Q(user=self.user) | Q(user__isnull=True))
        else:
            qs = qs.filter(user=self.user)

        # exclude self (edit case)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            for field in self.unique_fields:
                name = self.cleaned_data.get(field)
                self.add_error(field, f'"{name}" already exists!')

        return cleaned_data