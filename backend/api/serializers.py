from rest_framework import serializers
from django.contrib.auth import get_user_model
from employeeApp.models import department_model, employee_model, team_model
from attendance.models import Attendance
from leave.models import LeaveRequest
from notification.models import Notification

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ["email", "name", "password", "city"]
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data, role="EMPLOYEE", is_active=True)
        employee_model.objects.get_or_create(user=user, defaults={"name": user.name, "email": user.email, "role":"EMPLOYEE"})
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","email","name","city","role"]

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = department_model
        fields = "__all__"
        read_only_fields = ["id","created_at"]

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = employee_model
        fields = "__all__"
        read_only_fields = ["id","created_at","user"]
    def validate_manager(self, value):
        if value and value.role != "MANAGER":
            raise serializers.ValidationError("Selected manager must have MANAGER role.")
        return value

    def validate(self, attrs):
        manager = attrs.get("manager", getattr(self.instance, "manager", None))
        employee_role = attrs.get("role", getattr(self.instance, "role", None))
        if manager and manager.role != "MANAGER":
            raise serializers.ValidationError({"manager": "Selected manager must have MANAGER role."})
        if manager and self.instance and manager.pk == self.instance.pk:
            raise serializers.ValidationError({"manager": "An employee cannot be their own manager."})
        return attrs

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = team_model
        fields = "__all__"
        # manager is always the logged-in MANAGER (set in the view), same
        # as manager.views.create_team never lets the form pick a manager.
        read_only_fields = ["id","created_at","manager"]

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    class Meta:
        model = Attendance
        fields = "__all__"
        read_only_fields = ["id","created_at","updated_at"]

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    class Meta:
        model = LeaveRequest
        fields = ["id","employee","employee_name","manager","start_date","end_date","reason","status","manager_comment","applied_at","reviewed_at","total_days"]
        read_only_fields = ["id","employee","employee_name","manager","status","applied_at","reviewed_at","total_days"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source="recipient.name", read_only=True)
    class Meta:
        model = Notification
        fields = ["id","recipient","recipient_name","message","notification_type","is_read","created_at"]
        read_only_fields = ["id","recipient","recipient_name","created_at"]
