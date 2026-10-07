from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from notification.models import Notification
from notification.views import create_notification
from employeeApp.models import department_model, employee_model, team_model
from notification.views import create_notification

def _is_manager(user):
    return getattr(user, 'role', '').upper() == 'MANAGER'


def _manager_profile(user):
    profile = employee_model.objects.filter(user=user).first()
    if profile:
        return profile
    return employee_model.objects.filter(email__iexact=user.email).first()


@login_required
def manager_dashboard(request):
    if not _is_manager(request.user):
        return redirect('home' if getattr(request.user, 'role', '') == 'HR' else 'employee_dashboard')

    manager = _manager_profile(request.user)
    teams = team_model.objects.filter(manager=manager).prefetch_related('members') if manager else team_model.objects.none()
    team_members = employee_model.objects.filter(teams__manager=manager).distinct() if manager else employee_model.objects.none()
    notifications = Notification.objects.filter(
    recipient=manager
    )[:5]

    return render(
        request,
        'manager/manager_dashboard.html',
        {
            'manager': manager,
            'teams': teams,
            'team_members_count': team_members.count(),
            'notifications': notifications,
        },
    )


@login_required
def manager_team(request):
    if not _is_manager(request.user):
        return redirect('home')

    manager = _manager_profile(request.user)
    if not manager:
        messages.error(request, 'Manager profile not found.')
        return redirect('manager_dashboard')

    teams = team_model.objects.filter(manager=manager).select_related('department').prefetch_related('members')
    return render(request, 'manager/team.html', {'teams': teams, 'manager': manager})



@login_required
def create_team(request):
    if not _is_manager(request.user):
        return redirect('home')

    manager = _manager_profile(request.user)

    if not manager:
        messages.error(request, 'Manager profile not found.')
        return redirect('manager_dashboard')

    departments = department_model.objects.all()

    # Fetch all employees except the current manager
    employees = employee_model.objects.exclude(
        pk=manager.pk
    ).order_by('name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        department_id = request.POST.get('department')
        description = request.POST.get('description', '').strip()

        department = get_object_or_404(
            department_model,
            id=department_id
        )

        if not name:
            messages.error(request, 'Team name is required.')

        else:
            # Create team
            team = team_model.objects.create(
                name=name,
                department=department,
                manager=manager,
                description=description,
            )

            # Get selected employees
            member_ids = request.POST.getlist('members')

            selected_employees = employee_model.objects.filter(
                id__in=member_ids
            ).exclude(pk=manager.pk)

            # Add members to team
            team.members.set(selected_employees)

            # Set manager for selected employees
            for employee in selected_employees:
                employee.manager = manager
                employee.save(update_fields=['manager'])

            messages.success(
                request,
                'Team created successfully.'
            )

            return redirect('manager_team')

    return render(
        request,
        'manager/create_team.html',
        {
            'departments': departments,
            'employees': employees,
        }
    )


@login_required
def add_team_member(request, team_id):
    if not _is_manager(request.user):
        return redirect('home')

    manager = _manager_profile(request.user)
    team = get_object_or_404(team_model, id=team_id, manager=manager)

    if request.method == 'POST':
        employee = get_object_or_404(employee_model, id=request.POST.get('employee_id'))
        team.members.add(employee)
        # Keep the legacy manager field useful as well.
        if employee.pk != manager.pk:
            employee.manager = manager
            employee.save(update_fields=['manager'])
            create_notification(
                recipient=employee,
                message=f"Your manager added you to the {team.name} team.",
                notification_type="TEAM_ADDED"
            )
        messages.success(request, f'{employee.name} added to {team.name}.')
        return redirect('manager_team')

    employees = employee_model.objects.exclude(teams=team).exclude(pk=manager.pk).order_by('name')
    return render(request, 'manager/add_team_member.html', {'team': team, 'employees': employees})


@login_required
def remove_team_member(request, team_id, employee_id):
    if not _is_manager(request.user):
        return redirect('home')

    manager = _manager_profile(request.user)
    team = get_object_or_404(team_model, id=team_id, manager=manager)
    employee = get_object_or_404(team.members, id=employee_id)

    if request.method == 'POST':
        team.members.remove(employee)
        if employee.manager_id == manager.id and not employee.teams.filter(manager=manager).exists():
            employee.manager = None
            employee.save(update_fields=['manager'])
            create_notification(
                recipient=employee,
                message=f"You have been removed from the {team.name} team.",
                notification_type="TEAM_REMOVED"
        )
        messages.success(request, f'{employee.name} removed from {team.name}.')

    return redirect('manager_team')
