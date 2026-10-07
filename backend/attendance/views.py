from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

from employeeApp.models import employee_model
from notification.views import create_notification
from .forms import AttendanceForm
from .models import Attendance


def _notify_manager(employee, message, notification_type):
    """
    Notify the employee's manager.
    """

    manager = employee.manager

    if manager:
        create_notification(
            recipient=manager,
            message=message,
            notification_type=notification_type
        )




def _role(user):
    """
    Get the user's role in uppercase.

    Example:
    HR       -> HR
    Manager  -> MANAGER
    Employee -> EMPLOYEE
    """
    return getattr(user, 'role', '').upper()


def _employee_for_user(user):
    """
    Find the employee profile connected to the logged-in user.

    First we check the user relationship.
    If that does not exist, we try to find the profile using email.
    """

    employee = employee_model.objects.filter(user=user).first()

    if employee:
        return employee

    employee = employee_model.objects.filter(
        email__iexact=user.email
    ).first()

    if employee:
        employee.user = user
        employee.save(update_fields=['user'])

    return employee


def _allowed_attendance(user):
    """
    Return the attendance records the logged-in user
    is allowed to see.

    HR:
        Can see everyone's attendance.

    Manager:
        Can see their own attendance and their team's attendance.

    Employee:
        Can see only their own attendance.
    """

    role = _role(user)

    attendance = Attendance.objects.select_related(
        'employee',
        'employee__department',
    )

    # HR can see all attendance records.
    if role == 'HR':
        return attendance

    # Manager can see:
    # 1. Their own attendance
    # 2. Their team's attendance
    if role == 'MANAGER':

        manager = _employee_for_user(user)

        if not manager:
            return attendance.none()

        return attendance.filter(
            Q(employee=manager) |
            Q(employee__teams__manager=manager)
        ).distinct()

    # Employee can see only their own attendance.
    if role == 'EMPLOYEE':

        employee = _employee_for_user(user)

        if not employee:
            return attendance.none()

        return attendance.filter(
            employee=employee
        )

    # Unknown roles cannot see attendance.
    return attendance.none()


def _role_redirect(user):
    """
    Send the user back to the correct dashboard
    when they do not have permission for an action.
    """

    role = _role(user)

    if role == 'HR':
        return redirect('home')

    if role == 'MANAGER':
        return redirect('manager_dashboard')

    return redirect('employee_dashboard')


@login_required
def attendance_list(request):
    """
    Display attendance according to the user's role.

    Features:
    - Search by employee name or email
    - Filter by status
    - Filter by date
    - Pagination
    """

    # Get attendance records allowed for the logged-in user.
    attendances = _allowed_attendance(request.user)

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------

    search_query = request.GET.get('search', '').strip()

    if search_query:
        attendances = attendances.filter(
            Q(employee__name__icontains=search_query) |
            Q(employee__email__icontains=search_query)
        )

    # ---------------------------------------------------------
    # STATUS FILTER
    # ---------------------------------------------------------

    status_filter = request.GET.get('status', '').strip()

    if status_filter:
        attendances = attendances.filter(
            status=status_filter
        )

    # ---------------------------------------------------------
    # DATE FILTER
    # ---------------------------------------------------------

    date_filter = request.GET.get('date', '').strip()

    if date_filter:
        attendances = attendances.filter(
            date=date_filter
        )

    # ---------------------------------------------------------
    # ORDERING
    # ---------------------------------------------------------

    attendances = attendances.order_by(
        '-date',
        'employee__name'
    )

    # ---------------------------------------------------------
    # PAGINATION
    # ---------------------------------------------------------

    paginator = Paginator(
        attendances,
        10
    )

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    # ---------------------------------------------------------
    # TODAY'S ATTENDANCE
    # ---------------------------------------------------------

    employee = _employee_for_user(request.user)

    today_record = None

    if employee:
        today_record = Attendance.objects.filter(
            employee=employee,
            date=timezone.localdate()
        ).first()

    return render(
        request,
        'attendance/attendance_list.html',
        {
            'attendances': page_obj,
            'page_obj': page_obj,

            'search_query': search_query,
            'status_filter': status_filter,
            'date_filter': date_filter,

            'today_record': today_record,
        }
    )

@login_required
def check_in(request):
    """
    Check in the currently logged-in user.

    HR, Manager and Employee can all check in.
    """

    if request.method != 'POST':
        return redirect('attendance_list')

    employee = _employee_for_user(request.user)

    if not employee:
        messages.error(
            request,
            'Employee profile not found.'
        )
        return _role_redirect(request.user)

    today = timezone.localdate()

    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=today,
        defaults={
            'status': 'Present',
            'check_in': timezone.localtime().time(),
        },
    )

    if created:

        messages.success(
            request,
            'Check-in successful.'
        )


    elif attendance.check_in:

        messages.warning(
            request,
            'You have already checked in today.'
        )

    else:

        attendance.check_in = timezone.localtime().time()
        attendance.status = 'Present'

        attendance.save(
            update_fields=[
                'check_in',
                'status',
                'updated_at',
            ]
        )

        messages.success(
            request,
            'Check-in successful.'
        )

        _notify_manager(
                employee,
                f'{employee.name} checked in at '
                f'{timezone.localtime().strftime("%I:%M %p")}',
                'CHECK_IN'
            )

    return redirect('attendance_list')


@login_required
def check_out(request):
    """
    Check out the currently logged-in user.

    HR, Manager and Employee can all check out.
    """

    if request.method != 'POST':
        return redirect('attendance_list')

    employee = _employee_for_user(request.user)

    if not employee:
        messages.error(
            request,
            'Employee profile not found.'
        )
        return _role_redirect(request.user)

    attendance = Attendance.objects.filter(
        employee=employee,
        date=timezone.localdate(),
    ).first()

    if not attendance:

        messages.error(
            request,
            'Please check in first.'
        )

    elif not attendance.check_in:

        messages.error(
            request,
            'Please check in first.'
        )

    elif attendance.check_out:

        messages.warning(
            request,
            'You have already checked out today.'
        )

    else:

        attendance.check_out = timezone.localtime().time()

        attendance.save(
            update_fields=[
                'check_out',
                'updated_at',
            ]
        )

        messages.success(
            request,
            'Check-out successful.'
        )

        _notify_manager(
            employee,
            f'{employee.name} checked out at '
            f'{timezone.localtime().strftime("%I:%M %p")}',
            'CHECK_OUT'
        )

    return redirect('attendance_list')


@login_required
def mark_attendance(request):
    """
    HR can manually create attendance records.
    """

    if _role(request.user) != 'HR':
        messages.error(
            request,
            'Only HR can manually mark attendance.'
        )
        return _role_redirect(request.user)

    if request.method == 'POST':

        form = AttendanceForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Attendance marked successfully.'
            )

            return redirect('attendance_list')

    else:

        form = AttendanceForm()

    return render(
        request,
        'attendance/mark_attendance.html',
        {
            'form': form,
            'title': 'Mark Attendance',
        },
    )


@login_required
def edit_attendance(request, id):
    """
    Only HR can edit attendance records.
    """

    if _role(request.user) != 'HR':
        messages.error(
            request,
            'Only HR can edit attendance.'
        )
        return _role_redirect(request.user)

    attendance = get_object_or_404(
        Attendance,
        id=id,
    )

    if request.method == 'POST':

        form = AttendanceForm(
            request.POST,
            instance=attendance,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Attendance updated successfully.'
            )

            return redirect('attendance_list')

    else:

        form = AttendanceForm(
            instance=attendance
        )

    return render(
        request,
        'attendance/mark_attendance.html',
        {
            'form': form,
            'attendance': attendance,
            'title': 'Edit Attendance',
        },
    )


@login_required
def delete_attendance(request, id):
    """
    Only HR can delete attendance records.
    """

    if _role(request.user) != 'HR':
        messages.error(
            request,
            'Only HR can delete attendance.'
        )
        return _role_redirect(request.user)

    attendance = get_object_or_404(
        Attendance,
        id=id,
    )

    if request.method == 'POST':

        attendance.delete()

        messages.success(
            request,
            'Attendance deleted successfully.'
        )

        return redirect('attendance_list')

    return render(
        request,
        'attendance/delete_attendance.html',
        {
            'attendance': attendance
        },
    )
