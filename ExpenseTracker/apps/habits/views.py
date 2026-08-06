from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, reverse, get_object_or_404
from django.utils import timezone

from apps.base.navigation import redirect_to_next
from apps.base.views import delete_object_view
from apps.base.utils import TimeFrame
from apps.habits.forms import HabitForm, HabitPlanForm, DailyProgressForm, ProgressTrendForm
from apps.habits.models import Habit, HabitPlan, DailyProgress


@login_required(login_url="accounts:login")
def home_view(request):

    today = timezone.localdate()

    HabitPlan.objects.for_user(
        request.user
    ).ensure_progress_until(today)

    progresses = (
        DailyProgress.objects
        .for_user(request.user)
        .filter(date=today)
        .with_habit()
    )

    form = ProgressTrendForm(request.GET)
    selected_timeframe = TimeFrame.SEVEN_DAYS
    if form.is_valid():
        selected_timeframe = form.cleaned_data.get('timeFrame') or TimeFrame.SEVEN_DAYS

    data = (
        DailyProgress.objects
        .for_user(request.user)
        .with_habit()
        .get_trend_data(selected_timeframe)
    )

    return render(
        request,
        template_name='habits/pages/home.html',
        context={
            "progresses": progresses,
            'form': form,
            **data,
        }
    )


@login_required(login_url="accounts:login")
def manage_habits_view(request):
    habits = Habit.objects.for_user(request.user)
    goals = HabitPlan.objects.for_user(request.user).with_habit()
    return render(
        request,
        template_name='habits/pages/manage_habits.html',
        context={
            "habits": habits,
            "goals": goals,
        }
    )


@login_required(login_url="accounts:login")
def add_habit_view(request):

    if request.method == 'POST':

        form = HabitForm(request.POST, user=request.user)

        if form.is_valid():
            instance = form.save()
            messages.success(request, f'Created a new habit - "{instance}"')
            return redirect_to_next(request, reverse('habits:home'))

    else:
        form = HabitForm(user=request.user)

    return render(
        request,
        template_name="generic_form.html",
        context={
            'form': form,
            'form_id': 'add-habit-form',
            'item_name': 'Habit',
            'sub_title': 'Target Value and Unit will be used as defaults values for future goals.',
        }
    )


@login_required(login_url="accounts:login")
def edit_habit_view(request, habit_id):

    habit = get_object_or_404(
        Habit.objects.for_user(request.user),
        pk=habit_id
    )

    if request.method == 'POST':
        form = HabitForm(request.POST, user=request.user, instance=habit)

        if form.is_valid():
            form.save()
            messages.success(request, f'Updated "{habit}"')
            return redirect_to_next(request, reverse('habits:home'))

    else:
        form = HabitForm(user=request.user, instance=habit)

    return render(
        request,
        template_name="generic_form.html",
        context={
            'form': form,
            'form_id': 'edit-habit-form',
            'item_name': 'Habit',
            'sub_title': 'Target Value and Unit will be used as defaults values for future goals.',
        }
    )


@login_required(login_url="accounts:login")
def delete_habit_view(request, habit_id):
    return delete_object_view(
        request=request,
        model=Habit,
        obj_id=habit_id,
        final_redirect_fallback="habits:home",
    )


@login_required(login_url="accounts:login")
def add_habit_plan_view(request):

    if request.method == 'POST':

        form = HabitPlanForm(request.POST, user=request.user)

        if form.is_valid():
            instance = form.save()
            messages.success(
                request,
                f"{instance} is all set. Time to get started!"
            )
            return redirect_to_next(
                request,
                reverse("habits:home"),
            )

    else:
        form = HabitPlanForm(user=request.user)

    return render(
        request,
        template_name="habits/pages/habit_plan_form.html",
        context={
            'form': form,
            'form_id': 'add-habit-plan-form',
            'item_name': 'Goal',
        }
    )


@login_required(login_url="accounts:login")
def edit_habit_plan_view(request, plan_id):

    goal = get_object_or_404(
        HabitPlan.objects.for_user(request.user),
        pk=plan_id
    )

    if request.method == 'POST':
        form = HabitPlanForm(request.POST, user=request.user, instance=goal)

        if form.is_valid():
            form.save()
            messages.success(request,f'Updated goal, "{goal}"')
        return redirect_to_next(request, reverse('habits:home'))

    else:
        form = HabitPlanForm(user=request.user, instance=goal)

    return render(
        request,
        template_name="habits/pages/habit_plan_form.html",
        context={
            'form': form,
            'form_id': 'edit-habit-plan-form',
            'item_name': 'Goal',
        }
    )


@login_required(login_url="accounts:login")
def delete_habit_plan_view(request, plan_id):
    return delete_object_view(
        request=request,
        model=HabitPlan,
        obj_id=plan_id,
        final_redirect_fallback="habits:home",
    )


@login_required(login_url="accounts:login")
def edit_daily_progress_view(request, prog_id):

    prog = get_object_or_404(
        DailyProgress.objects.for_user(request.user).with_habit(),
        pk=prog_id,
    )

    if request.method == 'POST':

        form = DailyProgressForm(request.POST, instance=prog)

        if form.is_valid():
            form.save()
            messages.success(request,f'Updated "{prog}"')
            return redirect_to_next(
                request,
                reverse("habits:home"),
            )

    else:
        form = DailyProgressForm(instance=prog)

    return render(
        request,
        template_name="habits/pages/daily_progress_form.html",
        context={
            'form': form,
            'form_id': 'edit-daily-progress-form',
            'item_name': 'Daily Progress',
        }
    )