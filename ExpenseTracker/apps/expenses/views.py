from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from . import forms, models

@login_required(login_url="accounts:login")
def home_view(request):
    qs = models.Expense.browser.all_for_user(request.user)[:10]
    return render(request, 'expenses/home.html', {"expenses": qs})


@login_required(login_url='accounts:login')
def add_expense_view(request):

    if request.method == 'POST':

        form = forms.ExpenseForm(request.POST)

        if form.is_valid():

            new_expense = form.save(commit=False)
            new_expense.user = request.user
            new_expense.save()

            messages.success(request, 'Expense successfully added.')
            return redirect("expenses:home")

    else:
        form = forms.ExpenseForm()

    return render(request, "expenses/expense_form.html", {"form": form})


@login_required(login_url='accounts:login')
def edit_expense_view(request, exp_id):

    expense = get_object_or_404(models.Expense, id=exp_id, user=request.user)

    if request.method == 'POST':
        form = forms.ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense successfully updated.')
        else:
            messages.error(request, 'Failed to update. Please try again later.')

        return redirect("expenses:home")
    else:
        form = forms.ExpenseForm(instance=expense)

    return render(request, "expenses/expense_form.html", {"form": form})


@login_required(login_url='accounts:login')
def delete_expense_view(request, exp_id):

    expense = get_object_or_404(models.Expense, id=exp_id, user=request.user)

    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense successfully deleted.')
    else:
        messages.error(request, 'Failed to delete. Please try again later.')

    return redirect("expenses:home")


@login_required(login_url='accounts:login')
def filtered_expense_view(request):

    expenses = models.Expense.browser.all_for_user(request.user)
    form = forms.ExpenseFilterForm(request.GET)

    stats = None
    if form.is_valid():
        stats = models.Expense.browser.get_stats(request.user, form.cleaned_data)
        expenses = models.Expense.browser.filtered_for_user(request.user, form.cleaned_data)

    return render(request, 'expenses/history.html', {
        'form': form,
        'expenses': expenses,
        'stats': stats,
    })


@login_required(login_url='accounts:login')
def dashboard_view(request):

    form = forms.DashboardForm(request.GET)

    data = None
    if form.is_valid():
        data = models.Expense.browser.get_dashboard_data(
            user=request.user,
            timeFrame=form.cleaned_data['timeFrame'],
        )

    return render(request, 'expenses/dashboard.html', {
        'form': form,
        'data': data,
    })