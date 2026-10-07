from django.urls import path
from . import views

urlpatterns = [
    path('employee_dashboard/', views.employee_dashboard, name='employee_dashboard'),
]
