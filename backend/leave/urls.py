from django.urls import path
from . import views

urlpatterns = [
    path('', views.leave_list, name='leave_list'),
    path('request/', views.request_leave, name='request_leave'),
    path('<int:leave_id>/approve/', views.approve_leave, name='approve_leave'),
    path('<int:leave_id>/reject/', views.reject_leave, name='reject_leave'),
]
