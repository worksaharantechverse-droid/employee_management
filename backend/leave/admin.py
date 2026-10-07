from django.contrib import admin
from .models import LeaveRequest


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'manager', 'start_date', 'end_date', 'status', 'applied_at', 'reviewed_at')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('employee__name', 'employee__email', 'manager__name', 'manager__email')
