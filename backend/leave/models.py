from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from employeeApp.models import employee_model


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(
        employee_model,
        on_delete=models.CASCADE,
        related_name='leave_requests',
    )
    manager = models.ForeignKey(
        employee_model,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leave_requests_to_review',
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
    )
    manager_comment = models.TextField(blank=True, default='')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_at']

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date.')
        if self.employee_id and self.manager_id and self.employee_id == self.manager_id:
            raise ValidationError('Employee and manager cannot be the same person.')

    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f'{self.employee.name} - {self.start_date} to {self.end_date} - {self.status}'
