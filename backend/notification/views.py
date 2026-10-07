from django.shortcuts import render, redirect
from .models import Notification
# Create your views here.

def create_notification(
    recipient,
    message,
    notification_type
):
    """
    Create a notification for a user.
    """

    if not recipient:
        return

    Notification.objects.create(
        recipient=recipient,
        message=message,
        notification_type=notification_type
    )

