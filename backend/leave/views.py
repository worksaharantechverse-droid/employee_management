from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from notification.models import Notification
from notification.views import create_notification

from employeeApp.models import employee_model
from .forms import LeaveRequestForm
from .models import LeaveRequest


def _role(user):
    return getattr(user, 'role', '').upper()


def _employee_for_user(user):
    profile = employee_model.objects.filter(user=user).first()
    if profile:
        return profile
    profile = employee_model.objects.filter(email__iexact=user.email).first()
    if profile:
        profile.user = user
        profile.save(update_fields=['user'])
    return profile


def _role_redirect(user):
    role = _role(user)
    if role == 'HR':
        return redirect('home')
    if role == 'MANAGER':
        return redirect('manager_dashboard')
    return redirect('employee_dashboard')


@login_required
def leave_list(request):
    """
    Display leave requests according to the user's role.

    HR:
        Can see all leave requests.

    Manager:
        Can see leave requests from their team.

    Employee:
        Can see only their own leave requests.

    Features:
        - Search by employee name or email
        - Filter by status
        - Filter by start date
        - Pagination
    """

    role = getattr(request.user, 'role', '').upper()

    # ---------------------------------------------------------
    # BASE QUERY
    # ---------------------------------------------------------

    leave_requests = LeaveRequest.objects.select_related(
        'employee',
        'manager',
    )

    # ---------------------------------------------------------
    # ROLE-BASED ACCESS
    # ---------------------------------------------------------

    if role == 'HR':

        # HR can see all leave requests.
        leave_requests = leave_requests.all()

    elif role == 'MANAGER':

        manager = _employee_for_user(request.user)

        if not manager:
            leave_requests = leave_requests.none()
        else:
            # Manager can see only requests
            # belonging to their team.
            leave_requests = leave_requests.filter(
                manager=manager
            )

    elif role == 'EMPLOYEE':

        employee = employee_model.objects.filter(
            user=request.user
        ).first()

        if not employee:
            employee = employee_model.objects.filter(
                email__iexact=request.user.email
            ).first()

        if not employee:
            leave_requests = leave_requests.none()
        else:
            # Employee can see only their own requests.
            leave_requests = leave_requests.filter(
                employee=employee
            )

    else:

        leave_requests = leave_requests.none()

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------

    search_query = request.GET.get(
        'search',
        ''
    ).strip()

    if search_query:

        leave_requests = leave_requests.filter(
            Q(employee__name__icontains=search_query)
            |
            Q(employee__email__icontains=search_query)
        )

    # ---------------------------------------------------------
    # STATUS FILTER
    # ---------------------------------------------------------

    status_filter = request.GET.get(
        'status',
        ''
    ).strip()

    if status_filter:

        leave_requests = leave_requests.filter(
            status=status_filter
        )

    # ---------------------------------------------------------
    # DATE FILTER
    # ---------------------------------------------------------

    date_filter = request.GET.get(
        'date',
        ''
    ).strip()

    if date_filter:

        leave_requests = leave_requests.filter(
            start_date=date_filter
        )

    # ---------------------------------------------------------
    # ORDERING
    # ---------------------------------------------------------

    leave_requests = leave_requests.order_by(
        '-start_date',
        '-id'
    )

    # ---------------------------------------------------------
    # PAGINATION
    # ---------------------------------------------------------

    paginator = Paginator(
        leave_requests,
        10
    )

    page_number = request.GET.get(
        'page'
    )

    page_obj = paginator.get_page(
        page_number
    )

    # ---------------------------------------------------------
    # RENDER PAGE
    # ---------------------------------------------------------

    return render(
        request,
        'leave/leave_list.html',
        {
            'leave_requests': page_obj,
            'page_obj': page_obj,

            'search_query': search_query,
            'status_filter': status_filter,
            'date_filter': date_filter,
        }
    )

@login_required
def request_leave(request):
    if _role(request.user) != 'EMPLOYEE':
        messages.error(request, 'Only employees can submit leave requests.')
        return _role_redirect(request.user)

    employee = _employee_for_user(request.user)
    if not employee:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')

    manager = employee.manager
    if not manager:
        messages.error(request, 'You do not have a manager assigned yet. Please contact HR or your team manager.')
        return redirect('leave_list')

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data['start_date']
            end = form.cleaned_data['end_date']

            overlapping = LeaveRequest.objects.filter(
                employee=employee,
                status__in=['PENDING', 'APPROVED'],
                start_date__lte=end,
                end_date__gte=start,
            ).exists()
            if overlapping:
                form.add_error(None, 'You already have a pending or approved leave overlapping these dates.')
            else:
                leave_request = form.save(commit=False)
                leave_request.employee = employee
                leave_request.manager = manager
                leave_request.status = 'PENDING'
                leave_request.save()

                # Notify the manager
                create_notification(
                    recipient=manager,
                    message=(
                        f'{employee.name} submitted a leave request '
                        f'from {start} to {end}.'
                    ),
                    notification_type='LEAVE_SUBMITTED'
                )

                # Notify the employee
                create_notification(
                    recipient=employee,
                    message=(
                        f'Your leave request has been sent to '
                        f'{manager.name}.'
                    ),
                    notification_type='LEAVE_SUBMITTED'
                )

                messages.success(request, f'Leave request sent to {manager.name}.')
                return redirect('leave_list')
    else:
        form = LeaveRequestForm()

    return render(
        request,
        'leave/request_leave.html',
        {'form': form, 'manager': manager},
    )


@login_required
def approve_leave(request, leave_id):
    if _role(request.user) != 'MANAGER':
        messages.error(request, 'Only the respective manager can approve leave requests.')
        return _role_redirect(request.user)

    manager = _employee_for_user(request.user)
    leave_request = get_object_or_404(
        LeaveRequest.objects.select_related('employee', 'manager'),
        id=leave_id,
        manager=manager,
    )

    if request.method != 'POST':
        return redirect('leave_list')

    if leave_request.status != 'PENDING':
        messages.warning(request, 'This leave request has already been reviewed.')
        return redirect('leave_list')

    leave_request.status = 'APPROVED'
    leave_request.reviewed_at = timezone.now()
    leave_request.manager_comment = request.POST.get('manager_comment', '').strip()
    leave_request.save(update_fields=['status', 'reviewed_at', 'manager_comment'])

    # Notify the employee
    create_notification(
        recipient=leave_request.employee,
        message=(
            f'{manager.name} approved your leave request '
            f'from {leave_request.start_date} '
            f'to {leave_request.end_date}.'
        ),
        notification_type='LEAVE_APPROVED'
    )

    # Notify the manager
    create_notification(
        recipient=manager,
        message=(
            f'You approved the leave request of '
            f'{leave_request.employee.name}.'
        ),
        notification_type='LEAVE_APPROVED'
    )

    messages.success(request, f'Leave request from {leave_request.employee.name} approved.')
    return redirect('leave_list')


@login_required
def reject_leave(request, leave_id):
    if _role(request.user) != 'MANAGER':
        messages.error(request, 'Only the respective manager can reject leave requests.')
        return _role_redirect(request.user)

    manager = _employee_for_user(request.user)
    leave_request = get_object_or_404(
        LeaveRequest.objects.select_related('employee', 'manager'),
        id=leave_id,
        manager=manager,
    )

    if request.method != 'POST':
        return redirect('leave_list')

    if leave_request.status != 'PENDING':
        messages.warning(request, 'This leave request has already been reviewed.')
        return redirect('leave_list')

    leave_request.status = 'REJECTED'
    leave_request.reviewed_at = timezone.now()
    leave_request.manager_comment = request.POST.get('manager_comment', '').strip()
    leave_request.save(update_fields=['status', 'reviewed_at', 'manager_comment'])

    
    # Notify the employee
    create_notification(
        recipient=leave_request.employee,
        message=(
            f'{manager.name} rejected your leave request '
            f'from {leave_request.start_date} '
            f'to {leave_request.end_date}.'
        ),
        notification_type='LEAVE_REJECTED'
    )

    # Notify the manager
    create_notification(
        recipient=manager,
        message=(
            f'You rejected the leave request of '
            f'{leave_request.employee.name}.'
        ),
        notification_type='LEAVE_REJECTED'
    )


    messages.success(request, f'Leave request from {leave_request.employee.name} rejected.')
    return redirect('leave_list')
