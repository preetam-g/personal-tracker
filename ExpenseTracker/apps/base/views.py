from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from apps.expenses import (
    models as expense_models,
    forms as expense_forms
)
from apps.ledger import (
    models as ledger_models,
    forms as ledger_forms
)
from apps.forex import (
    forms as forex_forms
)


def delete_object_view(request, model, obj_id, final_redirect: str , name: str, cache_delete_func = None):
    """
    Base template view for deleting an object.
    Use cache_delete_func if you want to call a function to invalidate cache keys, the object that is being deleted is passed as a parameter.
    """
    obj = get_object_or_404(model, id=obj_id, user=request.user)
    if not name: name = getattr(obj, 'name', str(obj))

    if request.method == 'POST':
        cnt, _ = obj.delete()

        if cnt:
            if cache_delete_func:
                cache_delete_func(obj)
            messages.success(request, f'{name} successfully deleted.')
        else:
            messages.error(request, 'Failed to delete. Try again later.')

    return redirect(final_redirect)


@login_required(login_url='accounts:login')
def preferences_view(request):

    curr_user = request.user
    categories = expense_models.ExpenseCategory.objects.user_items(
        user=curr_user,
        include_global=False,
    )
    types = expense_models.ExpenseType.objects.user_items(
        user=curr_user,
        include_global=False,
    )

    contacts = ledger_models.Contact.objects.base_for_user(user=request.user)

    preferences = curr_user.preferences
    expenses_filter_form = expense_forms.ExpenseFilterDefaultsForm(
        initial=preferences.get_expenses_preferences(
            key='expenses_filter_defaults',
            default={}
        ),
        user=curr_user,
    )

    ledger_summary_form = ledger_forms.LedgerSummaryDefaultsForm(
        initial=preferences.get_ledger_preferences(
            key='ledger_summary_defaults',
            default={}
        ),
        user=curr_user,
    )

    forex_features_preferences_form = forex_forms.ForexFeaturesForm(
        instance=preferences,
        user=curr_user,
    )

    return render(
        request,
        "base/user_preferences/preferences.html",
        {
            "categories": categories,
            "types": types,
            "contacts": contacts,
            "expenses_filter_form": expenses_filter_form,
            "ledger_summary_form": ledger_summary_form,
            "forex_features_preferences_form": forex_features_preferences_form,
        }
    )


@login_required(login_url='accounts:login')
def add_category_view(request):

    if request.method == 'POST':
        form = expense_forms.ExpenseCategoryForm(request.POST, user=request.user)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()

            messages.success(request, f'"{instance.name}" successfully added.')
            return redirect("base:preferences")

    else:
        form = expense_forms.ExpenseCategoryForm()

    return render(
        request=request,
        template_name="base/user_preferences/common_base_form.html",
        context={
            "form": form,
            "title": "Category",
            "form_id": "expense-category-form",
            "cancel_url_name": "base:preferences",
        },
    )


@login_required(login_url='accounts:login')
def edit_category_view(request, cat_id):

    cat = get_object_or_404(expense_models.ExpenseCategory, id=cat_id, user=request.user)
    old_name = cat.name
    if request.method == 'POST':
        form = expense_forms.ExpenseCategoryForm(request.POST, instance=cat, user=request.user)

        if form.is_valid():
            new_cat = form.save()
            messages.success(request, f'"{old_name}" successfully updated as "{new_cat.name}".')
            return redirect("base:preferences") # must change to preferences page
    else:
        form = expense_forms.ExpenseCategoryForm(instance=cat, user=request.user)

    return render(
        request=request,
        template_name="base/user_preferences/common_base_form.html",
        context={
            "form": form,
            "title": "Category",
            "form_id": "expense-category-form",
            "cancel_url_name": "base:preferences",
        },
    )


@login_required(login_url='accounts:login')
def delete_category_view(request, cat_id):
    return delete_object_view(
        request,
        model=expense_models.ExpenseCategory,
        obj_id=cat_id,
        final_redirect="base:preferences", # preferences
    )


@login_required(login_url='accounts:login')
def add_type_view(request):

    if request.method == 'POST':
        form = expense_forms.ExpenseTypeForm(request.POST, user=request.user)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()

            messages.success(request, f'"{instance.name}" successfully added.')
            return redirect("base:preferences") # must change to preferences page

    else:
        form = expense_forms.ExpenseTypeForm()

    return render(
        request=request,
        template_name="base/user_preferences/common_base_form.html",
        context={
            "form": form,
            "title": "Type",
            "form_id": "expense-type-form",
            "cancel_url_name": "base:preferences",
        },
    )


@login_required(login_url='accounts:login')
def edit_type_view(request, type_id):

    type = get_object_or_404(expense_models.ExpenseType, id=type_id, user=request.user)
    old_name = type.name
    if request.method == 'POST':
        form = expense_forms.ExpenseTypeForm(request.POST, instance=type, user=request.user)

        if form.is_valid():
            new_cat = form.save()
            messages.success(request, f'"{old_name}" successfully updated as "{new_cat.name}".')
            return redirect("base:preferences") # must change to preferences page
    else:
        form = expense_forms.ExpenseTypeForm(instance=type, user=request.user)

    return render(
        request=request,
        template_name="base/user_preferences/common_base_form.html",
        context={
            "form": form,
            "title": "Type",
            "form_id": "expense-type-form",
            "cancel_url_name": "base:preferences",
        },
    )


@login_required(login_url='accounts:login')
def delete_type_view(request, type_id):
    return delete_object_view(
        request=request,
        model=expense_models.ExpenseType,
        obj_id=type_id,
        final_redirect="base:preferences", # preferences
    )


@login_required(login_url='accounts:login')
def add_contact_view(request):

    if request.method == 'POST':
        form = ledger_forms.ContactForm(request.POST, user=request.user)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()

            messages.success(request, f'"{instance.name}" successfully added.')
            return redirect("base:preferences")
    else:
        form = ledger_forms.ContactForm(user=request.user)

    return render(
        request=request,
        template_name="base/user_preferences/common_base_form.html",
        context={
            "form": form,
            "title": "Contact",
            "form_id": "ledger-contact-form",
            "cancel_url_name": "base:preferences",
        },
    )


@login_required(login_url='accounts:login')
def edit_contact_view(request, cont_id):

    contact = get_object_or_404(ledger_models.Contact, id=cont_id, user=request.user)
    old = contact.name
    if request.method == 'POST':
        form = ledger_forms.ContactForm(request.POST, instance=contact, user=request.user)

        if form.is_valid():
            new_item = form.save()
            messages.success(request, f'"{old}" successfully updated as "{new_item.name}".')
            return redirect("base:preferences")
    else:
        form = ledger_forms.ContactForm(instance=contact, user=request.user)

    return render(
        request=request,
        template_name="base/user_preferences/common_base_form.html",
        context={
            "form": form,
            "title": "Contact",
            "form_id": "expense-contact-form",
            "cancel_url_name": "base:preferences",
        },
    )


@login_required(login_url='accounts:login')
def delete_contact_view(request, cont_id):
    return delete_object_view(
        request=request,
        model=ledger_models.Contact,
        obj_id=cont_id,
        final_redirect="base:preferences",
    )