from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from . import forms, models

from apps.base.utils import get_start_date, TimeFrame
from apps.base.views import delete_object_view


@login_required(login_url="accounts:login")
def home_view(request):
    qs = models.Expense.objects.all_for_user(request.user)[:10]
    return render(request, 'expenses/home.html', {"expenses": qs})


@login_required(login_url='accounts:login')
def add_expense_view(request):

    if request.method == 'POST':

        form = forms.ExpenseForm(request.POST, user=request.user)

        if form.is_valid():

            new_expense = form.save(commit=False)
            new_expense.user = request.user
            new_expense.save()

            messages.success(request, 'Expense successfully added.')
            return redirect("expenses:home")

    else:
        form = forms.ExpenseForm(user=request.user)

    return render(request, "expenses/expense_form.html", {"form": form})


@login_required(login_url='accounts:login')
def edit_expense_view(request, exp_id):

    expense = get_object_or_404(models.Expense, id=exp_id, user=request.user)

    if request.method == 'POST':
        form = forms.ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense successfully updated.')
        else:
            messages.error(request, 'Failed to update. Please try again later.')

        return redirect("expenses:home")
    else:
        form = forms.ExpenseForm(instance=expense, user=request.user)

    return render(request, "expenses/expense_form.html", {"form": form})


@login_required(login_url='accounts:login')
def delete_expense_view(request, exp_id):
    return delete_object_view(
        request=request,
        model=models.Expense,
        name="Expense",
        obj_id=exp_id,
        final_redirect="expenses:home"
    )


@login_required(login_url='accounts:login')
def filtered_expense_view(request):

    fallback_data = {
        'start_date': get_start_date(timezone.localdate(), TimeFrame.SEVEN_DAYS),
        'end_date': timezone.localdate(),
    }

    data = request.GET.copy()
    if not data:
        data = fallback_data

    form = forms.ExpenseFilterForm(data, user=request.user)

    if form.is_valid():
        stats = models.Expense.objects.get_stats(request.user, form.cleaned_data)
        expenses = models.Expense.objects.filtered_for_user(request.user, form.cleaned_data)
    else:
        form = forms.ExpenseFilterForm(fallback_data, user=request.user)
        form.is_valid()

        stats = models.Expense.objects.get_stats(request.user, form.cleaned_data)
        expenses = models.Expense.objects.filtered_for_user(request.user, form.cleaned_data)

    return render(request, 'expenses/history.html', {
        'form': form,
        'expenses': expenses,
        'stats': stats,
    })


@login_required(login_url='accounts:login')
def dashboard_view(request):

    data = request.GET.dict()
    if not data.get('timeFrame'):
        data['timeFrame'] = TimeFrame.SEVEN_DAYS

    form = forms.DashboardForm(data)

    dashboard_data = None
    if form.is_valid():
        dashboard_data = models.Expense.objects.get_dashboard_data(
            user=request.user,
            timeFrame=form.cleaned_data['timeFrame'],
        )

    return render(request, 'expenses/dashboard.html', {
        'form': form,
        'data': dashboard_data,
    })