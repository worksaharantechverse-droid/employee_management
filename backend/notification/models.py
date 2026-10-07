from django.db import models
from employeeApp.models import employee_model
# Create your models here.

class Notification(models.Model):
    """
    Stores notifications for employees, managers and HR.
    """

    recipient = models.ForeignKey(
        employee_model,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.CharField(
        max_length=255
    )

    notification_type = models.CharField(
        max_length=50
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.name} - {self.message}"
