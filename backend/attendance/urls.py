from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_list, name='attendance_list'),
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/', views.check_out, name='check_out'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('edit/<int:id>/', views.edit_attendance, name='edit_attendance'),
    path('delete/<int:id>/', views.delete_attendance, name='delete_attendance'),
]
