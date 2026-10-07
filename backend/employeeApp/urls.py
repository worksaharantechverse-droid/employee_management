from django.contrib import admin
from django.urls import path, include
from employeeApp import views


urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('employee_list/', views.employee_list, name= 'employee_list'),
    path('add_employee/', views.add_employee, name='add_employee'),
    path('employee/<int:pk>/edit', views.employee_edit, name = 'employee_edit'),
    path('employee/<int:pk>/', views.view_employee, name='view_employee'),
    path('employee/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path("hr/teams/", views.hr_teams, name="hr_teams"),

]
