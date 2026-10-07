from django.urls import path
from .views import *
urlpatterns = [
 path("auth/register/", RegisterAPIView.as_view()),     path("auth/login/", LoginAPIView.as_view()), path("auth/firebase/", FirebaseLoginAPIView.as_view()), 
 path("departments/", DepartmentAPIView.as_view()),     path("departments/<int:pk>/", DepartmentAPIView.as_view()),
 path("employees/", EmployeeAPIView.as_view()),         path("employees/<int:pk>/", EmployeeAPIView.as_view()),
 path("teams/", TeamAPIView.as_view()),                 path("teams/<int:pk>/", TeamAPIView.as_view()),
 path("teams/<int:pk>/members/", TeamMemberAPIView.as_view()),
 path("teams/<int:pk>/members/<int:employee_id>/", TeamMemberAPIView.as_view()),
 path("attendance/", AttendanceAPIView.as_view()),      path("attendance/<int:pk>/", AttendanceAPIView.as_view()),
 path("leaves/", LeaveRequestAPIView.as_view()),        path("leaves/<int:pk>/", LeaveRequestAPIView.as_view()),
 path("notifications/", NotificationAPIView.as_view()), path("notifications/<int:pk>/", NotificationAPIView.as_view()),
 path("dashboard/hr/", HRDashboardAPIView.as_view()),
]