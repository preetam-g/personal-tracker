from django import forms
from django.db.models import Q


class CategoryTypeValidationForm(forms.ModelForm):
    """
    Reusable form to enforce uniqueness per user (+ optional global)
    This is used for Expense Category and Expense Type Models.
    Make sure to call super().save() and super().commit() when overriding these methods.
    """
    unique_fields = ['name']  # override in child if needed
    include_global = True     # check global (user=None)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self._restore_instance = None

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

        model = self._meta.model
        base_qs = model.objects.filter(filters)

        if self.include_global:
            base_qs = base_qs.filter(Q(user=self.user) | Q(user__isnull=True))
        else:
            base_qs = base_qs.filter(user=self.user)

        # exclude self (edit case)
        if self.instance.pk:
            base_qs = base_qs.exclude(pk=self.instance.pk)

        if base_qs.exists():
            for field in self.unique_fields:
                name = self.cleaned_data.get(field)
                self.add_error(field, f'"{name}" already exists!')
                return cleaned_data

        return cleaned_data

    def save(self, commit=True):
        """
        If a deleted instance exists → restore it instead of creating new
        """
        if self._restore_instance:
            obj = self._restore_instance
            obj.is_deleted = False
            obj.deleted_at = None

            for field in self.unique_fields:
                setattr(obj, field, self.cleaned_data.get(field))

            if commit:
                obj.save()

            return obj

        obj = super().save(commit=False)
        if not obj.pk:
            obj.user = self.user
        if commit:
            obj.save()

        return obj