from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from employeeApp.models import employee_model
from notification.models import Notification


@login_required
def employee_dashboard(request):
    if getattr(request.user, 'role', '').upper() != 'EMPLOYEE':
        if getattr(request.user, 'role', '').upper() == 'HR':
            return redirect('home')
        if getattr(request.user, 'role', '').upper() == 'MANAGER':
            return redirect('manager_dashboard')
        return redirect('login')

    employee = employee_model.objects.filter(user=request.user).first()
    if not employee:
        employee = employee_model.objects.filter(email__iexact=request.user.email).first()
        if employee:
            employee.user = request.user
            employee.save(update_fields=['user'])

    teams = employee.teams.select_related('department', 'manager').all() if employee else []
    notifications = Notification.objects.filter(
    recipient=employee
    )[:5]

    return render(
        request,
        'employee/employee_dashboard.html',
        {'employee': employee, 'teams': teams, 'notifications': notifications,},
    )
