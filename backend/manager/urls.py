from django.urls import path
from . import views

urlpatterns = [
    path('manager_dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('team/', views.manager_team, name='manager_team'),
    path('team/create/', views.create_team, name='create_team'),
    path('team/<int:team_id>/add-member/', views.add_team_member, name='add_team_member'),
    path('team/<int:team_id>/remove-member/<int:employee_id>/', views.remove_team_member, name='remove_team_member'),
]
