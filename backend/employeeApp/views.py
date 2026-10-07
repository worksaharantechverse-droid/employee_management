from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from notification.views import create_notification
from attendance.models import Attendance
from leave.models import LeaveRequest
from notification.models import Notification

from employeeApp.forms import employee_form
from employeeApp.models import department_model, employee_model, team_model


def _role(user):
    return getattr(user, 'role', '').upper()


def _employee_for_user(user):
    profile = employee_model.objects.filter(user=user).first()
    if profile:
        return profile

    # Compatibility for old employee rows created before the User relation.
    profile = employee_model.objects.filter(email__iexact=user.email).first()
    if profile:
        profile.user = user
        profile.role = user.role
        profile.name = user.name
        profile.save(update_fields=['user', 'role', 'name'])
    return profile


def _allowed_employee_queryset(user):
    role = _role(user)
    if role == 'HR':
        return employee_model.objects.all()
    if role == 'MANAGER':
        manager = _employee_for_user(user)
        if not manager:
            return employee_model.objects.none()
        return employee_model.objects.filter(teams__manager=manager).distinct()
    if role == 'EMPLOYEE':
        return employee_model.objects.filter(user=user)
    return employee_model.objects.none()


def _redirect_by_role(user):
    role = _role(user)
    if role == 'HR':
        return redirect('home')
    if role == 'MANAGER':
        return redirect('manager_dashboard')
    return redirect('employee_dashboard')


@login_required
def home_view(request):
    if _role(request.user) != 'HR':
        return _redirect_by_role(request.user)
    teams_count = team_model.objects.count()
    total_employees = employee_model.objects.count()
    active_employees = employee_model.objects.filter(status=True).count()
    inactive_employees = employee_model.objects.filter(status=False).count()

    return render(
        request,
        'employeeApp/home.html',
        {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'inactive_employees': inactive_employees,
            'attendance_today': Attendance.objects.filter(date=timezone.localdate()).select_related('employee')[:10],
            'leave_requests': LeaveRequest.objects.select_related('employee', 'manager')[:10],
            'notifications': Notification.objects.select_related('recipient')[:10],
            'pending_leaves': LeaveRequest.objects.filter(status='PENDING').count(),
            "teams_count": teams_count,
        },
    )


@login_required
def employee_list(request):
    employees = _allowed_employee_queryset(request.user).select_related(
        'department', 'manager'
    )

    search = request.GET.get('search', '').strip()
    if search:
        employees = employees.filter(
            Q(name__icontains=search)
            | Q(employee_id__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )

    department = request.GET.get('department', '')
    if department:
        employees = employees.filter(department_id=department)

    gender = request.GET.get('gender', '')
    if gender:
        employees = employees.filter(gender=gender)

    role_filter = request.GET.get('role', '')
    if role_filter:
        employees = employees.filter(role=role_filter)

    status = request.GET.get('status', '')
    if status == 'active':
        employees = employees.filter(status=True)
    elif status == 'inactive':
        employees = employees.filter(status=False)

    paginator = Paginator(employees.order_by('name'), 10)
    page_number = request.GET.get('page')
    employees_page = paginator.get_page(page_number)

    return render(
        request,
        'employeeApp/employee_list.html',
        {
            'employees': employees_page,
            'departments': department_model.objects.all(),
            'search': search,
            'selected_department': department,
            'selected_gender': gender,
            'selected_role': role_filter,
            'selected_status': status,
        },
    )


@login_required
def add_employee(request):
    if _role(request.user) != 'HR':
        messages.error(request, 'Only HR can add employees.')
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        form = employee_form(request.POST)
        if form.is_valid():
            employee = form.save()
            # If HR enters an email belonging to an existing login account,
            # link the employee profile to that account automatically.
            from account.models import User
            account = User.objects.filter(email__iexact=employee.email).first()
            if account and not employee.user_id:
                employee.user = account
                employee.save(update_fields=['user'])

                create_notification(
                recipient=employee,
                message='Your employee profile has been created.',
                notification_type='EMPLOYEE_CREATED')
                
            messages.success(request, 'Employee added successfully.')
            return redirect('employee_list')
    else:
        form = employee_form()

    return render(request, 'employeeApp/employee_form.html', {'form': form, 'title': 'Add New Employee'})


@login_required
def employee_edit(request, pk):
    if _role(request.user) != 'HR':
        messages.error(request, 'Only HR can edit employees.')
        return _redirect_by_role(request.user)

    employee = get_object_or_404(employee_model, pk=pk)
    if request.method == 'POST':
        form = employee_form(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            # Keep login account role/name/email in sync with the HR profile.
            if employee.user_id:
                employee.user.name = employee.name
                employee.user.email = employee.email
                employee.user.role = employee.role
                employee.user.save(update_fields=['name', 'email', 'role'])

                create_notification(
                    recipient=employee,
                    message='HR updated your profile.',
                    notification_type='PROFILE_UPDATED'
)
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_list')
    else:
        form = employee_form(instance=employee)

    return render(request, 'employeeApp/employee_form.html', {'form': form, 'title': 'Edit Employee'})


@login_required
def view_employee(request, pk):
    employee = get_object_or_404(employee_model, pk=pk)
    role = _role(request.user)

    if role == 'HR':
        pass
    elif role == 'EMPLOYEE':
        own_profile = _employee_for_user(request.user)
        if not own_profile or employee.pk != own_profile.pk:
            messages.error(request, 'You can only view your own profile.')
            return _redirect_by_role(request.user)
    elif role == 'MANAGER':
        manager = _employee_for_user(request.user)
        if not manager or (employee.pk != manager.pk and not employee.teams.filter(manager=manager).exists()):
            messages.error(request, 'You can only view your own profile or your team members.')
            return _redirect_by_role(request.user)
    else:
        return redirect('login')

    return render(request, 'employeeApp/employee_detail.html', {'employee': employee})


@login_required
def employee_delete(request, pk):
    if _role(request.user) != 'HR':
        messages.error(request, 'Only HR can delete employees.')
        return _redirect_by_role(request.user)

    employee = get_object_or_404(employee_model, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully.')
        return redirect('employee_list')

    return render(request, 'employeeApp/employee_confirm_delete.html', {'employee': employee})


@login_required
def hr_teams(request):
    if request.user.role != "HR":
        return redirect("home")

    teams = team_model.objects.select_related(
        "department",
        "manager"
    ).prefetch_related(
        "members"
    ).order_by("name")

    return render(
        request,
        "employeeApp/hr_teams.html",
        {
            "teams": teams
        }
    )
