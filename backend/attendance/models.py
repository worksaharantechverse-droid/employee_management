from django.db import models
from employeeApp.models import employee_model


class Attendance(models.Model):

    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Half Day', 'Half Day'),
        ('Leave', 'Leave'),
    ]

    employee = models.ForeignKey(employee_model,on_delete=models.CASCADE,related_name='attendances')

    date = models.DateField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    check_in = models.TimeField(null=True,blank=True)

    check_out = models.TimeField(null=True,blank=True)

    remarks = models.TextField(null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'date'],
                name='unique_employee_attendance'
            )
        ]

    def __str__(self):
        return f"{self.employee.name} - {self.date} - {self.status}"
