from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, reverse, get_object_or_404

from apps.base.navigation import redirect_to_next, get_safe_next_url
from apps.base.views import delete_object_view
from apps.habits.forms import HabitForm, HabitPlanForm
from apps.habits.models import Habit


@login_required(login_url="accounts:login")
def home_view(request):
    return render(request, 'habits/pages/home.html')


def manage_habits_view(request):
    habits = Habit.objects.all_for_user(request.user)
    return render(
        request,
        template_name='habits/pages/manage_habits.html',
        context={
            "habits": habits,
        }
    )


def add_habit_view(request):

    if request.method == 'POST':

        form = HabitForm(request.POST, user=request.user)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()

            messages.success(request, f'Created a new habit, "{instance.name}"')
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
        }
    )


def edit_habit_view(request, habit_id):

    habit = get_object_or_404(Habit, pk=habit_id, user=request.user)

    if request.method == 'POST':
        form = HabitForm(request.POST, user=request.user, instance=habit)

        if form.is_valid():
            form.save()

            messages.success(request, f'Updated habit, "{habit.name}"')
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
        }
    )


def delete_habit_view(request, habit_id):
    return delete_object_view(
        request=request,
        model=Habit,
        obj_id=habit_id,
        final_redirect_fallback="habits:home",
    )


def add_habit_plan_view(request):

    if request.method == 'POST':

        form = HabitPlanForm(request.POST, user=request.user)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()

            messages.success(request, f"""Let's start working on {instance.habit.name}""")
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