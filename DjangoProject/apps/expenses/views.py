from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from . import forms, models


def home_view(request):
    qs = models.Expense.objects.all().filter(user=request.user)
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
            return redirect("expenses:home")
        else:
            messages.error(request, 'Failed to update. Please try again later.')

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