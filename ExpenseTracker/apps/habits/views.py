from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, reverse, get_object_or_404

from apps.base.navigation import redirect_to_next, get_safe_next_url
from apps.base.views import delete_object_view
from apps.habits.forms import HabitForm, HabitPlanForm
from apps.habits.models import Habit, HabitPlan


@login_required(login_url="accounts:login")
def home_view(request):
    return render(request, 'habits/pages/home.html')


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
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()

            messages.success(request, f'Created a new habit, "{instance}"')
        else:
            messages.error(request, 'Failed to add. Please try again later.')

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
        else:
            messages.error(request, 'Failed to update. Please try again later.')

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
            messages.success(request, f"""{instance} is all set. Time to get started!""")
        else:
            messages.error(request, 'Failed to create. Please try again later.')

        return redirect_to_next(request, reverse('habits:home'))

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
            messages.success(request, f'Updated goal, "{goal}"')
        else:
            messages.error(request, 'Failed to update. Please try again later.')

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