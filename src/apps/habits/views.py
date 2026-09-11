from logging import exception

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache as django_cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render, reverse, get_object_or_404
from django.utils import timezone

from apps.base.navigation import redirect_to_next
from apps.base.views import delete_object_view
from apps.base.utils import TimeFrame

from .forms import HabitForm, HabitPlanForm, DailyProgressForm
from .models import Habit, HabitPlan, DailyProgress
from .utils import HabitPlanStatus
from . import cache


@login_required(login_url="accounts:login")
def home_view(request):

    today = timezone.localdate()

    created = HabitPlan.objects.for_user(
        request.user
    ).ensure_progress_until(today)
    if len(created) > 0:
        cache.invalidate_cache(request.user.id, DailyProgress)

    p_key = cache.home_progresses_key(
        request.user.id,
        today
    )
    progresses = django_cache.get_or_set(
        key=p_key,
        default= lambda: list(
            DailyProgress.objects
            .for_user(request.user)
            .filter(date=today)
            .with_habit()
        )
    )

    t_key = cache.home_trend_key(
        request.user.id,
        today
    )
    start_date = TimeFrame.get_start_date(today, TimeFrame.SEVEN_DAYS)
    data = django_cache.get_or_set(
        key=t_key,
        default=lambda: dict(
            DailyProgress.objects
            .for_user(request.user)
            .with_habit()
            .get_trend_data(start_date, today)
        )
    )

    return render(
        request,
        template_name='habits/pages/home.html',
        context={
            "progresses": progresses,
            **data,
        }
    )


@login_required(login_url="accounts:login")
def manage_view(request):

    h_key = cache.manage_habits_key(request.user.id)
    habits = django_cache.get_or_set(
        key=h_key,
        default=lambda: list(
            Habit.objects
            .for_user(request.user)
        )
    )

    g_key = cache.manage_goals_key(request.user.id)
    goals = django_cache.get_or_set(
        key=g_key,
        default=lambda: list(
            HabitPlan.objects
            .for_user(request.user)
            .by_status(
                HabitPlanStatus.UPCOMING,
                HabitPlanStatus.ACTIVE
            )
            .with_habit()
        )
    )

    return render(
        request,
        template_name='habits/pages/manage_habits.html',
        context={
            "habits": habits,
            "goals": goals,
        }
    )


@login_required(login_url="accounts:login")
def history_view(request):

    his_key = cache.history_key(request.user.id)
    goals = django_cache.get_or_set(
        key=his_key,
        default = lambda : list(
            HabitPlan.objects
            .for_user(request.user)
            .by_status(
                HabitPlanStatus.ACTIVE,
                HabitPlanStatus.ENDED
            )
            .with_habit()
        )
    )

    return render(
        request,
        template_name="habits/pages/history.html",
        context={
            'goals': goals,
        }
    )


@login_required(login_url="accounts:login")
def add_habit_view(request):

    if request.method == 'POST':

        form = HabitForm(request.POST, user=request.user)

        if form.is_valid():
            instance = form.save()
            cache.invalidate_cache(request.user.id, instance)
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
            cache.invalidate_cache(request.user.id, habit)
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
def archive_habit_view(request, habit_id):
    habit = get_object_or_404(
        Habit.objects.for_user(request.user).active(),
        pk=habit_id,
    )

    if request.method == "POST":
        try:
            with transaction.atomic():
                habit.is_active = False
                habit.save()
            cache.invalidate_cache(request.user.id, habit)
            messages.success(request, f'You will no longer see "{habit}" while creating goals.')
        except exception:
            messages.error(request, "Something went wrong. Please try again later.")

    return redirect_to_next(
        request,
        reverse("habits:home"),
    )


@login_required(login_url="accounts:login")
def unarchive_habit_view(request, habit_id):
    habit = get_object_or_404(
        Habit.objects.for_user(request.user).filter(is_active=False),
        pk=habit_id,
    )

    if request.method == "POST":
        try:
            with transaction.atomic():
                habit.is_active = True
                habit.save()
            cache.invalidate_cache(request.user.id, habit)
            messages.success(request, f'You can now create new goals using "{habit}"')
        except exception:
            messages.error(request, "Something went wrong. Please try again later.")

    return redirect_to_next(
        request,
        reverse("habits:home"),
    )


@login_required(login_url="accounts:login")
def add_habit_plan_view(request):

    if request.method == 'POST':

        form = HabitPlanForm(request.POST, user=request.user)

        if form.is_valid():
            instance = form.save()
            cache.invalidate_cache(request.user.id, instance)
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
    if goal.is_ended:
        messages.error(request, 'An ended goal can not be modified')
        raise PermissionDenied

    if request.method == 'POST':
        form = HabitPlanForm(
            request.POST,
            user=request.user,
            instance=goal,
            extra_habit=goal.habit,
        )

        if form.is_valid():
            with transaction.atomic():
                instance = form.save()
                if not instance.habit.is_active:
                    instance.habit.is_active = True
                    instance.habit.save()
            cache.invalidate_cache(request.user.id, instance)
            messages.success(request,f'Updated goal, "{goal}"')
            return redirect_to_next(request, reverse('habits:home'))

    else:
        form = HabitPlanForm(
            user=request.user,
            instance=goal,
            extra_habit=goal.habit,
        )

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

    plan = get_object_or_404(
        HabitPlan.objects.for_user(request.user),
        pk=plan_id,
    )
    if not plan.is_upcoming:
        messages.error(request, 'Only upcoming plans can be deleted.')
        raise PermissionDenied

    return delete_object_view(
        request=request,
        model=HabitPlan,
        obj_id=plan_id,
        final_redirect_fallback="habits:home",
        cache_delete_func=cache.invalidate_cache,
    )


@login_required(login_url="accounts:login")
def end_habit_plan_view(request, plan_id):

    goal = get_object_or_404(
        HabitPlan.objects.for_user(request.user),
        pk=plan_id,
    )
    if not goal.is_active:
        messages.error(request, 'Only active goals can be ended.')
        raise PermissionDenied

    if request.method == 'POST':

        try:
            with transaction.atomic():
                goal.end_date = timezone.localdate()
                goal.save()
            cache.invalidate_cache(request.user.id, goal)
            messages.success(request,f'Ended "{goal}"')
        except exception:
            messages.error(request, 'Failed to end goal. Please try again later.')

    return redirect_to_next(request, reverse('habits:home'))


@login_required(login_url="accounts:login")
def detail_habit_plan_view(request, plan_id):

    plan = get_object_or_404(
        HabitPlan.objects.for_user(request.user).with_habit(),
        pk=plan_id,
    )

    d_key = cache.details_key(request.user.id, plan_id)
    progresses = django_cache.get_or_set(
        key=d_key,
        default= lambda : list(
            plan.daily_progress.all()
        )
    )

    chart_data = [
        {
            'date': p.date.strftime('%b %d'),
            'value': p.value,
        }
        for p in reversed(progresses)
    ]

    return render(
        request,
        template_name="habits/pages/plan_details.html",
        context={
            "progresses": progresses,
            "plan": plan,
            "chart_data": chart_data,
        }
    )


@login_required(login_url="accounts:login")
def restart_habit_plan_view(request, plan_id):

    plan = get_object_or_404(
        HabitPlan.objects.for_user(request.user),
        pk=plan_id,
    )
    if not plan.is_ended:
        messages.error(request, 'Only ended goals can be started again.')
        raise PermissionDenied

    form = HabitPlanForm(
        request.POST or None,
        user=request.user,
        extra_habit=plan.habit,
        initial={
            "habit": plan.habit_id,
            "target_value": plan.target_value,
            "unit": plan.unit,
            "start_date": timezone.localdate(),
        },
    )

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            instance = form.save()
            if not instance.habit.is_active:
                instance.habit.is_active = True
                instance.habit.save(update_fields=["is_active"])
        cache.invalidate_cache(request.user.id, instance)
        messages.success(
            request,
            f"{instance} is all set. Time to get started!",
        )

        return redirect_to_next(
            request,
            reverse("habits:home"),
        )

    return render(
        request,
        template_name="habits/pages/habit_plan_form.html",
        context={
            "form": form,
            "form_id": "restart-habit-plan-form",
            "item_name": "Goal",
        },
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
            cache.invalidate_cache(request.user.id, prog)
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


@login_required(login_url="accounts:login")
def mark_completed_daily_progress_view(request, prog_id):

    if request.method == 'POST':
        progress = get_object_or_404(
            DailyProgress.objects.for_user(request.user),
            pk=prog_id,
        )

        try:
            with transaction.atomic():
                progress.value = progress.plan.target_value
                progress.save()
            cache.invalidate_cache(request.user.id, progress)
            messages.success(request, f"{progress} successfully marked as completed!")
        except exception:
            messages.error(request, "Something went wrong. Please try again later.")

    return redirect_to_next(request, reverse('habits:home'))