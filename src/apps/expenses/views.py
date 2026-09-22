from django.contrib import messages
from django.shortcuts import render, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.cache import cache as django_cache
from django.utils.timezone import localdate

from . import forms, models, cache

from apps.base.utils import TimeFrame
from apps.base.views import delete_object_view
from apps.base.navigation import redirect_to_next


@login_required(login_url="accounts:login")
def home_view(request):

    cache_key = cache.home_key(user_id=request.user.id)
    expenses = django_cache.get_or_set(
        key=cache_key,
        default=lambda: list(
            models.Expense.objects
            .for_user(user=request.user)[:10]
        ),
    )

    return render(request, 'expenses/home.html', {"expenses": expenses})


@login_required(login_url='accounts:login')
def add_expense_view(request):

    if request.method == 'POST':

        form = forms.ExpenseForm(request.POST, user=request.user)

        if form.is_valid():
            new_expense = form.save(commit=False)
            new_expense.user = request.user
            new_expense.save()

            cache.invalidate_cache(request.user.id)

            messages.success(request, f'{new_expense} successfully added.')
            return redirect_to_next(request, reverse("expenses:home"))

    else:
        form = forms.ExpenseForm(user=request.user)

    return render(
        request,
        template_name="expenses/expense_form.html",
        context={
            "form": form,
            "form_id": 'add-expense-form',
            "item_name": 'Expense',
        },
    )


@login_required(login_url='accounts:login')
def edit_expense_view(request, exp_id):

    expense = get_object_or_404(
        models.Expense.objects.for_user(request.user),
        id=exp_id,
    )

    if request.method == 'POST':
        form = forms.ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()

            cache.invalidate_cache(request.user.id)

            messages.success(request, f'{expense} successfully updated.')
            return redirect_to_next(request, reverse("expenses:home"))

    else:
        form = forms.ExpenseForm(instance=expense, user=request.user)

    return render(
        request,
        template_name="expenses/expense_form.html",
        context={
            "form": form,
            "form_id": 'edit-expense-form',
            "item_name": 'Expense',
        }
    )


@login_required(login_url='accounts:login')
def delete_expense_view(request, exp_id):
    return delete_object_view(
        request=request,
        model=models.Expense,
        obj_id=exp_id,
        final_redirect_fallback="expenses:home",
        cache_delete_func=cache.invalidate_cache,
    )


@login_required(login_url='accounts:login')
def filtered_expense_view(request):

    form = forms.ExpenseFilterForm(
        request.GET or None,
        user=request.user
    )

    filters = dict(
        form.cleaned_data
        if form.is_valid()
        else form.initial
    )

    stats = models.Expense.objects.get_stats(request.user, filters)
    expenses = models.Expense.objects.filtered_for_user(request.user, filters)

    return render(request, 'expenses/history.html', {
        'form': form,
        'expenses': expenses,
        'stats': stats,
    })


@login_required(login_url='accounts:login')
def dashboard_view(request):

    preferences = getattr(request.user, 'preferences', {})

    data = request.GET.dict()
    if not data.get('timeFrame'):
        data['timeFrame'] = (
            preferences.get_expenses_preferences(
                'dashboard_last_timeframe',
                TimeFrame.SEVEN_DAYS,
            )
        )

    form = forms.DashboardForm(data)

    dashboard_data = None
    if form.is_valid():
        timeframe = form.cleaned_data['timeFrame']

        preferences.set_expenses_preferences(
            dashboard_last_timeframe=timeframe,
        )

        cache_key = cache.summary_key(
            user_id=request.user.id,
            date=localdate(),
            timeframe=timeframe,
        )
        dashboard_data = django_cache.get_or_set(
            key=cache_key,
            default=lambda: dict(
                models.Expense.objects
                .get_dashboard_data(
                    user=request.user,
                    timeframe=timeframe,
                )
            )
        )

    return render(
        request,
        template_name='expenses/dashboard.html',
        context={
            'form': form,
            'data': dashboard_data,
        }
    )